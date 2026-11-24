"""II.4 smoke test: run the training loop with the real CodeBERT on 20 toy pairs.

Purpose: check that tokenizer, model, loss, optimiser, checkpointing and the
run report work end to end. The toy pairs are hand-written, so the losses
printed here are NOT research results and must not be reported.

Example (CPU is enough, a few minutes):
    python scripts/smoke_train_codebert.py --run-id II4-smoke-01
Outputs go to experiments/results/<run-id>/ (git-ignored).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.contrastive_model import BiEncoder  # noqa: E402
from src.models.train import PairExample, TrainConfig, train  # noqa: E402

TOY_PROGRAMS = [
    "#include <iostream>\nint main() {\n    int a, b;\n    std::cin >> a >> b;\n    std::cout << a + b;\n    return 0;\n}\n",
    "#include <iostream>\nint main() {\n    int n, x, best = -1000000;\n    std::cin >> n;\n    for (int i = 0; i < n; i++) {\n        std::cin >> x;\n        if (x > best) best = x;\n    }\n    std::cout << best;\n}\n",
    "#include <iostream>\nint main() {\n    int n;\n    long long f = 1;\n    std::cin >> n;\n    for (int i = 2; i <= n; i++) f *= i;\n    std::cout << f;\n}\n",
    "#include <iostream>\nint main() {\n    int n, a = 0, b = 1;\n    std::cin >> n;\n    for (int i = 0; i < n; i++) {\n        int t = a + b;\n        a = b;\n        b = t;\n    }\n    std::cout << a;\n}\n",
    "#include <iostream>\n#include <string>\n#include <algorithm>\nint main() {\n    std::string s;\n    std::cin >> s;\n    std::reverse(s.begin(), s.end());\n    std::cout << s;\n}\n",
    "#include <iostream>\n#include <string>\nint main() {\n    std::string s;\n    std::getline(std::cin, s);\n    int count = 0;\n    for (char c : s)\n        if (c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u') count++;\n    std::cout << count;\n}\n",
    "#include <iostream>\nint main() {\n    int n;\n    std::cin >> n;\n    bool prime = n > 1;\n    for (int d = 2; d * d <= n; d++)\n        if (n % d == 0) prime = false;\n    std::cout << (prime ? \"YES\" : \"NO\");\n}\n",
    "#include <iostream>\nint main() {\n    int n, a[100];\n    std::cin >> n;\n    for (int i = 0; i < n; i++) std::cin >> a[i];\n    for (int i = 0; i < n; i++)\n        for (int j = 0; j + 1 < n - i; j++)\n            if (a[j] > a[j + 1]) { int t = a[j]; a[j] = a[j + 1]; a[j + 1] = t; }\n    for (int i = 0; i < n; i++) std::cout << a[i] << ' ';\n}\n",
    "#include <iostream>\nint main() {\n    int x, y;\n    std::cin >> x >> y;\n    while (y != 0) {\n        int t = x % y;\n        x = y;\n        y = t;\n    }\n    std::cout << x;\n}\n",
    "#include <iostream>\n#include <string>\nint main() {\n    std::string s;\n    std::cin >> s;\n    bool ok = true;\n    for (size_t i = 0; i < s.size() / 2; i++)\n        if (s[i] != s[s.size() - 1 - i]) ok = false;\n    std::cout << (ok ? \"YES\" : \"NO\");\n}\n",
]


def whitespace_variant(code: str) -> str:
    """Type-1 style variant: tabs instead of 4 spaces, blank line after each '{'."""
    lines = []
    for line in code.replace("    ", "\t").split("\n"):
        lines.append(line)
        if line.rstrip().endswith("{"):
            lines.append("")
    return "\n".join(lines)


def toy_pairs() -> tuple[list[PairExample], list[PairExample]]:
    pairs = []
    for index, code in enumerate(TOY_PROGRAMS):
        pairs.append(PairExample(code, whitespace_variant(code), 1))
        pairs.append(PairExample(code, TOY_PROGRAMS[(index + 1) % len(TOY_PROGRAMS)], 0))
    # 16 train / 4 validation, both balanced.
    return pairs[:16], pairs[16:]


def main() -> int:
    parser = argparse.ArgumentParser(description="II.4 smoke test with real CodeBERT")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--model", default="microsoft/codebert-base")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--output-root", default="experiments/results")
    args = parser.parse_args()

    from transformers import AutoTokenizer

    config = TrainConfig(
        model_name=args.model,
        batch_size=4,
        epochs=args.epochs,
        device=args.device,
        run_id=args.run_id,
        dataset_version="toy",
        output_dir=str(Path(args.output_root) / args.run_id),
    )
    train_pairs, val_pairs = toy_pairs()
    tokenizer = AutoTokenizer.from_pretrained(config.model_name)
    model = BiEncoder.from_pretrained(config.model_name, pooling=config.pooling)

    result = train(model, tokenizer, train_pairs, val_pairs, config)

    for record in result.history:
        print(
            f"epoch {record.epoch}: train_loss={record.train_loss:.4f} "
            f"val_loss={record.val_loss:.4f} best={record.is_best}"
        )
    print(f"Best checkpoint: {result.best_checkpoint}")
    print("Toy data only: these numbers are a pipeline check, not research results.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
