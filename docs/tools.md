# Tool Reference

Reference for Preciz tools in the orchestrator.

## Overview

The CLI uses `DocumentOrchestrator` from `orchestrator.py`, which coordinates four specialized tools:

```
DocumentOrchestrator (used by CLI)
    ├── GenerateTool  → Create content blocks
    ├── ReviewTool    → Check quality
    ├── ImproveTool   → Fix issues
    └── AppendTool    → Write to file
```

**Note:** The older `BlockContentGenerator` from `generator_v2.py` is **not** used by the current CLI. The CLI (`generate_cli.py`) uses `DocumentOrchestrator` exclusively.

## GenerateTool

Creates a content block (100-200 lines).

### Usage

```python
from preciz.orchestrator import GenerateTool
from preciz.config import Config
from preciz.llm import LLMClient

config = Config.from_env()
llm = LLMClient(config)
gen_tool = GenerateTool(llm)

content = gen_tool.generate(
    topic="Differential Calculus",
    section_title="The Chain Rule",
    description="How to differentiate composite functions",
    context="Previous sections covered basic rules...",
    include_mermaid=True,
    include_table=True,
    include_examples=True,
)
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `topic` | str | Yes | Overall document topic |
| `section_title` | str | Yes | Title for this section |
| `description` | str | Yes | What this section covers |
| `context` | str | Yes | What came before (for continuity) |
| `include_mermaid` | bool | No | Include mermaid diagram? |
| `include_table` | bool | No | Include comparison table? |
| `include_examples` | bool | No | Include code examples? |

### Returns

`str` - Markdown content (100-200 lines)

### Example

```python
content = gen_tool.generate(
    topic="Python Sets",
    section_title="Set Operations",
    description="Union, intersection, difference",
    context="Introduction covered basic set creation",
    include_mermaid=True,
    include_table=True,
    include_examples=True,
)

print(content)
# ### Set Operations
#
# Sets support mathematical operations...
#
# ```mermaid
# flowchart LR
#     A[Set A] -->|Union| C[Combined]
# ...
# ```
#
# | Operation | Symbol | Description |
# |-----------|--------|-------------|
# | Union | \| | Combine sets |
# ...
```

## ReviewTool

Reviews content against quality checklist.

### Usage

```python
from preciz.orchestrator import ReviewTool

review_tool = ReviewTool(llm)

feedback = review_tool.review(
    content=content,
    title="Set Operations",
)
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | str | Yes | Content to review |
| `title` | str | Yes | Section title |

### Returns

```python
{
    "passed": True/False,
    "issues": ["Missing examples", "No diagram"],
    "suggestions": ["Add concrete example"]
}
```

### Quality Checklist

1. **Examples** - At least 2 code examples?
2. **Diagrams** - Needs mermaid diagram?
3. **Tables** - Needs comparison table?
4. **Length** - At least 100 lines?
5. **Clarity** - Clear explanations?

### Example

```python
feedback = review_tool.review(content, "Set Operations")

if feedback["passed"]:
    print("✓ Quality check passed")
else:
    print(f"✗ Issues: {feedback['issues']}")
    for issue in feedback["issues"]:
        print(f"  - {issue}")
```

## ImproveTool

Improves content based on review feedback.

### Usage

```python
from preciz.orchestrator import ImproveTool

improve_tool = ImproveTool(llm)

if not feedback["passed"]:
    improved = improve_tool.improve(
        content=content,
        title="Set Operations",
        feedback=feedback,
    )
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | str | Yes | Original content |
| `title` | str | Yes | Section title |
| `feedback` | dict | Yes | Review feedback |

### Returns

`str` - Improved content

### Example

```python
feedback = {
    "passed": False,
    "issues": ["Missing examples", "Too short"],
    "suggestions": ["Add 2 code examples", "Expand explanations"]
}

improved = improve_tool.improve(content, "Set Operations", feedback)

# Content now has more examples and is longer
print(f"Original: {len(content)} lines")
print(f"Improved: {len(improved)} lines")
```

## AppendTool

Appends content to output file.

### Usage

```python
from preciz.orchestrator import AppendTool

append_tool = AppendTool("output.md")

line_count = append_tool.append(content)
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | str | Yes | Content to append |

### Returns

`int` - New line count of document

### Methods

#### `append(content: str) -> int`

Append content to document.

```python
line_count = append_tool.append("# New Section\n\nContent here...")
```

#### `get_line_count() -> int`

Get current line count.

```python
current = append_tool.get_line_count()
print(f"Document has {current} lines")
```

### Example

```python
append_tool = AppendTool("tutorial.md")

# Append multiple sections
sections = ["# Section 1\n...", "# Section 2\n..."]

for section in sections:
    append_tool.append(section)
    print(f"Current: {append_tool.get_line_count()} lines")
```

## Tool Composition

```python
from preciz.orchestrator import (
    GenerateTool,
    ReviewTool,
    ImproveTool,
    AppendTool,
)
from preciz.config import Config
from preciz.llm import LLMClient

# Initialize
config = Config.from_env()
llm = LLMClient(config)

gen_tool = GenerateTool(llm)
review_tool = ReviewTool(llm)
improve_tool = ImproveTool(llm)
append_tool = AppendTool("output.md")

# Generate section
content = gen_tool.generate(
    topic="Python",
    section_title="Introduction",
    description="Overview",
    context="",
    include_examples=True,
)

# Review and improve (if needed)
for iteration in range(2):
    feedback = review_tool.review(content, "Introduction")
    if feedback["passed"]:
        break
    content = improve_tool.improve(content, "Introduction", feedback)

# Append to file
append_tool.append(content)
```

## Custom Tools

### Custom Generate Tool

```python
class MyGenerateTool(GenerateTool):
    def generate(self, topic, section_title, description, context, **kwargs):
        # Add custom preamble
        preamble = f"# {section_title}\n\n"

        # Call parent
        content = super().generate(
            topic, section_title, description, context, **kwargs
        )

        # Custom post-processing
        return preamble + self._format(content)

    def _format(self, content: str) -> str:
        # Custom formatting logic
        return content
```

### Custom Review Tool

```python
class MyReviewTool(ReviewTool):
    def review(self, content, title):
        # Get base feedback
        feedback = super().review(content, title)

        # Add custom checks
        if "TODO" in content:
            feedback["issues"].append("Contains TODO markers")

        if len(content.split("\n")) < 50:
            feedback["issues"].append("Too short (need 50+ lines)")

        return feedback
```

## Tool Configuration

### LLM Client

All tools share an LLM client:

```python
from preciz.llm import LLMClient
from preciz.config import Config

config = Config(
    api_key="sk-...",
    model="gpt-4o-mini",
    provider="openai",
    timeout=120,  # Longer timeout
)

llm = LLMClient(config)

# All tools use same client
gen_tool = GenerateTool(llm)
review_tool = ReviewTool(llm)
improve_tool = ImproveTool(llm)
```

### Temperature Settings

Tools use different temperatures:

| Tool | Temperature | Reason |
|------|-------------|--------|
| GenerateTool | 0.7 | Creative content |
| ReviewTool | 0.3 | Consistent evaluation |
| ImproveTool | 0.5 | Balanced |

## See Also

- [Orchestrator Pattern](orchestrator.md)
- [API Reference](api.md)
- [Architecture](architecture.md)
