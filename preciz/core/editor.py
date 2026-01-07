"""Precise file editing functionality."""

from dataclasses import dataclass
from typing import Literal

from .file_ops import FileError, FileReadError, FileWriteError, read_file, write_file


class EditError(FileError):
    """Exception raised when edit operation fails."""

    pass


@dataclass(frozen=True)
class EditOperation:
    """A single edit operation."""

    old_text: str
    new_text: str
    replace_all: bool = False


class Editor:
    """
    Precise file editor using exact string matching.

    Inspired by Claude Code's Edit tool - uses exact string matching
    to ensure precise edits without accidentally changing unrelated code.
    """

    def __init__(self, file_path: str) -> None:
        """
        Initialize editor for a file.

        Args:
            file_path: Path to the file to edit.
        """
        self.file_path = file_path
        self._content: str | None = None

    def _ensure_read(self) -> str:
        """Ensure file content is loaded."""
        if self._content is None:
            self._content = read_file(self.file_path)
        return self._content

    def apply_edit(self, edit: EditOperation) -> None:
        """
        Apply a single edit operation.

        Args:
            edit: The edit operation to apply.

        Raises:
            EditError: If the old_text is not found or ambiguous.
        """
        content = self._ensure_read()

        if edit.old_text == edit.new_text:
            return  # No change needed

        if edit.replace_all:
            if edit.old_text not in content:
                raise EditError(
                    f"Old text not found in {self.file_path}. "
                    "Cannot apply edit."
                )
            new_content = content.replace(edit.old_text, edit.new_text)
        else:
            # Single replacement - old_string must be unique
            count = content.count(edit.old_text)
            if count == 0:
                raise EditError(
                    f"Old text not found in {self.file_path}. "
                    "Cannot apply edit."
                )
            if count > 1:
                raise EditError(
                    f"Old text appears {count} times in {self.file_path}. "
                    "Use replace_all=True or provide more context."
                )
            new_content = content.replace(edit.old_text, edit.new_text, 1)

        self._content = new_content

    def apply_edits(self, edits: list[EditOperation]) -> None:
        """
        Apply multiple edit operations in order.

        Args:
            edits: List of edit operations to apply.
        """
        for edit in edits:
            self.apply_edit(edit)

    def save(self) -> None:
        """Write edited content back to file."""
        if self._content is None:
            return  # No changes made
        write_file(self.file_path, self._content)

    def preview_changes(self) -> str:
        """Get current content with unapplied changes."""
        return self._ensure_read()

    def revert(self) -> None:
        """Revert all unapplied changes by reloading from disk."""
        self._content = None


def edit_file(
    file_path: str,
    old_text: str,
    new_text: str,
    replace_all: bool = False,
) -> None:
    """
    Convenience function to edit a file in one call.

    Args:
        file_path: Path to the file to edit.
        old_text: Exact text to replace.
        new_text: Replacement text.
        replace_all: Whether to replace all occurrences.
    """
    editor = Editor(file_path)
    edit = EditOperation(old_text=old_text, new_text=new_text, replace_all=replace_all)
    editor.apply_edit(edit)
    editor.save()
