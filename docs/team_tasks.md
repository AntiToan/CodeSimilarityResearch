# PHÂN CÔNG NHIỆM VỤ
## Đề tài: Hệ thống phát hiện tương đồng mã nguồn C/C++

### Thành viên 1 — Baseline
- Nghiên cứu SequenceMatcher và các phương pháp so sánh chuỗi.
- Triển khai baseline.
- Kiểm thử và đánh giá.

### Thành viên 2 — CodeBERT
- Nghiên cứu Embedding, Transformer, CodeBERT.
- Triển khai tạo embedding.
- Tính Cosine Similarity.
- Thử nghiệm inference.

### Thành viên 3 — Token và Winnowing
- Nghiên cứu Tokenization, K-gram, Hashing, Winnowing.
- Xây dựng tokenizer.
- Triển khai Winnowing.
- Kiểm thử.

### Thành viên 4 — AST
- Nghiên cứu AST, CST và Tree-sitter.
- Xây dựng parser C++.
- Trích xuất đặc trưng cấu trúc.
- Triển khai AST Similarity.

### Công việc chung
- Thu thập và khảo sát dataset.
- Xây dựng dataset và nhãn.
- Thống nhất preprocessing.
- Tích hợp các thuật toán.
- Đánh giá thực nghiệm.
- Xây dựng ứng dụng.
- Viết báo cáo nghiên cứu.

### Quy định
- Mỗi thành viên làm việc trên branch riêng.
- Không commit trực tiếp lên main.
- Code cần có test.
- Mỗi module cần README hoặc tài liệu hướng dẫn.
- Điểm similarity thống nhất trong khoảng 0.0 đến 1.0.
- Thay đổi phải được review trước khi merge.