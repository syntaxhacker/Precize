"""CLI for checking incomplete sections in Markdown files."""

import sys
from pathlib import Path

from .checker import detect_incomplete_sections, print_incomplete_report


def print_usage():
    """Print usage information."""
    print("Preciz Completion Checker")
    print()
    print("Detect incomplete sections in generated markdown files.")
    print()
    print("Usage:")
    print("  preciz-completion-check <input_file>")
    print()
    print("Examples:")
    print("  preciz-completion-check document.md")
    print()


def main() -> int:
    """Main CLI entry point."""
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print_usage()
        return 0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help", "help") else 1

    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"Error: File not found: {sys.argv[1]}")
        return 1

    content = input_file.read_text()
    issues = detect_incomplete_sections(content)
    print_incomplete_report(issues)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
