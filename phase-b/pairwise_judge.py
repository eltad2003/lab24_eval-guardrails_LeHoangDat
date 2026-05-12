import os
import json
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

# Load environment variables
load_dotenv()

JUDGE_PROMPT = PromptTemplate.from_template("""
You are an impartial evaluator. Compare two answers to the same question.

Question: {question}
Answer A: {answer_a}
Answer B: {answer_b}

Rate based on:
- Factual accuracy
- Relevance to question
- Conciseness

Output JSON only:
{{"winner": "A" or "B" or "tie", "reason": "..."}}
""")

def parse_judge_output(text):
    """Robust JSON parsing với fallback."""
    try:
        # Strip markdown code fences if any
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except json.JSONDecodeError:
        return {"winner": "tie", "reason": "Parse error"}

def pairwise_judge_with_swap(question, ans1, ans2, judge_llm):
    """Swap-and-average for position bias mitigation."""
    # Run 1: ans1 first, ans2 second
    prompt1 = JUDGE_PROMPT.format(question=question, answer_a=ans1, answer_b=ans2)
    out1 = judge_llm.invoke(prompt1)
    r1 = parse_judge_output(out1.content)
    
    # Run 2: swap order
    prompt2 = JUDGE_PROMPT.format(question=question, answer_a=ans2, answer_b=ans1)
    out2 = judge_llm.invoke(prompt2)
    r2 = parse_judge_output(out2.content)
    
    # IMPORTANT: flip winner because order was swapped
    winner2 = r2['winner']
    if winner2 == 'A':
        final_winner2 = 'B'
    elif winner2 == 'B':
        final_winner2 = 'A'
    else:
        final_winner2 = 'tie'
    
    # Aggregate: both agree -> that. Disagree -> tie.
    final_winner = 'tie'
    if r1['winner'] == final_winner2:
        final_winner = r1['winner']
    
    return {
        'run1_winner': r1['winner'],
        'run2_winner': winner2,
        'winner_after_swap': final_winner,
        'reason': r1['reason']
    }

def run_pairwise_judge():
    # 1. Load answers
    input_path = "phase-b/answers_to_judge.csv"
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return
    
    df = pd.read_csv(input_path)
    
    # 2. Setup Judge LLM
    judge_llm = ChatOpenAI(model="gpt-4o-mini")
    
    # 3. Run judge
    results = []
    print(f"Running Pairwise Judge on {len(df)} questions...")
    
    for i, row in df.iterrows():
        print(f"  [{i+1}/{len(df)}] Judging...")
        res = pairwise_judge_with_swap(row['question'], row['answer_a'], row['answer_b'], judge_llm)
        results.append({
            'question': row['question'],
            'answer_a': row['answer_a'],
            'answer_b': row['answer_b'],
            **res
        })
        
    # 4. Save results
    df_results = pd.DataFrame(results)
    df_results.to_csv("phase-b/pairwise_results.csv", index=False)
    print(f"Done! Saved results to phase-b/pairwise_results.csv")

if __name__ == "__main__":
    run_pairwise_judge()
