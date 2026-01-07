"""Utility to detect incomplete sections in generated markdown."""

import re
from pathlib import Path


def detect_incomplete_sections(content: str) -> list[dict]:
    """Detect incomplete sections in markdown content.

    Args:
        content: Markdown content to check

    Returns:
        List of dicts with incomplete section info:
        [{'type': 'mermaid', 'line': 123, 'context': '...'}, ...]
    """
    issues = []
    lines = content.split('\n')

    # Check for incomplete mermaid code blocks
    in_mermaid = False
    mermaid_start = 0
    mermaid_lines = []

    for i, line in enumerate(lines, 1):
        # Check for mermaid block start
        if line.strip() == '```mermaid':
            in_mermaid = True
            mermaid_start = i
            mermaid_lines = [line]
            continue

        # Inside mermaid block
        if in_mermaid:
            mermaid_lines.append(line)
            if line.strip() == '```' and line.strip() != '```mermaid':
                # Block closed - validate it
                mermaid_content = '\n'.join(mermaid_lines)

                # Check for common incomplete patterns
                if _is_incomplete_mermaid(mermaid_content):
                    issues.append({
                        'type': 'incomplete_mermaid',
                        'line': mermaid_start,
                        'end_line': i,
                        'context': _get_context(lines, mermaid_start, i),
                        'content': mermaid_content
                    })

                in_mermaid = False
                mermaid_lines = []
            elif i - mermaid_start > 50:  # Suspiciously long mermaid
                issues.append({
                    'type': 'suspiciously_long_mermaid',
                    'line': mermaid_start,
                    'end_line': i,
                    'context': _get_context(lines, mermaid_start, i),
                    'content': '\n'.join(mermaid_lines[-10:])
                })
                in_mermaid = False

    # Check for incomplete code blocks
    in_code = False
    code_start = 0
    code_lang = ''

    for i, line in enumerate(lines, 1):
        if line.startswith('```'):
            if not in_code:
                in_code = True
                code_start = i
                code_lang = line[3:].strip()
            elif line.strip() != '```' + code_lang:
                # Code block closed
                in_code = False

    # Check if file ends with open code block
    if in_code:
        issues.append({
            'type': 'unclosed_code_block',
            'line': code_start,
            'lang': code_lang,
            'context': _get_context(lines, code_start, len(lines))
        })

    # Check for sections ending mid-sentence
    for i in range(len(lines) - 1):
        # If a section header is followed by incomplete content
        if lines[i].startswith('##') and i + 1 < len(lines):
            # Check if next 20 lines look incomplete
            next_section = i + 1
            for j in range(i + 1, min(i + 20, len(lines))):
                if lines[j].startswith('##'):
                    next_section = j
                    break

            section_content = '\n'.join(lines[i+1:next_section])
            if _is_incomplete_section(section_content):
                issues.append({
                    'type': 'incomplete_section',
                    'line': i,
                    'section_title': lines[i].strip(),
                    'context': _get_context(lines, i, next_section)
                })

    return issues


def _is_incomplete_mermaid(content: str) -> bool:
    """Check if mermaid block is incomplete."""
    # Check for unclosed branches
    if '-->' in content and not any(br in content for br in ['-->|', '--->']):
        # Has edges but may be incomplete
        lines = content.split('\n')

        # Check if ends abruptly
        for line in lines[-5:]:
            if line.strip() and not line.strip().startswith('```'):
                # Last non-empty line before closing
                if any(char in line for char in ['-->|', '-->', '[(', '])']):
                    # Ends with an edge or node definition
                    if '```' not in line:
                        return True

    return False


def _is_incomplete_section(content: str) -> bool:
    """Check if section content looks incomplete."""
    if not content or len(content.strip()) < 100:
        return True

    # Ends with incomplete list/item
    lines = content.strip().split('\n')
    if lines and lines[-1].strip().startswith('-') and len(lines[-1]) < 20:
        return True

    return False


def _get_context(lines: list[str], start: int, end: int) -> str:
    """Get context around an issue."""
    context_start = max(0, start - 2)
    context_end = min(len(lines), end + 3)
    return '\n'.join(lines[context_start:context_end])


def print_incomplete_report(issues: list[dict]):
    """Print a readable report of incomplete sections."""
    if not issues:
        print("✅ No incomplete sections detected!")
        return

    print(f"\n⚠️  Found {len(issues)} incomplete section(s):\n")

    for i, issue in enumerate(issues, 1):
        print(f"[{i}] {issue['type'].replace('_', ' ').title()}")
        print(f"    Line: {issue['line']}" + (f"-{issue.get('end_line', '')}" if 'end_line' in issue else ""))
        if 'section_title' in issue:
            print(f"    Section: {issue['section_title']}")
        if 'lang' in issue:
            print(f"    Language: {issue['lang']}")
        print(f"    Context:\n{'─' * 60}")
        print(issue['context'][:500])
        if len(issue['context']) > 500:
            print("...")
        print('─' * 60 + '\n')


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python completion_checker.py <file.md>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    content = file_path.read_text()

    issues = detect_incomplete_sections(content)
    print_incomplete_report(issues)

    sys.exit(1 if issues else 0)
