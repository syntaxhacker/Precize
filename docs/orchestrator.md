# Orchestrator Pattern

The DocumentOrchestrator is the core component that enables generating 10,000+ line documents by coordinating specialized tools.

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    DocumentOrchestrator                      │
│                                                              │
│  ┌──────────────┐    ┌───────────────┐    ┌─────────────┐ │
│  │   Todo List  │───▶│ Tool Sequence │───▶│   Output    │ │
│  │              │    │               │    │   Document  │ │
│  └──────────────┘    └───────────────┘    └─────────────┘ │
│                                                              │
│  For each block in todo list:                               │
│    1. GENERATE → Create content (100-200 lines)            │
│    2. REVIEW   → Check quality                               │
│    3. IMPROVE  → Fix issues (if needed)                     │
│    4. APPEND   → Add to file                                 │
│    5. UPDATE   → Track progress                              │
└─────────────────────────────────────────────────────────────┘
```

## Why Orchestrator?

### Problem: LLM Context Limits

LLMs have limited context windows (4K-32K tokens). A 10,000 line document is ~150K tokens - too large to generate at once.

### Solution: Block-Based Generation

1. **Split** document into manageable blocks (100-200 lines each)
2. **Generate** each block independently
3. **Review** each block for quality
4. **Improve** if review fails
5. **Append** to final document
6. **Repeat** until complete

This approach:
- ✅ Works with any LLM
- ✅ Scales to arbitrary document length
- ✅ Maintains quality via review
- ✅ Resumable if interrupted

## Tools

### GenerateTool

Creates a content block (100-200 lines).

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

**Parameters:**
- `topic`: Overall document topic (for context)
- `section_title`: Title for this section
- `description`: What this section should cover
- `context`: What came before (for continuity)
- `include_mermaid`: Add mermaid diagram?
- `include_table`: Add comparison table?
- `include_examples`: Add code examples?

**Returns:**
- Markdown content (100-200 lines)

### ReviewTool

Reviews content against quality checklist.

```python
from preciz.orchestrator import ReviewTool

review_tool = ReviewTool(llm)

feedback = review_tool.review(
    content=content,
    title="The Chain Rule",
)

# Returns:
# {
#     "passed": True/False,
#     "issues": ["Missing examples", "Needs diagram"],
#     "suggestions": ["Add concrete example with numbers"]
# }
```

**Quality Checks:**
1. Sufficient examples (2+ required)
2. Clear explanations
3. Appropriate diagrams/tables
4. Adequate length (100+ lines)

### ImproveTool

Improves content based on review feedback.

```python
from preciz.orchestrator import ImproveTool

improve_tool = ImproveTool(llm)

if not feedback["passed"]:
    improved = improve_tool.improve(
        content=content,
        title="The Chain Rule",
        feedback=feedback,
    )
    # Returns improved content
```

### AppendTool

Appends content to output file.

```python
from preciz.orchestrator import AppendTool

append_tool = AppendTool("output.md")

line_count = append_tool.append(content)
print(f"Document now has {line_count} lines")

# Can also check current line count
current = append_tool.get_line_count()
```

## BlockTask

A single task in the todo list.

```python
@dataclass
class BlockTask:
    title: str                # Section title
    description: str          # What to cover
    level: int                # Heading level (1-3)
    require_mermaid: bool     # Needs diagram?
    require_table: bool       # Needs table?
    require_examples: bool    # Needs examples?
    completed: bool          # Done?
    content: str             # Generated content
```

## OrchestrationState

State tracking for resumable generation.

```python
@dataclass
class OrchestrationState:
    topic: str
    output_file: str
    target_lines: int
    tasks: list[BlockTask]
    current_task_index: int  # Where we are
    total_lines: int         # Lines written so far
    start_time: float
```

**State Persistence:**

```python
# Save state
state.save("generation_state.json")

# Resume from state
state = OrchestrationState.load("generation_state.json", llm)
```

## Complete Example

```python
from preciz.orchestrator import (
    DocumentOrchestrator,
    BlockTask,
    OrchestrationState,
)
from preciz.config import Config

# Initialize
config = Config.from_env()
orchestrator = DocumentOrchestrator(config)

# Create todo list
tasks = [
    BlockTask(
        title="Introduction",
        description="Overview and prerequisites",
        level=1,
        require_mermaid=False,
        require_table=True,
        require_examples=True,
    ),
    BlockTask(
        title="Basic Concepts",
        description="Core ideas and terminology",
        level=1,
        require_mermaid=True,
        require_table=True,
        require_examples=True,
    ),
    # ... 50-100 more tasks
]

# Generate
orchestrator.generate_document(
    topic="Python Programming",
    output_file="python.md",
    target_lines=10000,
    max_iterations=2,
    state_file="python_state.json",  # Resume capability!
)
```

## Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  1. CREATE TODO LIST                                        │
│     Use LLM to generate detailed outline                     │
│     Convert to BlockTask objects                            │
├─────────────────────────────────────────────────────────────┤
│  2. INITIALIZE                                               │
│     Create output file with header                           │
│     Initialize state                                         │
├─────────────────────────────────────────────────────────────┤
│  3. FOR EACH TASK:                                           │
│     ┌─────────────────────────────────────────────────────┐  │
│     │ a) GENERATE                                          │  │
│     │    - Call GenerateTool                              │  │
│     │    - Get 100-200 lines of content                   │  │
│     ├─────────────────────────────────────────────────────┤  │
│     │ b) REVIEW (up to max_iterations)                     │  │
│     │    - Call ReviewTool                                │  │
│     │    - If passed: continue                            │  │
│     │    - If failed: call ImproveTool, then review again │  │
│     ├─────────────────────────────────────────────────────┤  │
│     │ c) APPEND                                            │  │
│     │    - Call AppendTool                                │  │
│     │    - Add to output file                             │  │
│     ├─────────────────────────────────────────────────────┤  │
│     │ d) UPDATE STATE                                      │  │
│     │    - Mark task complete                             │  │
│     │    - Save state (every 5 tasks)                     │  │
│     └─────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  4. COMPLETE                                                 │
│     Clean up state file                                      │
│     Print summary                                            │
└─────────────────────────────────────────────────────────────┘
```

## Fault Tolerance

### Resume from Interruption

```python
# Start generation
orchestrator.generate_document(
    "Topic", "output.md",
    state_file="state.json"
)

# If interrupted (Ctrl+C, crash, etc.):
# Just run again with same state_file!

orchestrator.generate_document(
    "Topic", "output.md",
    state_file="state.json"  # Will resume!
)
```

The state file tracks:
- Which tasks completed
- Current line count
- All task specifications

### Automatic State Saving

State is saved:
- Every 5 tasks
- At completion
- On interruption (if handled)

## Customization

### Custom Tools

```python
class MyGenerateTool(GenerateTool):
    def generate(self, topic, section_title, description, context, **kwargs):
        # Custom generation logic
        content = super().generate(...)
        # Post-process
        return self._format(content)
```

### Custom Review Criteria

```python
class MyReviewTool(ReviewTool):
    def review(self, content, title):
        feedback = super().review(content, title)

        # Add custom checks
        if "TODO" in content:
            feedback["issues"].append("Contains TODO markers")

        return feedback
```

### Custom Todo Creation

```python
def create_custom_todo(topic: str) -> list[BlockTask]:
    # Create tasks from database, API, etc.
    tasks = []
    for section in get_sections_from_api(topic):
        tasks.append(BlockTask(
            title=section["title"],
            description=section["description"],
            level=section["level"],
            # ... other fields
        ))
    return tasks
```

## Performance

| Metric | Value |
|--------|-------|
| Avg block size | 100-200 lines |
| Blocks per 10K lines | ~50-100 |
| Time per block | 5-15 seconds |
| Total time (10K lines) | ~5-15 minutes |
| Memory usage | ~50MB (constant) |

## See Also

- [Architecture](architecture.md)
- [Usage Guide](usage.md)
- [API Reference](api.md)
