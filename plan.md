
```markdown
# 📋 PLAN.MD - Lộ trình thực hiện Lab 24: Full Evaluation & Guardrail System

## 🎯 Mục tiêu
Hoàn thành Lab 24 theo đúng cấu trúc 4 Phase, đảm bảo đạt threshold ≥ 60/100 điểm, tối ưu chi phí API, latency và dễ bảo trì. File này đóng vai trò checklist & roadmap step-by-step.

---

## 🗂️ 1. Cấu trúc Repository chuẩn
*(Tạo repo GitHub theo đúng template yêu cầu)*
```text
lab24-eval-guardrails-<tên>/
├── .github/workflows/eval-gate.yml
├── phase-a/
├── phase-b/
├── phase-c/
├── phase-d/
├── demo/
├── requirements.txt
├── prompts.md
├── SUMMARY.md          # 📝 File tổng hợp kiến trúc & kết quả (yêu cầu)
├── RUN_GUIDE.md        # 📖 File hướng dẫn chạy (yêu cầu)
└── README.md
```

## 🛠️ 2. Chuẩn bị môi trường
- Python 3.10+
- Cài đặt dependencies: `pip install ragas langchain langchain-openai pandas scikit-learn presidio-analyzer presidio-anonymizer transformers torch asyncio matplotlib numpy requests`
- Setup API Keys: `OPENAI_API_KEY`, `GROQ_API_KEY` (cho Llama Guard)
- Verify RAG pipeline từ Day 18 còn chạy.

---

## 🔹 PHASE A: RAGAS Evaluation (60 phút)
### Step A.1: Synthetic Test Set Generation
- [ ] Load document corpus (≥50 trang markdown).
- [ ] Chạy script `TestsetGenerator` với `gpt-4o-mini`.
- [ ] Phân bố: `simple: 0.5, reasoning: 0.25, multi_context: 0.25`.
- [ ] Xuất `phase-a/testset_v1.csv` (≥50 rows, đủ 4 cột: `question, ground_truth, contexts, evolution_type`).
- [ ] **Manual Review:** Kiểm tra 10 câu, chỉnh sửa ít nhất 1 câu, ghi log vào `phase-a/testset_review_notes.md`.

### Step A.2: Run RAGAS 4 Metrics
- [ ] Loop qua testset, gọi RAG pipeline để lấy `answer` và `contexts`.
- [ ] Chạy `evaluate()` với 4 metrics: `faithfulness, answer_relevancy, context_precision, context_recall`.
- [ ] Xuất `phase-a/ragas_results.csv` và `phase-a/ragas_summary.json`.
- [ ] Log tổng chi phí API vào `README.md`. Nếu metric < 0.5, ghi observation.

### Step A.3: Failure Cluster Analysis
- [ ] Lọc 10 câu có điểm trung bình thấp nhất.
- [ ] Phân nhóm thất bại (ít nhất 2 clusters, ví dụ: Multi-hop reasoning, Off-topic retrieval).
- [ ] Viết `phase-a/failure_analysis.md` theo template (có Pattern, Root cause, Proposed fix kỹ thuật cụ thể).

### Step A.4: CI/CD Integration Plan
- [ ] Tạo `.github/workflows/eval-gate.yml` với threshold gate (ví dụ: `faithfulness < 0.85 → exit 1`).
- [ ] Validate YAML bằng `yamllint`. Đảm bảo có artifact upload.

---

## 🔹 PHASE B: LLM-as-Judge & Calibration (60 phút)
### Step B.1: Pairwise Judge Pipeline
- [ ] Implement `pairwise_judge_with_swap()` (chạy 2 lần/ cặp, đảo order A-B, so sánh kết quả để mitigate position bias).
- [ ] Chạy trên ≥30 câu, xuất `phase-b/pairwise_results.csv` (có `run1_winner`, `run2_winner`, `winner_after_swap`).

### Step B.2: Absolute Scoring với Rubric
- [ ] Implement `absolute_score()` chấm 4 chiều (accuracy, relevance, conciseness, helpfulness).
- [ ] Tính `overall = mean(4 dims)`. Chạy trên 30 câu, xuất `phase-b/absolute_scores.csv`.

### Step B.3: Human Calibration với Cohen’s Kappa
- [ ] Random sample 10 cặp từ `pairwise_results.csv` → `phase-b/to_label.csv`.
- [ ] Tự tay gán nhãn `phase-b/human_labels.csv` (có `confidence`, `notes`).
- [ ] Tính `cohen_kappa_score` bằng `sklearn`. Ghi nhận xét theo bảng scale.
- [ ] Nếu `kappa < 0.6`, viết phân tích nguyên nhân (bias, prompt drift, labeling inconsistent) vào cùng file.

### Step B.4: Bias Observations Report
- [ ] Quantify Position Bias & Length Bias bằng code/pandas.
- [ ] Vẽ 1 chart/table (matplotlib).
- [ ] Viết `phase-b/judge_bias_report.md` kèm chiến lược mitigate.

---

## 🔹 PHASE C: Guardrails Stack (90 phút)
### Step C.1: Input Guardrail - PII Redaction
- [ ] Implement `InputGuard` kết hợp Presidio + Regex tiếng Việt (CCCD, SĐT, MST, Email).
- [ ] Test 10 input mix EN/VN, đảm bảo detection ≥ 80%, P95 latency < 50ms.
- [ ] Xử lý edge cases (empty, long text). Xuất `phase-c/pii_test_results.csv`.
- [ ] **Tối ưu:** Wrap hàm `sanitize` sang `asyncio` để chuẩn bị cho Phase C.5.

### Step C.2: Input Guardrail - Topic Scope Validator
- [ ] **Chọn Option 1 (Embedding Similarity):** Nhanh, rẻ, ổn định cho production. Ngưỡng `> 0.6`.
- [ ] Test 20 input (10 on-topic, 10 off-topic). Đạt accuracy ≥ 75%.
- [ ] Thiết kế fallback message thân thiện (không chỉ "rejected").

### Step C.3: Adversarial Testing
- [ ] Build 20 attack mẫu (DAN, roleplay, payload splitting, encoding).
- [ ] Chạy qua pipeline `InputGuard` + `TopicGuard`.
- [ ] Đo detection rate (≥ 70%) & false positive rate trên 10 query thường (≤ 10%).
- [ ] Xuất `phase-c/adversarial_test_results.csv`.

### Step C.4: Output Guardrail - Llama Guard 3
- [ ] **Chọn Option B (Groq API):** Không cần GPU, free tier đủ dùng, latency ổn (~40-80ms).
- [ ] Test 10 unsafe + 10 safe output. Detection ≥ 80%, FP ≤ 20%.
- [ ] Đo latency P95, ghi log.

### Step C.5: Full Stack Integration & Latency Benchmark
- [ ] Gộp L1 (PII + Topic), L2 (RAG Day 18), L3 (Llama Guard) vào `phase-c/full_pipeline.py`.
- [ ] Dùng `asyncio.create_task` chạy song song L1 & L3.
- [ ] Benchmark ≥ 100 requests, report P50/P95/P99. Đảm bảo L1 P95 < 50ms, L3 P95 < 100ms.
- [ ] So sánh overhead với baseline (không guardrail). Xuất `phase-c/latency_benchmark.csv`.

---

## 🔹 PHASE D: Blueprint Document (30 phút)
- [ ] Viết `phase-d/blueprint.md` (4-6 trang).
- [ ] **Section 1:** ≥ 5 SLOs + alert thresholds.
- [ ] **Section 2:** Architecture diagram (Mermaid/draw.io) rõ 4 layers + latency annotation.
- [ ] **Section 3:** Alert Playbook (≥ 3 incidents: format Severity → Detection → Cause → Steps → Resolution → TTD/TTR).
- [ ] **Section 4:** Cost Analysis (100k queries/month, breakdown + optimization tips).

---

## 💡 Đề xuất Option tối ưu & Best Practices
| Thành phần | Option đề xuất | Lý do |
|---|---|---|
| **LLM Generator/Judge** | `gpt-4o-mini` | Nhanh, rẻ (~5x cheaper than 4o), đủ tốt cho eval |
| **Llama Guard** | Groq API (Option B) | Tránh tải 8B model, không cần GPU, P95 ~40-60ms |
| **Topic Validator** | Embedding Similarity (Option 1) | Latency cực thấp (<20ms), không tốn API call, dễ tune threshold |
| **Async Handling** | `asyncio` + `langchain` async | Bắt buộc cho C.5, tránh blocking I/O khi benchmark |
| **Cost Control** | Log every LLM call, set `max_concurrent=2` | Tránh vượt $20, dễ debug rate limit |

---

## 📦 Deliverables bắt buộc (Tự động sinh theo yêu cầu)
Sau khi hoàn thành code, bạn cần tạo 2 file tổng hợp sau ở root repo:

### 1. `SUMMARY.md` (Kiến trúc & Tổng hợp kết quả)
```markdown
# 📊 Lab 24 Summary & Architecture Overview
## 🏗️ Kiến trúc hệ thống
- [Chèn Mermaid diagram vào đây]
- Giải thích luồng dữ liệu: User → L1(Input Guards parallel) → L2(RAG) → L3(Llama Guard) → L4(Audit Async)
- Công nghệ chính: Presidio, LangChain, RAGAS, Groq/LlamaGuard3, asyncio, pandas.

## 📈 Kết quả thực nghiệm
- **Phase A (RAGAS):** Scores (F, AR, CP, CR), Top 3 failure clusters & root causes.
- **Phase B (Judge):** Cohen's Kappa, Bias mitigation results (position/length).
- **Phase C (Guardrails):** PII recall, Topic accuracy, Adversarial defense rate, Llama Guard latency P95.
- **Phase D (Blueprint):** SLOs met, Cost projection & optimization.

## 🛠️ Lessons Learned
- Điểm mạnh/yếu của pipeline.
- Kinh nghiệm tune threshold, xử lý async, tránh API rate limit, cách debug low Kappa.
```

### 2. `RUN_GUIDE.md` (Hướng dẫn chạy từ A-Z)
```markdown
# 🚀 RUN_GUIDE.md
## 1. Cài đặt môi trường
```bash
python -m venv venv && source venv/bin/activate  # hoặc venv\Scripts\activate trên Windows
pip install -r requirements.txt
export OPENAI_API_KEY="your_key"
export GROQ_API_KEY="your_key"
```

## 2. Chạy từng Phase riêng lẻ
- **Phase A:** `python phase-a/run_ragas.py`
- **Phase B:** `python phase-b/run_judge.py`
- **Phase C (Test Guardrails):** `python phase-c/test_guardrails.py`
- **Phase C (Benchmark):** `python phase-c/benchmark_latency.py`

## 3. Chạy Full Pipeline (End-to-End)
```bash
python phase-c/full_pipeline.py --mode interactive  # Chạy thử 1 câu
python phase-c/full_pipeline.py --mode benchmark    # Chạy 100 requests, xuất latency report
```

## 4. Generate Demo Video
- Dùng Loom/OBS quay màn hình chạy lần lượt: RAGAS → Judge Swap → Adversarial Block → Latency Output.
- Upload YouTube (Unlisted), paste link vào `README.md`.
```

---

## ✅ Checklist tự kiểm tra trước khi nộp
*(Đối chiếu với Phần 8 trong đề bài)*
- [ ] Repo đúng cấu trúc, commit history rõ ràng (commit mỗi 30 phút).
- [ ] `README.md` có overview 200-300 từ, kết quả tổng hợp, link demo.
- [ ] `prompts.md` log đầy đủ prompt đã dùng (academic integrity).
- [ ] Demo video 5 phút đủ 4 phần yêu cầu.
- [ ] Tất cả file `.csv`, `.json`, `.md` đã sinh đúng path.
- [ ] Latency thresholds đạt chuẩn (L1<50ms, L3<100ms).
- [ ] Cohen's Kappa được tính & giải thích đúng. Nếu <0.6 có root cause analysis.
- [ ] CI/CD YAML valid, có threshold gate & artifact upload.
- [ ] `SUMMARY.md` & `RUN_GUIDE.md` đã hoàn thiện ở root repo.

> 💡 **Lưu ý quan trọng:** Không skip phase. Nếu stuck >20 phút, hỏi ngay Slack `#lab24-eval-guardrails`. Tổng thời gian dự kiến: 4-6 giờ focused work. Chúc bạn build được production-ready stack!
```