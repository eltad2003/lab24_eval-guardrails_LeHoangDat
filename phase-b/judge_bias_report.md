# Bias Observations Report

## Bias 1: Position Bias
- **Metric:** A wins as first: 6/30 = 20.0%
- **Observation:** No strong position bias observed (~50%)

## Bias 2: Length Bias
- **Metric:** B wins when longer: 5/9 = 55.6%
- **Observation:** No strong length bias observed

## Summary Table
| Bias Type | Value | Interpretation |
|---|---|---|
| Position Bias | 20.0% | High |
| Length Bias | 55.6% | Low |

## Mitigation Strategy
1. **Position Bias:** Already mitigated using Swap-and-average in Task B.1.
2. **Length Bias:** Add an explicit instruction to the Judge prompt to ignore answer length and focus on factual density.
