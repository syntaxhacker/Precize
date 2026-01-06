"""Prompts for fixing broken Mermaid diagrams."""


def build_fix_mermaid_prompt(original_code: str, error: str, context: str) -> str:
    """Build prompt to ask LLM to fix broken mermaid diagram.

    Args:
        original_code: The broken mermaid diagram code
        error: Error message from mermaid-cli
        context: Description of what the diagram should show

    Returns:
        Formatted prompt string
    """
    return f"""Fix this broken Mermaid diagram code.

**Parse Error from mermaid-cli:**
{error}

**Broken Mermaid Code:**
```mermaid
{original_code}
```

**Context:** This diagram should show: {context[:200]}

**Common Fixes Based on Error Messages:**
- If error mentions 'PS', 'SQS', or similar: Node labels with parentheses () or brackets [] MUST be quoted
  - WRONG: A[Calculate F(5)]
  - RIGHT: A["Calculate F(5)"]
- If error mentions 'got ... end': Reserved keyword used (end, start, class, style)
- If error mentions special chars: Remove {{}}, [], <br/> from labels

**Style Requirements (maintain these after fixing):**
- Use horizontal layout: flowchart LR or graph LR
- Include init directive with neutral theme
- Use emoji icons: 🚀, ✅, 🚨, 🔄, 📊, 🎯, 🧠
- Add classDef with proper colors
- Use descriptive labels

**Return ONLY the fixed mermaid code (no explanation, no markdown wrapping):"""
