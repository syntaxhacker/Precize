"""Test real long document generation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from preciz.generator_v2 import BlockContentGenerator
from preciz.config import Config


def test_small_generation():
    """Test with a smaller target first to validate flow."""
    print("\n" + "="*70)
    print("TESTING SMALL DOCUMENT GENERATION (1000 lines)")
    print("="*70 + "\n")

    try:
        config = Config.from_env()
        print(f"Model: {config.model}")
        print(f"Provider: {config.provider}\n")

        generator = BlockContentGenerator(config)

        output = generator.generate_document(
            topic="Introduction to Python Functions",
            output_file="output/test_small.md",
            target_lines=1000,
            max_iterations=1,
        )

        print(f"\n✓ Generation complete: {output}")

        # Check output
        content = Path(output).read_text()
        lines = content.split("\n")
        print(f"  Generated {len(lines)} lines")

        return output

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Create output directory
    Path("output").mkdir(exist_ok=True)

    result = test_small_generation()

    if result:
        print("\n" + "="*70)
        print("SUCCESS! Ready for larger generation.")
        print("="*70)
        print("\nTo generate a 10,000+ line document, run:")
        print("  preciz-gen-long 'Differential Calculus' calculus.md --lines 10000")
    else:
        print("\nGeneration failed - check the errors above")
