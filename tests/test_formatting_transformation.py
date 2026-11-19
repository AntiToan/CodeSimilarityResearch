from src.transformations import FormattingTransformation

def test_transformation_name():
    transformation = FormattingTransformation()
    assert transformation.name == "formatting"

def test_normalizes_leading_tabs():
    source = "\tint x = 10;\n"

    result = FormattingTransformation().transform(source)

    assert result.transformed_text == "    int x = 10;\n"
    assert result.changed is True

def test_removes_trailing_whitespace_from_safe_code():
    source = "int x = 10;   \nint y = 20;\t\n"

    result = FormattingTransformation().transform(source)

    assert result.transformed_text == "int x = 10;\nint y = 20;\n"

def test_preserves_string_literal_line():
    source = '\tcout << "hello   world";   \n'

    result = FormattingTransformation().transform(source)

    assert result.transformed_text == source

def test_preserves_line_comment():
    source = "\t// comment with trailing spaces   \n"

    result = FormattingTransformation().transform(source)

    assert result.transformed_text == source

def test_preserves_block_comment():
    source = (
        "\t/* comment start   \n"
        "\t   content   \n"
        "\t*/   \n"
        "\tint x = 1;   \n"
    )

    result = FormattingTransformation().transform(source)

    assert result.transformed_text == (
        "\t/* comment start   \n"
        "\t   content   \n"
        "\t*/   \n"
        "    int x = 1;\n"
    )

def test_preserves_preprocessor_directive():
    source = "#include <iostream>   \n"

    result = FormattingTransformation().transform(source)

    assert result.transformed_text == source

def test_preserves_macro_continuation():
    source = (
        "#define ADD(a, b) \\\n"
        "\t((a) + (b))   \n"
        "\tint x = 1;   \n"
    )

    result = FormattingTransformation().transform(source)

    assert result.transformed_text == (
        "#define ADD(a, b) \\\n"
        "\t((a) + (b))   \n"
        "    int x = 1;\n"
    )

def test_preserves_crlf_line_endings():
    source = "\tint x = 1;   \r\n"

    result = FormattingTransformation().transform(source)

    assert result.transformed_text == "    int x = 1;\r\n"

def test_original_source_is_unchanged():
    source = "\tint x = 1;   \n"

    result = FormattingTransformation().transform(source)

    assert result.source_text == source
    assert source == "\tint x = 1;   \n"

def test_deterministic_output():
    source = "\tint x = 1;   \n"

    transformation = FormattingTransformation()

    first = transformation.transform(source, seed=42)
    second = transformation.transform(source, seed=42)

    assert first.transformed_text == second.transformed_text

def test_metadata():
    source = "\tint x = 1;   \n"

    result = FormattingTransformation().transform(source, seed=42)

    assert result.transformation_type == "formatting"
    assert result.config["trim_trailing_whitespace"] is True
    assert result.config["strategy"] == (
        "conservative_line_formatting"
    )
    assert result.config["seed"] == 42

def test_preserves_multiline_raw_string():
    source = (
        'const char* text = R"tag(\n'
        '  content with trailing spaces   \n'
        '\tcontent with tab   \n'
        ')tag";\n'
        'int x = 1;   \n'
    )

    result = FormattingTransformation().transform(source)

    assert result.transformed_text == (
        'const char* text = R"tag(\n'
        '  content with trailing spaces   \n'
        '\tcontent with tab   \n'
        ')tag";\n'
        'int x = 1;\n'
    )
