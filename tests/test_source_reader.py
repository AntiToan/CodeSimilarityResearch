
import pytest

from src.preprocessing.source_reader import (
    SourceReadError,
    normalize_source_text,
    read_source_file,
)


def test_read_utf8_file(tmp_path):
    """Test reading a normal UTF-8 source file."""
    file_path = tmp_path / "test.cpp"
    content = '#include <iostream>\nint main() { return 0; }\n'

    file_path.write_bytes(content.encode("utf-8"))

    result = read_source_file(file_path)

    assert result["content"] == content
    assert result["encoding"] == "utf-8-sig"
    assert result["original_size"] == len(content.encode("utf-8"))
    assert result["processed_size"] == len(content.encode("utf-8"))


def test_read_utf8_bom_file(tmp_path):
    """Test reading a UTF-8 file with BOM."""
    file_path = tmp_path / "bom.cpp"
    content = '\ufeffint main() { return 0; }\n'

    file_path.write_bytes(content.encode("utf-8"))

    result = read_source_file(file_path)

    assert result["content"] == 'int main() { return 0; }\n'
    assert result["encoding"] == "utf-8-sig"


def test_read_cp1252_file(tmp_path):
    """Test fallback decoding using cp1252."""
    file_path = tmp_path / "cp1252.cpp"
    content = "// café\nint main() { return 0; }\n"

    file_path.write_bytes(content.encode("cp1252"))

    result = read_source_file(file_path)

    assert result["content"] == content
    assert result["encoding"] == "cp1252"


def test_normalize_line_endings():
    """Test normalization of CRLF and CR to LF."""
    original = "line1\r\nline2\rline3\n"
    expected = "line1\nline2\nline3\n"

    result = normalize_source_text(original)

    assert result == expected


def test_preserve_comments_and_strings():
    """Test that comments and string literals are preserved."""
    content = (
        '// This is a comment\n'
        'const char* message = "Hello World";\n'
        '/* Multi-line\n'
        '   comment */\n'
    )

    result = normalize_source_text(content)

    assert result == content
    assert "// This is a comment" in result
    assert '"Hello World"' in result
    assert "/* Multi-line" in result


def test_read_nonexistent_file():
    """Test error handling for a nonexistent file."""
    with pytest.raises(SourceReadError):
        read_source_file("this_file_does_not_exist.cpp")


def test_unsupported_encoding_file(tmp_path):
    """Test error handling when all supported decoders fail."""
    file_path = tmp_path / "unsupported.cpp"

    # UTF-8 and cp1252 cannot decode this byte sequence.
    file_path.write_bytes(b"\x81")

    with pytest.raises(SourceReadError):
        read_source_file(file_path)
