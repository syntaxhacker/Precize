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
1. **CRITICAL: Reserved keywords** - NEVER use these as classDef names or node IDs
   - FORBIDDEN: end, start, subgraph, end, style, link, classDef, class
   - Use alternatives: final, begin, group, finish, styling, connector, styleDef, category
2. **CRITICAL: Special characters in edge labels** - These cause parse errors:
   - NO curly braces: {{}} - Use quotes or remove
   - NO square brackets: [] - Use words like "empty array" instead
   - NO HTML tags: <br/> <strong> etc - Use plain text
   - WRONG: A -->|Props: {{name}}| B or B -->|Array: []| C
   - RIGHT: A -->|"Props name"| B or B -->|Empty array| C
3. **CRITICAL: Incomplete classDef** - Every classDef must have style definitions
   - WRONG: classDef child
   - RIGHT: classDef child fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#155724
4. **CRITICAL: Wrong layout** - Always use horizontal LR, never TD
   - WRONG: flowchart TD
   - RIGHT: flowchart LR
5. Missing semicolons after statements (in sequenceDiagram)
6. Incorrect syntax (flowchart vs graph vs sequenceDiagram)
7. Invalid node IDs (use alphanumeric and underscores only, no spaces)
8. Missing quotes around labels with special characters
9. Unclosed brackets or parentheses
10. Double curly braces in init (use {{{{ and }}}} for escaping)

**Mermaid Style Requirements:**
- Use horizontal layout: flowchart LR or graph LR
- Include %%{{{{init: {{'theme':'neutral'}}}}}}%%
- Use emoji icons in labels: 🚀, ✅, 🚨, 🔄, 📊, 🎯, 🧠
- Add classDef with proper colors (fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#155724)
- Use descriptive labels (not A, B, C)
- Make diagrams wide (3.5:1 to 4:1 aspect ratio)

**Return ONLY the fixed mermaid code (no markdown wrapping, no explanation):"""
