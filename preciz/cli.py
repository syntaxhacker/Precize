"""CLI interface for Preciz.

DEPRECATED: The original file editing agent has been archived.
Use `preciz-gen-long` for long document generation instead.
"""

import sys


def main() -> int:
    """Main CLI entry point."""
    print("Preciz: The original file editing agent has been archived.")
    print("")
    print("Available commands:")
    print("  preciz-gen-long  - Generate long educational documents")
    print("  preciz-generate  - Generate short content")
    print("")
    print("Use 'preciz-gen-long --help' for more information.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
