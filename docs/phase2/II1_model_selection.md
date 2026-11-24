# II.1 — Research baseline & model selection

Tài liệu tóm tắt để chọn mô hình biểu diễn mã nguồn cho Phase II. Chỉ ghi những điểm đã đối chiếu với bài báo gốc; mục nào cần kiểm tra lại được đánh dấu **[cần kiểm tra]**. Không có số liệu thực nghiệm nào trong tài liệu này.

## 1. CodeBERT

- **Nguồn:** Feng và cộng sự, *CodeBERT: A Pre-Trained Model for Programming and Natural Languages*, Findings of EMNLP 2020. Mô hình: `microsoft/codebert-base`.
- **Kiến trúc:** giống RoBERTa-base: 12 lớp Transformer encoder, kích thước ẩn 768, 12 attention head, khoảng 125 triệu tham số. Vector đầu ra mỗi đoạn code có 768 chiều.
- **Dữ liệu tiền huấn luyện:** CodeSearchNet, gồm 6 ngôn ngữ: Python, Java, JavaScript, PHP, Ruby, Go. **Không có C/C++.**
- **Mục tiêu tiền huấn luyện:** Masked Language Modeling và Replaced Token Detection.
- **Giới hạn đầu vào:** 512 token (gồm token đặc biệt). Code dài hơn bị cắt, xem II.2.
- **Ý nghĩa với đề tài:** vì không được học trên C/C++, embedding zero-shot của CodeBERT cho bài C/C++ có thể kém. Đây là lý do cần đo baseline zero-shot (II.7) trước, rồi mới fine-tune để so sánh.

## 2. UniXcoder

- **Nguồn:** Guo và cộng sự, *UniXcoder: Unified Cross-Modal Pre-training for Code Representation*, ACL 2022. Mô hình: `microsoft/unixcoder-base`.
- **Đặc điểm:**
  - Dùng chung một Transformer cho ba chế độ: chỉ encoder, chỉ decoder, encoder-decoder. Chế độ được chọn bằng token đặc biệt ở đầu chuỗi và mặt nạ attention.
  - Khi tiền huấn luyện có dùng thông tin AST và comment, cùng contrastive learning để học vector đại diện cho cả đoạn code.
  - Bài báo có đánh giá clone detection trên POJ-104.
- **Cách dùng đúng:** tạo embedding theo hướng dẫn trong repo chính thức của UniXcoder (chế độ encoder-only, cách pooling). Không dùng `AutoModel` rồi lấy `[CLS]` như CodeBERT khi chưa đối chiếu **[cần kiểm tra]**.
- **Dữ liệu tiền huấn luyện có C/C++ hay không:** **[cần kiểm tra]** trong bài báo trước khi viết vào báo cáo.

## 3. Hàm mất mát contrastive

- **Nguồn:** Hadsell, Chopra, LeCun, *Dimensionality Reduction by Learning an Invariant Mapping*, CVPR 2006.
- **Ý tưởng:** mạng "siamese" gồm hai nhánh dùng chung trọng số. Cặp giống nhau bị kéo lại gần; cặp khác nhau bị đẩy ra xa tới khi khoảng cách vượt một biên (margin).
- **Dạng dùng trong đề tài** (theo cosine, vì vector đã chuẩn hóa L2):
  - cặp positive (nhãn 1): `loss = (1 − cos)²`
  - cặp negative (nhãn 0): `loss = max(0, cos − margin)²`
  - Cài đặt: `src/models/contrastive_model.py`, `contrastive_loss`.
- **Phương án khác để thử sau:** InfoNCE với in-batch negatives. Khi dùng phải loại khỏi mẫu âm những mẫu cùng `parent_id` hoặc cùng nhóm duplicate, để tránh "âm giả".

## 4. Lựa chọn cho đề tài

| Bước | Mô hình | Lý do |
|---|---|---|
| 1 | CodeBERT zero-shot (chưa fine-tune) | Baseline bắt buộc trước khi fine-tune |
| 2 | CodeBERT fine-tune bằng contrastive loss | Phương pháp chính trong đề cương |
| 3 | UniXcoder (zero-shot, rồi fine-tune) | Thử khi pipeline đã ổn định; so sánh với CodeBERT |

- Kiến trúc dùng cho cả hai mô hình: **bi-encoder** (mỗi đoạn code mã hóa riêng bằng cùng một encoder, so sánh bằng cosine). Cách này cho phép tính vector một lần cho mỗi bài rồi so mọi cặp trong lô, phù hợp với ứng dụng (n bài cho n(n−1)/2 cặp).
- Không huấn luyện mạng từ đầu; không huấn luyện song song hai mô hình ngay từ đầu.
- Mô hình cuối cùng được chọn theo kết quả trên **validation**, sau khi dataset pairs freeze.

## 5. Việc còn mở

- Đối chiếu các mục **[cần kiểm tra]** với bài báo UniXcoder.
- Nhóm cần chốt độ phủ dataset (hiện chỉ có biến thể Type-1) trước khi fine-tune; nếu không, kết quả fine-tune không chứng minh được mục tiêu Type-2, Type-3 và bài viết lại bằng LLM.
