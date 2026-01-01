"""Tests for file operations."""

import tempfile
from pathlib import Path

import pytest

from preciz.file_ops import (
    FileReadError,
    FileWriteError,
    file_exists,
    get_file_size,
    read_file,
    write_file,
)


class TestReadFile:
    """Test file reading functionality."""

    def test_read_existing_file(self, tmp_path):
        """Test reading an existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!", encoding="utf-8")

        content = read_file(test_file)
        assert content == "Hello, world!"

    def test_read_with_path_str(self, tmp_path):
        """Test reading with string path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Content here", encoding="utf-8")

        content = read_file(str(test_file))
        assert content == "Content here"

    def test_read_nonexistent_file(self, tmp_path):
        """Test reading a file that doesn't exist."""
        with pytest.raises(FileReadError, match="File not found"):
            read_file(tmp_path / "nonexistent.txt")

    def test_read_directory(self, tmp_path):
        """Test reading a directory raises error."""
        with pytest.raises(FileReadError):
            read_file(tmp_path)

    def test_read_utf8_content(self, tmp_path):
        """Test reading UTF-8 content with special characters."""
        test_file = tmp_path / "unicode.txt"
        content = "Hello 世界 🌍"
        test_file.write_text(content, encoding="utf-8")

        assert read_file(test_file) == content

    def test_read_with_bom(self, tmp_path):
        """Test reading file with UTF-8 BOM."""
        test_file = tmp_path / "bom.txt"
        # Write with BOM
        test_file.write_bytes(b"\xef\xbb\xbfHello")

        content = read_file(test_file, encoding="utf-8-sig")
        assert content == "Hello"


class TestWriteFile:
    """Test file writing functionality."""

    def test_write_new_file(self, tmp_path):
        """Test writing a new file."""
        test_file = tmp_path / "new.txt"
        write_file(test_file, "New content")

        assert test_file.read_text(encoding="utf-8") == "New content"

    def test_write_overwrite(self, tmp_path):
        """Test overwriting existing file."""
        test_file = tmp_path / "existing.txt"
        test_file.write_text("Old content", encoding="utf-8")

        write_file(test_file, "New content")
        assert test_file.read_text(encoding="utf-8") == "New content"

    def test_write_creates_directories(self, tmp_path):
        """Test that write_file creates parent directories."""
        deep_file = tmp_path / "a" / "b" / "c" / "file.txt"
        write_file(deep_file, "Deep content")

        assert deep_file.read_text(encoding="utf-8") == "Deep content"

    def test_write_with_path_str(self, tmp_path):
        """Test writing with string path."""
        test_file = tmp_path / "str.txt"
        write_file(str(test_file), "String path")

        assert test_file.read_text(encoding="utf-8") == "String path"

    def test_write_unicode(self, tmp_path):
        """Test writing Unicode content."""
        test_file = tmp_path / "unicode.txt"
        content = "Hello 世界 🌍"

        write_file(test_file, content)
        assert test_file.read_text(encoding="utf-8") == content


class TestFileExists:
    """Test file_exists function."""

    def test_existing_file(self, tmp_path):
        """Test existing file returns True."""
        test_file = tmp_path / "exists.txt"
        test_file.write_text("content")

        assert file_exists(test_file) is True

    def test_nonexistent_file(self, tmp_path):
        """Test nonexistent file returns False."""
        assert file_exists(tmp_path / "does_not_exist.txt") is False

    def test_directory(self, tmp_path):
        """Test directory returns True."""
        assert file_exists(tmp_path) is True


class TestGetFileSize:
    """Test get_file_size function."""

    def test_existing_file(self, tmp_path):
        """Test getting size of existing file."""
        test_file = tmp_path / "size.txt"
        content = "Hello, world!"
        test_file.write_text(content, encoding="utf-8")

        assert get_file_size(test_file) == len(content.encode("utf-8"))

    def test_nonexistent_file(self, tmp_path):
        """Test nonexistent file returns 0."""
        assert get_file_size(tmp_path / "does_not_exist.txt") == 0
