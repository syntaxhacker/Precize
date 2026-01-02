"""Prompts for the block-based content generator (v2)."""


def build_outline_prompt(topic: str, target_lines: int = 10000) -> str:
    """Build prompt for creating a detailed outline."""
    return f"""You are creating a comprehensive technical tutorial on: {topic}

Target length: ~{target_lines} lines of markdown

Your task: Create a detailed hierarchical outline.

## Requirements

1. **Hierarchical Structure**: Use 3-4 levels of headings
   - Level 1: Main parts (Introduction, Core Concepts, Advanced Topics, etc.)
   - Level 2: Major sections
   - Level 3: Subsections with specific topics
   - Level 4: Detailed sub-points (if needed)

2. **Block Size**: Each leaf node should cover ~100-200 lines of content
   - Break large topics into multiple subsections
   - Keep topics focused and specific

3. **Comprehensive Coverage**: Include:
   - Introduction and prerequisites
   - Core concepts (detailed)
   - Practical examples throughout
   - Advanced topics
   - Summary/exercises

4. **Visual Elements**: Mark which sections need:
   - mermaid diagrams (flows, sequences, architectures)
   - comparison tables
   - ASCII art diagrams
   - code examples
   - exercises/problems

## Output Format

Respond ONLY with valid JSON:

```json
{{
  "title": "{topic}",
  "estimated_total_lines": {target_lines},
  "sections": [
    {{
      "title": "Section Title",
      "level": 1,
      "description": "Brief description of what this covers",
      "need_mermaid": false,
      "need_table": false,
      "need_examples": true,
      "need_exercises": false,
      "estimated_lines": 200,
      "subsections": [
        {{
          "title": "Subsection Title",
          "level": 2,
          "description": "...",
          "need_mermaid": true,
          "need_table": false,
          "need_examples": true,
          "estimated_lines": 150,
          "subsections": []
        }}
      ]
    }}
  ]
}}
```

Make the outline detailed enough to generate {target_lines}+ lines.
Break topics into small, manageable chunks."""


def build_block_generation_prompt(
    title: str,
    description: str,
    context: str,
    require_mermaid: bool = False,
    require_table: bool = False,
    require_examples: bool = True,
    require_exercises: bool = False,
) -> str:
    """Build prompt for generating a single content block."""
    requirements = []
    if require_mermaid:
        requirements.append("- Include at least one mermaid diagram (flowchart, sequence, etc.)")
    if require_table:
        requirements.append("- Include a comparison/summary table")
    if require_examples:
        requirements.append("- Include 2-3 concrete examples with code")
    if require_exercises:
        requirements.append("- Include practice exercises or problems")

    req_text = "\n".join(requirements) if requirements else "- Standard content"

    return f"""You are writing a section of a technical tutorial.

## Section to Write

**Title**: {title}

**Description**: {description}

**Context** (what comes before this):
{context[:1000] if len(context) > 1000 else context}

## Requirements for This Section

{req_text}

## Content Guidelines

1. **Length**: Aim for 100-200 lines of markdown
2. **Tone**: Educational, clear, progressively detailed
3. **Format**: Proper markdown with:
   - Clear headings (use ### for subsections within this block)
   - Code blocks with syntax highlighting
   - Bulleted/numbered lists where appropriate
   - Inline code for technical terms

4. **Quality**:
   - Start simple, add complexity gradually
   - Use analogies and real-world examples
   - Explain WHY, not just HOW
   - Include common pitfalls

## Output

Respond ONLY with the markdown content for this section.
Start directly with the heading (### if this is a subsection, ## if main section).
Do not include any intro/outro text - just the content."""


def build_review_prompt(content: str, title: str) -> str:
    """Build prompt for reviewing a block."""
    return f"""Review this section of a technical tutorial.

**Section**: {title}

**Content**:
```
{content[:3000] if len(content) > 3000 else content}
```

## Review Checklist

1. **Completeness**: Does it fully cover the topic?
2. **Clarity**: Is it easy to understand?
3. **Examples**: Are there 2-3 concrete examples?
4. **Visuals**: Does it need diagrams/tables that are missing?
5. **Length**: Is it substantial enough (100+ lines)?

## Response Format

```json
{{
  "passed": true/false,
  "issues": ["specific issue 1", "specific issue 2"],
  "suggestions": ["specific suggestion 1"],
  "missing_elements": ["mermaid diagram", "table", "examples", "exercises"]
}}
```

Be thorough - if content could be better, say so."""


def build_improve_prompt(content: str, title: str, feedback: dict) -> str:
    """Build prompt for improving a block."""
    issues = "\n".join(f"- {i}" for i in feedback.get("issues", []))
    suggestions = "\n".join(f"- {s}" for s in feedback.get("suggestions", []))

    return f"""Improve this tutorial section.

**Current Content**:
```
{content[:4000] if len(content) > 4000 else content}
```

**Issues to Fix**:
{issues}

**Suggestions**:
{suggestions}

**Missing Elements**: {', '.join(feedback.get('missing_elements', []))}

## Task

Rewrite the section to address all issues. Add missing elements.
Maintain the same structure but improve quality and completeness.

Respond ONLY with the improved markdown content."""
