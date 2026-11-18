
import sys
import importlib.metadata

PACKAGES = [
    "numpy",
    "pandas",
    "scikit-learn",
    "matplotlib",
    "seaborn",
    "PyYAML",
    "tqdm",
    "tree-sitter",
    "pytest",
    "jupyter",
    "ipykernel",
]

def check_environment():
    print("=" * 50)
    print("CODE SIMILARITY RESEARCH")
    print("ENVIRONMENT VALIDATION")
    print("=" * 50)

    print(f"\nPython version: {sys.version}")
    print(f"Python executable: {sys.executable}")

    print("\nInstalled packages:")

    for package in PACKAGES:
        try:
            version = importlib.metadata.version(package)
            print(f"[OK] {package}: {version}")
        except importlib.metadata.PackageNotFoundError:
            print(f"[MISSING] {package}")

    print("\nEnvironment check completed.")

if __name__ == "__main__":
    check_environment()

# python scripts/check_environment.py