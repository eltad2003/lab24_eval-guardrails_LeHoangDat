import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Set PYTHONPATH to include project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline import build_pipeline, run_query

# Load environment variables
load_dotenv()

def generate():
    # 1. Load test set (first 30 questions)
    testset_path = "phase-a/testset_v1.csv"
    if not os.path.exists(testset_path):
        print(f"Error: {testset_path} not found.")
        return
    
    df_test = pd.read_csv(testset_path).head(30)
    
    # 2. Build RAG pipeline
    search, reranker = build_pipeline()
    
    # 3. Generate two versions of answers
    results_data = []
    print(f"Generating 2 versions of answers for {len(df_test)} questions...")
    
    for i, row in df_test.iterrows():
        question = row['question']
        
        try:
            # Version A: without reranking
            print(f"  [{i+1}/30] Generating Version A (no rerank)...")
            ans_a, _ = run_query(question, search, reranker, use_rerank=False)
            
            # Version B: with reranking
            print(f"  [{i+1}/30] Generating Version B (with rerank)...")
            ans_b, _ = run_query(question, search, reranker, use_rerank=True)
            
            results_data.append({
                'question': question,
                'answer_a': ans_a,
                'answer_b': ans_b
            })
        except Exception as e:
            print(f"    Error processing question {i}: {e}")
            
    # 4. Save to CSV for the judge
    df_results = pd.DataFrame(results_data)
    output_path = "phase-b/answers_to_judge.csv"
    df_results.to_csv(output_path, index=False)
    print(f"Done! Saved {len(df_results)} pairs to {output_path}")

if __name__ == "__main__":
    generate()
