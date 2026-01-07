"""CLI for content generation."""

import sys
from pathlib import Path

from preciz._archive.generator import ContentGenerator, ContentSpec, generate_tutorial


def print_usage():
    """Print usage information."""
    print("Preciz Content Generator")
    print()
    print("Usage:")
    print("  preciz-generate <topic> <output_file> [options]")
    print()
    print("Examples:")
    print("  preciz-generate 'Differential Calculus' calculus.md")
    print("  preciz-generate 'Python Async Programming' async.md --brief")
    print("  preciz-generate 'Machine Learning Basics' ml.md --advanced")
    print()
    print("Options:")
    print("  --brief         Generate shorter content")
    print("  --advanced      Target advanced audience")
    print("  --beginner      Target beginner audience")
    print("  --no-practical  Skip practical exercises")


def parse_args(args: list[str]) -> tuple[str, str, dict]:
    """Parse command line arguments."""
    if len(args) < 2:
        return None, None, {}

    topic = args[0]
    output = args[1]

    spec_kwargs = {
        "target_length": "comprehensive",
        "target_audience": "intermediate",
        "include_practical": True,
        "include_theory": True,
    }

    for arg in args[2:]:
        if arg == "--brief":
            spec_kwargs["target_length"] = "brief"
        elif arg == "--advanced":
            spec_kwargs["target_audience"] = "advanced"
        elif arg == "--beginner":
            spec_kwargs["target_audience"] = "beginner"
        elif arg == "--no-practical":
            spec_kwargs["include_practical"] = False

    return topic, output, spec_kwargs


def main() -> int:
    """Main CLI entry point."""
    if len(sys.argv) < 3 or sys.argv[1] in ("-h", "--help", "help"):
        print_usage()
        return 0 if sys.argv[1] in ("-h", "--help", "help") else 1

    args = sys.argv[1:]
    topic, output, spec_kwargs = parse_args(args)

    if topic is None:
        print_usage()
        return 1

    try:
        # Validate output path
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate content
        spec = ContentSpec(topic=topic, **spec_kwargs)
        generator = ContentGenerator()

        print(f"\n{'='*60}")
        print(f"PRECIZ CONTENT GENERATOR")
        print(f"{'='*60}")
        print(f"\nTopic: {topic}")
        print(f"Output: {output}")
        print(f"Audience: {spec_kwargs['target_audience']}")
        print(f"Length: {spec_kwargs['target_length']}\n")

        generator.generate_with_review(spec, output_file=output)

        print(f"\n✓ Tutorial saved to: {output}")
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
