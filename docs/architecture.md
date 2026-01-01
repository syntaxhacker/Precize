# Preciz Architecture

Preciz uses a modular, tool-based architecture designed for scalability and precision.

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Preciz                               │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │   Editor    │  │  Generator   │  │   Orchestrator      │ │
│  │  (edit)     │  │  (generate)  │  │   (coordinate)      │ │
│  └─────────────┘  └──────────────┘  └─────────────────────┘ │
│         │                  │                     │            │
│         └──────────────────┴─────────────────────┘            │
│                            │                                  │
│                    ┌───────▼───────┐                         │
│                    │    Config     │                         │
│                    │  + File Ops   │                         │
│                    │  + LLM Client │                         │
│                    └───────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Config Module (`config.py`)

Configuration management using environment variables.

```python
from preciz.config import Config

config = Config.from_env()
# Supports: OpenRouter, OpenAI
# Auto-loads from .env file
```

**Features:**
- Frozen dataclass for immutability
- OpenRouter and OpenAI support
- Configurable timeouts and retries

### 2. File Operations (`file_ops.py`)

Safe file read/write operations with error handling.

```python
from preciz.file_ops import read_file, write_file

content = read_file("file.md")
write_file("output.md", content)
```

**Features:**
- UTF-8 handling with BOM support
- Automatic parent directory creation
- Custom exceptions for error handling

### 3. Editor (`editor.py`)

Precise file editing using exact string matching.

```python
from preciz.editor import Editor, EditOperation

editor = Editor("file.md")
editor.apply_edit(EditOperation(
    old_text="old",
    new_text="new",
    replace_all=False
))
editor.save()
```

**Key Design:**
- **Exact string matching** - prevents accidental edits
- **Ambiguity detection** - errors if old_text appears multiple times
- **Multiple edits** - applies edits sequentially
- **Revert capability** - reload from disk if needed

### 4. LLM Client (`llm.py`)

Unified client for OpenAI/OpenRouter APIs.

```python
from preciz.llm import LLMClient, Message

client = LLMClient(config)
response = client.complete([
    Message(role="user", content="Hello")
])
```

**Features:**
- Streaming support
- Token usage tracking
- Configurable temperature/max_tokens

### 5. Agent (`agent.py`)

Main agent coordinating LLM with file editing.

```python
from preciz.agent import PrecizAgent

agent = PrecizAgent()
agent.edit_file("Fix the typo", "file.md")
```

**Workflow:**
1. Read file content
2. Send to LLM with instruction
3. Parse LLM response into edit operations
4. Apply edits using Editor
5. Save file

### 6. Orchestrator (`orchestrator.py`)

**NEW**: Tool-based orchestrator for long document generation.

```
┌─────────────────────────────────────────────────────────────┐
│                    DocumentOrchestrator                      │
│  - Maintains todo list of sections                          │
│  - Coordinates tools in sequence                            │
│  - Tracks progress (resumable!)                             │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
    ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
    │GENERATE│    │ REVIEW │    │IMPROVE │    │ APPEND │
    │  Tool  │    │  Tool  │    │  Tool  │    │  Tool  │
    └────────┘    └────────┘    └────────┘    └────────┘
```

**Tools:**

| Tool | Purpose |
|------|---------|
| `GenerateTool` | Generate a content block (100-200 lines) |
| `ReviewTool` | Review content against quality checklist |
| `ImproveTool` | Improve content based on feedback |
| `AppendTool` | Append content to document file |

**State Management:**

```python
@dataclass
class OrchestrationState:
    topic: str
    output_file: str
    target_lines: int
    tasks: list[BlockTask]
    current_task_index: int
    total_lines: int
```

State can be saved/resumed for fault tolerance.

## File Structure

```
preciz/
├── preciz/
│   ├── __init__.py         # Package init
│   ├── config.py           # Configuration (26 lines)
│   ├── file_ops.py         # File I/O (37 lines)
│   ├── editor.py           # Edit engine (49 lines)
│   ├── llm.py              # LLM client (37 lines)
│   ├── agent.py            # Edit agent (57 lines)
│   ├── cli.py              # Edit CLI (52 lines)
│   ├── orchestrator.py     # NEW: Orchestrator (400+ lines)
│   │   ├── GenerateTool    # Block generation
│   │   ├── ReviewTool      # Quality review
│   │   ├── ImproveTool     # Content improvement
│   │   ├── AppendTool      # File appending
│   │   └── DocumentOrchestrator  # Coordinator
│   ├── generator_v2.py     # Block-based generator
│   ├── content_cli.py      # Original generator CLI
│   └── generate_cli.py     # Long doc CLI
├── tests/                  # Comprehensive tests
│   ├── test_editor.py
│   ├── test_file_ops.py
│   ├── test_llm.py
│   ├── test_agent.py
│   ├── test_generator_v2.py
│   └── ...
├── docs/                   # This documentation
├── output/                 # Generated documents
└── README.md
```

## Design Principles

### 1. Modularity
Each component has a single, well-defined responsibility.

### 2. Immutability
Configuration and data structures use frozen dataclasses.

### 3. Error Handling
Custom exceptions (`FileError`, `EditError`) for clear error messages.

### 4. Testability
100% mockable - all LLM calls can be stubbed.

### 5. Scalability
Block-based approach allows arbitrary document lengths.

## Data Flow

### Editing Flow

```
User Input → Agent → LLM → Parse Edits → Editor → File
                     ↑                   │
                     └──── Error ←────────┘
```

### Generation Flow

```
Topic → Orchestrator → Create Todo List
                       ↓
For Each Task:
  GenerateTool → LLM → Content Block
       ↓
  ReviewTool → LLM → Feedback
       ↓
  (if needed) ImproveTool → LLM → Improved Content
       ↓
  AppendTool → File
       ↓
  Update Progress
```

## Key Design Decisions

### Why Exact String Matching for Editing?

- **Precision**: No ambiguity about what changes
- **Safety**: Can't accidentally change wrong occurrences
- **Verifiable**: Edits can be checked before applying

### Why Orchestrator Pattern for Generation?

- **Scalability**: Process any length document
- **Resumability**: Save state, resume if interrupted
- **Tool Separation**: Each tool does one thing well
- **Progress Tracking**: Always know where you are

### Why Frozen Dataclasses?

- **Immutability**: Prevent accidental modifications
- **Clarity**: Clear what data is passed
- **Type Safety**: Pydantic validation built-in

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| File Read | O(n) | n = file size |
| File Write | O(n) | n = content size |
| Single Edit | O(n) | Must scan file for match |
| LLM Call | O(1) | Depends on API |
| Block Generate | O(1) | 100-200 lines fixed |
| Full Document | O(k) | k = number of blocks |

## Extension Points

### Adding New Tools

```python
class MyCustomTool:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def process(self, data: str) -> str:
        # Custom logic
        return result
```

### Adding New LLM Providers

Extend `Config.from_env()` to support new providers.

### Custom Review Criteria

Modify `QualityChecklist` in `generator.py`.

## See Also

- [Orchestrator Pattern](orchestrator.md)
- [API Reference](api.md)
- [Extending Preciz](extending.md)
