# Mermaid Diagram Verification

Automatic conversion of Mermaid diagrams to PNG images during document generation.

## Overview

Preciz automatically detects, converts, and replaces Mermaid diagram code blocks with rendered PNG images:

- ✅ **Extracts** Mermaid blocks from generated content
- ✅ **Converts** to PNG using `mmdc` (mermaid-cli)
- ✅ **Fixes** broken syntax with LLM (up to 3 retries)
- ✅ **Replaces** code blocks with image references
- ✅ **Logs** all conversions and fix attempts

## How It Works

### During Generation

```
┌─────────────────────────────────────────────────────────────┐
│  Section Generated with Mermaid Code                       │
│                                                             │
│  ## Component Flow                                         │
│                                                             │
│  ```mermaid                                                 │
│  flowchart LR                                              │
│    A[Parent] --> B[Child]                                  │
│  ```                                                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  1. EXTRACT Mermaid Blocks                                 │
│     Find all ```mermaid...``` blocks                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  2. CONVERT to PNG (mmdc)                                  │
│     Write temp.mmd → Run mmdc → Save PNG                   │
└─────────────────────────────────────────────────────────────┘
                            │
                    ┌─────────┴─────────┐
                    │                   │
                SUCCESS             FAILURE
                    │                   │
                    ▼                   ▼
┌──────────────────────────┐  ┌─────────────────────────────┐
│  3. SAVE PNG              │  │  3. FIX WITH LLM             │
│     images/diagram-1.png  │  │     - Send error + code       │
└──────────────────────────┘  │     - Get fixed code          │
                              │     - Retry (max 3)          │
                              └─────────────┬───────────────┘
                                            │
                            ┌───────────┴───────────┐
                            │                       │
                        SUCCESS                 FAILURE
                            │                       │
                            ▼                       ▼
              ┌──────────────────┐  ┌─────────────────────────┐
              │  4. REPLACE WITH   │  │  4. KEEP ORIGINAL CODE    │
              │     ![image]()    │  │     (Mermaid block)       │
              └──────────────────┘  └─────────────────────────┘
```

## Installation

### Install mermaid-cli

```bash
npm install -g @mermaid-js/mermaid-cli
```

### Verify Installation

```bash
mmdc --version
# Should output version number
```

### System Requirements

- **Node.js** (required by mermaid-cli)
- **Puppeteer/Chromium** (for PNG rendering)

## Usage

### Automatic During Generation

Mermaid verification is automatic when diagrams are enabled:

```bash
# This will automatically convert mermaid to PNG
preciz-gen-long "React Components" react.md --audience beginner
```

Console output:
```
[1/3] React Components
  → Generated 165 lines
  → Review 1/2
    ✓ Passed
  → Found 2 Mermaid diagram(s)
     Converting diagram 1...
  ✓ Converted: mermaid-1-1-React_Components.png
     Converting diagram 2...
  ✓ Converted: mermaid-1-2-React_Components.png
  → Appended (total: 173 lines)
```

### Skip Mermaid Conversion

```bash
# Skip diagram conversion entirely
preciz-gen-long "Topic" output.md --no-diagrams
```

### Standalone Verification

Convert mermaid diagrams in existing markdown files:

```bash
# Verify and convert all mermaid in a file
preciz-mermaid-verify document.md

# Custom images directory
preciz-mermaid-verify document.md --images-dir diagrams

# Don't modify original, create new file
preciz-mermaid-verify document.md --output verified.md

# Skip LLM fixing (fail fast on errors)
preciz-mermaid-verify document.md --no-fix

# Dry run (show what would be done)
preciz-mermaid-verify document.md --dry-run
```

## Diagram Styling

Generated diagrams automatically follow these style requirements:

### Layout & Theme

```mermaid
%%{init: {'theme':'neutral', 'themeVariables': {'lineColor': '#ffffff', 'edgeLabelBackground':'#ffffff'}}}%%
flowchart LR
    A[🚀 Start] --> B[🎯 Process] --> C[✅ End]
```

### Color Coding

```mermaid
classDef success fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#155724
classDef error fill:#f8d7da,stroke:#dc3545,stroke-width:2px,color:#721c24
classDef warning fill:#fff3cd,stroke:#ffc107,stroke-width:2px,color:#856404
classDef info fill:#cce5ff,stroke:#0066cc,stroke-width:2px,color:#004085
```

### Requirements

| Requirement | Value |
|-------------|-------|
| Layout | Horizontal (`flowchart LR` or `graph LR`) |
| Theme | `neutral` with white arrows |
| Aspect Ratio | 3.5:1 to 4:1 (wide) |
| Labels | Descriptive, context-specific |
| Icons | Emojis (🚀, ✅, 🚨, 🔄, 📊, 🎯, 🧠) |

## LLM-Based Fixing

When mermaid conversion fails, the LLM is prompted to fix the syntax.

### What Gets Fixed

Common mermaid syntax errors:
- Missing semicolons
- Invalid node IDs (spaces, special characters)
- Unclosed brackets/parentheses
- Incorrect syntax (flowchart vs graph vs sequenceDiagram)
- Missing quotes around labels
- Invalid classDef syntax
- Double curly braces in init directive

### Fix Process

```
Attempt 1: Original code
    ↓ Failure
Attempt 2: LLM fixes based on error
    ↓ Failure
Attempt 3: LLM fixes again
    ↓ Failure
Attempt 4: LLM fixes one more time
    ↓ Success or Give up
```

### Example Fix

**Broken Code:**
```mermaid
flowchart LR
    A[Parent Component] -->|passes data| B[Child Component]
    B --> C[Internal State]
```

**Error:** `Syntax error: Invalid node ID 'Child Component' (contains spaces)`

**Fixed Code:**
```mermaid
%%{init: {'theme':'neutral', 'themeVariables': {'lineColor': '#ffffff'}}}%%
flowchart LR
    A[🎯 Parent Component] -->|passes data| B[🧩 Child Component]
    B -->|manages| C[🔄 Internal State]

    classDef parent fill:#cce5ff,stroke:#0066cc,stroke-width:2px,color:#004085
    classDef child fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#155724
    classDef state fill:#fff3cd,stroke:#ffc107,stroke-width:2px,color:#856404

    class A parent
    class B child
    class C state
```

## File Structure

After generation with mermaid diagrams:

```
project/
├── react.md                  # Markdown with image references
└── images/
    ├── mermaid-1-1-React_Components.png
    ├── mermaid-1-2-React_Components.png
    ├── mermaid-2-1-Data_Flow.png
    └── ...
```

## Troubleshooting

### mermaid-cli Not Found

**Error:**
```
Error: mmdc command not found
```

**Solution:**
```bash
npm install -g @mermaid-js/mermaid-cli
```

### Conversion Timeout

**Error:**
```
✗ Failed: Conversion timed out after 30 seconds
```

**Solution:** Complex diagrams may take longer. The timeout is set to 30 seconds. Consider simplifying very complex diagrams.

### Persistent Failures

If a diagram fails after 3 LLM fix attempts:

1. **Check the log file** for error details
2. **Manual fix**: Extract the mermaid code, fix it manually, and run `mmdc` directly
3. **Keep original**: The original mermaid code block is preserved in the markdown if all attempts fail

### No Images Directory Created

**Issue**: `images/` directory doesn't exist

**Solution**: It's only created if mermaid diagrams are found and successfully converted.

## Advanced Usage

### Python API

```python
from preciz.mermaid_verifier import verify_and_convert_mermaid
from preciz.config import Config
from preciz.llm import LLMClient

config = Config.from_env()
llm = LLMClient(config)

# Verify and convert mermaid in content
content_with_images = verify_and_convert_mermaid(
    content=markdown_content,
    section_index=0,
    section_title="Component Flow",
    llm=llm,
    images_dir="diagrams",
    logger=logger
)
```

### Custom Fix Prompt

Edit `preciz/prompts/mermaid_fixer.py` to customize the fix prompt:

```python
def build_fix_mermaid_prompt(original_code: str, error: str, context: str) -> str:
    return f"""Fix this broken Mermaid diagram.

**Error from mermaid-cli:**
{error}

**Original Mermaid Code:**
```mermaid
{original_code}
```

**Your custom requirements here...**

Return ONLY the fixed mermaid code:
"""
```

## See Also

- [Long Document Generation](generation.md)
- [CLI Commands](cli.md)