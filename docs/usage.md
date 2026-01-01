# Preciz Usage Guide

Complete guide for using Preciz for file editing and long document generation.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [CLI Usage](#cli-usage)
- [Python API](#python-api)
- [Generating Long Documents](#generating-long-documents)
- [Examples](#examples)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/preciz.git
cd preciz

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install
pip install -e .
```

## Configuration

Create a `.env` file in your project root:

```bash
# For OpenRouter (recommended)
API_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-key-here
LLM_MODEL=xiaomi/mimo-v2-flash:free

# OR for OpenAI
API_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4o-mini
```

## CLI Usage

### Editing Files

```bash
# Basic edit
preciz "Fix the typo in line 5" README.md

# More complex edit
preciz "Update the installation instructions" docs/setup.md

# Edit with confirmation
preciz "Change all 'foo' to 'bar'" src/main.py
```

The CLI will:
1. Read the file
2. Send to LLM with your instruction
3. Show you the planned edits
4. Ask for confirmation
5. Apply changes

### Generating Long Documents

```bash
# Generate a 10,000 line tutorial
preciz-gen-long "Differential Calculus" calculus.md --lines 10000

# With custom iterations
preciz-gen-long "Python Async" async.md --lines 5000 --iter 2

# Target different lengths
preciz-gen-long "Topic" output.md --lines 15000
```

## Python API

### File Editing

```python
from preciz import PrecizAgent
from preciz.config import Config

# Initialize agent
agent = PrecizAgent(Config.from_env())

# Plan edits (dry run)
plan = agent.plan_edits(
    instruction="Update the version number",
    file_path="README.md",
    file_content=None,  # Optional: pre-read content
)

# Apply edits
agent.apply_plan("README.md", plan)

# Or do it in one call
agent.edit_file("Change version to 2.0", "README.md")

# Dry run (don't apply changes)
agent.edit_file("Make changes", "file.md", dry_run=True)
```

### Direct Editing

```python
from preciz.editor import edit_file, Editor, EditOperation

# Convenience function
edit_file(
    file_path="README.md",
    old_text="Version 1.0",
    new_text="Version 2.0",
    replace_all=False,
)

# Or use Editor for more control
editor = Editor("README.md")
editor.apply_edit(EditOperation(
    old_text="old text",
    new_text="new text",
    replace_all=True,
))
editor.save()

# Preview before saving
print(editor.preview_changes())
editor.revert()  # Discard changes
```

### Reading Files

```python
from preciz.file_ops import read_file, write_file

# Read file
content = read_file("README.md")

# Write file (creates directories if needed)
write_file("output/new.md", content)

# Check file info
from preciz.file_ops import file_exists, get_file_size
if file_exists("README.md"):
    size = get_file_size("README.md")
```

## Generating Long Documents

### Basic Usage

```python
from preciz.orchestrator import generate_long_document

# Generate a 10,000 line document
generate_long_document(
    topic="Differential Calculus",
    output_file="calculus.md",
    target_lines=10000,
)
```

### Using the Orchestrator Directly

```python
from preciz.orchestrator import DocumentOrchestrator, BlockTask
from preciz.config import Config

config = Config.from_env()
orchestrator = DocumentOrchestrator(config)

# Create custom todo list
tasks = [
    BlockTask(
        title="Introduction",
        description="Overview of the topic",
        level=1,
        require_mermaid=True,
        require_table=True,
        require_examples=True,
    ),
    # ... more tasks
]

# Generate with state file (for resume capability)
orchestrator.generate_document(
    topic="My Topic",
    output_file="output.md",
    target_lines=10000,
    max_iterations=2,
    state_file="generation_state.json",  # Can resume!
)
```

### Using Tools Directly

```python
from preciz.orchestrator import GenerateTool, AppendTool
from preciz.config import Config
from preciz.llm import LLMClient

config = Config.from_env()
llm = LLMClient(config)

# Create tools
gen_tool = GenerateTool(llm)
append_tool = AppendTool("output.md")

# Generate and append
for i in range(50):
    content = gen_tool.generate(
        topic="Python Programming",
        section_title=f"Section {i+1}",
        description="Content description",
        context="",
        include_mermaid=True,
        include_table=True,
        include_examples=True,
    )

    append_tool.append(content)
    print(f"Section {i+1} added")
```

## Examples

### Example 1: Fix Typos

```python
from preciz import PrecizAgent

agent = PrecizAgent()
agent.edit_file(
    "Fix all occurrences of 'recieve' to 'receive'",
    "document.md"
)
```

### Example 2: Update Configuration

```python
from preciz.editor import edit_file

edit_file(
    file_path="config.yaml",
    old_text="port: 8080",
    new_text="port: 443",
)
```

### Example 3: Generate Tutorial

```python
from preciz.orchestrator import generate_long_document

# Generate a comprehensive Python tutorial
generate_long_document(
    topic="Python Advanced Programming",
    output_file="python_advanced.md",
    target_lines=15000,  # ~75 sections
)
```

### Example 4: Incremental Edits

```python
from preciz.editor import Editor, EditOperation

editor = Editor("README.md")

# Apply multiple edits
edits = [
    EditOperation("v1.0", "v2.0", replace_all=True),
    EditOperation("2023", "2024", replace_all=True),
    EditOperation("old@example.com", "new@example.com", replace_all=False),
]

for edit in edits:
    editor.apply_edit(edit)

editor.save()
```

### Example 5: Generate with Resume

```python
from preciz.orchestrator import DocumentOrchestrator
from preciz.config import Config

config = Config.from_env()
orchestrator = DocumentOrchestrator(config)

# Start generation (will save state)
orchestrator.generate_document(
    topic="Machine Learning",
    output_file="ml.md",
    target_lines=20000,
    state_file="ml_generation_state.json",
)

# If interrupted, just run again with same state_file
# It will resume from where it left off!
```

## Best Practices

### For File Editing

1. **Be Specific**: More context = better edits
   ```python
   # Good
   agent.edit_file("Change the API endpoint in the __init__ method", "file.py")

   # Less good
   agent.edit_file("Change API endpoint", "file.py")
   ```

2. **Use Dry Run First**: Preview before applying
   ```python
   plan = agent.plan_edits("instruction", "file.md")
   print(plan.edits)  # Check what will change
   ```

3. **Handle Errors**:
   ```python
   from preciz.editor import EditError

   try:
       agent.edit_file("instruction", "file.md")
   except EditError as e:
       print(f"Edit failed: {e}")
   ```

### For Document Generation

1. **Break Down Topics**: Smaller topics = better quality
   ```python
   # Good
   "Python Async Programming"

   # Less good
   "Python Programming Everything"
   ```

2. **Adjust Iterations**: More iterations = higher quality
   ```python
   # Quick draft
   generate_long_document("Topic", "output.md", max_iterations=1)

   # Polished version
   generate_long_document("Topic", "output.md", max_iterations=3)
   ```

3. **Use State Files for Long Documents**:
   ```python
   # Allows resuming if interrupted
   orchestrator.generate_document(
       "Topic", "output.md",
       target_lines=50000,
       state_file="state.json",
   )
   ```

## Tips

- **Preview Changes**: Use `dry_run=True` to see edits without applying
- **Save State**: Use `state_file` for long generations
- **Adjust Context**: The orchestrator uses previous content for continuity
- **Review First**: Set `max_iterations=2` for better quality
- **Monitor Progress**: The CLI shows real-time progress

## Troubleshooting

See [Troubleshooting](troubleshooting.md) for common issues.

## See Also

- [Architecture](architecture.md)
- [API Reference](api.md)
- [Orchestrator Pattern](orchestrator.md)
