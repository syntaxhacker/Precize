"""Content completion checker tool.

Detects incomplete sections in generated markdown.
"""

from .checker import (
    detect_incomplete_sections,
    print_incomplete_report,
)

__all__ = [
    "detect_incomplete_sections",
    "print_incomplete_report",
]
