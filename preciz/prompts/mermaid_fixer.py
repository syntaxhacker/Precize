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

**Error from mermaid-cli:**
{error}

**Original Mermaid Code:**
```mermaid
{original_code}
```

**Context (what this diagram should show):**
{context[:300]}

**Common Mermaid Issues to Fix:**
1. **CRITICAL: Curly braces {{}} in edge labels** - Edge labels containing curly braces MUST be quoted
   - WRONG: A -->|Props: {{name}}| B
   - RIGHT: A -->|"Props: name"| B or A -->|Props name| B
2. **CRITICAL: Incomplete classDef** - Every classDef must have style definitions
   - WRONG: classDef child
   - RIGHT: classDef child fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#155724
3. Missing semicolons after statements (in sequenceDiagram)
4. Incorrect syntax (flowchart vs graph vs sequenceDiagram)
5. Invalid node IDs (use alphanumeric and underscores only, no spaces)
6. Missing quotes around labels with special characters
7. Unclosed brackets or parentheses
8. Double curly braces in init (use {{{{ and }}}} for escaping)

**Mermaid Style Requirements:**
- Use horizontal layout: flowchart LR or graph LR
- Include %%{{{{init: {{'theme':'neutral'}}}}}}%%
- Use emoji icons in labels: 🚀, ✅, 🚨, 🔄, 📊, 🎯, 🧠
- Add classDef with proper colors (fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#155724)
- Use descriptive labels (not A, B, C)
- Make diagrams wide (3.5:1 to 4:1 aspect ratio)

**Return ONLY the fixed mermaid code (no markdown wrapping, no explanation):"""
