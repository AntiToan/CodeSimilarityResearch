from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from pathlib import Path, PureWindowsPath
import stat

# Exceptions
class PathSafetyError(Exception):
    """Base exception for all PathSafety errors."""

class PathResolutionError(PathSafetyError):
    """Raised when a path cannot be resolved safely."""

class PathContainmentError(PathSafetyError):
    """Raised when a candidate path escapes its authorized root."""

class RootConfigurationError(PathSafetyError):
    """Raised when source/output root configuration is invalid."""

class SymlinkPolicyError(PathSafetyError):
    """Raised when symlink or reparse-point policy is violated."""

class WriteTargetValidationError(PathSafetyError):
    """Raised when a write destination is invalid or unsupported."""

# Result types
@dataclass(frozen=True)
class PathSafetyResult:
    """Immutable result of a successful PathSafety validation."""

    path: Path
    root: Path
    relative_path: Path

# PathSafety
class PathSafety:
    """
    Centralized filesystem path safety boundary.

    This module validates paths only.

    It must not:
    - create directories or files
    - write or modify filesystem objects
    - delete filesystem objects
    - perform persistence or commit operations
    """

    @staticmethod
    def canonicalize(
        path: Path | str,
        *,
        base_dir: Path | str | None = None,
    ) -> Path:
        """
        Resolve a path to canonical absolute form.

        Relative paths require an explicit absolute base_dir.
        Existing symlink/junction components must resolve successfully.
        The final leaf may not exist.

        This method performs no filesystem mutation.
        """
        try:
            raw = str(path)
            if not raw or not raw.strip():
                raise PathResolutionError("Path must not be empty.")

            if "\x00" in raw:
                raise PathResolutionError("Path contains a null byte.")

            candidate = Path(raw)
            windows_candidate = PureWindowsPath(raw)

            # Reject Windows drive-relative forms such as C:folder\file.py.
            if windows_candidate.drive and not windows_candidate.root:
                raise PathResolutionError(
                    f"Drive-relative paths are not supported: {raw!r}"
                )

            if candidate.is_absolute():
                unresolved = candidate
            else:
                if base_dir is None:
                    raise PathResolutionError(
                        "Relative paths require an explicit base_dir."
                    )

                base_raw = str(base_dir)
                if not base_raw or not base_raw.strip():
                    raise PathResolutionError("base_dir must not be empty.")

                base = Path(base_raw)

                base_windows = PureWindowsPath(base_raw)
                if base_windows.drive and not base_windows.root:
                    raise PathResolutionError(
                        "base_dir must not be drive-relative."
                    )

                if not base.is_absolute():
                    raise PathResolutionError(
                        "base_dir must be an absolute path."
                    )

                # base_dir is an authority anchor and must resolve to
                # an existing directory.
                try:
                    base = base.resolve(strict=True)
                except (OSError, RuntimeError) as exc:
                    raise PathResolutionError(
                        f"Unable to resolve base_dir: {base_raw!r}"
                    ) from exc

                if not base.is_dir():
                    raise PathResolutionError(
                        f"base_dir is not an existing directory: {base}"
                    )

                unresolved = base / candidate

            if not unresolved.is_absolute():
                raise PathResolutionError(
                    "Canonicalization did not produce an absolute path."
                )

            # Walk existing components. Existing links/junctions must
            # resolve strictly; broken links and loops fail closed.
            current = Path(unresolved.anchor)

            for component in unresolved.parts[1:]:
                current = current / component

                try:
                    if current.is_symlink():
                        current.resolve(strict=True)
                except (OSError, RuntimeError) as exc:
                    raise PathResolutionError(
                        f"Unable to resolve link component: {current}"
                    ) from exc

            # strict=False permits a missing leaf/remaining suffix,
            # while resolving existing parent links.
            try:
                canonical = unresolved.resolve(strict=False)
            except (OSError, RuntimeError) as exc:
                raise PathResolutionError(
                    f"Unable to canonicalize path: {unresolved}"
                ) from exc

            if not canonical.is_absolute():
                raise PathResolutionError(
                    "Canonical path is not absolute."
                )

            return canonical

        except PathSafetyError:
            raise
        except (OSError, RuntimeError, ValueError, TypeError) as exc:
            raise PathResolutionError(
                f"Path canonicalization failed for {path!r}"
            ) from exc

    @staticmethod
    def validate_containment(
        path: Path | str,
        root: Path | str,
    ) -> PathSafetyResult:
        """
        Validate that a canonical path is contained within a canonical root.

        The root must be an existing directory.
        The candidate path may be missing, provided its resolution
        can be determined safely.

        No filesystem mutation is performed.
        """
        try:
            canonical_root = PathSafety.canonicalize(root)
            canonical_path = PathSafety.canonicalize(path)

            # The authority root must exist and be a directory.
            if not canonical_root.exists():
                raise PathContainmentError(
                    f"Containment root does not exist: {canonical_root}"
                )

            if not canonical_root.is_dir():
                raise PathContainmentError(
                    f"Containment root is not a directory: {canonical_root}"
                )

            # Root itself is an allowed containment target.
            if canonical_path == canonical_root:
                relative_path = Path(".")
            else:
                try:
                    relative_path = canonical_path.relative_to(
                        canonical_root
                    )
                except ValueError as exc:
                    raise PathContainmentError(
                        f"Path is outside authorized root: "
                        f"{canonical_path} (root={canonical_root})"
                    ) from exc

            return PathSafetyResult(
                path=canonical_path,
                root=canonical_root,
                relative_path=relative_path,
            )

        except PathSafetyError:
            raise

        except (OSError, RuntimeError, ValueError, TypeError) as exc:
            raise PathContainmentError(
                f"Containment validation failed for path={path!r}, "
                f"root={root!r}"
            ) from exc

    @staticmethod
    def validate_distinct_roots(
        source_root: Path | str,
        output_root: Path | str,
    ) -> tuple[Path, Path]:
        """
        Validate that source_root and output_root are distinct,
        non-overlapping canonical directory roots.

        Both roots must exist and be directories.

        Neither root may contain the other.

        No filesystem mutation is performed.
        """
        try:
            canonical_source = PathSafety.canonicalize(source_root)
            canonical_output = PathSafety.canonicalize(output_root)

            # Both authority roots must exist and be directories.
            if not canonical_source.exists():
                raise RootConfigurationError(
                    f"Source root does not exist: {canonical_source}"
                )

            if not canonical_source.is_dir():
                raise RootConfigurationError(
                    f"Source root is not a directory: {canonical_source}"
                )

            if not canonical_output.exists():
                raise RootConfigurationError(
                    f"Output root does not exist: {canonical_output}"
                )

            if not canonical_output.is_dir():
                raise RootConfigurationError(
                    f"Output root is not a directory: {canonical_output}"
                )

            # Canonical equality is forbidden.
            if canonical_source == canonical_output:
                raise RootConfigurationError(
                    "Source root and output root must be different."
                )

            # Reject source -> output containment.
            try:
                canonical_output.relative_to(canonical_source)
            except ValueError:
                pass
            else:
                raise RootConfigurationError(
                    "Output root must not be nested inside source root."
                )

            # Reject output -> source containment.
            try:
                canonical_source.relative_to(canonical_output)
            except ValueError:
                pass
            else:
                raise RootConfigurationError(
                    "Source root must not be nested inside output root."
                )

            return canonical_source, canonical_output

        except PathSafetyError:
            raise

        except (OSError, RuntimeError, ValueError, TypeError) as exc:
            raise RootConfigurationError(
                "Distinct root validation failed for "
                f"source={source_root!r}, output={output_root!r}"
            ) from exc

    @staticmethod
    def validate_write_target(
        path: Path | str,
        output_root: Path | str,
    ) -> PathSafetyResult:
        """
        Validate a file write target within an authorized output root.

        The output root must exist and be a directory.
        The target must be a descendant file target, not the root itself.

        Missing target and missing parent directories are allowed
        if canonical containment can be established.

        Existing regular files are allowed. Collision handling belongs
        to SafePersistence.

        Leaf symlinks, junctions, directories, and special files
        are rejected.

        No filesystem mutation is performed.
        """
        try:
            raw_target = Path(path)

            if not raw_target.is_absolute():
                raise WriteTargetValidationError(
                    "Write target must be an absolute path."
                )

            # Reject a leaf link before canonicalization, because resolve()
            # would otherwise erase the identity of the link itself.
            try:
                leaf_stat = raw_target.lstat()
            except FileNotFoundError:
                leaf_stat = None
            except (OSError, RuntimeError) as exc:
                raise WriteTargetValidationError(
                    f"Unable to inspect write target: {raw_target}"
                ) from exc

            if leaf_stat is not None:
                # Reject symbolic links.
                if stat.S_ISLNK(leaf_stat.st_mode):
                    raise WriteTargetValidationError(
                        f"Write target leaf must not be a symlink: "
                        f"{raw_target}"
                    )

                # Reject Windows junctions and any leaf reparse point.
                file_attributes = getattr(
                    leaf_stat,
                    "st_file_attributes",
                    0,
                )
                reparse_point_flag = getattr(
                    stat,
                    "FILE_ATTRIBUTE_REPARSE_POINT",
                    0x400,
                )

                if file_attributes & reparse_point_flag:
                    raise WriteTargetValidationError(
                        f"Write target leaf must not be a reparse point: "
                        f"{raw_target}"
                    )

                # Only a regular file is an acceptable existing leaf.
                if not stat.S_ISREG(leaf_stat.st_mode):
                    raise WriteTargetValidationError(
                        f"Write target is not a regular file: {raw_target}"
                    )

            # Validate root and candidate using canonical containment.
            result = PathSafety.validate_containment(
                raw_target,
                output_root,
            )

            # The root itself is not a valid file write target.
            if result.path == result.root:
                raise WriteTargetValidationError(
                    "Write target must be a file descendant of output_root, "
                    "not output_root itself."
                )

            # relative_path must not be empty or ".".
            if result.relative_path == Path("."):
                raise WriteTargetValidationError(
                    "Write target must identify a descendant file."
                )

            return result

        except WriteTargetValidationError:
            raise

        except PathSafetyError as exc:
            raise WriteTargetValidationError(
                f"Write-target validation rejected path={path!r}, "
                f"output_root={output_root!r}"
            ) from exc

        except (OSError, RuntimeError, ValueError, TypeError) as exc:
            raise WriteTargetValidationError(
                f"Write-target validation failed for {path!r}"
            ) from exc
