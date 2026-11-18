
# Code Similarity Research

## 1. Project Overview

This project focuses on source code similarity detection
using traditional algorithms, structural analysis, and
pre-trained language models.

## 2. Research Components

- Code preprocessing
- Token-based similarity
- Winnowing
- Greedy String Tiling (GST)
- AST-based similarity analysis
- CodeBERT-based similarity detection
- Model evaluation

## 3. Project Structure

```text
CodeSimilarityResearch/
├── config/
├── data/
├── src/
├── backend/
├── frontend/
├── experiments/
├── tests/
├── docs/
├── scripts/
├── requirements.txt
└── README.md
```

## 4. Environment Setup

Python 3.12.5

Create virtual environment:

```bash
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## 5. Run Environment Validation

```bash
python scripts/check_environment.py
```

## 6. Run Tests

```bash
python -m pytest tests/ -v
```

## 7. Development Environment

- Python
- VS Code
- Git
- Google Colab (optional for ML experiments)
