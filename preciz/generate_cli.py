"""CLI for long document generation using block-based approach."""

import sys
from pathlib import Path

from .generator_v2 import BlockContentGenerator, generate_long_document


def print_usage():
    """Print usage information."""
    print("Preciz Long Document Generator")
    print()
    print("Generate 10,000+ line educational documents block by block.")
    print()
    print("Usage:")
    print("  preciz-gen-long <topic> <output_file> [options]")
    print()
    print("Examples:")
    print("  preciz-gen-long 'Differential Calculus' calculus.md")
    print("  preciz-gen-long 'Python Async Programming' async.md --lines 5000")
    print("  preciz-gen-long 'Machine Learning' ml.md --lines 15000")
    print()
    print("Options:")
    print("  --lines <n>     Target line count (default: 10000)")
    print("  --iter <n>      Max review iterations per block (default: 2)")


def parse_args(args: list[str]) -> tuple[str, str, int, int]:
    """Parse command line arguments."""
    if len(args) < 2:
        return None, None, 10000, 2

    topic = args[0]
    output = args[1]
    target_lines = 10000
    max_iterations = 2

    i = 2
    while i < len(args):
        if args[i] == "--lines" and i + 1 < len(args):
            target_lines = int(args[i + 1])
            i += 2
        elif args[i] == "--iter" and i + 1 < len(args):
            max_iterations = int(args[i + 1])
            i += 2
        else:
            i += 1

    return topic, output, target_lines, max_iterations


def main() -> int:
    """Main CLI entry point."""
    if len(sys.argv) < 3 or sys.argv[1] in ("-h", "--help", "help"):
        print_usage()
        return 0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help", "help") else 1

    args = sys.argv[1:]
    topic, output, target_lines, max_iterations = parse_args(args)

    if topic is None:
        print_usage()
        return 1

    try:
        # Validate output path
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate
        generator = BlockContentGenerator()
        generator.generate_document(
            topic=topic,
            output_file=output,
            target_lines=target_lines,
            max_iterations=max_iterations,
        )

        return 0

    except KeyboardInterrupt:
        print("\n\nInterrupted.")
        return 130
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
