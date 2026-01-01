"""Test small document generation with minimal blocks."""

import sys
from pathlib import Path
import signal

sys.path.insert(0, str(Path(__file__).parent))

from preciz.generator_v2 import BlockContentGenerator
from preciz.config import Config


def timeout_handler(signum, frame):
    raise TimeoutError("Generation timed out")


def test_mini_generation():
    """Generate a mini document with just a few sections."""
    print("\n" + "="*60)
    print("TEST: Mini Document Generation")
    print("="*60 + "\n")

    try:
        config = Config.from_env()
        print(f"Model: {config.model}\n")

        generator = BlockContentGenerator(config)

        # Create a simple outline manually
        from preciz.generator_v2 import OutlineNode

        outline = OutlineNode(title="Test", level=0, description="")
        outline.children = [
            OutlineNode(title="Introduction", level=1, description="Brief intro"),
            OutlineNode(title="Basic Concepts", level=1, description="Core ideas"),
        ]

        print("Generating 2 sections...")

        # Generate blocks one by one
        for node in outline.children:
            print(f"\n→ {node.title}")
            content = generator.generate_block(node, "")
            print(f"  {len(content.split())} words, {len(content.split(chr(10)))} lines")

        print("\n✓ Test passed!")
        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Set timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(120)  # 2 minutes

    try:
        success = test_mini_generation()
        sys.exit(0 if success else 1)
    finally:
        signal.alarm(0)
