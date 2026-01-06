"""Mermaid diagram verification and conversion utilities."""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .llm import LLMClient, Message


@dataclass
class MermaidBlock:
    """A mermaid code block found in content."""
    index: int
    full_match: str      # The entire ```mermaid...``` block
    code: str            # Just the mermaid code inside


def extract_mermaid_blocks(content: str) -> list[MermaidBlock]:
    """Extract all mermaid code blocks from markdown content.

    Args:
        content: Markdown content to search

    Returns:
        List of MermaidBlock objects
    """
    # Pattern to match mermaid code blocks including delimiters
    pattern = r'```mermaid\n(.*?)\n```'

    blocks = []
    for i, match in enumerate(re.finditer(pattern, content, re.DOTALL), 1):
        full_match = match.group(0)  # The entire ```mermaid...``` block
        code = match.group(1).strip()  # Just the mermaid code inside

        blocks.append(MermaidBlock(
            index=i,
            full_match=full_match,
            code=code
        ))

    return blocks


def try_convert_mermaid(code: str, output_path: Path):
    """Convert mermaid code to PNG using mmdc CLI.

    Args:
        code: Mermaid diagram code
        output_path: Where to save the PNG file

    Returns:
        (success: bool, error_message: str)
    """
    # Write temporary .mmd file
    temp_mmd = output_path.with_suffix('.mmd')
    temp_mmd.write_text(code)

    try:
        # Run mmdc command
        result = subprocess.run(
            ['mmdc', '-i', str(temp_mmd), '-o', str(output_path), '-b', 'transparent'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return True, ""
        else:
            error_output = result.stderr or result.stdout or "Unknown error"
            return False, error_output

    except subprocess.TimeoutExpired:
        return False, "Conversion timed out after 30 seconds"
    except FileNotFoundError:
        return False, (
            "mmdc command not found. Install with: npm install -g @mermaid-js/mermaid-cli"
        )
    finally:
        # Clean up temp file
        if temp_mmd.exists():
            try:
                temp_mmd.unlink()
            except:
                pass


def fix_mermaid_with_llm(
    broken_code: str,
    error: str,
    context: str,
    llm: LLMClient
) -> str:
    """Ask LLM to fix broken mermaid code.

    Args:
        broken_code: The broken mermaid diagram code
        error: Error message from mermaid-cli
        context: Description of what the diagram should show
        llm: LLM client

    Returns:
        Fixed mermaid code
    """
    from .prompts.mermaid_fixer import build_fix_mermaid_prompt

    prompt = build_fix_mermaid_prompt(broken_code, error, context)

    response = llm.complete([
        Message(role="system", content="You are a Mermaid diagram syntax expert. Fix broken diagrams and return only the corrected code."),
        Message(role="user", content=prompt)
    ], temperature=0.3, max_tokens=1000)

    # Extract fixed code from response
    fixed = response.content.strip()

    # Remove markdown code blocks if present
    if "```mermaid" in fixed:
        match = re.search(r'```mermaid\n(.*?)```', fixed, re.DOTALL)
        if match:
            return match.group(1).strip()

    # If no code block found, return as-is
    return fixed


def convert_mermaid_with_retry(
    mermaid_code: str,
    output_path: Path,
    context: str,
    llm: LLMClient,
    max_retries: int = 3
):
    """Convert mermaid to PNG with LLM-based fix retries.

    Args:
        mermaid_code: Original mermaid code
        output_path: Where to save PNG
        context: Description for LLM fixing
        llm: LLM client for fixing
        max_retries: Maximum number of fix attempts

    Returns:
        (success: bool, final_code_used: str, last_error: str)
    """
    current_code = mermaid_code
    last_error = ""

    for attempt in range(max_retries + 1):
        # Try conversion
        success, error = try_convert_mermaid(current_code, output_path)
        last_error = error

        if success:
            return True, current_code, ""

        if attempt < max_retries:
            # Ask LLM to fix it
            current_code = fix_mermaid_with_llm(current_code, error, context, llm)

    return False, current_code, last_error


def verify_and_convert_mermaid(
    content: str,
    section_index: int,
    section_title: str,
    llm: LLMClient,
    images_dir: str = "images",
    logger = None
) -> str:
    """Extract mermaid blocks, convert to PNG, replace with image references.

    Args:
        content: Generated section content
        section_index: Section number (0-based)
        section_title: Title for naming images
        llm: LLM client for fixing broken mermaid
        images_dir: Directory to save PNGs
        logger: Optional logger for output

    Returns:
        Content with mermaid blocks replaced by image references
    """
    # 1. Extract all mermaid blocks
    blocks = extract_mermaid_blocks(content)

    if not blocks:
        if logger:
            logger.info("  → No Mermaid diagrams found")
        return content

    if logger:
        logger.info(f"  → Found {len(blocks)} Mermaid diagram(s)")

    # 2. Convert each block
    updated_content = content
    images_dir_path = Path(images_dir)
    images_dir_path.mkdir(parents=True, exist_ok=True)

    for block in blocks:
        if logger:
            logger.info(f"     Converting diagram {block.index}...")

        # Generate filename
        safe_title = "".join(c if c.isalnum() else "_" for c in section_title)[:30]
        filename = f"mermaid-{section_index+1}-{block.index}-{safe_title}.png"
        output_path = images_dir_path / filename

        # Pre-fix common syntax errors before attempting conversion
        from .mermaid_prefixer import pre_fix_mermaid
        code_to_convert = pre_fix_mermaid(block.code)

        # Check if pre-fix made changes
        if code_to_convert != block.code and logger:
            logger.info(f"     → Applied pre-fix to common syntax errors")

        # Try to convert (with LLM fix retries)
        success, fixed_code, error = convert_mermaid_with_retry(
            mermaid_code=code_to_convert,
            output_path=output_path,
            context=section_title,
            llm=llm,
            max_retries=3
        )

        if success:
            # Replace mermaid block with image reference
            image_ref = f"![{section_title} Diagram {block.index}]({images_dir}/{filename})"
            updated_content = updated_content.replace(
                block.full_match,
                image_ref
            )
            if logger:
                logger.success(f"     ✓ Converted: {filename}")
        else:
            # Keep original mermaid code if conversion fails
            if logger:
                logger.warning(f"     ✗ Failed to convert diagram {block.index} after retries")
                if error:
                    logger.warning(f"     → Error: {error[:200]}")  # First 200 chars of error
                logger.warning(f"     → Keeping original mermaid code")

    return updated_content
