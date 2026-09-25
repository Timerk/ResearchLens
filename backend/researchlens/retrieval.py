import json
from pathlib import Path

from pydantic import TypeAdapter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from researchlens.models import Passage, SearchHit


class Retriever:
    """Lexical preview using word TF-IDF and cosine similarity.

    A positive score indicates word overlap, not sufficient evidence to answer.
    Refit deterministically from the saved passages when the server starts.
    """

    def __init__(self, passages: list[Passage]) -> None:
        self.passages = passages
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform([passage.text for passage in passages])

    @classmethod
    def from_path(cls, path: Path) -> "Retriever":
        artifact = json.loads(path.read_text(encoding="utf-8"))
        if artifact["schema_version"] != 1:
            raise ValueError("Unsupported index schema; rebuild the index")
        return cls(TypeAdapter(list[Passage]).validate_python(artifact["passages"]))

    def search(self, question: str, limit: int = 4) -> list[SearchHit]:
        if limit < 1:
            raise ValueError("limit must be positive")
        query = self.vectorizer.transform([question])
        scores = cosine_similarity(query, self.matrix).ravel()
        ranked = sorted(range(len(scores)), key=lambda index: (-scores[index], index))
        return [
            SearchHit(**self.passages[index].model_dump(), score=float(scores[index]))
            for index in ranked[:limit]
            if scores[index] > 0
        ]
