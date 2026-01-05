# Troubleshooting

Common issues and solutions.

## Installation Issues

### ModuleNotFoundError: No module named 'preciz'

**Problem:**
```bash
python -c "import preciz"
ModuleNotFoundError: No module named 'preciz'
```

**Solutions:**

1. Activate virtual environment:
```bash
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

2. Reinstall Preciz:
```bash
pip install -e .
```

3. Check Python path:
```bash
which python
python -m pip list | grep preciz
```

### Permission Denied

**Problem:**
```bash
pip install -e .
error: [Errno 13] Permission denied
```

**Solution:**
```bash
# Use user install
pip install --user -e .

# Or use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## Configuration Issues

### API Key Not Found

**Problem:**
```bash
ValueError: API key not found. Set OPENROUTER_API_KEY or OPENAI_API_KEY.
```

**Solutions:**

1. Create `.env` file:
```bash
API_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-key-here
LLM_MODEL=xiaomi/mimo-v2-flash:free
```

2. Set environment variable:
```bash
export OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

3. Pass config directly:
```python
from preciz.config import Config
config = Config(
    api_key="sk-or-v1-...",
    model="gpt-4o-mini",
    provider="openai",
)
```

### Invalid Model Name

**Problem:**
```bash
Error: Model 'unknown-model' not found
```

**Solution:**

Check available models:
- OpenRouter: https://openrouter.ai/models
- OpenAI: gpt-4o, gpt-4o-mini, gpt-3.5-turbo

```bash
# Correct
LLM_MODEL=xiaomi/mimo-v2-flash:free
LLM_MODEL=openai/gpt-4o-mini

# Incorrect
LLM_MODEL=gpt-4  # Need provider prefix
```

## Editing Issues

### EditError: Old Text Not Found

**Problem:**
```python
raise EditError("Old text not found")
```

**Solutions:**

1. Check the exact text (whitespace matters!):
```python
# Read file first
from preciz.file_ops import read_file
content = read_file("file.md")
print(repr(content))  # See exact formatting
```

2. Use more context:
```python
# Too vague
edit_file("file.md", "function", "def")

# Better
edit_file("file.md", "def my_function():", "def new_function():")
```

3. Check if file was already modified:
```bash
git diff file.md  # See what changed
```

### EditError: Multiple Occurrences

**Problem:**
```python
EditError: "Old text appears 5 times. Use replace_all=True"
```

**Solutions:**

1. Use replace_all:
```python
edit_file("file.md", "old", "new", replace_all=True)
```

2. Provide more unique context:
```python
# Instead of
edit_file("file.md", "print('hello')", "print('hi')")

# Use more context
edit_file("file.md", """
def main():
    print('hello')
""", """
def main():
    print('hi')
""")
```

## Generation Issues

### Generation is Too Slow

**Problem:** Taking too long to generate.

**Solutions:**

1. Use faster model:
```bash
LLM_MODEL=xiaomi/mimo-v2-flash:free  # Fast
```

2. Reduce iterations:
```python
generate_long_document(
    "Topic", "output.md",
    max_iterations=1,  # Less review
)
```

3. Reduce target length:
```bash
preciz-gen-long "Topic" output.md --lines 5000
```

### Quality is Inconsistent

**Problem:** Some sections are better than others.

**Solutions:**

1. Increase iterations:
```python
generate_long_document(
    "Topic", "output.md",
    max_iterations=3,  # More review cycles
)
```

2. Use better model:
```bash
LLM_MODEL=openai/gpt-4o-mini
```

3. Add custom review criteria:
```python
class StrictReviewTool(ReviewTool):
    def review(self, content, title):
        feedback = super().review(content, title)
        # Add more checks
        return feedback
```

### Document Too Short

**Problem:** Generated fewer lines than requested.

**Solutions:**

1. Increase target_lines:
```python
generate_long_document("Topic", "output.md", target_lines=15000)
```

2. Create more sections manually:
```python
tasks = [
    BlockTask("Section 1", "...", 1),
    BlockTask("Section 2", "...", 1),
    # ... add 50-100 sections
]
```

3. Check LLM response length:
```python
# Some models have output limits
LLM_MODEL=xiaomi/mimo-v2-flash:free  # May limit output
LLM_MODEL=openai/gpt-4o-mini           # Higher limits
```

## LLM API Issues

### Rate Limiting

**Problem:**
```bash
Error: 429 Too Many Requests
```

**Solutions:**

1. Add delays between requests:
```python
import time

for i, task in enumerate(tasks):
    content = gen_tool.generate(...)
    time.sleep(1)  # Wait 1 second between requests
```

2. Use exponential backoff:
```python
import time

def generate_with_retry(tool, ...):
    for attempt in range(3):
        try:
            return tool.generate(...)
        except RateLimitError:
            time.sleep(2 ** attempt)  # 1, 2, 4 seconds
```

### Timeout Errors

**Problem:**
```bash
Error: Request timeout
```

**Solutions:**

1. Increase timeout:
```python
from preciz.config import Config

config = Config(
    api_key="sk-...",
    model="gpt-4o-mini",
    provider="openai",
    timeout=120,  # 2 minutes
)
```

2. Reduce max_tokens:
```python
# In orchestrator.py, reduce from 3000 to 2000
response = self.llm.complete(..., max_tokens=2000)
```

## File Issues

### Permission Denied

**Problem:**
```python
FileWriteError: Permission denied: /root/file.md
```

**Solutions:**

1. Check file permissions:
```bash
ls -la file.md
chmod u+w file.md
```

2. Write to different location:
```python
output_file = Path.home() / "output.md"  # User's home directory
```

### Disk Full

**Problem:**
```python
FileWriteError: No space left on device
```

**Solutions:**

1. Check disk space:
```bash
df -h
```

2. Clean up:
```bash
# Remove large files
find . -name "*.md" -size +10M -delete

# Clean package cache
pip cache purge
```

## Debugging

### Check Session Logs

Every CLI session automatically creates a detailed log file:

```bash
# View the latest log
cat logs/preciz-latest.log

# Search for errors
grep "ERROR" logs/preciz-latest.log

# View LLM requests/responses
grep "LLM REQUEST" -A 20 logs/preciz-latest.log
```

See [Logging](logging.md) for complete documentation.

### Enable Verbose Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Now run your code
agent = PrecizAgent()
```

### Check LLM Responses

```python
from preciz.llm import LLMClient
from preciz.config import Config

config = Config.from_env()
llm = LLMClient(config)

# Test connection
response = llm.complete([
    Message(role="user", content="Hello")
])

print(f"Model: {response.model}")
print(f"Content: {response.content}")
print(f"Tokens: {response.input_tokens + response.output_tokens}")
```

### Inspect State File

```python
from preciz.orchestrator import OrchestrationState

state = OrchestrationState.load("state.json", llm)

print(f"Current task: {state.current_task_index}")
print(f"Total lines: {state.total_lines}")
print(f"Completed: {sum(1 for t in state.tasks if t.completed)}/{len(state.tasks)}")
```

## Getting Help

### Check Version

```bash
pip show preciz
```

### Run Tests

```bash
cd preciz
pytest tests/ -v
```

### Report Issues

When reporting issues, include:

1. Preciz version
2. Python version
3. Operating system
4. Error message
5. Steps to reproduce
6. `.env` configuration (remove API key!)

```bash
python --version
pip show preciz | grep Version
uname -a
```

### Community

- GitHub Issues: [preciz/issues](https://github.com/yourusername/preciz/issues)
- Discussions: [preciz/discussions](https://github.com/yourusername/preciz/discussions)

## See Also

- [Installation](installation.md)
- [Configuration](configuration.md)
- [API Reference](api.md)
