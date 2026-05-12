import os
import json
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

# Load environment variables
load_dotenv()

ABSOLUTE_PROMPT = PromptTemplate.from_template("""
Score the answer on 4 dimensions, each 1-5 scale:
1. Factual accuracy (1=many errors, 5=fully accurate)
2. Relevance (1=off-topic, 5=directly answers)
3. Conciseness (1=verbose, 5=appropriately brief)
4. Helpfulness (1=unclear, 5=actionable)

Question: {question}
Answer: {answer}

Output JSON only:
{{"accuracy": int, "relevance": int, "conciseness": int, "helpfulness": int, "overall": float}}
""")

def parse_judge_output(text):
    """Robust JSON parsing với fallback."""
    try:
        # Strip markdown code fences if any
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except json.JSONDecodeError:
        return {"accuracy": 3, "relevance": 3, "conciseness": 3, "helpfulness": 3, "overall": 3.0}

def absolute_score(question, answer, judge_llm):
    prompt = ABSOLUTE_PROMPT.format(question=question, answer=answer)
    out = judge_llm.invoke(prompt)
    parsed = parse_judge_output(out.content)
    
    # Compute overall as average if not provided
    if 'overall' not in parsed:
        dims = ['accuracy', 'relevance', 'conciseness', 'helpfulness']
        parsed['overall'] = sum(parsed[d] for d in dims if d in parsed) / 4.0
    return parsed

def run_absolute_scorer():
    # 1. Load answers (Version B - with reranking)
    input_path = "phase-b/answers_to_judge.csv"
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return
    
    df = pd.read_csv(input_path)
    
    # 2. Setup Judge LLM
    judge_llm = ChatOpenAI(model="gpt-4o-mini")
    
    # 3. Run scorer
    results = []
    print(f"Running Absolute Scorer on {len(df)} answers...")
    
    for i, row in df.iterrows():
        print(f"  [{i+1}/{len(df)}] Scoring...")
        scores = absolute_score(row['question'], row['answer_b'], judge_llm)
        results.append({
            'question': row['question'],
            'answer': row['answer_b'],
            **scores
        })
        
    # 4. Save results
    df_results = pd.DataFrame(results)
    df_results.to_csv("phase-b/absolute_scores.csv", index=False)
    print(f"Done! Saved results to phase-b/absolute_scores.csv")

if __name__ == "__main__":
    run_absolute_scorer()
