# File Editing

Precise file editing with exact string matching.

## Overview

Preciz edits files using exact string matching, ensuring precision and safety.

```python
from preciz import PrecizAgent

agent = PrecizAgent()
agent.edit_file("Change version to 2.0", "README.md")
```

## How It Works

```
┌─────────────┐
│ Instruction │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   Read File Content  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│   Send to LLM       │
│   (with context)    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│   Parse Response    │
│   → Edit Plan       │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│   Apply Edits       │
│   (exact match)     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│   Save File         │
└─────────────────────┘
```

## CLI Usage

```bash
# Basic edit
preciz "Fix the typo in line 5" README.md

# Update content
preciz "Update the year to 2024" README.md

# Complex edit
preciz "Rearrange the sections" docs/guide.md
```

### Confirmation Prompt

The CLI always asks for confirmation:

```bash
$ preciz "Change version to 2.0" README.md

Plan: Update version number
Edits to apply: 1

1. Replace:
   'Version 1.0'
   with:
   'Version 2.0'

Apply these changes? [y/N]
```

## Python API

### Basic Editing

```python
from preciz import PrecizAgent

agent = PrecizAgent()
agent.edit_file(
    instruction="Change version to 2.0",
    file_path="README.md",
)
```

### Dry Run

```python
# Plan without applying
plan = agent.plan_edits(
    instruction="Make changes",
    file_path="file.md",
)

# Review plan
print(f"Reasoning: {plan.reasoning}")
for edit in plan.edits:
    print(f"- Replace: {edit.old_text[:50]}")
    print(f"  with: {edit.new_text[:50]}")

# Apply if happy
agent.apply_plan("file.md", plan)
```

### Direct Editing

```python
from preciz.editor import edit_file, Editor, EditOperation

# Convenience function
edit_file(
    file_path="README.md",
    old_text="Version 1.0",
    new_text="Version 2.0",
)

# With Editor (more control)
editor = Editor("README.md")
editor.apply_edit(EditOperation(
    old_text="old text",
    new_text="new text",
    replace_all=False,  # Replace first occurrence only
))
editor.save()
```

## Edit Operation

```python
from preciz.editor import EditOperation

edit = EditOperation(
    old_text="exact text to replace",  # Must match exactly!
    new_text="replacement text",
    replace_all=False,  # Replace all occurrences?
)
```

### Safety Features

**Ambiguity Detection:**

```python
# If old_text appears multiple times and replace_all=False:
editor.apply_edit(EditOperation(
    old_text="hello",  # Appears 3 times in file
    new_text="hi",
    replace_all=False,
))

# Raises EditError:
# "Old text appears 3 times. Use replace_all=True or provide more context."
```

**Exact Matching:**

```python
# Whitespace matters!
EditOperation(
    old_text="def foo():",    # Must match exactly
    new_text="def bar():",
)
```

## Multiple Edits

```python
from preciz.editor import Editor, EditOperation

editor = Editor("config.py")

edits = [
    EditOperation("localhost", "0.0.0.0", replace_all=True),
    EditOperation("8080", "443"),
    EditOperation("debug=True", "debug=False"),
]

for edit in edits:
    editor.apply_edit(edit)

editor.save()
```

## Examples

### Example 1: Update Version Numbers

```python
from preciz.editor import edit_file

edit_file(
    file_path="setup.py",
    old_text="version='1.0.0'",
    new_text="version='2.0.0'",
)
```

### Example 2: Replace All Occurrences

```python
edit_file(
    file_path="config.yaml",
    old_text="localhost",
    new_text="production.example.com",
    replace_all=True,  # Replace all!
)
```

### Example 3: Complex Edit with LLM

```python
from preciz import PrecizAgent

agent = PrecizAgent()

agent.edit_file(
    instruction="Rearrange sections: put Installation before Usage",
    file_path="README.md",
)
```

### Example 4: Preview Before Apply

```python
from preciz import PrecizAgent

agent = PrecizAgent()

# Dry run
plan = agent.edit_file(
    instruction="Update documentation",
    file_path="README.md",
    dry_run=True,  # Don't apply!
)

# Review
print(f"Edits planned: {len(plan.edits)}")
for i, edit in enumerate(plan.edits, 1):
    print(f"{i}. {edit.old_text[:50]}...")

# Apply manually if happy
if input("Apply? [y/N] ").lower() == "y":
    agent.apply_plan("README.md", plan)
```

## Error Handling

```python
from preciz import PrecizAgent
from preciz.editor import EditError

agent = PrecizAgent()

try:
    agent.edit_file("Make changes", "file.md")
except EditError as e:
    print(f"Edit failed: {e}")
    # "Old text not found"
    # "Old text appears 5 times. Use replace_all=True"
```

## Tips

1. **Be Specific** - More context = better edits
2. **Use Dry Run** - Preview before applying
3. **Handle Errors** - Always catch EditError
4. **Check Results** - Verify file after edit

## See Also

- [Usage Guide](usage.md)
- [API Reference](api.md)
- [Architecture](architecture.md)
