"""Simple test of block generation with timeout."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from preciz.generator_v2 import BlockContentGenerator
from preciz.config import Config
from preciz.llm import LLMResponse, Message


def test_outline_only():
    """Test just the outline creation."""
    print("\n" + "="*60)
    print("TEST: Outline Creation Only")
    print("="*60 + "\n")

    try:
        config = Config.from_env()
        print(f"Model: {config.model}")
        print(f"Provider: {config.provider}\n")

        generator = BlockContentGenerator(config)

        print("Creating outline for 'Python Functions'...")
        outline = generator.create_outline(
            topic="Python Functions",
            target_lines=500,
        )

        print(f"\n✓ Outline created!")
        print(f"Root title: {outline.title}")
        print(f"Children: {len(outline.children)}")

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_outline_only()
    sys.exit(0 if success else 1)
