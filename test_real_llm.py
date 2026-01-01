"""Test with real OpenRouter API."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from preciz.agent import PrecizAgent
from preciz.config import Config
from preciz.file_ops import read_file, write_file


def test_real_llm():
    """Test with actual OpenRouter API."""
    print("\n=== Testing Real LLM Integration ===\n")

    # Load config from env
    config = Config.from_env()
    print(f"Provider: {config.provider}")
    print(f"Model: {config.model}")
    print(f"Base URL: {config.base_url}\n")

    agent = PrecizAgent(config)

    # Test file
    test_file = "test_samples/todo.md"
    original = read_file(test_file)

    print("Original content:")
    print("-" * 40)
    print(original)
    print("-" * 40)

    # Test 1: Simple addition
    print("\n[Test 1] Adding a new todo item...")
    instruction = "Add a new item 'Write code' under the Tomorrow section"
    plan = agent.plan_edits(instruction, test_file)
    print(f"Reasoning: {plan.reasoning}")
    print(f"Edits planned: {len(plan.edits)}")

    if plan.edits:
        print("\nEdit preview:")
        for i, edit in enumerate(plan.edits, 1):
            old_preview = edit.old_text[:80] + "..." if len(edit.old_text) > 80 else edit.old_text
            print(f"  {i}. Replace: '{old_preview}'")

    # Apply the edit
    agent.apply_plan(test_file, plan)
    result = read_file(test_file)
    print("\nResult after edit:")
    print("-" * 40)
    print(result)
    print("-" * 40)

    # Test 2: Another edit
    print("\n[Test 2] Changing an item...")
    instruction = "Change 'Buy groceries' to 'Buy groceries and cook dinner'"
    plan = agent.plan_edits(instruction, test_file)
    print(f"Reasoning: {plan.reasoning}")

    if plan.edits:
        agent.apply_plan(test_file, plan)
        result = read_file(test_file)
        print("\nResult after second edit:")
        print("-" * 40)
        print(result)
        print("-" * 40)

    # Restore original
    write_file(test_file, original)
    print("\n✓ Real LLM test completed!")


if __name__ == "__main__":
    try:
        test_real_llm()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
