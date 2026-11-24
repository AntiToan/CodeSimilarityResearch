# Phase II — Model Development (CodeBERT / UniXcoder)

## Trạng thái

Phase II **chưa bắt đầu chính thức**: fine-tune và đánh giá chỉ chạy khi dataset pairs đã freeze (sau I.8/I.9). Branch `phase2/part-a` làm phần không cần dataset:

| Checkpoint | Đã có | File |
|---|---|---|
| II.1 | Tóm tắt CodeBERT, UniXcoder, contrastive loss; thứ tự chọn mô hình | `docs/phase2/II1_model_selection.md` |
| II.2 | Module embedding; đo độ dài token của POJ-104 | `src/algorithms/codebert.py`, `scripts/measure_truncation.py`, `docs/phase2/II2_representation.md` |
| II.3 | Bi-encoder dùng chung trọng số, contrastive loss | `src/models/contrastive_model.py` |
| II.4 (khung) | Vòng lặp huấn luyện, chạy thử với CodeBERT trên 20 cặp đồ chơi | `src/models/train.py`, `scripts/smoke_train_codebert.py` |
| II.6 (quy ước) | Tên checkpoint, chỉ giữ bản tốt nhất, không ghi đè lần chạy cũ | `src/models/train.py` |
| Test | Không cần tải mô hình | `tests/test_codebert_embedding.py`, `tests/test_phase2_models.py` |

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

## Huấn luyện (II.4) và checkpoint (II.6)

```python
from transformers import AutoTokenizer
from src.models.contrastive_model import BiEncoder
from src.models.train import PairExample, TrainConfig, train

config = TrainConfig(run_id="r01", dataset_version="v1.0", device="cuda",
                     output_dir="/content/drive/MyDrive/codesim/r01")
tokenizer = AutoTokenizer.from_pretrained(config.model_name)
model = BiEncoder.from_pretrained(config.model_name, pooling=config.pooling)
result = train(model, tokenizer, train_pairs, val_pairs, config)   # list[PairExample]
```

- Checkpoint lưu tại `<output_dir>/<model>-<dataset_version>-<run_id>-ep<k>/`; chỉ giữ bản có validation loss thấp nhất của lần chạy.
- `<output_dir>/run_report.json` ghi config, loss từng epoch, commit, phiên bản Python/torch/transformers, GPU.
- Thư mục đã có kết quả thì không ghi đè: lần chạy mới cần `run_id` hoặc `output_dir` mới.
- Hiện chọn checkpoint theo validation loss; khi có cặp validation thật (sau freeze), II.5 đổi sang F1 trên validation.
- Chạy thử toàn bộ đường đi với CodeBERT thật (chỉ để kiểm tra code, **không** phải kết quả nghiên cứu):
  `python scripts/smoke_train_codebert.py --run-id II4-smoke-01`

## Test

```powershell
python -m pytest tests/test_codebert_embedding.py -v      # không cần torch
python -m pytest tests/test_phase2_models.py -v           # cần torch + transformers, không tải mô hình
$env:RUN_MODEL_TESTS = "1"; python -m pytest tests/test_codebert_embedding.py -v   # tải CodeBERT (~500 MB) và chạy thật
```
