"""Simple test with real LLM - focus on simple replacements."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from preciz.agent import PrecizAgent
from preciz.config import Config
from preciz.file_ops import read_file, write_file


def test_simple_replacements():
    """Test simple replacements with real LLM."""
    print("\n=== Testing Simple Replacements ===\n")

    config = Config.from_env()
    print(f"Model: {config.model}\n")

    agent = PrecizAgent(config)

    # Test file with simple content
    test_file = "test_samples/sample.md"
    original = read_file(test_file)

    print("Original content:")
    print("-" * 40)
    print(original)
    print("-" * 40)

    # Test: Simple word replacement
    print("\n[Test] Change 'localhost' to '127.0.0.1'...")
    instruction = "Replace localhost with 127.0.0.1"
    plan = agent.plan_edits(instruction, test_file)

    print(f"Reasoning: {plan.reasoning}")
    print(f"Edits: {len(plan.edits)}")

    if plan.edits:
        for i, edit in enumerate(plan.edits, 1):
            print(f"\n  Edit {i}:")
            print(f"    old: '{edit.old_text[:100]}...'")
            print(f"    new: '{edit.new_text[:100]}...'")

        # Apply and show result
        agent.apply_plan(test_file, plan)
        result = read_file(test_file)

        print("\nResult:")
        print("-" * 40)
        print(result)
        print("-" * 40)

        # Restore
        write_file(test_file, original)
        print("\n✓ Test completed, file restored!")
    else:
        print("No edits planned")


if __name__ == "__main__":
    try:
        test_simple_replacements()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
