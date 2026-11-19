
from __future__ import annotations

import re

from src.transformations.base import (
    Transformation,
    TransformationResult,
)


_RAW_STRING_START = re.compile(r'R"([^ ()\\\t]{0,16})\(')


class FormattingTransformation(Transformation):
    """Conservative source formatting transformation."""

    INDENT_UNIT = "    "

    @property
    def name(self) -> str:
        return "formatting"

    def transform(
        self,
        source: str,
        seed: int | None = None,
    ) -> TransformationResult:
        lines = source.splitlines(keepends=True)
        transformed_lines: list[str] = []

        in_block_comment = False
        in_macro_continuation = False
        raw_string_delimiter: str | None = None

        for line in lines:
            original_line = line

            if in_macro_continuation:
                transformed_lines.append(original_line)
                in_macro_continuation = self._ends_with_continuation(line)
                continue

            if raw_string_delimiter is not None:
                transformed_lines.append(original_line)

                if f'){raw_string_delimiter}"' in line:
                    raw_string_delimiter = None

                continue

            if in_block_comment:
                transformed_lines.append(original_line)
                if "*/" in line:
                    in_block_comment = False
                continue

            stripped = line.lstrip(" \t")

            # Preserve blank lines and preprocessor directives.
            if not stripped.strip() or stripped.startswith("#"):
                transformed_lines.append(original_line)

                if stripped.startswith("#") and self._ends_with_continuation(line):
                    in_macro_continuation = True

                continue

            # Conservatively skip lines containing sensitive constructs.
            if self._contains_sensitive_construct(line):
                transformed_lines.append(original_line)

                if "/*" in line and "*/" not in line:
                    in_block_comment = True

                raw_start = _RAW_STRING_START.search(line)
                if raw_start:
                    delimiter = raw_start.group(1)
                    closing = f'){delimiter}"'

                    if closing not in line[raw_start.end():]:
                        raw_string_delimiter = delimiter

                continue

            leading = line[: len(line) - len(stripped)]
            normalized_leading = leading.replace(
                "\t",
                self.INDENT_UNIT,
            )

            content, newline = self._split_newline(stripped)
            normalized_content = content.rstrip(" \t")

            transformed_lines.append(
                normalized_leading + normalized_content + newline
            )

        transformed = "".join(transformed_lines)

        return TransformationResult(
            transformation_type=self.name,
            source_text=source,
            transformed_text=transformed,
            changed=(source != transformed),
            config={
                "indent_unit": self.INDENT_UNIT,
                "trim_trailing_whitespace": True,
                "strategy": "conservative_line_formatting",
                "seed": seed,
            },
        )

    @staticmethod
    def _split_newline(line: str) -> tuple[str, str]:
        if line.endswith("\r\n"):
            return line[:-2], "\r\n"

        if line.endswith("\n"):
            return line[:-1], "\n"

        if line.endswith("\r"):
            return line[:-1], "\r"

        return line, ""

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
