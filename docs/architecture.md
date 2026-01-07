# Preciz Architecture

Preciz uses a modular, agent-based architecture with reusable tools.

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Preciz                               │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │   Editor    │  │  Generator   │  │   Orchestrator      │ │
│  │  (deprecated)│  │  (deprecated) │  │   (teaching agent)  │ │
│  └─────────────┘  └──────────────┘  └─────────────────────┘ │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Teaching Agent (agents/teaching/)        │   │
│  │  - orchestrator.py (Document generation logic)       │   │
│  │  - preferences.py (Content preferences)               │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Tools (tools/)                       │   │
│  │  ┌────────────┐  ┌─────────────┐  ┌──────────────┐  │   │
│  │  │  Mermaid    │  │ Completion   │  │ (Future tools)│  │   │
│  │  │  Tool       │  │  Checker     │  │              │  │   │
│  │  └────────────┘  └─────────────┘  └──────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Core Infrastructure (core/)               │   │
│  │  - config.py    - llm.py      - logger.py           │   │
│  │  - file_ops.py  - editor.py                         │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              CLI Layer (cli/)                         │   │
│  │  - generate.py  - content.py  - verify.py            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Config Module (`core/config.py`)

Configuration management using environment variables.

```python
from preciz.core.config import Config

config = Config.from_env()
# Supports: OpenRouter, OpenAI
# Auto-loads from .env file
```

**Features:**
- Frozen dataclass for immutability
- OpenRouter and OpenAI support
- Configurable timeouts and retries

### 2. LLM Client (`core/llm.py`)

Unified client for OpenAI/OpenRouter APIs.

```python
from preciz.core import LLMClient, Message

client = LLMClient(config)
response = client.complete([
    Message(role="user", content="Hello")
])
```

**Features:**
- Streaming support
- Token usage tracking
- Configurable temperature/max_tokens

### 3. Logger (`core/logger.py`)

Session-based logging with metadata tracking.

```python
from preciz.core import SessionLogger

logger = SessionLogger(topic="My Topic", output_file="out.md")
with logger:
    logger.info("Processing...")
    logger.log_llm_request(...)
```

**Features:**
- Automatic log file creation
- LLM call tracking
- Structured output with colors

### 4. Teaching Agent (`agents/teaching/`)

Main agent for generating educational content.

```
DocumentOrchestrator
├── GenerateTool - Create content blocks (100-200 lines)
├── ReviewTool - Quality check against teaching standards
├── ImproveTool - Fix issues based on feedback
└── preferences.py - Content customization
```

**Tools:**

| Tool | Purpose |
|------|---------|
| `GenerateTool` | Generate a content block |
| `ReviewTool` | Review content against quality checklist |
| `ImproveTool` | Improve content based on feedback |
| `AppendTool` | Append content to document with validation |

### 5. Mermaid Tool (`tools/mermaid/`)

Extract, convert, and fix Mermaid diagrams.

```python
from preciz.tools.mermaid import verify_and_convert_mermaid, pre_fix_mermaid

# Convert mermaid blocks to PNG images
content = verify_and_convert_mermaid(
    content=markdown,
    section_index=0,
    section_title="My Section",
    llm=llm_client
)

# Pre-fix common syntax errors
fixed = pre_fix_mermaid(broken_mermaid_code)
```

**Components:**
- `verifier.py` - Extract blocks, convert to PNG, replace with image refs
- `prefixer.py` - Regex-based fixes for common syntax errors
- `cli.py` - Standalone mermaid verification command

### 6. Completion Checker Tool (`tools/completion/`)

Detect incomplete sections in generated markdown.

```python
from preciz.tools.completion import detect_incomplete_sections

issues = detect_incomplete_sections(markdown_content)
```

## File Structure

```
preciz/
├── agents/                    # Agent implementations
│   ├── teaching/              # Teaching/Content Generation Agent
│   │   ├── orchestrator.py     # Main document generation
│   │   └── preferences.py      # Content preferences
│   └── __init__.py
│
├── tools/                     # Reusable tools
│   ├── mermaid/               # Mermaid diagram tool
│   │   ├── verifier.py        # Extract & convert diagrams
│   │   ├── prefixer.py        # Pre-fix common errors
│   │   └── cli.py             # Standalone CLI
│   ├── completion/            # Content validation
│   │   ├── checker.py         # Incomplete section detection
│   │   └── cli.py             # Standalone CLI
│   └── __init__.py
│
├── core/                      # Shared infrastructure
│   ├── config.py              # Configuration
│   ├── llm.py                 # LLM client
│   ├── logger.py              # Logging utilities
│   ├── file_ops.py            # File operations
│   └── editor.py              # File editing
│
├── cli/                       # Top-level CLI commands
│   ├── generate.py            # preciz-gen-long
│   ├── content.py             # preciz-generate
│   └── verify.py              # Verification tests
│
├── prompts/                   # Prompts organized by agent/tool
│   ├── teaching/              # Teaching agent prompts
│   └── tools/                 # Tool-specific prompts
│
├── _archive/                  # Legacy files (deprecated)
│   ├── agent.py
│   ├── generator.py
│   └── generator_v2.py
│
└── __init__.py
```

## Design Principles

### 1. Agent-Based Architecture

- **Agents**: High-level coordinators (teaching, future agents)
- **Tools**: Reusable components that any agent can use
- **Core**: Shared infrastructure

### 2. Tool Reusability

Tools are independent and can be used by any agent:
- Mermaid tool can be used by teaching agent or future agents
- Completion checker can validate any markdown content

### 3. Clear Separation

- **Agents** orchestrate but don't implement low-level logic
- **Tools** implement specific functionality
- **Core** provides foundational services

### 4. Progressive Teaching

The teaching agent follows a specific pedagogical model:
- Foundation → Concepts → Implementation → Mastery
- Zero-to-expert buildup
- Analogies before technical terms

## Data Flow

### Content Generation Flow

```
Topic → Teaching Agent
         ↓
    Create Outline (LLM)
         ↓
    [User Approval with --approve-outline]
         ↓
    For Each Section:
      GenerateTool → LLM → Content (100-200 lines)
           ↓
      ReviewTool → LLM → Feedback
           ↓
      (if issues) ImproveTool → LLM → Improved Content
           ↓
      Mermaid Tool → Convert diagrams to PNG
           ↓
      AppendTool → File (with validation)
           ↓
      Update Progress
```

### Diagram Processing Flow

```
Markdown Content
       ↓
Extract Mermaid Blocks
       ↓
Pre-fix Common Errors (regex)
       ↓
Convert to PNG (mmdc)
       ↓
    Success?
       ├─ Yes → Save PNG + .mmd source → Replace block with image ref
       └─ No → LLM Fix (up to 3 retries) → Try again
```

## Key Design Decisions

### Why Agent-Based Architecture?

- **Scalability**: Easy to add new agents (code review, testing, etc.)
- **Reusability**: Tools can be shared across agents
- **Maintainability**: Clear boundaries between components

### Why Pre-Fixer Before LLM Fix?

- **Cost**: Regex is free, LLM calls cost money
- **Speed**: Regex is instant, LLM has latency
- **Reliability**: Consistent fixes for known patterns
- ~80% of issues caught by pre-fixer

### Why Save .mmd Source Files?

- **Debugging**: Can inspect what code was actually generated
- **Reusability**: Can edit and reconvert manually
- **Learning**: See working mermaid examples
- **Transparency**: Full visibility into fixes applied

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Pre-fix mermaid | O(n) | n = code length, regex is fast |
| LLM fix attempt | O(1) | Depends on API latency |
| mmdc conversion | O(1) | Depends on diagram complexity |
| Block generation | O(1) | 100-200 lines fixed |
| Full document | O(k) | k = number of sections |

## Extension Points

### Adding New Tools

Create a new directory under `tools/`:

```python
# tools/mytool/__init__.py
from .processor import process_data

__all__ = ["process_data"]
```

### Adding New Agents

Create a new directory under `agents/`:

```python
# agents/myagent/__init__.py
from .coordinator import MyAgent

__all__ = ["MyAgent"]
```

### Custom Prompts

Edit prompt files in `prompts/teaching/` or `prompts/tools/`.

## See Also

- [CLI Reference](cli.md)
- [Mermaid Documentation](mermaid.md)
- [API Reference](api.md)
