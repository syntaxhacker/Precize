"""More comprehensive LLM edit tests."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from preciz.agent import PrecizAgent
from preciz.config import Config
from preciz.file_ops import read_file, write_file


def test_multiple_simple_edits():
    """Test multiple simple edits in sequence."""
    print("\n=== Testing Multiple Sequential Edits ===\n")

    config = Config.from_env()
    agent = PrecizAgent(config)

    test_file = "test_samples/sample.md"
    original = read_file(test_file)

    tests = [
        ("Change 'Fast editing' to 'Quick editing'", "heading change"),
        ("Update the version number from 42 to 100", "number change"),
        ("Change 'Hello, World!' to 'Hello, Preciz!'", "string change"),
    ]

    for instruction, desc in tests:
        print(f"\n[Test] {desc}: {instruction}")
        plan = agent.plan_edits(instruction, test_file)

        if plan.edits:
            print(f"  Edits: {len(plan.edits)}")
            agent.apply_plan(test_file, plan)
            print(f"  ✓ Applied")
        else:
            print(f"  No edits needed")

    # Show final result
    result = read_file(test_file)
    print("\nFinal result:")
    print("-" * 40)
    print(result)
    print("-" * 40)

    # Restore
    write_file(test_file, original)
    print("\n✓ File restored")


if __name__ == "__main__":
    try:
        test_multiple_simple_edits()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
