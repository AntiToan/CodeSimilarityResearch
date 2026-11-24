# II.2 — Code representation & feature strategy

## 1. Biểu diễn đã chọn để bắt đầu

- Mỗi chương trình được mã hóa riêng bằng CodeBERT (`microsoft/codebert-base`) thành một vector 768 chiều, chuẩn hóa L2. Điểm của một cặp là `(cosine + 1) / 2`, nằm trong [0, 1].
- Pooling: bắt đầu với `[CLS]`; mean pooling (có attention mask) là phương án so sánh. Chọn cách nào là việc của validation (II.7), sau khi dataset freeze.
- Đầu vào: so sánh code ở chế độ Raw và Basic (bỏ comment, chuẩn hóa định dạng), cũng trên validation.
- Cài đặt: `src/algorithms/codebert.py` (zero-shot) và `src/models/contrastive_model.py` (fine-tune). Hai file dùng cùng một cách pooling.

## 2. Đo độ dài token của POJ-104

**Cách đo:** đếm số token của từng chương trình bằng tokenizer của CodeBERT, **tính cả 2 token đặc biệt**, rồi so với giới hạn 512.

**Nguồn số liệu:** `experiments/results/II2-truncation-codebert-02/truncation.json`. Thư mục `experiments/results` không commit; chạy lại lệnh bên dưới để tạo lại file.

| Mục | Giá trị |
|---|---|
| Dữ liệu | `google/code_x_glue_cc_clone_detection_poj104` trên Hugging Face, revision `701869dece36b32174ee48277eada423cdcf699c` |
| Tokenizer | `microsoft/codebert-base`, transformers 4.46.3, datasets 5.0.1, Python 3.12.10 |
| Commit của script | `eaf0cd4` |
| Lệnh | `python scripts/measure_truncation.py --run-id II2-truncation-codebert-02` |

**Kết quả trên 52.000 chương trình** (mỗi chương trình tính một lần):

| Số chương trình | Dài hơn 512 token | Tỷ lệ | Trung vị | P90 | P95 | P99 | Dài nhất |
|---|---|---|---|---|---|---|---|
| 52.000 | 13.585 | 26,1% | 370 | 730 | 919 | 1.550 | 10.512 |

**Theo split, đúng như bản Hugging Face công bố** (gồm cả phần bị lặp, xem mục 3):

| Split | Số dòng | Dài hơn 512 | Tỷ lệ | Trung vị | Dài nhất |
|---|---|---|---|---|---|
| train | 32.500 | 8.210 | 25,3% | 362 | 6.871 |
| validation | 8.500 | 2.828 | 33,3% | 425 | 10.512 |
| test | 12.000 | 2.662 | 22,2% | 351 | 6.763 |

**Nhận xét:**
- Khoảng **một phần tư** số chương trình bị cắt nếu chỉ đưa 512 token đầu vào CodeBERT. Phần bị mất là phần cuối chương trình, nơi thường chứa phần thân thuật toán.
- Tỷ lệ này đủ lớn để thêm một ablation ở II.5/II.7: chia chương trình thành các đoạn 512 token rồi gộp vector (ví dụ lấy trung bình), so với cách cắt đơn giản.
- Đây là thống kê trên POJ-104 gốc, chưa phải trên dataset pairs của nhóm. Khi dataset freeze, cần đo lại trên đúng các mẫu và biến thể trong dataset.

## 3. Lỗi của bản POJ-104 trên Hugging Face

- Bản này có **53.000 dòng**, trong khi CodeXGLUE công bố 52.000 chương trình (64/16/24 bài toán).
- Nguyên nhân: các split chồng lên nhau ở ranh giới.
  - Train gồm bài toán 1–65, validation gồm 65–81, test gồm 81–104.
  - 500 chương trình của **bài 65** có mặt nguyên vẹn ở cả train và validation.
  - 500 chương trình của **bài 81** có mặt ở cả validation và test.
  - Đã kiểm tra bằng sha256 của code: hai tập trùng khớp hoàn toàn.
- **Hệ quả:** nếu dùng thẳng các split của bản Hugging Face để đánh giá theo giao thức CodeXGLUE (MAP@R), sẽ có rò rỉ dữ liệu giữa train, validation và test.
- **Khuyến nghị:**
  - Pipeline Phase I của nhóm dùng dữ liệu gốc và tự chia split theo Decision 1, nên không bị ảnh hưởng.
  - Không dùng bản Hugging Face cho bất kỳ số liệu nào đưa vào báo cáo, trừ khi đã loại phần lặp như script này làm.
- Ngoài ra, trong 52.000 chương trình có 51.995 chuỗi code khác nhau, tức có vài chương trình trùng y hệt. Việc này khớp với chính sách duplicate của Phase I (Decision 2).
