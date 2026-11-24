# Phase II — Model Development (CodeBERT / UniXcoder)

## Trạng thái

Phase II **chưa bắt đầu chính thức**: fine-tune và đánh giá chỉ chạy khi dataset pairs đã freeze (sau I.8/I.9). Branch `phase2/codebert-embedding` chỉ chuẩn bị phần không cần dataset của II.1 và II.2.

## Thứ tự checkpoint

| ID | Nội dung | Làm ngay được | Phải chờ dataset freeze |
|---|---|---|---|
| II.1 | Research baseline & model selection | Đọc CodeBERT, UniXcoder, contrastive learning; ghi tóm tắt | Chốt mô hình dựa trên số đo validation |
| II.2 | Code representation & feature strategy | Module embedding (`src/algorithms/codebert.py`), đo tỷ lệ code bị cắt ở 512 token | So sánh pooling CLS/mean, Raw/Basic trên validation |
| II.3 | Model architecture | Phác thảo kiến trúc mã hóa đôi (bi-encoder) dùng chung trọng số | Chốt kiến trúc |
| II.4 | Training pipeline | Viết vòng lặp huấn luyện, chạy thử trên vài cặp giả | Huấn luyện thật |
| II.5 | Validation & hyperparameter tuning | — | Có |
| II.6 | Model checkpointing | Quy ước tên và nơi lưu checkpoint | Có |
| II.7 | Baseline evaluation | — | Có (embedding chưa fine-tune trên validation) |
| II.8 | Error analysis & refinement | — | Có |

## Quy ước

- Điểm tương đồng: `score = (cosine + 1) / 2`, nằm trong [0, 1], đối xứng, tất định (mô hình ở chế độ `eval`).
- Ngưỡng chọn trên validation rồi cố định trước khi chạy test; không mặc định ngưỡng 0.8.
- Seed 42. Mỗi lần chạy lưu config, commit, phiên bản dataset, phiên bản torch/transformers và loại GPU vào `experiments/results/<run_id>/` (thư mục này bị `.gitignore`).
- Không commit trọng số mô hình; lưu trên Google Drive hoặc Kaggle và ghi đường dẫn vào kết quả.
- Tên checkpoint: `<model>-<dataset_version>-<run_id>-ep<k>`; giữ bản tốt nhất theo metric trên validation.
- Cấu hình khởi điểm khi fine-tune: batch 8, learning rate 2e-5, 2–3 epoch, AdamW, contrastive loss, chạy thử 1.000–2.000 cặp trước.

## Cài đặt

```powershell
# 1. Cài PyTorch theo hướng dẫn tại https://pytorch.org (bản CPU là đủ để chạy thử)
# 2. Cài transformers
python -m pip install -r requirements-ml.txt
```

Trên Google Colab đã có sẵn PyTorch; chỉ cần `pip install transformers==4.46.3`.

## Dùng module embedding

```python
from src.algorithms.codebert import CodeEmbedder, EmbeddingConfig, similarity_matrix

embedder = CodeEmbedder(EmbeddingConfig(pooling="cls", device="cpu"))
codes = [open(p, encoding="utf-8").read() for p in paths]

print(embedder.truncation_stats(codes))        # bao nhiêu code dài hơn 512 token
vectors = embedder.embed(codes)                 # (N, 768), đã chuẩn hóa L2
scores = similarity_matrix(vectors)             # ma trận điểm (N, N) trong [0, 1]
```

Cấu hình thí nghiệm zero-shot: `experiments/configs/codebert_zero_shot.json` (`dataset_version` điền sau khi freeze).

## Test

```powershell
python -m pytest tests/test_codebert_embedding.py -v      # không cần torch
$env:RUN_MODEL_TESTS = "1"; python -m pytest tests/test_codebert_embedding.py -v   # tải CodeBERT (~500 MB) và chạy thật
```
