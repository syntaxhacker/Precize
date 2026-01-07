"""Content preferences for customized document generation."""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ContentPreferences:
    """User preferences for content generation.

    These preferences control how the LLM generates content,
    allowing customization for different audiences and use cases.
    """

    # Target audience
    audience_level: Literal["beginner", "intermediate", "advanced"] = "beginner"

    # Content inclusion flags
    include_analogies: bool = True
    include_code: bool = True
    include_diagrams: bool = True
    include_tables: bool = True

    # Teaching style
    teaching_style: Literal["progressive", "direct", "reference"] = "progressive"

    # Code preferences (if include_code=True)
    code_language: str | None = None  # Auto-detect if None
    code_examples_per_section: int = 3

    # Diagram preferences (if include_diagrams=True)
    diagram_types: list[str] = field(default_factory=lambda: ["flowchart", "sequence", "graph"])

    # Section structure
    lines_per_section: int = 150


def prompt_interactive_preferences(topic: str) -> ContentPreferences:
    """Ask user interactive questions and return preferences.

    Args:
        topic: The document topic being generated

    Returns:
        ContentPreferences with user's choices
    """
    print("\n" + "=" * 60)
    print(f"  Content Customization for: {topic}")
    print("=" * 60)
    print()

    # Audience level
    print("1. Target Audience:")
    print("   [1] Absolute Beginner (zero prior knowledge)")
    print("   [2] Intermediate (some prior knowledge)")
    print("   [3] Advanced (deep technical dive)")
    audience_input = input("   Choose [1-3] [default: 1]: ").strip() or "1"
    audience_map = {"1": "beginner", "2": "intermediate", "3": "advanced"}
    audience_level = audience_map.get(audience_input, "beginner")

    # Analogies
    print()
    print("2. Include Analogies?")
    print("   [Y]es - Use everyday analogies to explain concepts")
    print("   [N]o - Direct technical approach")
    analogies_input = input("   Include analogies? [Y/n] [default: Y]: ").strip().lower()
    include_analogies = analogies_input != "n"

    # Code examples
    print()
    print("3. Include Code Examples?")
    print("   [Y]es - With runnable examples")
    print("   [N]o - Concepts and theory only")
    code_input = input("   Include code? [Y/n] [default: Y]: ").strip().lower()
    include_code = code_input != "n"

    code_language = None
    code_examples_per_section = 3

    if include_code:
        lang_input = input("   Language [default: auto-detect]: ").strip() or None
        if lang_input:
            code_language = lang_input

        num_input = input("   Examples per section [default: 3]: ").strip() or "3"
        try:
            code_examples_per_section = int(num_input)
        except ValueError:
            code_examples_per_section = 3

    # Diagrams
    print()
    print("4. Include Diagrams?")
    print("   [Y]es - Add mermaid diagrams")
    print("   [N]o - Text-only content")
    diagrams_input = input("   Include diagrams? [Y/n] [default: Y]: ").strip().lower()
    include_diagrams = diagrams_input != "n"

    # Tables
    print()
    print("5. Include Comparison Tables?")
    print("   [Y]yes - Add tables for concepts")
    print("   [N]o - No tables")
    tables_input = input("   Include tables? [Y/n] [default: Y]: ").strip().lower()
    include_tables = tables_input != "n"

    # Teaching style
    print()
    print("6. Teaching Style:")
    print("   [1] Progressive - Foundation → Concept → Implementation")
    print("   [2] Direct - Jump straight to technical content")
    print("   [3] Reference - Encyclopedia style")
    style_input = input("   Choose [1-3] [default: 1]: ").strip() or "1"
    style_map = {"1": "progressive", "2": "direct", "3": "reference"}
    teaching_style = style_map.get(style_input, "progressive")

    print()
    print("=" * 60)
    print("  Configuration Summary")
    print("=" * 60)
    print(f"  Audience:      {audience_level.capitalize()}")
    print(f"  Style:         {teaching_style.capitalize()}")
    print(f"  Analogies:     {'Yes' if include_analogies else 'No'}")
    print(f"  Code:          {'Yes' if include_code else 'No'}")
    if include_code:
        print(f"    Language:    {code_language or 'Auto-detect'}")
        print(f"    Examples:    {code_examples_per_section}/section")
    print(f"  Diagrams:      {'Yes' if include_diagrams else 'No'}")
    print(f"  Tables:        {'Yes' if include_tables else 'No'}")
    print("=" * 60)
    print()

    return ContentPreferences(
        audience_level=audience_level,
        include_analogies=include_analogies,
        include_code=include_code,
        include_diagrams=include_diagrams,
        include_tables=include_tables,
        teaching_style=teaching_style,
        code_language=code_language,
        code_examples_per_section=code_examples_per_section,
    )


def parse_preferences_args(args: list[str]) -> ContentPreferences | None:
    """Parse CLI flags for non-interactive mode.

    Args:
        args: Command line arguments (sys.argv[1:])

    Returns:
        ContentPreferences if any preference flags found, None for interactive mode

    Examples:
        --audience advanced --style direct --no-analogies
        --audience beginner --no-code --no-diagrams
    """
    preferences = ContentPreferences()
    found_flags = False

    i = 0
    while i < len(args):
        arg = args[i]

        if arg == "--audience" and i + 1 < len(args):
            valid = ["beginner", "intermediate", "advanced"]
            if args[i + 1] in valid:
                preferences.audience_level = args[i + 1]
                found_flags = True
                i += 2

        elif arg == "--style" and i + 1 < len(args):
            valid = ["progressive", "direct", "reference"]
            if args[i + 1] in valid:
                preferences.teaching_style = args[i + 1]
                found_flags = True
                i += 2

        elif arg == "--no-analogies":
            preferences.include_analogies = False
            found_flags = True
            i += 1

        elif arg == "--no-code":
            preferences.include_code = False
            found_flags = True
            i += 1

        elif arg == "--no-diagrams":
            preferences.include_diagrams = False
            found_flags = True
            i += 1

        elif arg == "--no-tables":
            preferences.include_tables = False
            found_flags = True
            i += 1

        elif arg == "--include-code":
            preferences.include_code = True
            found_flags = True
            i += 1

        elif arg == "--code-lang" and i + 1 < len(args):
            preferences.code_language = args[i + 1]
            preferences.include_code = True
            found_flags = True
            i += 2

        elif arg == "--code-examples" and i + 1 < len(args):
            try:
                preferences.code_examples_per_section = int(args[i + 1])
                preferences.include_code = True
                found_flags = True
                i += 2
            except ValueError:
                i += 2

        else:
            i += 1

    return preferences if found_flags else None


def format_preferences_for_prompt(preferences: ContentPreferences) -> str:
    """Format preferences as a string for inclusion in prompts.

    Args:
        preferences: The content preferences

    Returns:
        Formatted string describing the preferences
    """
    lines = [
        f"**Audience Level**: {preferences.audience_level}",
        f"**Teaching Style**: {preferences.teaching_style}",
        "",
        "**Content Requirements**:",
    ]

    if preferences.include_analogies:
        if preferences.audience_level == "beginner":
            lines.append("- Include everyday analogies before technical terms")
        elif preferences.audience_level == "intermediate":
            lines.append("- Use analogies to bridge to known concepts")
    else:
        lines.append("- No analogies - direct technical approach")

    if preferences.include_code:
        lang_note = f" ({preferences.code_language})" if preferences.code_language else ""
        lines.append(f"- Include {preferences.code_examples_per_section} runnable code examples{lang_note}")
        lines.append("- Explain code line-by-line where needed")
    else:
        lines.append("- No code examples - concepts and theory only")

    if preferences.include_diagrams:
        diagram_list = ", ".join(preferences.diagram_types)
        lines.append(f"- Include mermaid diagrams ({diagram_list})")
    else:
        lines.append("- No diagrams - text only")

    if preferences.include_tables:
        lines.append("- Include comparison/summary tables")
    else:
        lines.append("- No tables")

    return "\n".join(lines)


def build_teaching_layers(
    teaching_style: str,
    audience_level: str,
) -> str:
    """Build teaching layer instructions based on style and audience.

    Args:
        teaching_style: progressive, direct, or reference
        audience_level: beginner, intermediate, or advanced

    Returns:
        Formatted teaching layer instructions
    """
    if teaching_style == "progressive":
        return build_progressive_layers(audience_level)
    elif teaching_style == "direct":
        return build_direct_layers(audience_level)
    else:  # reference
        return build_reference_style()


def build_progressive_layers(audience_level: str) -> str:
    """Build progressive teaching layer structure."""
    if audience_level == "beginner":
        return """
## TEACHING STRUCTURE

### Layer 1: Foundation (First 40%)
- Assume ZERO prior knowledge
- Start with everyday analogies (cooking, driving, organizing, etc.)
- Build concrete mental models before technical terms
- Explain "why" before "what"
- Never use jargon without 3+ simple examples

### Layer 2: Concept (Next 30%)
- Introduce formal terms ONLY after analogies mastered
- Show bridge: "If you understand [analogy], then [term] works like..."
- Step-by-step walkthroughs with visual representations
- Explain the reasoning behind each concept

### Layer 3: Implementation (Next 20%)
- Real, working code (not pseudocode)
- 3-5 concrete examples
- Explain each parameter/variable simply
- Show common mistakes and how to avoid them

### Layer 4: Mastery (Final 10%)
- Performance analysis
- Real-world applications
- Interview insights
"""
    elif audience_level == "intermediate":
        return """
## TEACHING STRUCTURE

### Layer 1: Context (First 30%)
- Bridge from known concepts to new topic
- Use targeted analogies for familiar domains
- Assume basic technical literacy
- Focus on "how this relates to what you know"

### Layer 2: Deep Dive (Next 40%)
- Formal definitions and terminology
- Architecture and design decisions
- Visual diagrams showing system interactions
- Step-by-step technical walkthroughs

### Layer 3: Implementation (Next 25%)
- Production-ready code examples
- Error handling and edge cases
- Integration patterns
- Performance considerations

### Layer 4: Advanced Topics (Final 5%)
- Anti-patterns to avoid
- Scaling considerations
- Real-world production advice
"""
    else:  # advanced
        return """
## TEACHING STRUCTURE

### Layer 1: Core Concepts (First 35%)
- Formal definitions and terminology
- Assume familiarity with related technologies
- Focus on architecture and design philosophy
- Technical depth over simplification

### Layer 2: Implementation Details (Next 40%)
- Production-ready code examples
- Advanced patterns and best practices
- Error handling and edge cases
- Performance optimization techniques

### Layer 3: Trade-offs and Decisions (Next 20%)
- When to use vs when not to use
- Comparison with alternatives
- Real-world scaling challenges
- Anti-patterns and pitfalls

### Layer 4: Mastery (Final 5%)
- Cutting-edge developments
- Research directions
- Expert-level insights
"""


def build_direct_layers(audience_level: str) -> str:
    """Build direct teaching style (no analogies, straight to technical)."""
    if audience_level == "beginner":
        return """
## TEACHING STRUCTURE

### Layer 1: Core Concepts (First 50%)
- Clear definitions upfront
- Simple examples
- Direct explanations
- Build complexity gradually

### Layer 2: Practical Application (Next 40%)
- How to use in real projects
- Common use cases
- Simple code examples
- Troubleshooting basics

### Layer 3: Reference (Final 10%)
- Quick summary
- Key points to remember
- Where to learn more
"""
    else:
        return """
## TEACHING STRUCTURE

### Layer 1: Technical Overview (First 40%)
- Formal definitions and specifications
- Architecture and design patterns
- Technical requirements and constraints
- System interactions

### Layer 2: Implementation (Next 50%)
- Production code examples
- Error handling and edge cases
- Integration patterns
- Performance considerations

### Layer 3: Expert Topics (Final 10%)
- Advanced patterns
- Anti-patterns and pitfalls
- Real-world scaling
- Performance optimization
"""


def build_reference_style() -> str:
    """Build reference/encyclopedia style."""
    return """
## TEACHING STRUCTURE

### Reference Style

- Clear, hierarchical organization
- Definitions and specifications first
- Comprehensive coverage of all aspects
- Historical context and evolution
- Comparison tables for variants
- Code examples where applicable
- Cross-references to related topics
- Quick reference summaries

Focus on completeness and accuracy over progressive learning.
"""
