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

Creates a detailed outline, then generates each section using the orchestrator pattern.

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--lines <n>` | Target line count | 10000 |
| `--iter <n>` | Max review iterations per block | 2 |
| `-h, --help` | Show help message | |

### Examples

```bash
# Basic usage
preciz-gen-long "Differential Calculus" calculus.md

# Custom length
preciz-gen-long "Python Basics" python.md --lines 5000

# More iterations (higher quality)
preciz-gen-long "React" react.md --lines 15000 --iter 3

# Very long document
preciz-gen-long "Machine Learning" ml.md --lines 50000
```

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
