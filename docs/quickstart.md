# Quick Start Guide

Get started with Preciz in 5 minutes.

## 1. Install

```bash
pip install preciz
```

Or from source:

```bash
git clone https://github.com/yourusername/preciz.git
cd preciz
pip install -e .
```

## 2. Configure

Create `.env` file:

```bash
API_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-key-here
LLM_MODEL=xiaomi/mimo-v2-flash:free
```

Get a free key at [openrouter.ai](https://openrouter.ai).

## 3. Edit Files

### CLI

```bash
# Edit a file
preciz "Fix the typo in line 5" README.md

# Update documentation
preciz "Update the installation instructions" docs/setup.md
```

### Python API

```python
from preciz import PrecizAgent

agent = PrecizAgent()
agent.edit_file("Change version to 2.0", "README.md")
```

## 4. Generate Long Documents

### CLI

```bash
# Generate a 10,000 line tutorial
preciz-gen-long "Differential Calculus" calculus.md --lines 10000
```

### Python API

```python
from preciz.orchestrator import generate_long_document

generate_long_document(
    topic="Python Programming",
    output_file="python.md",
    target_lines=10000,
)
```

## 5. See Results

```bash
# View generated document
wc -l calculus.md
head -50 calculus.md
```

## Examples

### Example 1: Quick Edit

```python
from preciz.editor import edit_file

edit_file(
    file_path="README.md",
    old_text="Version 1.0",
    new_text="Version 2.0",
)
```

### Example 2: Generate Tutorial

```python
from preciz.orchestrator import generate_long_document

# Generate a comprehensive tutorial
generate_long_document(
    topic="Machine Learning Basics",
    output_file="ml_basics.md",
    target_lines=5000,
)
```

### Example 3: Plan Then Apply

```python
from preciz import PrecizAgent

agent = PrecizAgent()

# Plan edits first
plan = agent.plan_edits(
    instruction="Update all version numbers",
    file_path="setup.py",
)

# Review plan
print(f"Reasoning: {plan.reasoning}")
print(f"Edits: {len(plan.edits)}")

# Apply if happy
if input("Apply? [y/N] ").lower() == "y":
    agent.apply_plan("setup.py", plan)
```

## What's Next?

- [Full Usage Guide](usage.md)
- [API Reference](api.md)
- [Architecture](architecture.md)

## Common Issues

**Issue**: `API key not found`

**Solution**: Make sure `.env` file exists with valid `OPENROUTER_API_KEY` or `OPENAI_API_KEY`.

**Issue**: `Module not found`

**Solution**: Make sure virtual environment is activated:
```bash
source venv/bin/activate  # macOS/Linux
```

**Issue**: Edit fails with "Old text not found"

**Solution**: The LLM couldn't find exact match. Try:
- Being more specific in instruction
- Using dry_run=True to see planned edits
- Providing more context

## Getting Help

- GitHub Issues: [preciz/issues](https://github.com/yourusername/preciz/issues)
- Documentation: [docs/](.)
- Examples: See `output/` directory
