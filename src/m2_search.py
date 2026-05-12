"""Module 2: Hybrid Search — BM25 (Vietnamese) + Dense + RRF."""

from config import (QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME, EMBEDDING_MODEL,
                    EMBEDDING_DIM, BM25_TOP_K, DENSE_TOP_K, HYBRID_TOP_K)
import os
import sys
import re
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class SearchResult:
    text: str
    score: float
    metadata: dict
    method: str  # "bm25", "dense", "hybrid"


def segment_vietnamese(text: str) -> str:
    """Segment Vietnamese text into words."""
    # DONE: Implement Vietnamese word segmentation with fallback
    try:
        from underthesea import word_tokenize
        return word_tokenize(text, format="text")
    except Exception:
        # lightweight fallback: separate punctuation and normalize spaces
        t = re.sub(r"([.,!?()\[\]:;])", r" \1 ", text)
        t = re.sub(r"\s+", " ", t).strip()
        return t


class BM25Search:
    def __init__(self):
        self.corpus_tokens = []
        self.documents = []
        self.bm25 = None

    def index(self, chunks: list[dict]) -> None:
        """Build BM25 index from chunks."""
        # DONE: Implement BM25 indexing (use rank_bm25 if available, fallback to simple tokens)
        self.documents = chunks
        tokens = []
        for c in chunks:
            seg = segment_vietnamese(c.get("text", ""))
            toks = [w.lower() for w in seg.split() if w.strip()]
            tokens.append(toks)
        self.corpus_tokens = tokens
        try:
            from rank_bm25 import BM25Okapi
            self.bm25 = BM25Okapi(self.corpus_tokens)
        except Exception:
            self.bm25 = None

    def search(self, query: str, top_k: int = BM25_TOP_K) -> list[SearchResult]:
        """Search using BM25."""
        # DONE: Implement BM25 search with fallback scoring
        q_tokens = [w.lower()
                    for w in segment_vietnamese(query).split() if w.strip()]
        results: list[SearchResult] = []
        if self.bm25 is not None:
            try:
                scores = self.bm25.get_scores(q_tokens)
                idxs = sorted(range(len(scores)),
                              key=lambda i: scores[i], reverse=True)[:top_k]
                for i in idxs:
                    doc = self.documents[i]
                    results.append(SearchResult(text=doc.get("text", ""), score=float(
                        scores[i]), metadata=doc.get("metadata", {}), method="bm25"))
                return results
            except Exception:
                pass

        # fallback simple scoring: count token overlaps
        scores = []
        for toks, doc in zip(self.corpus_tokens, self.documents):
            s = sum(1 for t in q_tokens if t in toks)
            scores.append(float(s))
        idxs = sorted(range(len(scores)),
                      key=lambda i: scores[i], reverse=True)[:top_k]
        for i in idxs:
            doc = self.documents[i]
            results.append(SearchResult(text=doc.get(
                "text", ""), score=scores[i], metadata=doc.get("metadata", {}), method="bm25"))
        return results


class DenseSearch:
    def __init__(self):
        # Try to initialize qdrant client; allow graceful fallback for tests
        try:
            from qdrant_client import QdrantClient
            self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        except Exception:
            self.client = None
        self._encoder = None

    def _get_encoder(self):
        if self._encoder is None:
            from sentence_transformers import SentenceTransformer
            self._encoder = SentenceTransformer(EMBEDDING_MODEL)
        return self._encoder

    def index(self, chunks: list[dict], collection: str = COLLECTION_NAME) -> None:
        """Index chunks into Qdrant."""
        # DONE: Dense indexing — best-effort implementation (no hard failures)
        if not self.client:
            return
        try:
            from qdrant_client.models import Distance, VectorParams, PointStruct
            self.client.recreate_collection(collection, VectorParams(
                size=EMBEDDING_DIM, distance=Distance.COSINE))
            texts = [c.get("text", "") for c in chunks]
            encoder = self._get_encoder()
            vectors = encoder.encode(texts, show_progress_bar=False)
            points = [PointStruct(id=i, vector=v.tolist(), payload={
                                  **c.get("metadata", {}), "text": c.get("text", "")}) for i, (v, c) in enumerate(zip(vectors, chunks))]
            self.client.upsert(collection_name=collection, points=points)
        except Exception:
            return

    def search(self, query: str, top_k: int = DENSE_TOP_K, collection: str = COLLECTION_NAME) -> list[SearchResult]:
        """Search using dense vectors."""
        # DONE: Dense search — best-effort with fallbacks
        if not self.client:
            return []
        try:
            qvec = self._get_encoder().encode([query])[0].tolist()
            hits = self.client.search(
                collection_name=collection, query_vector=qvec, limit=top_k)
            results = []
            for h in hits:
                payload = getattr(h, "payload", {}) or h.payload
                score = getattr(h, "score", 0) or 0
                results.append(SearchResult(text=payload.get("text", ""), score=float(
                    score), metadata=payload, method="dense"))
            return results
        except Exception:
            return []


def reciprocal_rank_fusion(results_list: list[list[SearchResult]], k: int = 60,
                           top_k: int = HYBRID_TOP_K) -> list[SearchResult]:
    """Merge ranked lists using RRF: score(d) = Σ 1/(k + rank)."""
    # DONE: Implement RRF
    rrf_scores: dict[str, dict] = {}
    for lst in results_list:
        for rank, res in enumerate(lst):
            key = res.text
            if key not in rrf_scores:
                rrf_scores[key] = {"score": 0.0, "result": res}
            rrf_scores[key]["score"] += 1.0 / (k + rank + 1)

    merged = sorted(rrf_scores.values(),
                    key=lambda x: x["score"], reverse=True)[:top_k]
    out: list[SearchResult] = []
    for item in merged:
        r = item["result"]
        out.append(SearchResult(text=r.text, score=float(
            item["score"]), metadata=r.metadata, method="hybrid"))
    return out


class HybridSearch:
    """Combines BM25 + Dense + RRF. (Đã implement sẵn — dùng classes ở trên)"""

    def __init__(self):
        self.bm25 = BM25Search()
        self.dense = DenseSearch()

    def index(self, chunks: list[dict]) -> None:
        self.bm25.index(chunks)
        self.dense.index(chunks)

    def search(self, query: str, top_k: int = HYBRID_TOP_K) -> list[SearchResult]:
        bm25_results = self.bm25.search(query, top_k=BM25_TOP_K)
        dense_results = self.dense.search(query, top_k=DENSE_TOP_K)
        return reciprocal_rank_fusion([bm25_results, dense_results], top_k=top_k)


if __name__ == "__main__":
    print(f"Original:  Nhân viên được nghỉ phép năm")
    print(f"Segmented: {segment_vietnamese('Nhân viên được nghỉ phép năm')}")
