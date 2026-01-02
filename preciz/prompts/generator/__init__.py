"""Prompts for the content generator module."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ContentSpec:
    """Specification for content generation."""

    topic: str
    target_length: str = "comprehensive"  # brief, standard, comprehensive
    target_audience: str = "intermediate"  # beginner, intermediate, advanced
    include_practical: bool = True
    include_theory: bool = True


@dataclass(frozen=True)
class SectionBlock:
    """A section block within a document."""

    content: str
    line_start: int
    line_end: int
    heading: str = ""
    level: int = 1


@dataclass
class ReviewFeedback:
    """Feedback from the review agent."""

    passed: bool
    issues: list[str]
    suggestions: list[str]
    block_index: int = -1


def build_generation_prompt(spec: ContentSpec) -> str:
    """Build prompt for content generation."""
    return f"""You are an expert educational content creator. Generate a comprehensive tutorial on: {spec.topic}

## Requirements

Target Audience: {spec.target_audience}
Length: {spec.target_length}
Include Theory: {spec.include_theory}
Include Practical: {spec.include_practical}

## Content Structure

Your response must be a well-structured markdown document with:

1. **Clear Hierarchy**: Use #, ##, ### headings appropriately
2. **Visual Aids**: Include Mermaid diagrams where concepts can be visualized
3. **Examples**: Provide ASCII art examples and code samples
4. **Tables**: Use tables for comparisons and summaries
5. **Progressive Flow**: Start simple, build complexity gradually

## Output Format

Return ONLY the markdown content, nothing else. Start directly with the title heading.

## Quality Standards

- Each major section should have at least 2 concrete examples
- Use code blocks with syntax highlighting
- Include mermaid diagrams for flows, processes, or relationships
- Use tables for comparing concepts or summarizing key points
- Add practical exercises or problems to solve
- Include ASCII art diagrams where helpful for visualization

Generate the complete tutorial now."""


def build_review_prompt(block: SectionBlock, min_examples_per_section: int = 2) -> str:
    """Build prompt for reviewing a content block."""
    return f"""You are a strict content quality reviewer. Review this section of an educational tutorial.

## Section Being Reviewed
Heading: {block.heading}
Level: {block.level}

Content:
```
{block.content}
```

## Quality Checklist

Review this section against these requirements:

1. **Mermaid Diagrams**: Should this section have a mermaid diagram? (flowchart, sequence, class, etc.)
2. **Tables**: Should this section have a comparison/summary table?
3. **ASCII Examples**: Are there enough ASCII art visualizations?
4. **Code Examples**: Are there practical code examples? (at least {min_examples_per_section})
5. **Exercises**: Are there practice problems or exercises?

## Your Task

Respond ONLY with valid JSON:

```json
{{
  "passed": true/false,
  "issues": ["list of specific missing elements"],
  "suggestions": ["specific improvements to make"],
  "needed_content": "exact markdown content to add (if needed)"
}}
```

Be thorough but reasonable - only require elements that genuinely add value for this topic.
If content already has required elements, set passed=true."""


def build_improve_prompt(block: SectionBlock, feedback: ReviewFeedback) -> str:
    """Build prompt for improving a content block."""
    issues_str = "\n".join(f"- {i}" for i in feedback.issues)
    suggestions_str = "\n".join(f"- {s}" for s in feedback.suggestions)

    return f"""You are improving an educational content section. The reviewer found issues.

## Current Section Content
```
{block.content}
```

## Issues to Fix
{issues_str}

## Suggestions
{suggestions_str}

## Your Task

Rewrite this section to address all issues. Your response must be:

1. Valid JSON only
2. Complete rewritten section content in `new_content` field
3. Preserve the heading structure
4. Add all missing elements (mermaid, tables, examples, etc.)

Response format:
```json
{{
  "new_content": "complete rewritten markdown section"
}}
```"""
