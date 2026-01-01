# Preciz

A precise file editing agent focused on accurate, incremental edits to files (especially markdown).

## Features

- **Precise Edits**: Uses exact string matching to ensure accurate edits
- **LLM-Powered**: Leverages OpenAI/OpenRouter models for intelligent editing
- **Minimal & Fast**: Small, modular codebase with focused functionality
- **CLI Interface**: Simple command-line interface for quick edits
- **Well-Tested**: Comprehensive test coverage from the start

## Installation

```bash
# Clone the repo
git clone <repo-url>
cd preciz

# Create venv and install
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -e .
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
API_PROVIDER=openrouter  # or "openai"
OPENROUTER_API_KEY=your-key-here
LLM_MODEL=xiaomi/mimo-v2-flash:free
```

## Usage

### CLI

```bash
preciz "Fix the typo in line 5" README.md
preciz "Update the installation instructions" docs/setup.md
preciz "Add a new example section" examples.md
```

### Python API

```python
from preciz import PrecizAgent
from preciz.config import Config

# Create agent
agent = PrecizAgent(Config.from_env())

# Plan and apply edits
plan = agent.edit_file(
    instruction="Change all occurrences of 'foo' to 'bar'",
    file_path="src/main.py",
)
```

### Direct Editing

```python
from preciz.editor import edit_file

# Simple edit
edit_file(
    file_path="README.md",
    old_text="Version 1.0",
    new_text="Version 2.0",
)

# Replace all occurrences
edit_file(
    file_path="config.yaml",
    old_text="localhost",
    new_text="0.0.0.0",
    replace_all=True,
)
```

## Project Structure

```
preciz/
├── preciz/
│   ├── __init__.py     # Package init
│   ├── config.py       # Configuration management
│   ├── file_ops.py     # File read/write operations
│   ├── editor.py       # Precise edit engine
│   ├── llm.py          # LLM client (OpenAI/OpenRouter)
│   ├── agent.py        # Main agent coordinator
│   └── cli.py          # CLI interface
├── tests/
│   ├── test_config.py
│   ├── test_file_ops.py
│   ├── test_editor.py
│   ├── test_llm.py
│   └── test_agent.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Running Tests

```bash
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest --cov=preciz       # With coverage
```

## License

MIT
