import pandas as pd
from sklearn.metrics import cohen_kappa_score

def analyze():
    # 1. Load labels
    human = pd.read_csv('phase-b/human_labels.csv')['human_winner'].tolist()
    judge = pd.read_csv('phase-b/pairwise_results.csv').head(10)['winner_after_swap'].tolist()
    
    # 2. Compute Cohen's kappa
    kappa = cohen_kappa_score(human, judge)
    print(f"Cohen's kappa: {kappa:.3f}")
    
    # 3. Interpretation
    if kappa < 0:
        interpretation = "WORSE than chance — judge sai hệ thống"
    elif kappa < 0.2:
        interpretation = "Slight agreement — không tin được"
    elif kappa < 0.4:
        interpretation = "Fair agreement — vẫn yếu"
    elif kappa < 0.6:
        interpretation = "Moderate agreement — có thể dùng cho monitoring"
    elif kappa < 0.8:
        interpretation = "Substantial agreement — production-ready ✓"
    else:
        interpretation = "Almost perfect agreement — hiếm gặp"
    
    print(f"Interpretation: {interpretation}")
    
    # Save results for report
    with open("phase-b/kappa_result.txt", "w", encoding="utf-8") as f:
        f.write(f"Cohen's kappa: {kappa:.3f}\n")
        f.write(f"Interpretation: {interpretation}\n")

if __name__ == "__main__":
    analyze()
