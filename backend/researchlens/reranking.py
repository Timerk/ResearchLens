"""Pinned local pair scoring and optional redundancy reduction, loaded once."""

import argparse
import hashlib

import numpy as np

from researchlens.embedding_models import package_version
from researchlens.models import SearchHit

MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"
REVISION = "233902d25c440f23af6f7d6e94d2946bac0bee0a"


def reranker_metadata() -> dict:
    return {
        "model": MODEL,
        "revision": REVISION,
        "runtime": "onnxruntime",
        "runtime_version": package_version("onnxruntime"),
        "device": "cpu",
        "precision": "float32",
        "quantization": "none",
        "weights": "onnx/model.onnx",
        "tokenizer": "tokenizer.json",
        "max_tokens": 512,
        "truncation": "longest-first",
        "batch_size": 8,
        "intra_op_threads": 2,
        "inter_op_threads": 1,
        "pair_order": "question-passage",
        "score": "raw-relevance-logit",
    }


class LocalReranker:
    """MS MARCO English MiniLM cross-encoder; logits are not answerability probabilities."""

    def __init__(self, *, download: bool = False) -> None:
        self.metadata = reranker_metadata()
        try:
            import onnxruntime as ort
            from huggingface_hub import hf_hub_download
            from tokenizers import Tokenizer
        except ImportError:
            raise ValueError(
                "Local reranking requires uv sync --locked --extra embeddings"
            ) from None
        try:
            paths = {
                key: hf_hub_download(
                    repo_id=MODEL,
                    revision=REVISION,
                    filename=self.metadata[key],
                    token=False,
                    local_files_only=not download,
                )
                for key in ("weights", "tokenizer")
            }
            self.tokenizer = Tokenizer.from_file(paths["tokenizer"])
            self.tokenizer.enable_truncation(max_length=512, strategy="longest_first")
            self.tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
            self.full_tokenizer = Tokenizer.from_str(self.tokenizer.to_str())
            self.full_tokenizer.no_truncation()
            self.full_tokenizer.no_padding()
            options = ort.SessionOptions()
            options.intra_op_num_threads = 2
            options.inter_op_num_threads = 1
            self.session = ort.InferenceSession(
                paths["weights"],
                sess_options=options,
                providers=["CPUExecutionProvider"],
            )
            self.input_names = {item.name for item in self.session.get_inputs()}
        except Exception:
            raise ValueError(
                "Pinned reranker is unavailable or invalid. Install the embeddings extra and "
                "explicitly download with: python -m researchlens.reranking --download. "
                "Startup and evaluation are cache-only."
            ) from None
        self.last_diagnostics: list[dict] = []

    def score(self, question: str, passages: list[SearchHit]) -> np.ndarray:
        scores = []
        diagnostics = []
        for start in range(0, len(passages), self.metadata["batch_size"]):
            batch = passages[start : start + self.metadata["batch_size"]]
            pairs = [(question, passage.text) for passage in batch]
            encoded = self.tokenizer.encode_batch(pairs)
            inputs = {
                "input_ids": np.asarray([item.ids for item in encoded], dtype=np.int64),
                "attention_mask": np.asarray(
                    [item.attention_mask for item in encoded], dtype=np.int64
                ),
                "token_type_ids": np.asarray([item.type_ids for item in encoded], dtype=np.int64),
            }
            logits = np.asarray(
                self.session.run(
                    None,
                    {key: value for key, value in inputs.items() if key in self.input_names},
                )[0]
            ).reshape(-1)
            if logits.shape != (len(batch),) or not np.isfinite(logits).all():
                raise ValueError("Reranker returned invalid relevance logits")
            scores.extend(logits.tolist())
            for passage, retained, pair in zip(batch, encoded, pairs, strict=True):
                original = self.full_tokenizer.encode(*pair)
                end = max(
                    (
                        offset[1]
                        for offset, sequence in zip(
                            retained.offsets,
                            retained.sequence_ids,
                            strict=True,
                        )
                        if sequence == 1
                    ),
                    default=0,
                )
                total = len(original.ids)
                used = sum(retained.attention_mask)
                if total == used:
                    end = len(passage.text)
                diagnostics.append(
                    {
                        "passage_id": passage.id,
                        "text_sha256": hashlib.sha256(passage.text.encode()).hexdigest(),
                        "input_tokens": total,
                        "encoded_tokens": used,
                        "truncated": end < len(passage.text),
                        "retained_ranges": [{"start": 0, "end": end}] if end else [],
                    }
                )
        self.last_diagnostics = diagnostics
        return np.asarray(scores, dtype=np.float32)


class RerankedRetriever:
    """Rerank a fixed candidate pool, optionally penalizing dense passage redundancy."""

    def __init__(self, base, reranker, *, candidates: int = 40, diversity: float = 0.0) -> None:
        if not 1 <= candidates <= 100 or not np.isfinite(diversity) or not 0 <= diversity <= 1:
            raise ValueError("Reranking needs 1..100 candidates and diversity within 0..1")
        self.base, self.reranker = base, reranker
        self.candidates, self.diversity = candidates, diversity
        self.passages = base.passages
        self.retrieval_settings = getattr(base, "retrieval_settings", {})
        self.reranking_settings = {
            **reranker.metadata,
            "candidates": candidates,
            "diversity": diversity,
        }
        self._last_question_hash = None
        self._last_pair_diagnostics: list[dict] = []
        self.embeddings = getattr(base, "embeddings", base)
        self.positions = {passage.id: i for i, passage in enumerate(self.passages)}
        if diversity and not hasattr(self.embeddings, "matrix"):
            raise ValueError("Diversity selection requires the saved dense vectors")

    def get_encoding_diagnostics(self) -> dict | None:
        hook = getattr(self.base, "get_encoding_diagnostics", None)
        return hook() if callable(hook) else None

    def get_reranking_diagnostics(self, question: str) -> list[dict]:
        return (
            self._last_pair_diagnostics
            if self._last_question_hash == hashlib.sha256(question.encode()).hexdigest()
            else []
        )

    def search(self, question: str, limit: int = 4) -> list[SearchHit]:
        if not 1 <= limit <= self.candidates:
            raise ValueError("Search limit must be within the reranking candidate count")
        hits = self.base.search(question, self.candidates)
        if not hits:
            return []
        scores = np.asarray(self.reranker.score(question, hits))
        if scores.shape != (len(hits),) or not np.isfinite(scores).all():
            raise ValueError("Reranker returned invalid relevance logits")
        ranked = sorted(range(len(hits)), key=lambda i: (-scores[i], self.positions[hits[i].id]))
        if self.diversity:
            # Rank utility avoids treating logits as calibrated relevance probabilities.
            utility = {i: 1 - rank / len(hits) for rank, i in enumerate(ranked)}
            matrix = self.embeddings.matrix[[self.positions[hit.id] for hit in hits]]
            similarity = np.clip(matrix @ matrix.T, 0, 1)
            selected = [ranked.pop(0)]
            while ranked:
                chosen = min(
                    ranked,
                    key=lambda i: (
                        -(
                            (1 - self.diversity) * utility[i]
                            - self.diversity * max(similarity[i, j] for j in selected)
                        ),
                        self.positions[hits[i].id],
                    ),
                )
                selected.append(chosen)
                ranked.remove(chosen)
            ranked = selected
        self._last_question_hash = hashlib.sha256(question.encode()).hexdigest()
        self._last_pair_diagnostics = self.reranker.last_diagnostics
        return [hits[i].model_copy(update={"score": float(scores[i])}) for i in ranked[:limit]]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--download", action="store_true", help="Explicitly allow pinned weight download"
    )
    args = parser.parse_args()
    LocalReranker(download=args.download)
    print("Pinned local CPU reranker is ready")


if __name__ == "__main__":
    main()
