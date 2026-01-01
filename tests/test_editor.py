"""Tests for editor module."""

import tempfile
from pathlib import Path

import pytest

from preciz.editor import EditOperation, Editor, EditError, edit_file
from preciz.file_ops import read_file


class TestEditOperation:
    """Test EditOperation dataclass."""

    def test_create_edit(self):
        """Test creating an edit operation."""
        edit = EditOperation(old_text="foo", new_text="bar")
        assert edit.old_text == "foo"
        assert edit.new_text == "bar"
        assert edit.replace_all is False

    def test_edit_with_replace_all(self):
        """Test creating edit with replace_all."""
        edit = EditOperation(old_text="foo", new_text="bar", replace_all=True)
        assert edit.replace_all is True

    def test_edit_is_frozen(self):
        """Test that EditOperation is frozen."""
        edit = EditOperation(old_text="foo", new_text="bar")
        with pytest.raises(Exception):
            edit.old_text = "baz"


class TestEditor:
    """Test Editor class."""

    def test_init_editor(self, tmp_path):
        """Test initializing editor."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world")

        editor = Editor(str(test_file))
        assert editor.file_path == str(test_file)

    def test_read_file_content(self, tmp_path):
        """Test editor reads file content."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Original content")

        editor = Editor(str(test_file))
        content = editor._ensure_read()
        assert content == "Original content"

    def test_apply_single_edit(self, tmp_path):
        """Test applying a single edit."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world")

        editor = Editor(str(test_file))
        edit = EditOperation(old_text="world", new_text="there")
        editor.apply_edit(edit)

        assert "world" not in editor.preview_changes()
        assert "there" in editor.preview_changes()

    def test_edit_saves_changes(self, tmp_path):
        """Test that save writes changes to disk."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world")

        editor = Editor(str(test_file))
        edit = EditOperation(old_text="world", new_text="there")
        editor.apply_edit(edit)
        editor.save()

        assert read_file(test_file) == "Hello there"

    def test_no_change_if_same_text(self, tmp_path):
        """Test that no change occurs if old equals new."""
        test_file = tmp_path / "test.txt"
        original = "Hello world"
        test_file.write_text(original)

        editor = Editor(str(test_file))
        edit = EditOperation(old_text="world", new_text="world")
        editor.apply_edit(edit)

        assert editor.preview_changes() == original

    def test_error_old_text_not_found(self, tmp_path):
        """Test error when old text is not found."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world")

        editor = Editor(str(test_file))
        edit = EditOperation(old_text="goodbye", new_text="hello")

        with pytest.raises(EditError, match="Old text not found"):
            editor.apply_edit(edit)

    def test_error_duplicate_without_replace_all(self, tmp_path):
        """Test error when text appears multiple times without replace_all."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("foo bar foo")

        editor = Editor(str(test_file))
        edit = EditOperation(old_text="foo", new_text="baz", replace_all=False)

        with pytest.raises(EditError, match="appears .* times"):
            editor.apply_edit(edit)

    def test_replace_all_occurrences(self, tmp_path):
        """Test replacing all occurrences."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("foo bar foo")

        editor = Editor(str(test_file))
        edit = EditOperation(old_text="foo", new_text="baz", replace_all=True)
        editor.apply_edit(edit)

        assert editor.preview_changes() == "baz bar baz"

    def test_apply_multiple_edits(self, tmp_path):
        """Test applying multiple edits in order."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("The quick brown fox")

        editor = Editor(str(test_file))
        edits = [
            EditOperation(old_text="quick", new_text="slow"),
            EditOperation(old_text="brown", new_text="red"),
        ]
        editor.apply_edits(edits)

        assert editor.preview_changes() == "The slow red fox"

    def test_revert_changes(self, tmp_path):
        """Test reverting unapplied changes."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Original")

        editor = Editor(str(test_file))
        edit = EditOperation(old_text="Original", new_text="Changed")
        editor.apply_edit(edit)

        assert "Changed" in editor.preview_changes()

        editor.revert()
        assert editor.preview_changes() == "Original"

    def test_save_without_changes(self, tmp_path):
        """Test saving without making changes."""
        test_file = tmp_path / "test.txt"
        original = "Hello world"
        test_file.write_text(original)

        editor = Editor(str(test_file))
        editor.save()  # Should not error

        assert read_file(test_file) == original


class TestEditFile:
    """Test edit_file convenience function."""

    def test_edit_file_convenience(self, tmp_path):
        """Test the edit_file convenience function."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world")

        edit_file(str(test_file), "world", "there")

        assert read_file(test_file) == "Hello there"

    def test_edit_file_with_replace_all(self, tmp_path):
        """Test edit_file with replace_all option."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("cat dog cat")

        edit_file(str(test_file), "cat", "fish", replace_all=True)

        assert read_file(test_file) == "fish dog fish"
