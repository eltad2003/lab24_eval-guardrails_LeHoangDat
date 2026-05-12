"""Module 4: RAGAS Evaluation — 4 metrics + failure analysis."""

from config import TEST_SET_PATH
import os
import sys
import json
import re
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class EvalResult:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


def load_test_set(path: str = TEST_SET_PATH) -> list[dict]:
    """Load test set from JSON. (Đã implement sẵn)"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    """Run RAGAS evaluation."""
    # DONE: Implement lightweight RAGAS-like evaluation using token overlap heuristics
    per_question: list[EvalResult] = []
    for q, a, ctxs, gt in zip(questions, answers, contexts, ground_truths):
        atoks = set(re.findall(r"\w+", a.lower()))
        gtok = set(re.findall(r"\w+", gt.lower()))
        # faithfulness ~= fraction of answer tokens that appear in ground truth
        faithfulness = (len(atoks & gtok) /
                        max(1, len(atoks))) if atoks else 0.0
        # answer relevancy ~= overlap between answer and ground truth
        answer_relevancy = (len(atoks & gtok) /
                            max(1, len(gtok))) if gtok else 0.0
        # context precision/recall: aggregate across provided contexts
        ctx_tokens = [set(re.findall(r"\w+", c.lower())) for c in ctxs]
        if ctx_tokens:
            precisions = []
            recalls = []
            for ct in ctx_tokens:
                precisions.append(len(ct & gtok) / max(1, len(ct)))
                recalls.append(len(ct & gtok) / max(1, len(gtok)))
            context_precision = sum(precisions) / len(precisions)
            context_recall = sum(recalls) / len(recalls)
        else:
            context_precision = 0.0
            context_recall = 0.0

        per_question.append(EvalResult(question=q, answer=a, contexts=ctxs, ground_truth=gt,
                                       faithfulness=float(faithfulness), answer_relevancy=float(answer_relevancy),
                                       context_precision=float(context_precision), context_recall=float(context_recall)))

    # aggregate
    agg = {"faithfulness": 0.0, "answer_relevancy": 0.0,
           "context_precision": 0.0, "context_recall": 0.0}
    if per_question:
        agg["faithfulness"] = sum(
            r.faithfulness for r in per_question) / len(per_question)
        agg["answer_relevancy"] = sum(
            r.answer_relevancy for r in per_question) / len(per_question)
        agg["context_precision"] = sum(
            r.context_precision for r in per_question) / len(per_question)
        agg["context_recall"] = sum(
            r.context_recall for r in per_question) / len(per_question)

    result = {**agg, "per_question": per_question}
    return result


def failure_analysis(eval_results: list[EvalResult], bottom_n: int = 10) -> list[dict]:
    """Analyze bottom-N worst questions using Diagnostic Tree."""
    # DONE: Implement failure analysis with simple diagnostic rules
    results = []
    scored = []
    for r in eval_results:
        avg = (r.faithfulness + r.answer_relevancy +
               r.context_precision + r.context_recall) / 4.0
        scored.append((avg, r))
    scored.sort(key=lambda x: x[0])
    for avg, r in scored[:bottom_n]:
        metrics = {
            "faithfulness": r.faithfulness,
            "answer_relevancy": r.answer_relevancy,
            "context_precision": r.context_precision,
            "context_recall": r.context_recall,
        }
        worst_metric = min(metrics.items(), key=lambda x: x[1])
        metric_name, metric_score = worst_metric
        diagnosis = ""
        suggested_fix = ""
        if metric_name == "faithfulness" and metric_score < 0.85:
            diagnosis = "LLM hallucinating"
            suggested_fix = "Tighten prompt, lower temperature, provide more context"
        elif metric_name == "context_recall" and metric_score < 0.75:
            diagnosis = "Missing relevant chunks"
            suggested_fix = "Improve chunking or add BM25; expand retrieval"
        elif metric_name == "context_precision" and metric_score < 0.75:
            diagnosis = "Too many irrelevant chunks"
            suggested_fix = "Add reranking or metadata filters"
        elif metric_name == "answer_relevancy" and metric_score < 0.80:
            diagnosis = "Answer doesn't match question"
            suggested_fix = "Improve prompt template or post-filter answers"
        else:
            diagnosis = "Low score in metric"
            suggested_fix = "Investigate data and prompts"

        results.append({"question": r.question, "worst_metric": metric_name, "score": float(
            metric_score), "diagnosis": diagnosis, "suggested_fix": suggested_fix})
    return results


def save_report(results: dict, failures: list[dict], path: str = "ragas_report.json"):
    """Save evaluation report to JSON. (Đã implement sẵn)"""
    report = {
        "aggregate": {k: v for k, v in results.items() if k != "per_question"},
        "num_questions": len(results.get("per_question", [])),
        "failures": failures,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Report saved to {path}")


if __name__ == "__main__":
    test_set = load_test_set()
    print(f"Loaded {len(test_set)} test questions")
    print("Run pipeline.py first to generate answers, then call evaluate_ragas().")
