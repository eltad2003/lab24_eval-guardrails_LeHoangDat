# Implementation Plan: Lab 24 — Full Evaluation & Guardrail System

Tài liệu này phác thảo các bước thực hiện bài Lab 24 theo yêu cầu từ đề bài, tập trung vào việc xây dựng hệ thống đánh giá (Evaluation) và phòng vệ (Guardrails) cho RAG pipeline.

## 1. Chuẩn bị (Prerequisites)
- [ ] **RAG Pipeline (Day 18):** Đảm bảo pipeline cũ hoạt động ổn định (Retrieval + Generation).
- [ ] **Document Corpus:** Chuẩn bị ít nhất 50 trang tài liệu (text/markdown).
- [ ] **API Keys:** OpenAI/Anthropic (Judge), HuggingFace (Llama Guard), Groq (nếu chạy Llama Guard qua API).
- [ ] **Môi trường:** Python 3.13, cài đặt các package: `ragas`, `presidio-analyzer`, `presidio-anonymizer`, `guardrails-ai`, `transformers`, `datasets`, `groq`, `langchain`.

---

## 2. Phase A: RAGAS Evaluation (60 phút)

### Task A.1: Synthetic Test Set Generation
- [ ] Sử dụng `TestsetGenerator` từ `ragas`.
- [ ] Cấu hình distribution: 50% simple, 25% reasoning, 25% multi-context.
- [ ] Xuất file `testset_v1.csv` (ít nhất 50 dòng).
- [ ] **Manual Review:** Review 10 câu, chỉnh sửa ít nhất 1 câu và ghi chú vào `testset_review_notes.md`.

### Task A.2: Run RAGAS 4 Metrics
- [ ] Chạy pipeline trên 50 câu hỏi từ test set.
- [ ] Đánh giá bằng 4 metrics: Faithfulness, Answer Relevancy, Context Precision, Context Recall.
- [ ] Lưu kết quả vào `ragas_results.csv` và `ragas_summary.json`.

### Task A.3: Failure Cluster Analysis
- [ ] Tìm 10 câu có điểm thấp nhất.
- [ ] Phân nhóm lỗi (ít nhất 2 clusters, ví dụ: "Multi-hop reasoning failures", "Off-topic retrieval").
- [ ] Đề xuất fix kỹ thuật (tăng top_k, re-ranker, hybrid search). Lưu vào `failure_analysis.md`.

### Task A.4: CI/CD Integration Plan
- [ ] Tạo file `.github/workflows/eval-gate.yml`.
- [ ] Cấu hình threshold gate (ví dụ: `faithfulness >= 0.85`) để block merge.

---

## 3. Phase B: LLM-as-Judge & Calibration (60 phút)

### Task B.1: Pairwise Judge Pipeline
- [ ] Xây dựng prompt cho Judge so sánh 2 câu trả lời (Version A vs Version B).
- [ ] **Kỹ thuật tối ưu:** Triển khai **Swap-and-average** để giảm Position Bias (chạy 2 lần đổi thứ tự A/B).
- [ ] Chạy trên ít nhất 30 câu, lưu vào `pairwise_results.csv`.

### Task B.2: Absolute Scoring với Rubric
- [ ] Đánh giá câu trả lời trên thang điểm 1-5 cho 4 tiêu chí: Accuracy, Relevance, Conciseness, Helpfulness.
- [ ] Lưu kết quả vào `absolute_scores.csv`.

### Task B.3: Human Calibration (Cohen’s Kappa)
- [ ] Chọn 10 cặp từ Phase B.1 để dán nhãn thủ công (`human_labels.csv`).
- [ ] Tính Cohen’s Kappa score để đo mức độ đồng thuận giữa người và AI Judge.

### Task B.4: Bias Observations Report
- [ ] Phân tích Position Bias và Length Bias (AI có xu hướng thích câu dài hơn không?).
- [ ] Lưu báo cáo vào `judge_bias_report.md`.

---

## 4. Phase C: Guardrails Stack (90 phút)

### Task C.1: Input Guardrail - PII Redaction
- [ ] Kết hợp Presidio (NER) và Regex (cho các mẫu Việt Nam như CCCD, mã số thuế).
- [ ] Chạy thử nghiệm với 10 inputs có PII, đo Latency.

### Task C.2: Input Guardrail - Topic Scope Validator
- [ ] **Đề xuất:** Sử dụng **Option 2 (LLM Zero-shot)** để có độ chính xác cao hoặc **Option 1 (Embedding Similarity)** để tối ưu Latency (< 50ms).
- [ ] Kiểm tra với 20 inputs (10 on-topic, 10 off-topic).

### Task C.3: Adversarial Testing
- [ ] Build test set với 20 câu hỏi tấn công (DAN, Jailbreak, Role-play).
- [ ] Đo tỷ lệ chặn (Defense Rate). Lưu kết quả `adversarial_test_results.csv`.

### Task C.4: Output Guardrail - Llama Guard 3
- [ ] **Đề xuất:** Sử dụng **Option B (Groq API)** để không cần GPU và có latency tốt.
- [ ] Test với 10 unsafe outputs và 10 safe outputs.

### Task C.5: Full Stack Integration & Latency Benchmark
- [ ] Tích hợp toàn bộ layers (L1: Input, L2: RAG, L3: Output, L4: Audit Log).
- [ ] **Tối ưu:** Sử dụng `asyncio` để chạy song song các check trong cùng 1 layer.
- [ ] Đo Latency P50/P95/P99 trên 100 requests.

---

## 5. Phase D: Blueprint Document & Finalization (30 phút)

### Task D.1: Blueprint Document (`blueprint.md`)
- [ ] **Section 1: SLO Definition:** Định nghĩa ít nhất 5 SLOs (Latency, Faithfulness, FP rate...).
- [ ] **Section 2: Architecture Diagram:** Vẽ sơ đồ Mermaid cho 4 lớp phòng vệ.
- [ ] **Section 3: Alert Playbook:** Quy trình xử lý khi SLO bị vi phạm.
- [ ] **Section 4: Cost Analysis:** Ước tính chi phí vận hành hàng tháng.

### Task D.2: Tổng hợp kết quả
- [ ] Cấu trúc thư mục theo đúng template yêu cầu (Phase A, B, C, D).
- [ ] Hoàn thiện `README.md` với Results Summary.
- [ ] Soạn file `instructions.md` (Hướng dẫn chạy) - tóm tắt các lệnh cần thực thi.

---

## 6. Đề xuất các Option tối ưu

1.  **Model Đánh giá (Phase A & B):** Ưu tiên `gpt-4o-mini` cho RAGAS và Judge để cân bằng giữa chi phí và độ chính xác. Nếu cần độ chính xác cao nhất cho calibration, hãy dùng `gpt-4o`.
2.  **Topic Guard (Phase C.2):** Nếu Latency là ưu tiên số 1, dùng Embedding similarity. Nếu context phức tạp, dùng LLM Zero-shot với prompt cực ngắn.
3.  **Llama Guard (Phase C.4):** Chạy qua Groq API (`llama-guard-3-8b`) là phương án nhanh nhất, không tốn tài nguyên GPU cục bộ.
4.  **Parallelism (Phase C.5):** Luôn sử dụng `asyncio.gather` cho các tác vụ độc lập trong Input Layer (PII check, Topic check, Injection check) để ép Latency xuống mức thấp nhất.

---

## 7. Sản phẩm bàn giao sau khi hoàn thành
1.  **`README.md`**: Tổng quan dự án, kết quả các phase, hướng dẫn setup.
2.  **`blueprint.md`**: Tài liệu kiến trúc và vận hành chi tiết.
3.  **`prompts.md`**: Lưu trữ toàn bộ prompt đã sử dụng.
4.  **`run_guide.md`**: Hướng dẫn chạy từng bước từ cài đặt đến benchmark.
