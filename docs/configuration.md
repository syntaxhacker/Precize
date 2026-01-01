# Configuration

Configure Preciz for your needs.

## Environment Variables

Preciz uses environment variables for configuration. Create a `.env` file:

```bash
# Required: API Provider
API_PROVIDER=openrouter  # or "openai"

# Required: API Key
OPENROUTER_API_KEY=sk-or-v1-your-key-here  # for OpenRouter
OPENAI_API_KEY=sk-your-key-here             # for OpenAI

# Optional: Model Selection
LLM_MODEL=xiaomi/mimo-v2-flash:free

# Optional: Advanced Settings
# LLM_MODEL=openai/gpt-4o-mini
# LLM_MODEL=anthropic/claude-3.5-haiku
```

## API Providers

### OpenRouter (Recommended)

**Pros:**
- Free models available
- Access to many LLM providers
- Single API key

**Free Models:**
- `xiaomi/mimo-v2-flash:free` - Fast, good quality
- `google/gemma-7b-it:free` - Google's Gemma
- `mistralai/mistral-7b-instruct:free` - Mistral AI

**Setup:**

```bash
API_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-key-here
LLM_MODEL=xiaomi/mimo-v2-flash:free
```

Get your key at [openrouter.ai](https://openrouter.ai).

### OpenAI

**Models:**
- `gpt-4o-mini` - Fast, cost-effective
- `gpt-4o` - Most capable
- `gpt-3.5-turbo` - Legacy model

**Setup:**

```bash
API_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4o-mini
```

Get your key at [platform.openai.com](https://platform.openai.com).

## Config Object

```python
from preciz.config import Config

# Load from environment
config = Config.from_env()

# Or create manually
from preciz.config import Config
config = Config(
    api_key="sk-...",
    model="gpt-4o-mini",
    provider="openai",
    max_retries=3,
    timeout=60,
)
```

## Config Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `api_key` | str | Required | Your API key |
| `model` | str | Required | Model name |
| `provider` | str | Required | "openrouter" or "openai" |
| `base_url` | str | auto | API base URL (auto-set by provider) |
| `max_retries` | int | 3 | Max retry attempts |
| `timeout` | int | 60 | Request timeout (seconds) |

## Model Recommendations

### For File Editing

| Model | Provider | Speed | Quality | Cost |
|-------|----------|-------|--------|------|
| `gpt-4o-mini` | OpenAI | ⚡⚡⚡ | ⭐⭐⭐⭐ | 💰 |
| `xiaomi/mimo-v2-flash:free` | OpenRouter | ⚡⚡⚡ | ⭐⭐⭐ | 🆓 |
| `claude-3.5-haiku` | OpenRouter | ⚡⚡ | ⭐⭐⭐⭐⭐ | 💰💰 |

### For Document Generation

| Model | Provider | Speed | Quality | Cost |
|-------|----------|-------|--------|------|
| `gpt-4o-mini` | OpenAI | ⚡⚡⚡ | ⭐⭐⭐⭐ | 💰 |
| `gpt-4o` | OpenAI | ⚡⚡ | ⭐⭐⭐⭐⭐ | 💰💰💰 |
| `claude-3.5-sonnet` | OpenRouter | ⚡⚡ | ⭐⭐⭐⭐⭐ | 💰💰💰 |

## Examples

### Free Model Setup

```bash
# .env
API_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
LLM_MODEL=xiaomi/mimo-v2-flash:free
```

### Production Setup

```bash
# .env
API_PROVIDER=openai
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
```

### High Quality Setup

```bash
# .env
API_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
LLM_MODEL=anthropic/claude-3.5-sonnet
```

## Python Configuration

### Global Config

```python
import os
from preciz.config import Config

# Set via environment
os.environ["API_PROVIDER"] = "openrouter"
os.environ["OPENROUTER_API_KEY"] = "sk-or-v1-..."
config = Config.from_env()
```

### Per-Component Config

```python
from preciz import PrecizAgent
from preciz.orchestrator import DocumentOrchestrator
from preciz.config import Config

# Use same config for all components
config = Config.from_env()

agent = PrecizAgent(config)
orchestrator = DocumentOrchestrator(config)
```

## Validation

The config is validated on creation:

```python
from preciz.config import Config

# Missing API key
try:
    config = Config(
        api_key="",  # Empty!
        model="gpt-4o-mini",
        provider="openai",
    )
except ValueError as e:
    print(f"Error: {e}")
    # "API key not found"
```

## Best Practices

1. **Never commit `.env`** - Add to `.gitignore`
2. **Use environment variables** - Don't hardcode keys
3. **Start with free models** - Test before paying
4. **Use different models for different tasks**
   - Fast/cheap for editing
   - Higher quality for generation

## See Also

- [Installation](installation.md)
- [Quick Start](quickstart.md)
- [API Reference](api.md)
