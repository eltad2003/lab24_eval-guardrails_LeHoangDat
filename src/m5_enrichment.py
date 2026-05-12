"""
Module 5: Enrichment Pipeline
==============================
Làm giàu chunks TRƯỚC khi embed: Summarize, HyQA, Contextual Prepend, Auto Metadata.

Test: pytest tests/test_m5.py
"""

from config import OPENAI_API_KEY
import os
import sys
import re
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class EnrichedChunk:
    """Chunk đã được làm giàu."""
    original_text: str
    enriched_text: str
    summary: str
    hypothesis_questions: list[str]
    auto_metadata: dict
    method: str  # "contextual", "summary", "hyqa", "full"


# ─── Technique 1: Chunk Summarization ────────────────────


def summarize_chunk(text: str) -> str:
    """
    Tạo summary ngắn cho chunk.
    Embed summary thay vì (hoặc cùng với) raw chunk → giảm noise.

    Args:
        text: Raw chunk text.

    Returns:
        Summary string (2-3 câu).
    """
    # DONE: Implement chunk summarization (extractive fallback)
    # Option A (với OpenAI):
    #   from openai import OpenAI
    #   client = OpenAI()
    #   resp = client.chat.completions.create(
    #       model="gpt-4o-mini",
    #       messages=[
    #           {"role": "system", "content": "Tóm tắt đoạn văn sau trong 2-3 câu ngắn gọn bằng tiếng Việt."},
    #           {"role": "user", "content": text},
    #       ],
    #       max_tokens=150,
    #   )
    #   return resp.choices[0].message.content.strip()
    #
    # Option B (không cần API — extractive):
    #   sentences = text.split(". ")
    #   return ". ".join(sentences[:2]) + "."  # Lấy 2 câu đầu
    # extractive: take first 2 sentences
    sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    if not sents:
        return text[:200].strip()
    if len(sents) == 1:
        return sents[0]
    return (sents[0] + " " + sents[1]).strip()


# ─── Technique 2: Hypothesis Question-Answer (HyQA) ─────


def generate_hypothesis_questions(text: str, n_questions: int = 3) -> list[str]:
    """
    Generate câu hỏi mà chunk có thể trả lời.
    Index cả questions lẫn chunk → query match tốt hơn (bridge vocabulary gap).

    Args:
        text: Raw chunk text.
        n_questions: Số câu hỏi cần generate.

    Returns:
        List of question strings.
    """
    # DONE: Implement hypothesis question generation (heuristic rules)
    questions: list[str] = []
    txt = text.strip()
    # rule: if mentions nghỉ phép -> ask how many days
    if "nghỉ phép" in txt.lower() or "nghỉ" in txt.lower():
        questions.append("Nhân viên được nghỉ phép bao nhiêu ngày?")
    # rule: extract numbers to make quantity questions
    nums = re.findall(r"\d+", txt)
    for n in nums[:n_questions]:
        questions.append(f"Có {n} liên quan đến nội dung nào?")
    # fallback generic questions based on first phrase
    if len(questions) < n_questions:
        head = " ".join(re.findall(r"\w+", txt)[:5])
        questions.append(f"Thông tin chính về: {head}?")
    # normalize and limit
    out = [q.rstrip(".") + "?" if not q.endswith("?")
           else q for q in questions]
    return out[:n_questions]


# ─── Technique 3: Contextual Prepend (Anthropic style) ──


def contextual_prepend(text: str, document_title: str = "") -> str:
    """
    Prepend context giải thích chunk nằm ở đâu trong document.
    Anthropic benchmark: giảm 49% retrieval failure (alone).

    Args:
        text: Raw chunk text.
        document_title: Tên document gốc.

    Returns:
        Text với context prepended.
    """
    # DONE: Implement contextual prepend (lightweight heuristic)
    if document_title:
        ctx = f"Trích từ {document_title}."
    else:
        ctx = "Trích dẫn đoạn văn dưới đây."
    return f"{ctx}\n\n{text}"


# ─── Technique 4: Auto Metadata Extraction ──────────────


def extract_metadata(text: str) -> dict:
    """
    LLM extract metadata tự động: topic, entities, date_range, category.

    Args:
        text: Raw chunk text.

    Returns:
        Dict with extracted metadata fields.
    """
    # DONE: Implement simple metadata extraction heuristics
    meta: dict = {}
    txt = text.lower()
    nums = re.findall(r"\d+", txt)
    meta["numbers"] = nums
    # detect simple categories
    if any(k in txt for k in ["mật khẩu", "vpn", "it"]):
        cat = "it"
    elif any(k in txt for k in ["nghỉ phép", "nghỉ", "thử việc", "nhân viên"]):
        cat = "hr"
    else:
        cat = "general"
    meta["category"] = cat
    # language heuristic
    meta["language"] = "vi" if re.search(
        r"[\u00C0-\u024F]|đ|ạ|ả|ầ|ấ", text) else "unknown"
    # simple entities: capitalized words
    ents = re.findall(r"\b[A-ZĐ][a-zạáàảãạéèêíóòôơúùăũỹ]+\b", text)
    meta["entities"] = ents
    return meta


# ─── Full Enrichment Pipeline ────────────────────────────


def enrich_chunks(
    chunks: list[dict],
    methods: list[str] | None = None,
) -> list[EnrichedChunk]:
    """
    Chạy enrichment pipeline trên danh sách chunks.

    Args:
        chunks: List of {"text": str, "metadata": dict}
        methods: List of methods to apply. Default: ["contextual", "hyqa", "metadata"]
                 Options: "summary", "hyqa", "contextual", "metadata", "full"

    Returns:
        List of EnrichedChunk objects.
    """
    if methods is None:
        methods = ["contextual", "hyqa", "metadata"]

    enriched = []

    # DONE: Implement enrichment pipeline
    for c in chunks:
        txt = c.get("text", "")
        meta = c.get("metadata", {})
        summary = ""
        questions = []
        enriched_text = txt
        auto_meta = {}

        if "summary" in methods or "full" in methods:
            summary = summarize_chunk(txt)
        if "hyqa" in methods or "full" in methods:
            questions = generate_hypothesis_questions(txt)
        if "contextual" in methods or "full" in methods:
            enriched_text = contextual_prepend(txt, meta.get("source", ""))
        if "metadata" in methods or "full" in methods:
            auto_meta = extract_metadata(txt)

        merged_meta = {**meta, **(auto_meta or {})}
        enriched.append(EnrichedChunk(original_text=txt, enriched_text=enriched_text, summary=summary or "",
                        hypothesis_questions=questions or [], auto_metadata=merged_meta, method="+".join(methods)))

    return enriched


# ─── Main ────────────────────────────────────────────────

if __name__ == "__main__":
    sample = "Nhân viên chính thức được nghỉ phép năm 12 ngày làm việc mỗi năm. Số ngày nghỉ phép tăng thêm 1 ngày cho mỗi 5 năm thâm niên công tác."

    print("=== Enrichment Pipeline Demo ===\n")
    print(f"Original: {sample}\n")

    s = summarize_chunk(sample)
    print(f"Summary: {s}\n")

    qs = generate_hypothesis_questions(sample)
    print(f"HyQA questions: {qs}\n")

    ctx = contextual_prepend(sample, "Sổ tay nhân viên VinUni 2024")
    print(f"Contextual: {ctx}\n")

    meta = extract_metadata(sample)
    print(f"Auto metadata: {meta}")
