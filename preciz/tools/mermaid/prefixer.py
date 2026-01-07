"""Pre-fix common Mermaid syntax errors before attempting mmdc conversion."""

import re


def pre_fix_mermaid(code: str) -> str:
    """Apply quick regex-based fixes to common Mermaid syntax errors.

    This catches ~80% of common issues before attempting expensive LLM fixes.

    Args:
        code: Raw mermaid diagram code

    Returns:
        Fixed mermaid code
    """
    lines = code.split('\n')
    fixed_lines = []

    for line in lines:
        original_line = line
        line = line.rstrip()

        # Skip empty lines and comments
        if not line or line.strip().startswith('%%'):
            fixed_lines.append(line)
            continue

        # Fix 1: Common typos in keywords (do this first)
        # Use word boundary to avoid replacing 'classD' inside 'classDef'
        line = re.sub(r'\bclassD\b', 'classDef', line)
        line = re.sub(r'\bclassd\b', 'classDef', line)

        # Fix 2: Incomplete classDef (missing style definition)
        # classDef name without styles -> add default style
        # Must check it's just "classDef name" with nothing after
        classdef_match = re.match(r'^(\s*)classDef\s+(\w+)\s*$', line)
        if classdef_match:
            indent = classdef_match.group(1)
            class_name = classdef_match.group(2)
            line = f'{indent}classDef {class_name} fill:#e2e3e5,stroke:#6c757d,stroke-width:2px,color:#383d41'

        # Fix 3: Quote node labels containing special characters
        # Matches: A[text with special chars] --> B
        # But NOT: A["already quoted"] --> B
        if '-->' in line and '[' in line:
            # Pattern: node identifier followed by [label with special chars]
            # Special chars: [], (), {}, <>, :
            pattern = r'(\w+)\[([^\]"\'\[]*[\[\]\(\)\{\}<>:][^\]"\'\]]*)\]'

            def quote_label(match):
                node_id = match.group(1)
                label = match.group(2)
                # If already contains quotes, don't double-quote
                if '"' not in label:
                    return f'{node_id}["{label}"]'
                return match.group(0)

            line = re.sub(pattern, quote_label, line)

        # Fix 4: Quote edge labels with special characters
        # A -->|label with []| B
        if '-->' in line and '|[' in line and '"]' not in line:
            # Pattern: -->|label[| or -->|label]| or -->|label[]|
            edge_pattern = r'(-->\|)([^\|"\[]*[\[\]]+)([^"]*\|)'
            # Find edge labels with brackets and quote them
            matches = list(re.finditer(edge_pattern, line))
            for match in reversed(matches):  # Reverse to maintain positions
                prefix = match.group(1)
                label = match.group(2)
                suffix = match.group(3)
                # Quote the label
                new_label = f'"{label}"'
                replacement = f'{prefix}{new_label}{suffix}'
                start, end = match.span()
                line = line[:start] + replacement + line[end:]

        # If line was modified, add a comment (for debugging)
        if line != original_line and not line.startswith('%%'):
            # Keep the fix silent for now
            pass

        fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def should_apply_prefix(code: str) -> bool:
    """Check if code has obvious syntax issues that pre-fix can handle.

    Args:
        code: Mermaid code to check

    Returns:
        True if pre-fix should be applied
    """
    # Check for unquoted special characters in node labels
    if re.search(r'\w\[.*[\[\]\(\)\{\}<>:].*\]', code):
        return True

    # Check for common typos
    if 'classD' in code or 'classd' in code:
        return True

    # Check for incomplete classDef
    if re.search(r'^classDef\s+\w+\s*$', code, re.MULTILINE):
        return True

    return False


# Test function
if __name__ == '__main__':
    # Test case 1: Unquoted brackets
    test1 = """flowchart LR
    A[dp[1]=1] --> B[dp[2]=2]
    B --> C"""

    print("Test 1: Unquoted brackets")
    print("Before:", repr(test1.split('\n')[1]))
    fixed1 = pre_fix_mermaid(test1)
    print("After:", repr(fixed1.split('\n')[1]))
    print()

    # Test case 2: Unquoted parentheses
    test2 = """flowchart LR
    A[Calculate F(5)] --> B[Calculate F(4)]"""

    print("Test 2: Unquoted parentheses")
    print("Before:", repr(test2.split('\n')[1]))
    fixed2 = pre_fix_mermaid(test2)
    print("After:", repr(fixed2.split('\n')[1]))
    print()

    # Test case 3: classD typo
    test3 = """flowchart LR
    A --> B
    classD start fill:red"""

    print("Test 3: classD typo")
    print("Before:", repr(test3.split('\n')[2]))
    fixed3 = pre_fix_mermaid(test3)
    print("After:", repr(fixed3.split('\n')[2]))
    print()

    # Test case 4: Incomplete classDef
    test4 = """flowchart LR
    A --> B
    classDef process"""

    print("Test 4: Incomplete classDef")
    print("Before:", repr(test4.split('\n')[2]))
    fixed4 = pre_fix_mermaid(test4)
    print("After:", repr(fixed4.split('\n')[2]))
