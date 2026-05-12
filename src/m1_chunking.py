"""
Module 1: Advanced Chunking Strategies
=======================================
Implement semantic, hierarchical, và structure-aware chunking.
So sánh với basic chunking (baseline) để thấy improvement.

Test: pytest tests/test_m1.py
"""

from config import (DATA_DIR, HIERARCHICAL_PARENT_SIZE, HIERARCHICAL_CHILD_SIZE,
                    SEMANTIC_THRESHOLD)
import os
import sys
import glob
import re
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)
    parent_id: str | None = None


def load_documents(data_dir: str = DATA_DIR) -> list[dict]:
    """Load all markdown/text files from data/. (Đã implement sẵn)"""
    docs = []
    for fp in sorted(glob.glob(os.path.join(data_dir, "*.md"))):
        with open(fp, encoding="utf-8") as f:
            docs.append({"text": f.read(), "metadata": {
                        "source": os.path.basename(fp)}})
    return docs


# ─── Baseline: Basic Chunking (để so sánh) ──────────────


def chunk_basic(text: str, chunk_size: int = 500, metadata: dict | None = None) -> list[Chunk]:
    """
    Basic chunking: split theo paragraph (\\n\\n).
    Đây là baseline — KHÔNG phải mục tiêu của module này.
    (Đã implement sẵn)
    """
    metadata = metadata or {}
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for i, para in enumerate(paragraphs):
        if len(current) + len(para) > chunk_size and current:
            chunks.append(Chunk(text=current.strip(), metadata={
                          **metadata, "chunk_index": len(chunks)}))
            current = ""
        current += para + "\n\n"
    if current.strip():
        chunks.append(Chunk(text=current.strip(), metadata={
                      **metadata, "chunk_index": len(chunks)}))
    return chunks


# ─── Strategy 1: Semantic Chunking ───────────────────────


def chunk_semantic(text: str, threshold: float = SEMANTIC_THRESHOLD,
                   metadata: dict | None = None) -> list[Chunk]:
    """
    Split text by sentence similarity — nhóm câu cùng chủ đề.
    Tốt hơn basic vì không cắt giữa ý.

    Args:
        text: Input text.
        threshold: Cosine similarity threshold. Dưới threshold → tách chunk mới.
        metadata: Metadata gắn vào mỗi chunk.

    Returns:
        List of Chunk objects grouped by semantic similarity.
    """
    metadata = metadata or {}
    # DONE: Implement semantic chunking (lightweight heuristic without heavy deps)
    # 1. Split text into sentences
    sentences = [s.strip() for s in re.split(
        r'(?<=[.!?])\s+|\n\n', text) if s.strip()]
    if not sentences:
        return []

    # Merge header-like lines (markdown) with following sentence to avoid isolated header chunks
    processed_sentences = []
    i = 0
    while i < len(sentences):
        s = sentences[i]
        if s.startswith("#") and i + 1 < len(sentences):
            merged = s + " " + sentences[i + 1]
            processed_sentences.append(merged)
            i += 2
        else:
            processed_sentences.append(s)
            i += 1
    sentences = processed_sentences

    def jaccard(a: str, b: str) -> float:
        sa = set(re.findall(r"\w+", a.lower()))
        sb = set(re.findall(r"\w+", b.lower()))
        if not sa or not sb:
            return 0.0
        return len(sa & sb) / len(sa | sb)

    chunks = []
    current = [sentences[0]]
    for i in range(1, len(sentences)):
        sim = jaccard(sentences[i - 1], sentences[i])
        # threshold parameter controls grouping strictness
        if sim < threshold:
            chunks.append(Chunk(text=" ".join(current), metadata={
                          **metadata, "chunk_index": len(chunks), "strategy": "semantic"}))
            current = []
        current.append(sentences[i])

    if current:
        chunks.append(Chunk(text=" ".join(current), metadata={
                      **metadata, "chunk_index": len(chunks), "strategy": "semantic"}))

    return chunks


# ─── Strategy 2: Hierarchical Chunking ──────────────────


def chunk_hierarchical(text: str, parent_size: int = HIERARCHICAL_PARENT_SIZE,
                       child_size: int = HIERARCHICAL_CHILD_SIZE,
                       metadata: dict | None = None) -> tuple[list[Chunk], list[Chunk]]:
    """
    Parent-child hierarchy: retrieve child (precision) → return parent (context).
    Đây là default recommendation cho production RAG.

    Args:
        text: Input text.
        parent_size: Chars per parent chunk.
        child_size: Chars per child chunk.
        metadata: Metadata gắn vào mỗi chunk.

    Returns:
        (parents, children) — mỗi child có parent_id link đến parent.
    """
    metadata = metadata or {}
    # DONE: Implement hierarchical chunking (parents + sliding-window children)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    parents: list[Chunk] = []
    children: list[Chunk] = []

    # build parents by concatenating paragraphs until parent_size
    cur = ""
    p_index = 0
    for para in paragraphs:
        if len(cur) + len(para) > parent_size and cur:
            pid = f"parent_{p_index}"
            parent_chunk = Chunk(text=cur.strip(), metadata={
                                 **metadata, "chunk_type": "parent", "parent_id": pid})
            parents.append(parent_chunk)
            # create children by sliding window
            txt = parent_chunk.text
            for i in range(0, max(len(txt) - 1, 1), child_size):
                child_text = txt[i:i + child_size]
                if child_text.strip():
                    child = Chunk(text=child_text.strip(), metadata={
                                  **metadata, "chunk_type": "child", "parent_id": pid}, parent_id=pid)
                    children.append(child)
            p_index += 1
            cur = ""
        cur += para + "\n\n"

    if cur.strip():
        pid = f"parent_{p_index}"
        parent_chunk = Chunk(text=cur.strip(), metadata={
                             **metadata, "chunk_type": "parent", "parent_id": pid})
        parents.append(parent_chunk)
        txt = parent_chunk.text
        for i in range(0, max(len(txt) - 1, 1), child_size):
            child_text = txt[i:i + child_size]
            if child_text.strip():
                child = Chunk(text=child_text.strip(), metadata={
                              **metadata, "chunk_type": "child", "parent_id": pid}, parent_id=pid)
                children.append(child)

    return parents, children


# ─── Strategy 3: Structure-Aware Chunking ────────────────


def chunk_structure_aware(text: str, metadata: dict | None = None) -> list[Chunk]:
    """
    Parse markdown headers → chunk theo logical structure.
    Giữ nguyên tables, code blocks, lists — không cắt giữa chừng.

    Args:
        text: Markdown text.
        metadata: Metadata gắn vào mỗi chunk.

    Returns:
        List of Chunk objects, mỗi chunk = 1 section (header + content).
    """
    metadata = metadata or {}
    # DONE: Implement structure-aware chunking (split by markdown headers)
    sections = re.split(r'(^#{1,3}\s+.+$)', text, flags=re.MULTILINE)
    chunks = []
    current_header = ""
    current_content = ""
    for part in sections:
        if re.match(r'^#{1,3}\s+', part):
            if current_header or current_content.strip():
                chunks.append(Chunk(text=f"{current_header}\n{current_content}".strip(), metadata={
                              **metadata, "section": current_header.strip('# ').strip(), "strategy": "structure"}))
            current_header = part.strip()
            current_content = ""
        else:
            current_content += part
    if current_header or current_content.strip():
        chunks.append(Chunk(text=f"{current_header}\n{current_content}".strip(), metadata={
                      **metadata, "section": current_header.strip('# ').strip(), "strategy": "structure"}))
    return chunks


# ─── A/B Test: Compare All Strategies ────────────────────


def compare_strategies(documents: list[dict]) -> dict:
    """
    Run all strategies on documents and compare.

    Returns:
        {"basic": {...}, "semantic": {...}, "hierarchical": {...}, "structure": {...}}
    """
    # DONE: Implement comparison across strategies (aggregate stats)
    results = {"basic": {}, "semantic": {},
               "hierarchical": {}, "structure": {}}
    for doc in documents:
        text = doc.get("text", "")
        # basic
        b = chunk_basic(text)
        s = chunk_semantic(text)
        parents, children = chunk_hierarchical(text)
        st = chunk_structure_aware(text)

        def stats(chunks_list):
            if isinstance(chunks_list, tuple):
                # hierarchical: count parents and children
                parents_list, children_list = chunks_list
                return {"num_parents": len(parents_list), "num_children": len(children_list)}
            if not chunks_list:
                return {"count": 0, "avg_len": 0}
            lengths = [len(c.text) for c in chunks_list]
            return {"count": len(chunks_list), "avg_len": sum(lengths) / len(lengths), "min_len": min(lengths), "max_len": max(lengths)}

        results["basic"] = stats(b)
        results["semantic"] = stats(s)
        results["hierarchical"] = stats((parents, children))
        results["structure"] = stats(st)

    return results


if __name__ == "__main__":
    docs = load_documents()
    print(f"Loaded {len(docs)} documents")
    results = compare_strategies(docs)
    for name, stats in results.items():
        print(f"  {name}: {stats}")
