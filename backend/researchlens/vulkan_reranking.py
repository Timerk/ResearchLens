"""Evaluation-only, pinned llama.cpp reranking on the RX 6800; no remote service."""

import hashlib
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import numpy as np

from researchlens.evaluation_schema import VulkanRerankerConfig

RUNTIME_TAG = "b11327"
RUNTIME_COMMIT = "552f18f912a32ea86edf82e2b76431cb7131538d"
SERVER_SHA256 = "32d43779061d318ab36d0cf8156f314f81ac7e5b805298b7fe9facf3cf0cc82d"
MODELS = {
    "bge": ("BAAI/bge-reranker-v2-m3", "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"),
    "qwen": ("Qwen/Qwen3-Reranker-0.6B", "e61197ed45024b0ed8a2d74b80b4d909f1255473"),
}
PREFIX = (
    "<|im_start|>system\nJudge whether the Document meets the requirements based on the Query "
    'and the Instruct provided. Note that the answer can only be "yes" or "no".'
    "<|im_end|>\n<|im_start|>user\n"
)
INSTRUCTION = "Given a web search query, retrieve relevant passages that answer the query"
SUFFIX = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
QWEN_TEMPLATE = (
    PREFIX + f"<Instruct>: {INSTRUCTION}\n<Query>: {{query}}\n<Document>: {{document}}" + SUFFIX
)
BGE_TEMPLATE = "<s>{query}</s></s>{document}</s>"
SERVER_PRIVATE_LIMIT_BYTES = 6 * 1024**3


def server_memory(process) -> dict[str, int]:
    """Native Windows counters for the owned server, separate from Python and VRAM."""
    if sys.platform != "win32":
        raise ValueError("Vulkan memory monitoring requires the verified Windows runtime")
    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
            (name, ctypes.c_size_t)
            for name in (
                "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
                "PagefileUsage", "PeakPagefileUsage", "PrivateUsage",
            )
        ]

    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD,
    ]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(int(process._handle), ctypes.byref(counters), counters.cb):
        raise ValueError("Cannot measure local server memory; stop and inspect the process")
    return {
        "rss_bytes": counters.WorkingSetSize,
        "private_bytes": counters.PrivateUsage,
        "peak_rss_bytes": counters.PeakWorkingSetSize,
        "peak_private_bytes": counters.PeakPagefileUsage,
    }


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def metadata(root: Path, alias: str, *, device: str = "Vulkan0") -> dict:
    """Bind both executable and locally converted weights before inference."""
    if alias not in MODELS or device != "Vulkan0":
        raise ValueError("Choose bge or qwen on the verified Vulkan0 RX 6800 adapter")
    runtime = json.loads((root / "runtime.json").read_text(encoding="utf-8"))
    models = json.loads((root / "models.json").read_text(encoding="utf-8"))
    model, revision = MODELS[alias]
    binary_hash = file_sha256(root / "bin/llama-server.exe")
    if (
        runtime["tag"] != RUNTIME_TAG
        or runtime["commit"] != RUNTIME_COMMIT
        or binary_hash != SERVER_SHA256
        or (models[alias]["model"], models[alias]["revision"]) != (model, revision)
    ):
        raise ValueError("Vulkan assets are incompatible; prepare the pinned runtime and models")
    return VulkanRerankerConfig(
        model=model,
        revision=revision,
        runtime="llama.cpp",
        runtime_version=RUNTIME_TAG,
        device=device,
        precision="float16",
        quantization="none",
        weights=f"{alias}-f16.gguf",
        tokenizer="pinned-Hugging-Face-tokenizer",
        max_tokens=511,
        truncation="reject-overflow",
        batch_size=4,
        intra_op_threads=8,
        inter_op_threads=1,
        pair_order="question-passage",
        score="raw-relevance-logit" if alias == "bge" else "yes-no-softmax",
        weights_sha256=file_sha256(root / f"{alias}-f16.gguf"),
        runtime_binary_sha256=binary_hash,
        runtime_commit=RUNTIME_COMMIT,
        device_name="AMD Radeon RX 6800",
        context_tokens=2048,
        batch_tokens=2048,
        gpu_layers=99,
        prompt_cache_ram_mib=0,
        server_private_limit_bytes=SERVER_PRIVATE_LIMIT_BYTES,
        prompt_template_sha256=hashlib.sha256(
            (BGE_TEMPLATE if alias == "bge" else QWEN_TEMPLATE).encode()
        ).hexdigest(),
    ).model_dump(exclude={"candidates", "diversity"})


def restore_scores(response: dict, count: int, expected_tokens: int) -> np.ndarray:
    """Restore candidate order; reject missing, duplicate, nonfinite or clipped results."""
    try:
        items = response["results"]
        if len(items) != count or response["usage"]["total_tokens"] != expected_tokens:
            raise ValueError
        scores = np.empty(count, dtype=np.float32)
        indexes = set()
        for item in items:
            index = item["index"]
            if type(index) is not int or not 0 <= index < count or index in indexes:
                raise ValueError
            indexes.add(index)
            scores[index] = item["relevance_score"]
        if not np.isfinite(scores).all():
            raise ValueError
        return scores
    except (KeyError, TypeError, ValueError, OverflowError):
        raise ValueError(
            "Local reranker returned invalid scores or unexpected token counts"
        ) from None


class VulkanReranker:
    """Own one hidden loopback server; reject overflow rather than silently clipping evidence."""

    def __init__(self, root: Path, alias: str, log: Path) -> None:
        self.metadata = metadata(root, alias)
        self.alias = alias
        self.root = root.resolve()
        self.log_path = log
        self.process = None
        self.client = None
        self.log = None
        self.last_diagnostics = []
        self._last_key = None
        self._last_tokens = []
        self.memory_samples = []
        from transformers import AutoTokenizer

        models = json.loads((root / "models.json").read_text(encoding="utf-8"))
        self.tokenizer = AutoTokenizer.from_pretrained(
            models[alias]["source"], local_files_only=True, trust_remote_code=False
        )

    def __enter__(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        self.client = httpx.Client(
            base_url=f"http://127.0.0.1:{port}",
            timeout=120,
            trust_env=False,
            follow_redirects=False,
        )
        self.log = self.log_path.open("w", encoding="utf-8")
        arguments = [
            str(self.root / "bin/llama-server.exe"),
            "-m",
            str(self.root / self.metadata["weights"]),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--embedding",
            "--reranking",
            "--pooling",
            "rank",
            "--device",
            "Vulkan0",
            "-ngl",
            "99",
            "--fit",
            "off",
            "-c",
            "2048",
            "-b",
            "2048",
            "-ub",
            "2048",
            "-np",
            "4",
            "-t",
            "8",
            "-tb",
            "8",
            "-lv",
            "4",
            "--no-warmup",
            "--no-webui",
            "--cache-ram",
            "0",
        ]
        try:
            self.process = subprocess.Popen(
                arguments,
                stdout=self.log,
                stderr=self.log,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    raise ValueError("Pinned Vulkan server failed to start; inspect its local log")
                try:
                    if self.client.get("/health", timeout=1).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(0.2)
            else:
                raise ValueError("Vulkan startup timed out; inspect GPU availability and local log")
            log = self.log_path.read_text(encoding="utf-8", errors="replace")
            layers = "25/25" if self.alias == "bge" else "29/29"
            if (
                "using device Vulkan0 (AMD Radeon RX 6800)" not in log
                or f"offloaded {layers} layers to GPU" not in log
            ):
                raise ValueError("Expected RX 6800 layer offload was not confirmed in startup log")
            self.check_memory()
            return self
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.client is not None:
            self.client.close()
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=10)
        if self.log is not None:
            self.log.close()

    def __exit__(self, *_):
        self.close()

    def check_memory(self):
        sample = server_memory(self.process)
        self.memory_samples.append(sample)
        if sample["peak_private_bytes"] > SERVER_PRIVATE_LIMIT_BYTES:
            self.close()
            raise ValueError(
                "Vulkan server exceeded its 6 GiB private-memory budget and was stopped; "
                "verify --cache-ram 0 and inspect the local log before rerunning"
            )

    def pair_tokens(self, question: str, text: str) -> list[int]:
        if any(marker in question or marker in text for marker in ("{query}", "{document}")):
            raise ValueError("Input contains a reserved llama.cpp rerank template placeholder")
        if self.alias == "bge":
            return self.tokenizer(question, text, truncation=False)["input_ids"]
        prompt = QWEN_TEMPLATE.format(query=question, document=text)
        return self.tokenizer(prompt, add_special_tokens=False, truncation=False)["input_ids"]

    def score(self, question: str, passages: list) -> np.ndarray:
        if self.client is None or self.process is None or self.process.poll() is not None:
            raise ValueError("Enter the local Vulkan reranker context before scoring")
        if not passages:
            self.last_diagnostics = []
            return np.empty(0, dtype=np.float32)
        key = (question, tuple((hit.id, hit.text) for hit in passages))
        if key != self._last_key:
            counts = [len(self.pair_tokens(question, hit.text)) for hit in passages]
            if max(counts) > self.metadata["max_tokens"]:
                raise ValueError(
                    "Reranker pair exceeds 511 tokens; use an explicitly revised budget"
                )
            self._last_key, self._last_tokens = key, counts
            self.last_diagnostics = [
                {
                    "passage_id": hit.id,
                    "text_sha256": hashlib.sha256(hit.text.encode()).hexdigest(),
                    "input_tokens": count,
                    "encoded_tokens": count,
                    "truncated": False,
                    "retained_ranges": [{"start": 0, "end": len(hit.text)}],
                }
                for hit, count in zip(passages, counts, strict=True)
            ]
        try:
            self.check_memory()
            response = self.client.post(
                "/rerank",
                json={
                    "query": question,
                    "documents": [hit.text for hit in passages],
                    "top_n": len(passages),
                },
            )
            response.raise_for_status()
            self.check_memory()
            return restore_scores(response.json(), len(passages), sum(self._last_tokens))
        except (httpx.HTTPError, json.JSONDecodeError):
            raise ValueError(
                "Local Vulkan reranking failed; inspect the local server log"
            ) from None
