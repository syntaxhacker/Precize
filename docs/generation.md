# Long Document Generation

Generate 10,000+ line educational documents with Preciz.

## Overview

Preciz can generate arbitrarily long documents using a block-based approach:

- ✅ Scales to any length (10K, 50K, 100K+ lines)
- ✅ Maintains quality via review cycle
- ✅ Resumable if interrupted
- ✅ Includes diagrams, tables, examples

## Quick Start

### CLI

```bash
# Generate a 10,000 line tutorial
preciz-gen-long "Differential Calculus" calculus.md --lines 10000

# With custom iterations
preciz-gen-long "Python Async" async.md --lines 5000 --iter 3
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

## How It Works

### Block-Based Generation

```
┌─────────────────────────────────────────────────────────────┐
│  1. CREATE OUTLINE                                          │
│     Break topic into 50-100 sections                        │
├─────────────────────────────────────────────────────────────┤
│  2. FOR EACH SECTION:                                       │
│     ┌─────────────────────────────────────────────────────┐  │
│     │ a) GENERATE block (100-200 lines)                   │  │
│     ├─────────────────────────────────────────────────────┤  │
│     │ b) REVIEW for quality                                │  │
│     ├─────────────────────────────────────────────────────┤  │
│     │ c) IMPROVE if needed (up to N iterations)           │  │
│     ├─────────────────────────────────────────────────────┤  │
│     │ d) APPEND to document                                │  │
│     └─────────────────────────────────────────────────────┘  │
│  3. ASSEMBLE final document                                 │
└─────────────────────────────────────────────────────────────┘
```

### Why This Works

| Challenge | Solution |
|-----------|----------|
| LLM context limits | Process in small blocks |
| Quality inconsistency | Review each block |
| Interruption handling | Save state periodically |
| Loss of context | Pass summary to next block |

## CLI Usage

### Basic Command

```bash
preciz-gen-long <topic> <output_file> [options]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--lines <n>` | Target line count | 10000 |
| `--iter <n>` | Max review iterations per block | 2 |

### Examples

```bash
# 10,000 lines (default)
preciz-gen-long "Machine Learning" ml.md

# 5,000 lines
preciz-gen-long "Docker Basics" docker.md --lines 5000

# 20,000 lines with more review
preciz-gen-long "React" react.md --lines 20000 --iter 3
```

## Python API

### Simple Generation

```python
from preciz.orchestrator import generate_long_document

generate_long_document(
    topic="Python Async Programming",
    output_file="async.md",
    target_lines=10000,
)
```

### With State File (Resume Capability)

```python
from preciz.orchestrator import DocumentOrchestrator
from preciz.config import Config

config = Config.from_env()
orchestrator = DocumentOrchestrator(config)

# Start generation (saves state)
orchestrator.generate_document(
    topic="Machine Learning",
    output_file="ml.md",
    target_lines=15000,
    max_iterations=2,
    state_file="ml_state.json",  # Can resume!
)
```

### Custom Todo List

```python
from preciz.orchestrator import DocumentOrchestrator, BlockTask
from preciz.config import Config

config = Config.from_env()
orchestrator = DocumentOrchestrator(config)

# Create custom sections
tasks = [
    BlockTask(
        title="Introduction",
        description="Overview",
        level=1,
        require_mermaid=False,
        require_table=True,
        require_examples=True,
    ),
    BlockTask(
        title="Getting Started",
        description="Installation and setup",
        level=1,
        require_mermaid=True,
        require_table=False,
        require_examples=True,
    ),
    # ... more tasks
]

# Generate
orchestrator.generate_document(
    topic="Python Tutorial",
    output_file="python.md",
    target_lines=10000,
)
```

## Output Quality

Each block is reviewed for:

- ✅ **Examples** - At least 2 code examples
- ✅ **Diagrams** - Mermaid diagrams where appropriate
- ✅ **Tables** - Comparison/summary tables
- ✅ **Length** - 100+ lines per section
- ✅ **Clarity** - Clear explanations

## Example Output

See `output/calculus.md` for a 16,000+ line example:

```bash
wc -l output/calculus.md
# 16202 output/calculus.md

head -100 output/calculus.md
# Shows mathematical formulas, mermaid diagrams, Python code...
```

## Scaling

### Lines per Section

| Sections | Lines | Time (approx) |
|----------|-------|---------------|
| 25 | ~2,500 | 5 min |
| 50 | ~5,000 | 10 min |
| 100 | ~10,000 | 20 min |
| 200 | ~20,000 | 40 min |

### Memory Usage

Constant ~50MB regardless of document length.

### Resumability

If interrupted, just run again with `state_file`:

```bash
# First run (interrupted at section 50)
preciz-gen-long "Topic" output.md --lines 20000

# Resume from section 50
preciz-gen-long "Topic" output.md --lines 20000
```

## Best Practices

### 1. Choose Appropriate Topics

```python
# Good - Specific, focused
"Python Decorators"
"Differential Calculus"
"React Hooks"

# Too broad - Hard to maintain quality
"Programming"
"Everything about Python"
```

### 2. Adjust Iterations

```python
# Fast draft
generate_long_document("Topic", "output.md", max_iterations=1)

# Polished version
generate_long_document("Topic", "output.md", max_iterations=3)
```

### 3. Use State Files

Always use `state_file` for long documents:

```python
orchestrator.generate_document(
    "Topic", "output.md",
    target_lines=50000,
    state_file="state.json",  # Resume capability!
)
```

### 4. Monitor Progress

The CLI shows real-time progress:

```bash
$ preciz-gen-long "Topic" output.md --lines 10000

[1/50] Introduction
  → Generating...
    150 lines
  → Review 1/2
    ✓ Passed
  → Appended (total: 150 lines)

[2/50] Basic Concepts
  → Generating...
    180 lines
  → Appended (total: 330 lines)
...
```

## Customization

### Custom Tools

```python
from preciz.orchestrator import GenerateTool

class MyGenerateTool(GenerateTool):
    def generate(self, topic, section_title, description, context, **kwargs):
        content = super().generate(...)
        # Custom formatting
        return self._format(content)
```

### Custom Review Criteria

```python
from preciz.orchestrator import ReviewTool

class MyReviewTool(ReviewTool):
    def review(self, content, title):
        feedback = super().review(content, title)

        # Add custom checks
        if "TODO" in content:
            feedback["issues"].append("Contains TODO")

        return feedback
```

## Troubleshooting

**Issue**: Generation is slow

**Solution**: Reduce `max_iterations` or use faster model.

**Issue**: Quality is inconsistent

**Solution**: Increase `max_iterations` to 2 or 3.

**Issue**: Document is too short

**Solution**: Increase `target_lines` or add more sections manually.

**Issue**: Interrupted and can't resume

**Solution**: Always use `state_file` parameter.

## See Also

- [Orchestrator Pattern](orchestrator.md)
- [Usage Guide](usage.md)
- [API Reference](api.md)
