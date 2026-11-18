
from pathlib import Path


SUPPORTED_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252")


class SourceReadError(Exception):
    """Raised when a source file cannot be read or decoded."""


def normalize_source_text(text: str) -> str:
    """
    Normalize source text without changing its code structure.

    Operations:
    - Remove a BOM at the beginning of the text.
    - Convert CRLF and standalone CR line endings to LF.

    Comments, strings, indentation, and blank lines are preserved.
    """
    text = text.removeprefix("\ufeff")
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    return text


def read_source_file(file_path: str | Path) -> dict:
    """
    Read and normalize a source code file.

    Returns:
        {
            "content": normalized source text,
            "encoding": encoding used to decode the file,
            "original_size": original file size in bytes,
            "processed_size": normalized UTF-8 size in bytes,
        }

    Raises:
        SourceReadError: If the file cannot be read or decoded.
    """
    path = Path(file_path)

    try:
        raw_bytes = path.read_bytes()
    except OSError as exc:
        raise SourceReadError(
            f"Cannot read file '{path}': {exc}"
        ) from exc

    decoded_text = None
    selected_encoding = None

    for encoding in SUPPORTED_ENCODINGS:
        try:
            decoded_text = raw_bytes.decode(encoding, errors="strict")
            selected_encoding = encoding
            break
        except UnicodeDecodeError:
            continue

    if decoded_text is None:
        raise SourceReadError(
            f"Cannot decode file '{path}' using supported encodings: "
            f"{SUPPORTED_ENCODINGS}"
        )

    normalized_text = normalize_source_text(decoded_text)

    return {
        "content": normalized_text,
        "encoding": selected_encoding,
        "original_size": len(raw_bytes),
        "processed_size": len(normalized_text.encode("utf-8")),
    }
