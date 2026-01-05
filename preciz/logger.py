"""
Session-based logging system for Preciz CLI.

Captures all output to both console and log files with detailed error tracking,
LLM response logging, and session metadata.
"""

import json
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class LogLevel(Enum):
    """Log levels for different message types."""
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"


@dataclass
class LLMMetadata:
    """Metadata for LLM requests/responses."""
    request_prompt: str
    response_preview: str
    response_tokens: int
    response_time_seconds: float
    model: str
    temperature: float
    max_tokens: int
    success: bool
    error_message: str = ""
    parsed_json: str = ""


@dataclass
class SessionMetadata:
    """Metadata about the generation session."""
    topic: str
    output_file: str
    target_lines: int
    mode: str
    max_iterations: int
    num_parts: int | None = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    exit_code: int = 0
    llm_calls: list[LLMMetadata] = field(default_factory=list)


class SessionLogger:
    """
    Context manager for logging CLI sessions.

    Logs to both console and file, capturing all output with timestamps.
    Automatically captures LLM requests/responses and errors.
    """

    # Max log files to keep
    MAX_LOG_FILES = 50

    def __init__(
        self,
        topic: str,
        output_file: str,
        target_lines: int,
        mode: str,
        max_iterations: int = 2,
        num_parts: int | None = None,
        log_dir: str | Path = "logs",
    ):
        """Initialize the session logger.

        Args:
            topic: Document topic
            output_file: Output file path
            target_lines: Target line count
            mode: Generation mode (auto, llm, parts, custom)
            max_iterations: Max review iterations
            num_parts: Number of parts (for parts mode)
            log_dir: Directory to store log files
        """
        self.topic = topic
        self.output_file = output_file
        self.target_lines = target_lines
        self.mode = mode
        self.max_iterations = max_iterations
        self.num_parts = num_parts

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Sanitize topic for filename
        safe_topic = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in topic)[:50]
        self.log_file = self.log_dir / f"preciz-{timestamp}_{safe_topic}.log"

        # Session metadata
        self.metadata = SessionMetadata(
            topic=topic,
            output_file=output_file,
            target_lines=target_lines,
            mode=mode,
            max_iterations=max_iterations,
            num_parts=num_parts,
        )

        # Open log file
        self.file_handle = open(self.log_file, "w", encoding="utf-8")

        # Track if this is the first write (for header)
        self._first_write = True

        # Output capture
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

    def __enter__(self):
        """Enter context manager."""
        # Redirect stdout/stderr to our logger
        sys.stdout = self
        sys.stderr = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and write summary."""
        # Restore original stdout/stderr
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr

        # Set end time and exit code
        self.metadata.end_time = datetime.now()
        if exc_type is not None:
            self.metadata.exit_code = 1
            self._log_exception(exc_type, exc_val, exc_tb)

        # Write session summary
        self._write_summary()

        # Close file
        self.file_handle.close()

        # Create symlink to latest log
        self._create_latest_symlink()

        # Rotate old logs
        self._rotate_logs()

        return False  # Don't suppress exceptions

    def write(self, text: str):
        """Write text to both console and file (for print() redirection)."""
        if text:
            self._write_to_file(text.rstrip("\n"))
            self._original_stdout.write(text)

    def flush(self):
        """Flush both streams."""
        self.file_handle.flush()
        self._original_stdout.flush()

    def info(self, message: str):
        """Log an info message."""
        self._log_with_level(LogLevel.INFO, message)

    def success(self, message: str):
        """Log a success message."""
        self._log_with_level(LogLevel.SUCCESS, message)

    def warning(self, message: str):
        """Log a warning message."""
        self._log_with_level(LogLevel.WARNING, message)

    def error(self, message: str):
        """Log an error message."""
        self._log_with_level(LogLevel.ERROR, message)

    def debug(self, message: str):
        """Log a debug message (only to file, not console)."""
        self._log_with_level(LogLevel.DEBUG, message, console=False)

    def log_llm_request(
        self,
        prompt: str,
        response: str,
        model: str,
        temperature: float,
        max_tokens: int,
        response_time_seconds: float,
        success: bool = True,
        error_message: str = "",
        parsed_json: str = "",
    ):
        """Log an LLM request/response pair with full details.

        Args:
            prompt: The prompt sent to LLM
            response: The raw response from LLM
            model: Model name used
            temperature: Temperature setting
            max_tokens: Max tokens setting
            response_time_seconds: Time taken for response
            success: Whether the request was successful
            error_message: Error message if failed
            parsed_json: Parsed JSON if applicable
        """
        # Count approximate tokens (rough estimate: 1 token ≈ 4 chars)
        response_tokens = len(response) // 4

        metadata = LLMMetadata(
            request_prompt=prompt,
            response_preview=response[:500] if len(response) > 500 else response,
            response_tokens=response_tokens,
            response_time_seconds=response_time_seconds,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            success=success,
            error_message=error_message,
            parsed_json=parsed_json[:1000] if len(parsed_json) > 1000 else parsed_json,
        )

        self.metadata.llm_calls.append(metadata)

        # Log to file (not console to avoid spam)
        self._write_separator()
        self._write_to_file("LLM REQUEST", console=False)
        self._write_to_file(f"  Model: {model}", console=False)
        self._write_to_file(f"  Temperature: {temperature}, Max tokens: {max_tokens}", console=False)
        self._write_to_file(f"  Time: {response_time_seconds:.2f}s", console=False)
        self._write_to_file(f"  Success: {success}", console=False)
        if error_message:
            self._write_to_file(f"  Error: {error_message}", console=False)
        self._write_to_file("", console=False)
        self._write_to_file("  --- PROMPT START ---", console=False)
        self._write_to_file(f"  {prompt}", console=False)
        self._write_to_file("  --- PROMPT END ---", console=False)
        self._write_to_file("", console=False)
        self._write_to_file("  --- RESPONSE START ---", console=False)
        self._write_to_file(f"  {response}", console=False)
        self._write_to_file("  --- RESPONSE END ---", console=False)
        if parsed_json:
            self._write_to_file("", console=False)
            self._write_to_file("  --- PARSED JSON START ---", console=False)
            self._write_to_file(f"  {parsed_json}", console=False)
            self._write_to_file("  --- PARSED JSON END ---", console=False)
        self._write_separator(console=False)

    def _log_with_level(self, level: LogLevel, message: str, console: bool = True):
        """Log a message with level and timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level_str = f"[{level.value}]"

        # Format: [timestamp] [LEVEL] message
        log_line = f"{timestamp} {level_str} {message}"

        # Always write to file
        self._write_to_file(log_line, console=False)

        # Write to console for INFO/SUCCESS/WARNING/ERROR
        if console and level != LogLevel.DEBUG:
            # For console, strip the level prefix for cleaner output
            # Keep timestamps for errors/warnings only
            if level == LogLevel.ERROR:
                print(f"{timestamp} {message}", file=self._original_stdout)
            else:
                print(message, file=self._original_stdout)

    def _write_to_file(self, message: str, console: bool = True):
        """Write a message to the log file."""
        if message:
            self.file_handle.write(message + "\n")
            self.file_handle.flush()

    def _write_separator(self, console: bool = True):
        """Write a separator line."""
        sep = "=" * 70
        self._write_to_file(sep, console=False)
        if console:
            print(sep, file=self._original_stdout)

    def _log_exception(self, exc_type, exc_val, exc_tb):
        """Log an exception with full traceback."""
        self._write_separator()
        self.error("EXCEPTION OCCURRED")
        self.error(f"  Type: {exc_type.__name__}")
        self.error(f"  Message: {exc_val}")

        # Write full traceback to file
        tb_lines = traceback.format_exception(exc_type, exc_val, exc_tb)
        self._write_to_file("  Full Traceback:")
        for line in tb_lines:
            self._write_to_file(f"    {line.rstrip()}", console=False)
        self._write_separator()

    def _write_summary(self):
        """Write session summary to the end of the log file."""
        duration = (self.metadata.end_time - self.metadata.start_time).total_seconds()

        self._write_separator()
        self._write_to_file("SESSION SUMMARY")
        self._write_to_file("")
        self._write_to_file(f"Topic: {self.metadata.topic}")
        self._write_to_file(f"Output: {self.metadata.output_file}")
        self._write_to_file(f"Target: {self.metadata.target_lines} lines")
        self._write_to_file(f"Mode: {self.metadata.mode}")
        self._write_to_file(f"Max iterations: {self.metadata.max_iterations}")
        if self.metadata.num_parts:
            self._write_to_file(f"Num parts: {self.metadata.num_parts}")
        self._write_to_file("")
        self._write_to_file(f"Start time: {self.metadata.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self._write_to_file(f"End time: {self.metadata.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self._write_to_file(f"Duration: {duration:.2f} seconds")
        self._write_to_file(f"Exit code: {self.metadata.exit_code}")
        self._write_to_file("")
        self._write_to_file(f"LLM calls: {len(self.metadata.llm_calls)}")

        if self.metadata.llm_calls:
            total_tokens = sum(call.response_tokens for call in self.metadata.llm_calls)
            total_time = sum(call.response_time_seconds for call in self.metadata.llm_calls)
            successful = sum(1 for call in self.metadata.llm_calls if call.success)
            self._write_to_file(f"  Successful: {successful}/{len(self.metadata.llm_calls)}")
            self._write_to_file(f"  Total tokens: {total_tokens}")
            self._write_to_file(f"  Total time: {total_time:.2f}s")

        self._write_separator()

    def _create_latest_symlink(self):
        """Create a symlink pointing to the latest log file."""
        symlink_path = self.log_dir / "preciz-latest.log"

        # Remove existing symlink
        if symlink_path.exists() or symlink_path.is_symlink():
            symlink_path.unlink()

        # Create new symlink (relative path)
        try:
            symlink_path.symlink_to(self.log_file.name)
        except OSError:
            # Symlinks might not work on all systems, silently ignore
            pass

    def _rotate_logs(self):
        """Remove old log files, keeping only the most recent MAX_LOG_FILES."""
        # Get all log files, filtering out broken symlinks
        log_files = []
        for p in self.log_dir.glob("preciz-*.log"):
            # Skip the symlink itself
            if p.name == "preciz-latest.log":
                continue
            # Skip broken symlinks
            if p.is_symlink() and not p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass
                continue
            # Only include actual files that exist
            try:
                if p.is_file():
                    log_files.append(p)
            except OSError:
                pass

        # Sort by modification time
        log_files = sorted(log_files, key=lambda p: p.stat().st_mtime, reverse=True)

        # Remove old files beyond MAX_LOG_FILES
        for old_log in log_files[self.MAX_LOG_FILES:]:
            try:
                old_log.unlink()
            except OSError:
                pass


def get_latest_log() -> str | None:
    """Get the contents of the latest log file.

    Returns:
        Log file contents or None if no logs exist
    """
    log_dir = Path("logs")
    latest_symlink = log_dir / "preciz-latest.log"

    if latest_symlink.is_symlink() or latest_symlink.exists():
        try:
            return latest_symlink.read_text(encoding="utf-8")
        except OSError:
            return None

    return None
