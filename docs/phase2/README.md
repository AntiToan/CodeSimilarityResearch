# Phase II — Model Development (CodeBERT / UniXcoder)

## Trạng thái

**Code của Phase II đã đủ cho cả 8 checkpoint**, đã kiểm tra bằng test và chạy thử đầu cuối trên dữ liệu giả. **Chưa có kết quả nghiên cứu nào.** Huấn luyện thật, chọn siêu tham số và đánh giá chỉ chạy khi dataset pairs đã freeze (luật 16). Hiện Phase I chưa có bộ xuất `pair_index.csv` (audit I.9 ghi là chưa cài).

| Checkpoint | Đã có | Còn chờ dataset freeze | File |
|---|---|---|---|
| II.1 | Tóm tắt CodeBERT, UniXcoder (đã đối chiếu repo chính thức), contrastive loss | Chốt mô hình theo số đo validation | `docs/phase2/II1_model_selection.md` |
| II.2 | Module embedding (CodeBERT, UniXcoder encoder-only); đo độ dài token POJ-104 | So sánh CLS/mean, Raw/Basic trên validation | `src/algorithms/codebert.py`, `scripts/measure_truncation.py`, `docs/phase2/II2_representation.md` |
| II.3 | Bi-encoder dùng chung trọng số, contrastive loss | Chốt kiến trúc | `src/models/contrastive_model.py` |
| II.4 | Vòng lặp huấn luyện, CLI huấn luyện | Huấn luyện thật | `src/models/train.py`, `scripts/train_encoder.py` |
| II.5 | Chọn epoch theo F1 trên validation, chọn ngưỡng, grid siêu tham số | Chạy grid | `src/evaluation/metrics.py`, `src/models/tuning.py`, `experiments/configs/codebert_finetune.json` |
| II.6 | Tên checkpoint, chỉ giữ bản tốt nhất, lưu ngưỡng và cách mã hóa trong checkpoint | — | `src/models/train.py` |
| II.7 | Đánh giá zero-shot và fine-tune: P, R, F1, ROC-AUC, AP, thời gian chạy | Chạy trên validation | `scripts/evaluate_encoder.py`, `src/models/pair_scoring.py` |
| II.8 | Bảng FP/FN theo loại cặp, loại biến đổi, bài toán | Phân tích trên kết quả thật | `src/evaluation/error_analysis.py`, `scripts/analyze_errors.py` |
| Dữ liệu | Đọc bản export của Phase I, kiểm tra fail-closed | Khớp với bộ xuất thật của I.9 | `src/models/pair_dataset.py` |

## Quy trình sau khi dataset freeze

1. **Điền `dataset_version`** (ví dụ `"v1.0"`) vào các file trong `experiments/configs/`. Để trống thì mọi script từ chối chạy; `--allow-unfrozen` chỉ dành cho chạy thử.
2. **II.7 — baseline zero-shot trên validation:**
   ```powershell
   python scripts/evaluate_encoder.py --config experiments/configs/codebert_zero_shot.json --run-id II7-codebert-zs-val-01
   python scripts/evaluate_encoder.py --config experiments/configs/unixcoder_zero_shot.json --run-id II7-unixcoder-zs-val-01
   ```
3. **II.5 — pilot rồi grid** (nên chạy trên Colab/Kaggle GPU):
   ```powershell
   python scripts/train_encoder.py --config experiments/configs/codebert_finetune.json --run-id II5-pilot-01 --device cuda --max-train-pairs 2000
   python scripts/train_encoder.py --config experiments/configs/codebert_finetune.json --run-id II5-grid-01 --device cuda
   ```
   `tuning_report.json` ghi kết quả từng trial và trial tốt nhất (F1 validation cao nhất, hòa thì validation loss thấp hơn).
4. **II.7 — đánh giá checkpoint tốt nhất trên validation:**
   ```powershell
   python scripts/evaluate_encoder.py --config experiments/configs/codebert_finetune.json --checkpoint <thư mục checkpoint> --run-id II7-codebert-ft-val-01 --device cuda
   ```
5. **II.8 — phân tích lỗi:**
   ```powershell
   python scripts/analyze_errors.py --run-dir experiments/results/II7-codebert-ft-val-01
   ```
6. **Tập test thuộc III.2**, chỉ chạy một lần cho mô hình đã chốt:
   - cần `--threshold-from` (file kết quả validation chứa ngưỡng) và `--confirm-test`;
   - mỗi lần chạy được ghi thêm một dòng vào `experiments/results/test_runs.log`.

Mỗi lần chạy tạo thư mục `experiments/results/<run-id>/` mới (không ghi đè). Thư mục chứa:
- config, commit, phiên bản thư viện, GPU;
- `dataset_version` và sha256 của các file dataset.

## Phase I cần xuất gì

Bộ đọc `src/models/pair_dataset.py` theo đúng thiết kế trong `docs/pair_design_merged_v3.md` ("Output Structure"):

| File | Nội dung cần có |
|---|---|
| `data/pairs/pair_index.csv` | `pair_id, sample_a_id, sample_b_id, label, pair_type, split, problem_a_id, problem_b_id, generation_method` (cột khác được giữ lại để phân tích) |
| `data/pairs/splits/{train,validation,test}.csv` | cột `pair_id` |
| `data/processed/poj104/metadata/samples.csv` | `sample_id, source_path, status`; `source_path` tương đối so với `data/processed` |
| `data/processed/poj104/metadata/source_splits.csv` | `sample_id, split` |
| `data/processed/poj104/metadata/variant_registry.csv` | `variant_id, split, transformation_type, validation_status, source_path, source_hash` |

Đọc dữ liệu theo nguyên tắc fail-closed: thiếu cột, thiếu file, sai hash, cặp lặp, split lệch, đường dẫn ra ngoài thư mục, bài lỗi hoặc biến thể không PASS đều làm dừng chương trình.

**Lưu ý cho I.9:**
- `variant_registry.csv` hiện lưu **đường dẫn tuyệt đối** của máy chạy pipeline. Đem dataset sang Colab thì các đường dẫn đó không còn đúng.
- Đề nghị bộ xuất cuối ghi `source_path` **tương đối** so với `data/processed/poj104/variants`.
- Nếu tên cột khác bảng trên, chỉ cần sửa một chỗ trong `src/models/pair_dataset.py`.

## Quy ước

- Điểm tương đồng: `score = (cosine + 1) / 2`, nằm trong [0, 1], đối xứng, tất định (mô hình ở chế độ `eval`). Cặp được coi là giống khi `score >= threshold`.
- Ngưỡng là giá trị cho F1 cao nhất trên validation; nếu hòa thì lấy ngưỡng cao hơn, để ít cặp bị đánh dấu nhầm hơn. Ngưỡng được cố định trước khi chạy test; không mặc định 0.8.
- Seed 42. Không commit trọng số mô hình: lưu trên Google Drive hoặc Kaggle và ghi đường dẫn vào kết quả.
- Tên checkpoint: `<model>-<dataset_version>-<run_id>-ep<k>`. File `bi_encoder.json` trong checkpoint ghi:
  - cách pooling, token chế độ, độ dài tối đa;
  - ngưỡng chọn trên validation.
- **CodeBERT:** `pooling="cls"`, `mode_token=null`.
- **UniXcoder:** `pooling="mean"`, `mode_token="<encoder-only>"`, đúng như `unixcoder.py` chính thức. `unixcoder-base` không được huấn luyện trên C/C++; `unixcoder-base-nine` thì có (xem II.1).
- Chế độ tiền xử lý hiện chỉ có `raw`. Chế độ `basic` sẽ dùng module tiền xử lý chung (skill `similarity-engine`) khi module đó có.

## Chạy trên Google Colab

```python
!git clone https://github.com/thannhf/CodeSimilarityResearch.git   # sau khi PR Phase II được merge
%cd CodeSimilarityResearch
!pip install -q transformers==4.46.3
from google.colab import drive; drive.mount('/content/drive')
# Chép dataset đã freeze (data/pairs, data/processed) vào đúng thư mục trong repo, rồi:
!python scripts/train_encoder.py --config experiments/configs/codebert_finetune.json \
    --run-id II5-grid-01 --device cuda --output-root /content/drive/MyDrive/codesim
```

Colab đã có sẵn PyTorch. Kết quả và checkpoint nằm trên Drive, không mất khi phiên Colab kết thúc.

## Chạy thử (không phải kết quả nghiên cứu)

```powershell
python scripts/smoke_phase2_pipeline.py --run-id II-smoke-01                      # CodeBERT
python scripts/smoke_phase2_pipeline.py --run-id II-smoke-02 --model microsoft/unixcoder-base --pooling mean --mode-token "<encoder-only>"
```

Script này:
- tạo một dataset giả theo đúng bố cục Phase I (`src/models/toy_export.py`);
- chạy lần lượt đánh giá zero-shot, fine-tune, đánh giá checkpoint, phân tích lỗi;
- kiểm tra rằng lệnh chạy test thiếu ngưỡng bị từ chối.

## Cài đặt

```powershell
# 1. Cài PyTorch theo hướng dẫn tại https://pytorch.org (bản CPU là đủ để chạy thử)
# 2. Cài transformers, datasets
python -m pip install -r requirements-ml.txt
```

## Dùng module embedding trực tiếp

```python
from src.algorithms.codebert import CodeEmbedder, EmbeddingConfig, similarity_matrix

embedder = CodeEmbedder(EmbeddingConfig(pooling="cls", device="cpu"))
vectors = embedder.embed(codes)            # (N, 768), đã chuẩn hóa L2
scores = similarity_matrix(vectors)        # ma trận điểm (N, N) trong [0, 1]

fine_tuned = CodeEmbedder(EmbeddingConfig.from_checkpoint("<thư mục checkpoint>"))
```

## Test

```powershell
python -m pytest tests/test_codebert_embedding.py tests/test_phase2_evaluation.py tests/test_pair_dataset.py -v   # không cần torch
python -m pytest tests/test_phase2_models.py -v           # cần torch + transformers, không tải mô hình
$env:RUN_MODEL_TESTS = "1"; python -m pytest tests/test_codebert_embedding.py -v   # tải CodeBERT (~500 MB) và chạy thật
```
