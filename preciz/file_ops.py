"""File operations for reading and writing files."""

from pathlib import Path
from typing import Literal


class FileError(Exception):
    """Base exception for file operations."""

    pass


class FileReadError(FileError):
    """Exception raised when file reading fails."""

    pass


class FileWriteError(FileError):
    """Exception raised when file writing fails."""

    pass


def read_file(
    path: str | Path,
    encoding: Literal["utf-8", "utf-8-sig", "latin-1"] = "utf-8",
) -> str:
    """
    Read file content as string.

    Args:
        path: File path to read.
        encoding: Text encoding to use.

    Returns:
        File content as string.

    Raises:
        FileReadError: If file cannot be read.
    """
    try:
        p = Path(path)
        content = p.read_text(encoding=encoding)
        return content
    except FileNotFoundError:
        raise FileReadError(f"File not found: {path}")
    except PermissionError:
        raise FileReadError(f"Permission denied: {path}")
    except UnicodeDecodeError as e:
        raise FileReadError(f"Encoding error in {path}: {e}")
    except Exception as e:
        raise FileReadError(f"Failed to read {path}: {e}")


def write_file(
    path: str | Path,
    content: str,
    encoding: Literal["utf-8", "utf-8-sig", "latin-1"] = "utf-8",
) -> None:
    """
    Write content to file.

    Args:
        path: File path to write.
        content: Content to write.
        encoding: Text encoding to use.

    Raises:
        FileWriteError: If file cannot be written.
    """
    try:
        p = Path(path)
        # Create parent directories if needed
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding=encoding)
    except PermissionError:
        raise FileWriteError(f"Permission denied: {path}")
    except Exception as e:
        raise FileWriteError(f"Failed to write {path}: {e}")


def file_exists(path: str | Path) -> bool:
    """Check if file exists."""
    return Path(path).exists()


def get_file_size(path: str | Path) -> int:
    """Get file size in bytes."""
    try:
        return Path(path).stat().st_size
    except Exception:
        return 0
