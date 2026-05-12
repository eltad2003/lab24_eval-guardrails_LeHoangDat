import pandas as pd
import matplotlib.pyplot as plt

def report():
    df = pd.read_csv('phase-b/pairwise_results.csv')
    
    # Bias 1: Position bias
    run1_a_wins = (df['run1_winner'] == 'A').sum()
    total = len(df)
    pos_bias_pct = (run1_a_wins/total) * 100
    
    # Bias 2: Length bias
    df['len_a'] = df['answer_a'].str.len()
    df['len_b'] = df['answer_b'].str.len()
    df['len_diff'] = df['len_b'] - df['len_a']
    
    b_wins_when_longer = ((df['winner_after_swap'] == 'B') & (df['len_diff'] > 0)).sum()
    b_total_longer = (df['len_diff'] > 0).sum()
    length_bias_pct = (b_wins_when_longer/b_total_longer * 100) if b_total_longer > 0 else 0
    
    with open("phase-b/judge_bias_report.md", "w", encoding="utf-8") as f:
        f.write("# Bias Observations Report\n\n")
        f.write(f"## Bias 1: Position Bias\n")
        f.write(f"- **Metric:** A wins as first: {run1_a_wins}/{total} = {pos_bias_pct:.1f}%\n")
        f.write(f"- **Observation:** {'Suggests position bias (>55%)' if pos_bias_pct > 55 else 'No strong position bias observed (~50%)'}\n\n")
        
        f.write(f"## Bias 2: Length Bias\n")
        f.write(f"- **Metric:** B wins when longer: {b_wins_when_longer}/{b_total_longer} = {length_bias_pct:.1f}%\n")
        f.write(f"- **Observation:** {'Suggests length bias' if length_bias_pct > 60 else 'No strong length bias observed'}\n\n")
        
        f.write(f"## Summary Table\n")
        f.write(f"| Bias Type | Value | Interpretation |\n")
        f.write(f"|---|---|---|\n")
        f.write(f"| Position Bias | {pos_bias_pct:.1f}% | {'High' if abs(50-pos_bias_pct) > 10 else 'Low'} |\n")
        f.write(f"| Length Bias | {length_bias_pct:.1f}% | {'High' if length_bias_pct > 70 else 'Low'} |\n\n")
        
        f.write(f"## Mitigation Strategy\n")
        f.write(f"1. **Position Bias:** Already mitigated using Swap-and-average in Task B.1.\n")
        f.write(f"2. **Length Bias:** Add an explicit instruction to the Judge prompt to ignore answer length and focus on factual density.\n")

    print("Done! Saved report to phase-b/judge_bias_report.md")

if __name__ == "__main__":
    report()
