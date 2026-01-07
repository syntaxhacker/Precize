# CLI Commands

Reference for Preciz command-line tools.

## preciz - File Editing

Edit files using natural language instructions.

### Synopsis

```bash
preciz <instruction> <file_path>
```

### Description

Reads a file, sends it to the LLM with your instruction, and applies precise edits after confirmation.

### Options

| Option | Description |
|--------|-------------|
| `-h, --help` | Show help message |

### Examples

```bash
# Fix a typo
preciz "Fix the typo in line 5" README.md

# Update content
preciz "Change version 1.0 to version 2.0" setup.py

# More complex edit
preciz "Reorganize the sections in order" docs/guide.md

# Replace all occurrences
preciz "Replace localhost with production.example.com" config.yaml
```

### Output

```bash
$ preciz "Change version to 2.0" README.md

Preciz: Analyzing README.md...
Task: Change version to 2.0

Plan: Update version number
Edits to apply: 1

1. Replace:
   'Version 1.0'
   with:
   'Version 2.0'

Apply these changes? [y/N] y
Changes applied successfully!
```

### Error Handling

```bash
$ preciz "Make changes" nonexistent.md

Error: File not found: nonexistent.md
```

## preciz-gen-long - Long Document Generation

Generate 10,000+ line educational documents.

### Synopsis

```bash
preciz-gen-long <topic> <output_file> [options]
```

### Description

Creates a detailed outline, then generates each section using the orchestrator pattern with customizable content preferences. The CLI uses `DocumentOrchestrator` (NOT `BlockContentGenerator`).

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--lines <n>` | Target line count | 10000 |
| `--iter <n>` | Max review iterations per block | 2 |
| `--gen-mode <mode>` | Generation mode (auto, llm, parts, custom) | auto |
| `--parts <n>` | Number of parts for 'parts' mode (overrides auto-calc) | auto |
| `--approve-outline` | Prompt to approve outline before generation | false |
| `-h, --help` | Show help message | |

### Content Customization

| Option | Description | Values |
|--------|-------------|--------|
| `--audience <level>` | Target audience level | beginner, intermediate, advanced |
| `--style <style>` | Teaching style | progressive, direct, reference |
| `--no-analogies` | Skip everyday analogies | - |
| `--no-code` | Skip code examples | - |
| `--no-diagrams` | Skip mermaid diagrams | - |
| `--no-tables` | Skip comparison tables | - |
| `--code-lang <lang>` | Specific language for code examples | python, javascript, etc. |
| `--code-examples <n>` | Number of code examples per section | 3 (default) |

**Note**: Without customization flags, the CLI will prompt you interactively for preferences.

### Outline Approval

When using `--approve-outline`, you can review and edit the outline before generation begins:

```bash
$ preciz-gen-long "Deep Learning" dl.md --approve-outline

======================================================================
  LLM created 25 sections
======================================================================

======================================================================
  OUTLINE PREVIEW
======================================================================

  1. Foundations: Neural Networks from Scratch
  2. The Perceptron: Building Block of Deep Learning
  3. Activation Functions: Bringing Non-Linearity
  ...
  25. Production Deployment: Model Serving

Total: 25 sections planned

Proceed with this outline? [Y/n/edit]: edit

✓ Outline saved to outline.json

Edit the file to modify sections, then press Enter to continue...
Press Ctrl+C to cancel
```

**Edit Workflow:**

1. Type `edit` to save the outline to `outline.json`
2. Open `outline.json` in your editor
3. Modify sections (add, remove, reorder, change titles)
4. Save and close the file
5. Press Enter in the terminal
6. Confirm the modified outline

**Example `outline.json`:**

```json
{
  "title": "Deep Learning",
  "sections": [
    {
      "title": "Foundations: Neural Networks from Scratch",
      "level": 1,
      "description": "Build intuition before math",
      "require_mermaid": true,
      "require_table": false,
      "require_examples": true
    }
  ]
}
```

### Generation Modes

| Mode | Description | When to Use |
|------|-------------|-------------|
| `auto` | Try LLM outline, fall back to parts if it fails | Default - best balance |
| `llm` | Use LLM to create detailed outline | When you want best quality and have a good model |
| `parts` | Simple numbered parts | Most reliable - when LLM outline fails |
| `custom` | Load sections from JSON file | When you want full control over structure |

### Audience Levels

| Level | Description | Content Style |
|-------|-------------|---------------|
| `beginner` | Zero prior knowledge | Everyday analogies, step-by-step, "why" before "what" |
| `intermediate` | Some prior knowledge | Bridges from known concepts, targeted analogies |
| `advanced` | Deep technical dive | Formal definitions, architecture, production patterns |

### Teaching Styles

| Style | Description | Structure |
|-------|-------------|-----------|
| `progressive` | Build from zero to mastery | Foundation → Concept → Implementation → Mastery |
| `direct` | Jump to technical content | Core Concepts → Implementation → Reference |
| `reference` | Encyclopedia style | Hierarchical organization, comprehensive coverage |

### Examples

```bash
# Basic usage (auto mode, interactive preferences)
preciz-gen-long "Differential Calculus" calculus.md

# Non-interactive: advanced audience, direct style
preciz-gen-long "API Design" api.md --audience advanced --style direct --no-analogies

# Non-interactive: beginner guide without diagrams
preciz-gen-long "Git Basics" git.md --audience beginner --no-diagrams

# Non-interactive: reference style, no code
preciz-gen-long "HTTP History" http.md --style reference --no-code

# Custom length with LLM mode
preciz-gen-long "Python Basics" python.md --lines 5000 --gen-mode llm

# Code-heavy with specific language
preciz-gen-long "React Patterns" react.md --audience advanced --code-lang typescript --code-examples 5

# Parts mode with automatic calculation
preciz-gen-long "Machine Learning" ml.md --lines 15000 --gen-mode parts

# Parts mode with explicit number of parts
preciz-gen-long "React" react.md --gen-mode parts --parts 20

# Custom mode with JSON file
preciz-gen-long "ML Basics" ml.md --gen-mode custom my_sections.json

# More iterations (higher quality)
preciz-gen-long "Distributed Systems" ds.md --lines 50000 --iter 3 --audience advanced
```

### Interactive Mode

When you run without customization flags, you'll be prompted:

```
============================================================
  Content Customization for: Differential Calculus
============================================================

1. Target Audience:
   [1] Absolute Beginner (zero prior knowledge)
   [2] Intermediate (some prior knowledge)
   [3] Advanced (deep technical dive)
   Choose [1-3] [default: 1]: 1

2. Include Analogies?
   [Y]es - Use everyday analogies to explain concepts
   [N]o - Direct technical approach
   Include analogies? [Y/n] [default: Y]: Y

3. Include Code Examples?
   [Y]es - With runnable examples
   [N]o - Concepts and theory only
   Include code? [Y/n] [default: Y]: Y
   Language [default: auto-detect]: python
   Examples per section [default: 3]: 5

4. Include Diagrams?
   [Y]es - Add mermaid diagrams
   [N]o - Text-only content
   Include diagrams? [Y/n] [default: Y]:

5. Include Comparison Tables?
   [Y]es - Add tables for concepts
   [N]o - No tables
   Include tables? [Y/n] [default: Y]:

6. Teaching Style:
   [1] Progressive - Foundation → Concept → Implementation
   [2] Direct - Jump straight to technical content
   [3] Reference - Encyclopedia style
   Choose [1-3] [default: 1]: 1

============================================================
  Configuration Summary
============================================================
  Audience:      Beginner
  Style:         Progressive
  Analogies:     Yes
  Code:          Yes
    Language:    python
    Examples:    5/section
  Diagrams:      Yes
  Tables:        Yes
============================================================
```

### Custom Sections File Format

For `--gen-mode custom`, create a JSON file:

```json
{
  "title": "Document Title",
  "sections": [
    {
      "title": "Introduction",
      "level": 1,
      "description": "Overview and history",
      "require_mermaid": true,
      "require_table": false,
      "require_examples": true
    },
    {
      "title": "Getting Started",
      "level": 1,
      "description": "Installation and setup",
      "require_mermaid": false,
      "require_table": true,
      "require_examples": true
    }
  ]
}
```

See `sections_example.json` for a complete example.

### Output

```bash
$ preciz-gen-long "Python Sets" sets.md --lines 1000

======================================================================
  ORCHESTRATOR: Long Document Generator
======================================================================

Topic: Python Sets
Target: 1000 lines
Output: sets.md

Creating outline...
  → Created 15 sections

======================================================================
  PHASE 2: GENERATING BLOCKS
======================================================================

[1/15] Introduction to Sets
------------------------------------------------------------
  → Generating: Introduction to Sets
    Generated 124 lines
  → Review 1/2
    ✓ Passed
  → Appended (total: 124 lines)

[2/15] Set Operations
------------------------------------------------------------
  → Generating: Set Operations
    Generated 156 lines
  → Review 1/2
    ✓ Passed
  → Appended (total: 280 lines)
...
```

### Progress Indicators

| Indicator | Meaning |
|-----------|---------|
| `→ Generating...` | Creating content block |
| `Generated X lines` | Block size |
| `Review N/M` | Review iteration |
| `✓ Passed` | Quality check passed |
| `⚠ Found N issues` | Quality check failed |
| `→ Appended` | Added to document |
| `total: X lines` | Current document size |

### Completion

```bash
======================================================================
  COMPLETE
======================================================================

Sections: 50
Lines: 10234
Time: 342.5s
Output: sets.md
```

## preciz-generate - Original Generator

Original content generator (deprecated, use `preciz-gen-long`).

### Synopsis

```bash
preciz-generate <topic> <output_file> [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--brief` | Generate shorter content |
| `--advanced` | Target advanced audience |
| `--beginner` | Target beginner audience |
| `--no-practical` | Skip practical exercises |

### Note

This is the original generator. Use `preciz-gen-long` for better results with long documents.

## Common Options

### Help

All commands support `-h` or `--help`:

```bash
preciz --help
preciz-gen-long --help
preciz-generate --help
```

### Environment

Commands respect `.env` file:

```bash
# Must have .env in current directory
cat .env
API_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
LLM_MODEL=xiaomi/mimo-v2-flash:free

preciz "edit" file.md  # Uses .env config
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error |
| 130 | Interrupted (Ctrl+C) |

## Tips

1. **Always confirm** - Review edits before applying
2. **Use quotes** - Wrap instruction in quotes
3. **Be specific** - More context = better edits
4. **Start small** - Test with shorter documents first

## See Also

- [Quick Start](quickstart.md)
- [Usage Guide](usage.md)
- [API Reference](api.md)
