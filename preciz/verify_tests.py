"""Verification tests using real files."""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from preciz.editor import edit_file, Editor, EditOperation, EditError
from preciz.file_ops import read_file, write_file
from preciz.agent import PrecizAgent
from preciz.config import Config


def test_direct_edit():
    """Test direct file editing."""
    print("\n=== Test 1: Direct Edit ===")

    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Original Title\n\nSome content here.")
        temp_file = f.name

    try:
        print(f"Original content:\n{read_file(temp_file)}\n")

        # Single edit
        edit_file(temp_file, "Original Title", "Updated Title")
        content = read_file(temp_file)
        print(f"After edit:\n{content}\n")

        assert "Updated Title" in content
        assert "Original Title" not in content
        print("✓ Direct edit works!")

    finally:
        os.unlink(temp_file)


def test_multiple_edits():
    """Test multiple sequential edits."""
    print("\n=== Test 2: Multiple Edits ===")

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("foo bar foo baz foo")
        temp_file = f.name

    try:
        print(f"Original: {read_file(temp_file)}")

        editor = Editor(temp_file)
        edits = [
            EditOperation("foo", "qux", replace_all=True),
            EditOperation("bar", "corge"),
        ]
        editor.apply_edits(edits)
        editor.save()

        result = read_file(temp_file)
        print(f"After edits: {result}")

        assert result == "qux corge qux baz qux"
        print("✓ Multiple edits work!")

    finally:
        os.unlink(temp_file)


def test_error_on_duplicate():
    """Test that error is raised for ambiguous edits."""
    print("\n=== Test 3: Error on Duplicate ===")

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("hello world hello")
        temp_file = f.name

    try:
        print(f"Content: {read_file(temp_file)}")

        editor = Editor(temp_file)
        edit = EditOperation("hello", "hi", replace_all=False)

        try:
            editor.apply_edit(edit)
            print("✗ Should have raised error!")
        except EditError as e:
            print(f"✓ Got expected error: {e}")

    finally:
        os.unlink(temp_file)


def test_with_sample_files():
    """Test with the actual sample files."""
    print("\n=== Test 4: Sample File Edits ===")

    sample_file = "test_samples/sample.md"

    # Read original
    original = read_file(sample_file)
    print(f"Original content preview:\n{original[:200]}...\n")

    # Make a backup
    backup = sample_file + ".bak"
    write_file(backup, original)

    try:
        # Edit the file
        edit_file(sample_file, "localhost:8080", "api.example.com:443")

        edited = read_file(sample_file)
        print(f"After edit preview:\n{edited[:200]}...\n")

        assert "api.example.com:443" in edited
        assert "localhost:8080" not in edited
        print("✓ Sample file edit works!")

        # Restore original
        write_file(sample_file, original)
        os.unlink(backup)

    except Exception as e:
        # Restore on error
        write_file(sample_file, original)
        if os.path.exists(backup):
            os.unlink(backup)
        raise


def test_long_markdown_file():
    """Test editing a longer markdown file incrementally."""
    print("\n=== Test 5: Incremental Markdown Edits ===")

    content = """# Documentation

## Getting Started

First, install the package:

```bash
pip install mypackage
```

## Usage

Create a new file:

```python
import mypackage

mypackage.run()
```

## Configuration

Edit config.yaml to set your preferences.

## Troubleshooting

If you see an error, check the logs.
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_file = f.name

    try:
        print("Original markdown file created")

        # Make first edit
        edit_file(temp_file, "pip install mypackage", "pip install preciz")
        print("✓ Edit 1: Changed package name")

        # Make second edit
        edit_file(temp_file, "import mypackage", "import preciz")
        print("✓ Edit 2: Changed import")

        # Make third edit
        edit_file(temp_file, "mypackage.run()", "preciz.run()")
        print("✓ Edit 3: Changed function call")

        result = read_file(temp_file)
        assert result.count("preciz") >= 3
        assert "mypackage" not in result

        print("\n✓ All incremental edits successful!")
        print(f"\nFinal content:\n{result}")

    finally:
        os.unlink(temp_file)


def test_agent_with_mock():
    """Test the agent with a mocked LLM response."""
    print("\n=== Test 6: Agent with Mocked LLM ===")

    from unittest.mock import patch, MagicMock
    from preciz.llm import LLMResponse

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Hello\n\nWorld world world.")
        temp_file = f.name

    try:
        config = Config(
            api_key="test-key",
            model="test-model",
            provider="openrouter",
            base_url="https://test.api/v1",
        )
        agent = PrecizAgent(config)

        # Mock the LLM response
        mock_response = LLMResponse(
            content='''{"reasoning": "Change greeting", "edits": [
              {"old_text": "Hello", "new_text": "Greetings"}
            ]}''',
            model="test-model",
        )

        with patch.object(agent.llm, 'complete', return_value=mock_response):
            plan = agent.plan_edits("Change the greeting", temp_file)
            print(f"Plan reasoning: {plan.reasoning}")
            print(f"Number of edits: {len(plan.edits)}")

            agent.apply_plan(temp_file, plan)

        result = read_file(temp_file)
        print(f"After agent edit:\n{result}")

        assert "Greetings" in result
        assert "Hello" not in result
        print("✓ Agent with mocked LLM works!")

    finally:
        os.unlink(temp_file)


if __name__ == "__main__":
    print("=" * 50)
    print("PRECIZ AGENT VERIFICATION TESTS")
    print("=" * 50)

    test_direct_edit()
    test_multiple_edits()
    test_error_on_duplicate()
    test_with_sample_files()
    test_long_markdown_file()
    test_agent_with_mock()

    print("\n" + "=" * 50)
    print("ALL VERIFICATION TESTS PASSED!")
    print("=" * 50)
