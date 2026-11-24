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
- **Cách tạo embedding** (đã đối chiếu với `UniXcoder/unixcoder.py` trong https://github.com/microsoft/CodeBERT):
  - Đầu vào là `<s> <encoder-only> </s>` + token của code + `</s>`. Code bị cắt còn `max_length − 4` token trước khi thêm token đặc biệt.
  - Vector của cả đoạn code là **trung bình các token không phải padding** (mean pooling), không phải `[CLS]`. README chuẩn hóa L2 trước khi tính cosine.
  - Script fine-tune POJ-104 trong cùng repo cũng dùng mean pooling rồi chuẩn hóa L2, với `block_size 400`.
  - Script đó viết token chế độ là `<encoder_only>` (gạch dưới). Với tokenizer của `microsoft/unixcoder-base`, chuỗi này thành `<unk>` (id 3), còn `<encoder-only>` là token riêng (id 6). Đề tài dùng `<encoder-only>` như `unixcoder.py`.
  - Cài đặt: `mode_token="<encoder-only>"` và `pooling="mean"` trong `EmbeddingConfig`/`TrainConfig`; cấu hình mẫu ở `experiments/configs/unixcoder_zero_shot.json`. Mô hình tải được bằng `AutoModel` (kiến trúc RoBERTa).
- **Dữ liệu tiền huấn luyện** (README của UniXcoder trong cùng repo):
  - `unixcoder-base`: "The model can support six languages: java, ruby, python, php, javascript, and go." **Không có C/C++.**
  - `unixcoder-base-nine`: thêm "1.5M NL-PL pairs of C, C++ and C# programming language".
  - Với bài C/C++, `microsoft/unixcoder-base-nine` có thể phù hợp hơn. Đổi mô hình trong stack là việc nhóm quyết; nên đo cả hai trên validation.

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

- Chọn `unixcoder-base` hay `unixcoder-base-nine` (hoặc đo cả hai) cho bước 3.
- Nhóm cần chốt độ phủ dataset (hiện chỉ có biến thể Type-1) trước khi fine-tune; nếu không, kết quả fine-tune không chứng minh được mục tiêu Type-2, Type-3 và bài viết lại bằng LLM.
