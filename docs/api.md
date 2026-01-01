# API Reference

Complete API reference for Preciz.

## Modules

### `preciz.config`

Configuration management.

```python
from preciz.config import Config
```

**Class: Config**

Frozen dataclass for configuration.

```python
@dataclass(frozen=True)
class Config:
    api_key: str
    model: str
    provider: Literal["openrouter", "openai"]
    base_url: str | None = None
    max_retries: int = 3
    timeout: int = 60
```

**Methods:**

- `Config.from_env() -> Config` - Load from environment variables

**Example:**

```python
config = Config.from_env()
print(config.model)  # "xiaomi/mimo-v2-flash:free"
```

---

### `preciz.file_ops`

File operations.

```python
from preciz.file_ops import read_file, write_file, file_exists, get_file_size
```

**Functions:**

```python
def read_file(
    path: str | Path,
    encoding: Literal["utf-8", "utf-8-sig", "latin-1"] = "utf-8",
) -> str:
    """Read file content as string."""

def write_file(
    path: str | Path,
    content: str,
    encoding: Literal["utf-8", "utf-8-sig", "latin-1"] = "utf-8",
) -> None:
    """Write content to file."""

def file_exists(path: str | Path) -> bool:
    """Check if file exists."""

def get_file_size(path: str | Path) -> int:
    """Get file size in bytes."""
```

**Exceptions:**

- `FileError` - Base exception
- `FileReadError` - Read operation failed
- `FileWriteError` - Write operation failed

---

### `preciz.editor`

Precise file editing.

```python
from preciz.editor import Editor, EditOperation, edit_file
```

**Class: EditOperation**

```python
@dataclass(frozen=True)
class EditOperation:
    old_text: str      # Exact text to replace
    new_text: str      # Replacement text
    replace_all: bool = False  # Replace all occurrences?
```

**Class: Editor**

```python
class Editor:
    def __init__(self, file_path: str) -> None:
        """Initialize editor for a file."""

    def apply_edit(self, edit: EditOperation) -> None:
        """Apply a single edit operation."""

    def apply_edits(self, edits: list[EditOperation]) -> None:
        """Apply multiple edits in order."""

    def save(self) -> None:
        """Write edited content back to file."""

    def preview_changes(self) -> str:
        """Get current content with unapplied changes."""

    def revert(self) -> None:
        """Revert all unapplied changes."""
```

**Function: edit_file**

```python
def edit_file(
    file_path: str,
    old_text: str,
    new_text: str,
    replace_all: bool = False,
) -> None:
    """Convenience function to edit a file."""
```

**Example:**

```python
# Single edit
edit_file("README.md", "v1.0", "v2.0")

# Replace all
edit_file("config.py", "localhost", "0.0.0.0", replace_all=True)

# With Editor
editor = Editor("file.md")
editor.apply_edit(EditOperation("old", "new"))
editor.save()
```

---

### `preciz.llm`

LLM client.

```python
from preciz.llm import LLMClient, Message, LLMResponse
```

**Class: Message**

```python
@dataclass(frozen=True)
class Message:
    role: Literal["system", "user", "assistant"]
    content: str
```

**Class: LLMResponse**

```python
@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str
    finish_reason: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
```

**Class: LLMClient**

```python
class LLMClient:
    def __init__(self, config: Config) -> None:
        """Initialize client."""

    def complete(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Get completion from LLM."""

    def complete_stream(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """Stream completion from LLM."""
```

**Example:**

```python
client = LLMClient(Config.from_env())

response = client.complete([
    Message(role="system", content="You are helpful."),
    Message(role="user", content="Hello"),
])

print(response.content)
```

---

### `preciz.agent`

Main agent.

```python
from preciz.agent import PrecizAgent, EditPlan, EditParseError
```

**Class: PrecizAgent**

```python
class PrecizAgent:
    def __init__(self, config: Config | None = None) -> None:
        """Initialize the agent."""

    def plan_edits(
        self,
        instruction: str,
        file_path: str,
        file_content: str | None = None,
    ) -> EditPlan:
        """Plan edits using LLM."""

    def apply_plan(self, file_path: str, plan: EditPlan) -> None:
        """Apply an edit plan to a file."""

    def edit_file(
        self,
        instruction: str,
        file_path: str,
        dry_run: bool = False,
    ) -> EditPlan:
        """Edit a file based on instruction."""
```

**Class: EditPlan**

```python
@dataclass
class EditPlan:
    edits: list[EditOperation]
    reasoning: str = ""
```

**Example:**

```python
agent = PrecizAgent()

# Plan and apply
plan = agent.plan_edits("Fix typos", "file.md")
print(plan.reasoning)
agent.apply_plan("file.md", plan)

# One-liner
agent.edit_file("Update version to 2.0", "README.md")

# Dry run
plan = agent.edit_file("Make changes", "file.md", dry_run=True)
# Preview without applying
```

---

### `preciz.orchestrator`

Document orchestrator.

```python
from preciz.orchestrator import (
    DocumentOrchestrator,
    BlockTask,
    OrchestrationState,
    GenerateTool,
    ReviewTool,
    ImproveTool,
    AppendTool,
    generate_long_document,
)
```

**Class: BlockTask**

```python
@dataclass
class BlockTask:
    title: str
    description: str
    level: int
    require_mermaid: bool = False
    require_table: bool = False
    require_examples: bool = True
    completed: bool = False
    content: str = ""
```

**Class: OrchestrationState**

```python
@dataclass
class OrchestrationState:
    topic: str
    output_file: str
    target_lines: int
    tasks: list[BlockTask]
    current_task_index: int = 0
    total_lines: int = 0
    start_time: float = 0
```

**Methods:**

- `state.save(path: str) -> None` - Save state to file
- `OrchestrationState.load(path: str, llm: LLMClient) -> OrchestrationState` - Load state

**Class: DocumentOrchestrator**

```python
class DocumentOrchestrator:
    def __init__(self, config: Config | None = None) -> None:
        """Initialize orchestrator."""

    def create_todo_list(
        self, topic: str, target_lines: int = 10000
    ) -> list[BlockTask]:
        """Create a todo list of sections."""

    def generate_document(
        self,
        topic: str,
        output_file: str,
        target_lines: int = 10000,
        max_iterations: int = 2,
        state_file: str | None = None,
    ) -> str:
        """Generate a long document."""
```

**Class: GenerateTool**

```python
class GenerateTool:
    def __init__(self, llm: LLMClient) -> None:
        """Initialize tool."""

    def generate(
        self,
        topic: str,
        section_title: str,
        description: str,
        context: str,
        include_mermaid: bool = False,
        include_table: bool = False,
        include_examples: bool = True,
    ) -> str:
        """Generate a content block."""
```

**Class: ReviewTool**

```python
class ReviewTool:
    def __init__(self, llm: LLMClient) -> None:
        """Initialize tool."""

    def review(self, content: str, title: str) -> dict:
        """Review content for quality."""
```

**Class: ImproveTool**

```python
class ImproveTool:
    def __init__(self, llm: LLMClient) -> None:
        """Initialize tool."""

    def improve(
        self, content: str, title: str, feedback: dict
    ) -> str:
        """Improve content based on feedback."""
```

**Class: AppendTool**

```python
class AppendTool:
    def __init__(self, output_file: str) -> None:
        """Initialize tool."""

    def append(self, content: str) -> int:
        """Append content to document."""

    def get_line_count(self) -> int:
        """Get current line count."""
```

**Function: generate_long_document**

```python
def generate_long_document(
    topic: str,
    output_file: str,
    target_lines: int = 10000,
    config: Config | None = None,
) -> str:
    """Convenience function for generation."""
```

**Example:**

```python
# Simple
generate_long_document(
    "Python Programming",
    "python.md",
    target_lines=10000,
)

# Full control
orchestrator = DocumentOrchestrator()
orchestrator.generate_document(
    topic="Calculus",
    output_file="calculus.md",
    target_lines=15000,
    max_iterations=2,
    state_file="state.json",
)
```

---

## CLI Commands

### `preciz` - File Editing

```bash
preciz <instruction> <file_path>
```

**Examples:**

```bash
preciz "Fix the typo" README.md
preciz "Update version to 2.0" setup.py
```

### `preciz-gen-long` - Long Document Generation

```bash
preciz-gen-long <topic> <output_file> [options]
```

**Options:**

- `--lines <n>` - Target line count (default: 10000)
- `--iter <n>` - Max review iterations (default: 2)

**Examples:**

```bash
preciz-gen-long "Differential Calculus" calculus.md
preciz-gen-long "Python Async" async.md --lines 5000 --iter 3
```

---

## Exceptions

```python
# File operations
class FileError(Exception): pass
class FileReadError(FileError): pass
class FileWriteError(FileError): pass

# Editing
class EditError(FileError): pass
class EditParseError(Exception): pass
```

---

## Type Aliases

```python
from typing import Literal

FilePath = str | Path
Encoding = Literal["utf-8", "utf-8-sig", "latin-1"]
Provider = Literal["openrouter", "openai"]
MessageRole = Literal["system", "user", "assistant"]
```

---

## See Also

- [Usage Guide](usage.md)
- [Orchestrator Pattern](orchestrator.md)
- [Architecture](architecture.md)
