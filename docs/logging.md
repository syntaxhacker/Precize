# Logging

Session-based logging for debugging and auditing Preciz CLI operations.

## Overview

Every CLI session automatically generates a detailed log file that captures:
- All console output with timestamps
- LLM requests and responses (full content)
- Error messages and stack traces
- Session metadata and statistics

## Log Files

### Location

Logs are stored in the `logs/` directory:

```
logs/
├── preciz-20260105_143052_TCP_AND_UDP.log
├── preciz-20260105_144815_Differential_Calculus.log
└── preciz-latest.log -> preciz-20260105_144815_Differential_Calculus.log
```

### File Naming

Format: `preciz-YYYYMMDD_HHMMSS_<topic>.log`

- Timestamp: When the session started
- Topic: Sanitized document topic (max 50 chars, alphanumeric + underscore/hyphen)

### Latest Log

A symlink `preciz-latest.log` always points to the most recent session log.

## Log Content

### Session Information

```
======================================================================
SESSION SUMMARY
Topic: TCP AND UDP
Output: /tmp/tcp_udp.md
Target: 500 lines
Mode: llm
Max iterations: 2
Start time: 2026-01-05 11:38:24
End time: 2026-01-05 11:45:30
Duration: 426.06 seconds
Exit code: 0
LLM calls: 45
  Successful: 45/45
  Total tokens: 12543
  Total time: 187.23s
======================================================================
```

### LLM Request/Response

Every LLM call is logged with full details:

```
======================================================================
LLM REQUEST
  Model: xiaomi/mimo-v2-flash:free
  Temperature: 0.5, Max tokens: 2000
  Time: 12.50s
  Success: True
  --- PROMPT START ---
  Create a detailed outline for a 500-line tutorial on: TCP AND UDP
  ...
  --- PROMPT END ---
  --- RESPONSE START ---
  {
    "title": "TCP AND UDP",
    "sections": [...]
  }
  --- RESPONSE END ---
  --- PARSED JSON START ---
  {"title": "TCP AND UDP", "sections": [...]}
  --- PARSED JSON END ---
======================================================================
```

### Error Tracking

When errors occur, full details are captured:

```
======================================================================
EXCEPTION OCCURRED
  Type: ValueError
  Message: Failed to parse LLM outline as JSON
  Full Traceback:
    Traceback (most recent call last):
      File "preciz/generate_cli.py", line 188, in create_llm_todo_list
        raise ValueError("Failed to parse LLM outline as JSON")
    ...
======================================================================
```

## Using Logs for Debugging

### Check Latest Log

```bash
# View the most recent log
cat logs/preciz-latest.log

# Or use tail for live monitoring
tail -f logs/preciz-latest.log
```

### Find Specific Session

```bash
# List all logs
ls -la logs/

# Find logs by topic
ls logs/*TCP* logs/*tcp*

# Find logs from a specific date
ls logs/preciz-20260105_*
```

### Search Within Logs

```bash
# Search for errors
grep "ERROR" logs/preciz-latest.log

# Search for LLM failures
grep "Success: False" logs/preciz-latest.log

# Search for specific section
grep "TCP Handshake" logs/preciz-latest.log
```

## Log Rotation

Old logs are automatically cleaned up:

- **Max files kept**: 50
- **Cleanup happens**: At the end of each session
- **Removal order**: Oldest files first

To change the limit, modify `MAX_LOG_FILES` in `preciz/logger.py`:

```python
class SessionLogger:
    MAX_LOG_FILES = 100  # Keep 100 logs instead of 50
```

## Viewing Logs in Code

```python
from preciz.logger import get_latest_log

# Get contents of the latest log
log_content = get_latest_log()
if log_content:
    print(log_content)
```

## Troubleshooting

### No Logs Created

**Check:** Is the `logs/` directory writable?

```bash
ls -la logs/
# Should be drwxr-xr-x
```

**Fix:** Change permissions or parent directory

### Symlink Errors

**Issue:** `preciz-latest.log` symlink doesn't work on Windows

**Result:** The symlink is simply skipped - logs still work normally

### Large Log Files

**Issue:** Logs for long documents can be several MB

**Solution:** Use `grep` or `tail` to find what you need:

```bash
# View just the summary
tail -20 logs/preciz-latest.log

# View just errors
grep "ERROR\|WARNING" logs/preciz-latest.log

# View just LLM calls
grep "LLM REQUEST" -A 20 logs/preciz-latest.log
```

## See Also

- [CLI Commands](cli.md)
- [Troubleshooting](troubleshooting.md)
