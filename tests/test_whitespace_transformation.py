
from src.transformations import WhitespaceTransformation


def test_transformation_name():
    transformation = WhitespaceTransformation()
    assert transformation.name == "whitespace"


def test_tab_indentation_is_normalized():
    source = "\tint main() {\n\t\treturn 0;\n\t}\n"

    result = WhitespaceTransformation().transform(source)

    expected = "    int main() {\n        return 0;\n    }\n"

    assert result.transformed_text == expected
    assert result.changed is True


def test_original_source_is_preserved():
    source = "\tint x = 10;\n"

    result = WhitespaceTransformation().transform(source)

    assert result.source_text == source
    assert source == "\tint x = 10;\n"


def test_transformation_result_metadata():
    source = "\tint x = 10;\n"

    result = WhitespaceTransformation().transform(source, seed=42)

    assert result.transformation_type == "whitespace"
    assert result.config["seed"] == 42
    assert result.config["strategy"] == (
        "conservative_indentation_normalization"
    )


def test_transformation_is_deterministic():
    source = "\tint main() {\n\t\treturn 0;\n\t}\n"

    transformation = WhitespaceTransformation()

    result_1 = transformation.transform(source, seed=42)
    result_2 = transformation.transform(source, seed=42)

    assert result_1.transformed_text == result_2.transformed_text


def test_no_change_when_source_has_no_tabs():
    source = "int main() {\n    return 0;\n"

    result = WhitespaceTransformation().transform(source)

    assert result.changed is False
    assert result.transformed_text == source


def test_string_literal_line_is_preserved():
    source = '\tcout << "hello   world";\n'

    result = WhitespaceTransformation().transform(source)

    assert result.transformed_text == source


def test_line_comment_is_preserved():
    source = "\t// comment with whitespace   \n"

    result = WhitespaceTransformation().transform(source)

    assert result.transformed_text == source


def test_block_comment_is_preserved():
    source = (
        "\t/* block comment\n"
        "\t   content with tabs\n"
        "\t*/\n"
        "\tint x = 1;\n"
    )

    result = WhitespaceTransformation().transform(source)

    assert result.transformed_text == (
        "\t/* block comment\n"
        "\t   content with tabs\n"
        "\t*/\n"
        "    int x = 1;\n"
    )


def test_preprocessor_macro_is_preserved():
    source = (
        "#define ADD(a, b) \\\n"
        "\t((a) + (b))\n"
        "\tint x = ADD(1, 2);\n"
    )

    result = WhitespaceTransformation().transform(source)

    assert result.transformed_text == (
        "#define ADD(a, b) \\\n"
        "\t((a) + (b))\n"
        "    int x = ADD(1, 2);\n"
    )


def test_multiline_raw_string_is_preserved():
    source = (
        '\tconst char* text = R"tag(\n'
        '\t  content with tabs\n'
        '\t)tag";\n'
        '\tint x = 1;\n'
    )

    result = WhitespaceTransformation().transform(source)

    assert result.transformed_text == (
        '\tconst char* text = R"tag(\n'
        '\t  content with tabs\n'
        '\t)tag";\n'
        '    int x = 1;\n'
    )
