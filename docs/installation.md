# Installation

Install Preciz on your system.

## Requirements

- Python 3.10 or higher
- pip or poetry for package management
- API key for OpenAI or OpenRouter

## Install from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/preciz.git
cd preciz

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Install with pip

```bash
pip install preciz
```

## Verify Installation

```bash
# Check CLI is available
preciz --help
preciz-gen-long --help

# Test Python import
python -c "from preciz import PrecizAgent; print('OK')"
```

## Configuration

Create a `.env` file in your project directory:

```bash
# OpenRouter (recommended for free models)
API_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-key-here
LLM_MODEL=xiaomi/mimo-v2-flash:free

# OR OpenAI
API_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4o-mini
```

## Getting an API Key

### OpenRouter (Free Models Available)

1. Visit [openrouter.ai](https://openrouter.ai)
2. Sign up for an account
3. Get your API key from settings
4. Free models available:
   - `xiaomi/mimo-v2-flash:free`
   - `google/gemma-7b-it:free`
   - And more

### OpenAI

1. Visit [platform.openai.com](https://platform.openai.com)
2. Sign up or log in
3. Create an API key
4. Add credits to your account

## Development Installation

For contributing to Preciz:

```bash
# Clone repository
git clone https://github.com/yourusername/preciz.git
cd preciz

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=preciz
```

## Docker Installation

```bash
# Build image
docker build -t preciz .

# Run container
docker run -v $(pwd)/output:/app/output --env-file .env preciz
```

## Next Steps

- [Quick Start Guide](quickstart.md)
- [Configuration](configuration.md)
- [Usage Guide](usage.md)
