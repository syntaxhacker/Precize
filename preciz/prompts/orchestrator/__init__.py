"""Prompts for the orchestrator-based document generator."""


def build_generate_section_prompt(
    topic: str,
    section_title: str,
    description: str,
    context: str,
    include_mermaid: bool = False,
    include_table: bool = False,
    include_examples: bool = True,
) -> str:
    """Build prompt for generating a content section."""
    requirements = []
    if include_mermaid:
        requirements.append("- Include at least one mermaid diagram")
    if include_table:
        requirements.append("- Include a comparison/summary table")
    if include_examples:
        requirements.append("- Include 2-3 concrete code examples")

    req_text = "\n".join(requirements) if requirements else "Standard educational content"

    return f"""Generate a section for a technical tutorial.

**Overall Topic**: {topic}

**This Section**: {section_title}

**Description**: {description}

**Previous Context** (what came before):
{context[-500:] if len(context) > 500 else context}

**Requirements**:
{req_text}

**Content Guidelines**:
- Aim for 100-200 lines
- Clear explanations
- Progressive complexity
- Real-world examples

Respond ONLY with the markdown content. Start with the section heading.
"""


def build_review_prompt(content: str, title: str) -> str:
    """Build prompt for reviewing a content section."""
    return f"""Review this tutorial section.

**Section**: {title}

**Content**:
```
{content[:2000]}
```

Check for:
1. Sufficient examples (at least 2)
2. Clear explanations
3. Missing diagrams/tables if needed
4. Adequate length (100+ lines)

Response JSON:
```json
{{
  "passed": true/false,
  "issues": ["issue1", "issue2"],
  "suggestions": ["suggestion1"]
}}
```
"""


def build_improve_prompt(content: str, issues: str, suggestions: str) -> str:
    """Build prompt for improving a content section."""
    return f"""Improve this tutorial section.

**Original**:
```
{content[:3000]}
```

**Issues to Fix**:
{issues}

**Suggestions**:
{suggestions}

Rewrite to address all issues. Respond ONLY with improved markdown.
"""


def build_create_outline_prompt(topic: str, target_lines: int = 10000) -> str:
    """Build prompt for creating a document outline."""
    return f"""Create a detailed outline for a {target_lines}-line tutorial on: {topic}

Return JSON with sections:
```json
{{
  "title": "{topic}",
  "sections": [
    {{
      "title": "Section Title",
      "level": 1,
      "description": "What this covers",
      "require_mermaid": false,
      "require_table": false,
      "require_examples": true
    }}
  ]
}}
```

Make 15-30 sections. Each section should be 100-200 lines when written.
"""
