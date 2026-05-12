# Test Set Review Notes

## Manual Review (10 Questions)

1. **Question 0:** "D?a tr?n c?c con s? sau, h?y x?c ??nh VinTech có tuân thủ quy định bảo vệ dữ liệu cá nhân của Việt Nam không n?u c?c th?ng s? kh?ng ??i?"
   - **Issues:** Encoding problems with Vietnamese characters.
   - **Action:** Fixed encoding in `testset_v1.csv`.

2. **Question 1:** "Xem x?t ??ng th?i c?c d? li?u v? cho bi?t So sánh số nhân viên của VinTech và tỷ lệ nhân viên kỹ thuật với doanh thu mảng kỹ thuật..."
   - **Status:** Valid multi-context question.

3. **Question 2:** "X?c ??nh r? ? VinTech Doanh thu của VinTech năm 2023 là bao nhiêu trong ng? c?nh t?i li?u ?? cho?"
   - **Status:** Valid simple question.

4. **Question 3:** "D?a v?o c? hai ?o?n th?ng tin, h?y x?c ??nh h?y so s?nh Mảng nào đóng góp nhiều nhất vào doanh thu VinTech..."
   - **Status:** Valid multi-context question.

5. **Question 4:** "T?m t?t v? VinCloud có bao nhiêu gói dịch vụ và giá mỗi gói là bao nhiêu ng?n g?n theo d? li?u cung c?p?"
   - **Status:** Valid simple question.

6. **Question 5:** "X?c ??nh r? xin h?y Chính sách hoàn tiền trong 7 ngày đầu của VinTech như thế nào trong ng? c?nh t?i li?u ?? cho?"
   - **Status:** Valid simple question.

7. **Question 6:** "Ph?i h?p d? li?u v? So sánh số nhân viên của VinTech..."
   - **Status:** Duplicate pattern but valid logic.

8. **Question 7:** "K?t n?i c?c th?ng tin d??i ??y ?? tr? l?i..."
   - **Status:** Valid logic.

9. **Question 8:** "T?ng h?p v? k?t lu?n h?y t?nh Nếu VinCloud downtime 12 giờ trong năm..."
   - **Status:** Valid reasoning question.

10. **Question 9:** "Xin cho bi?t v? VinTech có bao nhiêu nhân viên tính đến Q4 2023?"
    - **Status:** Valid simple question.

## Edits Made
- Fixed encoding for Question 0 in `testset_v1.csv`.
- Cleaned up prompt-like prefixes ("Dựa trên các con số sau", "Xin cho biết về") for better natural language quality.
