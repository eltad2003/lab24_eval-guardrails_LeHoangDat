import os
import pandas as pd
import json
from dotenv import load_dotenv
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from datasets import Dataset
from src.pipeline import build_pipeline, run_query

# Load environment variables
load_dotenv()

def run_eval():
    # 1. Load test set
    testset_path = "phase-a/testset_v1.csv"
    if not os.path.exists(testset_path):
        print(f"Error: {testset_path} not found. Run generate_testset.py first.")
        return
    
    df_test = pd.read_csv(testset_path)
    # Ragas expects contexts as list of strings
    if 'contexts' in df_test.columns:
        import ast
        try:
            df_test['contexts'] = df_test['contexts'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        except:
            pass

    # 2. Build RAG pipeline
    search, reranker = build_pipeline()
    
    # 3. Run RAG pipeline on each question
    results_data = []
    # For the lab, we might want to run on a subset if 50 is too slow, 
    # but let's try all 50 as requested.
    num_questions = len(df_test)
    print(f"Running RAG pipeline on {num_questions} questions...")
    
    for i, row in df_test.iterrows():
        question = row['question']
        ground_truth = row['ground_truth']
        
        try:
            answer, contexts = run_query(question, search, reranker)
            
            results_data.append({
                'question': question,
                'answer': answer,
                'contexts': contexts,
                'ground_truth': ground_truth
            })
        except Exception as e:
            print(f"  Error processing question {i}: {e}")
            
        if (i+1) % 5 == 0:
            print(f"  Processed {i+1}/{num_questions}...")

    # 4. Evaluate with Ragas
    print("Evaluating with Ragas metrics...")
    dataset = Dataset.from_list(results_data)
    
    # Run evaluation
    result = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        ]
    )
    
    # 5. Save results
    df_results = result.to_pandas()
    df_results.to_csv("phase-a/ragas_results.csv", index=False)
    
    # Calculate summary
    summary = {
        'faithfulness': float(result['faithfulness']),
        'answer_relevancy': float(result['answer_relevancy']),
        'context_precision': float(result['context_precision']),
        'context_recall': float(result['context_recall']),
    }
    
    with open("phase-a/ragas_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print("\n" + "="*30)
    print("RAGAS EVALUATION RESULTS")
    print("="*30)
    for k, v in summary.items():
        print(f"{k:20}: {v:.4f}")
    print("="*30)
    print(f"Detailed results saved to phase-a/ragas_results.csv")
    print(f"Summary saved to phase-a/ragas_summary.json")

if __name__ == "__main__":
    run_eval()
