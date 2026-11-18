
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score
from tree_sitter import Language, Parser


def test_numpy():
    result = np.array([1, 2, 3])
    assert result.sum() == 6


def test_pandas():
    df = pd.DataFrame({"code": ["a", "b", "c"]})
    assert len(df) == 3


def test_sklearn():
    y_true = [1, 0, 1]
    y_pred = [1, 0, 0]

    score = accuracy_score(y_true, y_pred)

    assert score == 2 / 3


def test_tree_sitter():
    parser = Parser()
    assert parser is not None

# python -m pytest tests/test_environment.py -v