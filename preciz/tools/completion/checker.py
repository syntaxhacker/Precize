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

    # Check for unclosed code blocks (any language)
    in_code = False
    code_start = 0
    code_lang = ''

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Check for code fence
        if stripped.startswith('```'):
            if not in_code:
                # Opening code fence
                in_code = True
                code_start = i
                code_lang = stripped[3:].strip()
            elif stripped == '```':
                # Closing code fence (just ```, not ```language)
                in_code = False
                code_lang = ''

    # Check if file ends with open code block
    if in_code:
        issues.append({
            'type': 'unclosed_code_block',
            'line': code_start,
            'lang': code_lang,
            'context': _get_context(lines, code_start, len(lines))
        })

    # Check for incomplete mermaid blocks (these get converted to images)
    # But if any remain, they're problematic
    in_mermaid = False
    mermaid_start = 0

    for i, line in enumerate(lines, 1):
        if line.strip() == '```mermaid':
            in_mermaid = True
            mermaid_start = i
        elif line.strip() == '```' and in_mermaid:
            in_mermaid = False

    if in_mermaid:
        issues.append({
            'type': 'unclosed_mermaid_block',
            'line': mermaid_start,
            'context': _get_context(lines, mermaid_start, len(lines))
        })

    # Check for obvious truncation at end of file
    # If the document ends mid-sentence or mid-word
    if len(lines) > 10:
        last_10 = [l for l in lines[-10:] if l.strip() and not l.strip().startswith('#')]
        if last_10:
            last_content_line = last_10[-1].strip()
            # If last line ends without punctuation and is substantial
            if (len(last_content_line) > 30 and
                not last_content_line.endswith(('.', '!', '?', '}', ')', ']', ':', '"', "'", '])', '*)')) and
                not last_content_line.startswith('|') and
                not last_content_line.startswith('!') and
                '```' not in last_content_line):
                issues.append({
                    'type': 'possible_truncation',
                    'line': len(lines),
                    'context': _get_context(lines, len(lines) - 5, len(lines))
                })

    return issues


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

    print(f"\n⚠️  Found {len(issues)} issue(s):\n")

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
