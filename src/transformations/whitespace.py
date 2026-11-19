from __future__ import annotations
import re 
from src.transformations.base import (
    Transformation,
    TransformationResult,
)

_RAW_STRING_START = re.compile(r'R"([^ ()\\\t]{0,16})\(')
_RAW_STRING_END_PREFIX = ")"

class WhitespaceTransformation(Transformation):
    """Conservative whitespace-only source transformation."""

    INDENT_UNIT = "    "

    @property
    def name(self) -> str:
        return "whitespace"

    def transform(
        self,
        source: str,
        seed: int | None = None,
    ) -> TransformationResult:
        lines = source.splitlines(keepends=True)

        transformed_lines: list[str] = []

        in_block_comment = False
        raw_string_delimiter: str | None = None 
        in_macro_continuation = False 

        for line in lines:
            original_line = line

            # protect lines belonging to continued preprocessor macros.
            if in_macro_continuation:
                transformed_lines.append(original_line)
                in_macro_continuation = self._ends_with_continuation(line)
                continue

            # Protect multiline raw string literal content
            if raw_string_delimiter is not None:
                transformed_lines.append(original_line)
                if self._raw_string_ends(
                    line, raw_string_delimiter,
                ):
                    raw_string_delimiter = None 
                continue

            # protect multiline block comments.
            if in_block_comment:
                transformed_lines.append(original_line)
                if "*/" in line:
                    in_block_comment = False
                continue

            stripped = line.lstrip(" \t")

            # preserve empty lines and preprocessor lines
            if not stripped.strip() or stripped.startswith("#"):
                transformed_lines.append(original_line)

                if stripped.startswith("#") and self._ends_with_continuation(line):
                    in_macro_continuation = True 

                # Correct continuation state for next line.
                if stripped.startswith("#") and self._ends_with_continuation(line):
                    in_macro_continuation = True 

                continue

            # Lines containing lexical-sensitive constructs are skipped.
            if self._contains_sensitive_construct(line):
                transformed_lines.append(original_line)

                if "/*" in line and "*/" not in line:
                    in_block_comment = True 

                raw_start = _RAW_STRING_START.search(line)
                if raw_start:
                    delimiter = raw_start.group(1)
                    if f"){delimiter}" not in line[raw_start.end():]:
                        raw_string_delimiter = delimiter

                continue

            # safe indentation-only change
            leading = line[: len(line) - len(stripped)]
            normalized_leading = leading.replace("\t", self.INDENT_UNIT)

            transformed_lines.append(
                normalized_leading + stripped
            )

        transformed = "".join(transformed_lines)

        return TransformationResult(
            transformation_type=self.name,
            source_text=source,
            transformed_text=transformed,
            changed=(source != transformed),
            config={
                "indent_unit": self.INDENT_UNIT,
                "strategy": "conservative_indentation_normalization",
                "seed": seed,
            },
        )

    @staticmethod
    def _ends_with_continuation(line: str) -> bool:
        content = line.rstrip("\r\n")
        return content.endswith("\\")

    @staticmethod
    def _contains_sensitive_construct(line: str) -> bool:
        return any(
            marker in line 
            for marker in ('"', "'", "//", "/*", "*/", "\\")
        )

    @staticmethod
    def _raw_string_ends(
        line: str,
        delimiter: str, 
    ) -> bool:
        return f"){delimiter}" in line