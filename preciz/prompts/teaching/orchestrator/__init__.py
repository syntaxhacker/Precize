"""Prompts for the orchestrator-based document generator."""

from preciz.agents.teaching.preferences import (
    ContentPreferences,
    build_teaching_layers,
    format_preferences_for_prompt,
)


def build_generate_section_prompt(
    topic: str,
    section_title: str,
    description: str,
    context: str,
    include_mermaid: bool = False,
    include_table: bool = False,
    include_examples: bool = True,
) -> str:
    """Build prompt for generating a content section using the comprehensive teaching style."""
    requirements = []
    if include_mermaid:
        requirements.append("- Include at least one mermaid diagram (flowchart, sequence, or graph)")
    if include_table:
        requirements.append("- Include a comparison/summary table for concepts or variations")
    if include_examples:
        requirements.append("- Include 3-5 concrete, runnable examples (not pseudocode)")

    req_text = "\n".join(requirements) if requirements else "Standard educational content"

    return f"""You are creating a comprehensive guide for: {topic}

**This Section**: {section_title}

**Section Description**: {description}

**Previous Context** (what was covered before):
{context[-800:] if len(context) > 800 else context}

---

## TEACHING STYLE REQUIREMENTS

Your content must follow this progressive teaching structure:

### Layer 1: Foundation (First 30-40% of section)
- **Assume ZERO prior knowledge** - Start completely from scratch
- Use **everyday analogies** from real life (cooking, driving, organizing, etc.)
- Build **concrete mental models** before introducing any technical terms
- **Never use jargon** without 3+ simple examples explaining it first
- Use phrases like: "Think of it like...", "Imagine you're...", "It's similar to..."

### Layer 2: Concept (Next 30% of section)
- **Introduce formal terms** ONLY after analogies are mastered
- Show the bridge: "If you understand the [analogy], then [technical term] works like..."
- **Step-by-step walkthroughs** - pencil-and-paper style explanations
- Include **ASCII diagrams or visual representations** showing 5-10 element cases
- Explain the "why" behind every concept

### Layer 3: Implementation (Next 20-30% of section)
- **Real, working code** - not pseudocode
- Build examples **visually** - show how data changes step by step
- Explain **each parameter, variable, and function** like you're teaching a 12-year-old
- Include **"what if" scenarios** - common mistakes and how to avoid them
- Show edge cases and what happens in each

### Layer 4: Mastery (Final 10% of section)
- **Performance analysis**: Why is this approach better than alternatives?
- **Real-world applications**: Where is this actually used in production systems?
- **Advanced variations**: What else can we do with this concept?
- **Common interview questions**: How to explain this to an interviewer

---

## CONTENT REQUIREMENTS

{req_text}

## STRUCTURE RULES

1. **DO NOT** print layer headers like "Foundation Layer:", "Concept Layer:", etc.
2. **DO** transition naturally between layers using phrases like:
   - "Now that we understand the intuition, let's look at the formal definition..."
   - "Let's see how this works in code..."
   - "In practice, you'll see this used for..."
3. **DO** use progressive complexity - start simple, add complexity gradually
4. **DO** maintain continuity with previous sections (refer back when relevant)

## QUALITY CHECKLIST

- Does this start from absolute zero knowledge?
- Are there everyday analogies before any technical terms?
- Are there 3-5 working code examples?
- Are examples explained line-by-line where needed?
- Is there at least one diagram or table?
- Are common mistakes addressed?
- Does it end with real-world context?

Aim for 120-200 lines of comprehensive content.

---

Respond ONLY with the markdown content. Start immediately with the section heading (## or ###).
Do NOT include any preamble, explanations, or layer labels in your response.
"""


def build_review_prompt(content: str, title: str) -> str:
    """Build prompt for reviewing a content section against the teaching style."""
    return f"""Review this tutorial section for comprehensive teaching quality.

**Section**: {title}

**Content Preview**:
```
{content[:3000]}
```

**Check against the Progressive Teaching Framework**:

### Foundation Layer Check (First 30-40%)
1. Starts from ZERO prior knowledge? (no assumptions)
2. Uses everyday analogies before technical terms?
3. Builds mental models concretely?
4. No jargon without 3+ examples?

### Concept Layer Check (Next 30%)
5. Formal terms introduced AFTER analogies?
6. Clear bridge from analogy to technical concept?
7. Step-by-step walkthroughs included?
8. Visual/ASCII diagrams showing 5-10 elements?

### Implementation Layer Check (Next 20-30%)
9. Real, working code (not pseudocode)?
10. 3-5 concrete examples included?
11. Each parameter/variable explained simply?
12. "What if" scenarios and common mistakes covered?

### Mastery Layer Check (Final 10%)
13. Performance analysis included?
14. Real-world applications mentioned?
15. Advanced variations shown?
16. Interview-relevant insights?

### General Quality
17. At least one mermaid diagram or comparison table?
18. 100+ lines of content?
19. Progressive complexity maintained?
20. No layer headers ("Foundation Layer:", etc.)?

Response JSON:
```json
{{
  "passed": true/false,
  "issues": ["Missing everyday analogies before introducing TCP handshake", "Only 1 code example, need 3-5", "No performance comparison"],
  "suggestions": ["Start with a phone call analogy for handshake", "Add success/error cases", "Compare TCP vs UDP performance"]
}}
```

Be strict - this should be a comprehensive guide from zero to advanced.
"""


def build_improve_prompt(content: str, issues: str, suggestions: str) -> str:
    """Build prompt for improving a content section."""
    return f"""Improve this tutorial section to meet comprehensive teaching standards.

**Original Section**:
```
{content[:4000]}
```

**Issues to Fix**:
{issues}

**Suggestions**:
{suggestions}

---

## IMPROVEMENT FRAMEWORK

Apply these fixes while maintaining the Progressive Teaching Structure:

### If Foundation Layer Issues:
- Add everyday analogies at the start
- Remove assumptions about prior knowledge
- Explain jargon with 3+ simple examples
- Build mental models concretely

### If Concept Layer Issues:
- Bridge analogies to formal definitions
- Add step-by-step walkthroughs
- Include ASCII/mermaid diagrams
- Show 5-10 element cases visually

### If Implementation Layer Issues:
- Replace pseudocode with real working code
- Add more examples (aim for 3-5)
- Explain each parameter/variable simply
- Add "what if" scenarios

### If Mastery Layer Issues:
- Add performance analysis
- Mention real-world use cases
- Show advanced variations
- Include interview insights

---

**Important**: Keep the expanded structure but DO NOT include layer headers.
Transition naturally between sections.

Rewrite to address all issues. Respond ONLY with improved markdown.
"""


def build_create_outline_prompt(topic: str, target_lines: int = 10000) -> str:
    """Build prompt for creating a document outline following the teaching style."""
    return f"""Create a detailed outline for a {target_lines}-line comprehensive tutorial on: {topic}

**Teaching Approach**: Progressive from absolute zero to advanced mastery

**Target Structure**:
- First 40%: Foundation (analogy-based, zero prior knowledge)
- Next 30%: Concepts (formal terms after intuition)
- Next 20%: Implementation (real code, multiple examples)
- Final 10%: Mastery (performance, real-world, interview prep)

Return ONLY valid JSON. Example format:
```json
{{
  "title": "Tutorial Topic",
  "sections": [
    {{
      "title": "Section One Title",
      "level": 1,
      "description": "Start with everyday analogies and examples, then introduce basic concepts with clear explanations.",
      "require_mermaid": true,
      "require_table": false,
      "require_examples": true
    }},
    {{
      "title": "Section Two Title",
      "level": 1,
      "description": "Build on previous section with formal definitions, diagrams showing step-by-step processes, and practical examples.",
      "require_mermaid": true,
      "require_table": true,
      "require_examples": true
    }}
  ]
}}
```

**For your topic ({topic})**:
- Create 20-40 sections (each ~100-200 lines when written)

**CRITICAL PROGRESSION REQUIREMENTS**:
1. **Foundation First (sections 1-8)**:
   - Start with ZERO-KNOWLEDGE analogies (everyday examples)
   - NO technical jargon in first 3-5 sections
   - Build mental models before introducing notation
   - For math/technical topics: Cover basic operations FIRST (order of operations, negative numbers, fractions)

2. **Concept Building (sections 9-20)**:
   - Introduce formal terminology AFTER intuition is established
   - Connect new concepts to previously learned analogies
   - Show "why" before "how"

3. **Practice & Application (sections 21-30)**:
   - Real code implementations with 3-5 examples each
   - Progressive difficulty: basic → intermediate → advanced

4. **Mastery (sections 31+)**:
   - Performance analysis, real-world use cases, interview prep
   - Advanced patterns and edge cases

**Section Flow Checklist**:
- [ ] Does section 1 start with pure analogies?
- [ ] Are prerequisites covered before dependent topics?
- [ ] Is there a clear "what" → "why" → "how" flow?
- [ ] Do examples come BEFORE abstract notation?

**Level meanings**:
- level 1: Major section heading
- level 2: Subsection
- level 3: Advanced/deep dive topic

Respond ONLY with the JSON object. No markdown, no code blocks, just the raw JSON.
"""


def build_generate_section_prompt_with_preferences(
    topic: str,
    section_title: str,
    description: str,
    context: str,
    preferences: ContentPreferences,
) -> str:
    """Build prompt for generating content with user preferences.

    Args:
        topic: Document topic
        section_title: Current section title
        description: Section description
        context: Previous content context
        preferences: User content preferences

    Returns:
        Formatted prompt string
    """
    # Build requirements based on preferences
    requirements = []

    if preferences.include_analogies and preferences.audience_level == "beginner":
        requirements.append("- Start with everyday analogies before technical terms")

    if preferences.include_code:
        lang = f" ({preferences.code_language})" if preferences.code_language else ""
        requirements.append(f"- Include {preferences.code_examples_per_section} runnable code examples{lang}")
        requirements.append("- Explain code line-by-line where needed")
    else:
        requirements.append("- **CRITICAL: NO CODE BLOCKS WHATSOEVER**")
        requirements.append("- **ABSOLUTELY NO** code blocks, syntax examples, or implementation details")
        requirements.append("- **DO NOT** use ```javascript, ```jsx, ```python, or ANY code fences")
        requirements.append("- Explain concepts using ONLY: analogies, diagrams, tables, and plain text descriptions")
        requirements.append("- If you feel tempted to show code, use a conceptual explanation instead")

    if preferences.include_diagrams:
        diagram_list = ", ".join(preferences.diagram_types)
        requirements.append(f"- Include 2-3 simple mermaid diagrams ({diagram_list}) - each diagram should focus on ONE concept with 3-6 nodes max")
        requirements.append("- **Multiple simple diagrams > One complex diagram** - Split complex ideas into separate diagrams")
    else:
        requirements.append("- No diagrams - text content only")

    if preferences.include_tables:
        requirements.append("- Include comparison/summary tables for concepts")
    else:
        requirements.append("- No tables")

    # Build teaching layers based on style
    teaching_layers = build_teaching_layers(
        preferences.teaching_style,
        preferences.audience_level,
    )

    req_text = "\n".join(requirements)

    # Build examples section based on what's enabled/disabled
    examples_section = build_examples_section(preferences)

    return f"""You are creating a comprehensive guide for: {topic}

**This Section**: {section_title}

**Section Description**: {description}

{format_preferences_for_prompt(preferences)}

---

{context if context else ""}

---

{teaching_layers}

## CONTENT REQUIREMENTS

{req_text}

{examples_section}

## STRUCTURE RULES

1. **DO NOT** print layer headers like "Foundation Layer:", "Concept Layer:", etc.
2. **DO** transition naturally between sections
3. **DO** use progressive complexity - start simple, add complexity gradually
4. **DO** maintain continuity with previous sections (refer back when relevant)
5. **CRITICAL** - Build knowledge progressively:
   - Start with analogies/metaphors before technical terms
   - Establish prerequisites BEFORE teaching dependent concepts
   - For math/technical topics: teach basic operations (order of operations, negative numbers) BEFORE variables/equations
   - Show concrete examples BEFORE abstract notation
   - Explain "what" before "why" before "how"

## QUALITY CHECKLIST

- Starts appropriate for {preferences.audience_level} level?
- {"Analogies included before technical terms?" if preferences.include_analogies else "Direct technical approach?"}
- {"3-5 working code examples?" if preferences.include_code else "No code as requested?"}
- {"Diagrams included?" if preferences.include_diagrams else "No diagrams as requested?"}
- Common mistakes addressed?
- Real-world context included?

Aim for 120-200 lines of comprehensive content.

---

Respond ONLY with the markdown content. Start immediately with the section heading (## or ###).
Do NOT include any preamble, explanations, or layer labels in your response.
"""


def build_examples_section(preferences: ContentPreferences) -> str:
    """Build concrete examples of what's right vs wrong based on preferences.

    Args:
        preferences: User content preferences

    Returns:
        Formatted examples section
    """
    examples = []

    # Code examples
    if not preferences.include_code:
        examples.append("""
### CODE - ABSOLUTELY FORBIDDEN:
**WRONG** ❌ - DO NOT DO THIS:
```javascript
function Welcome() {{
  return <h1>Hello</h1>;
}}
```
**WRONG** ❌ - DO NOT DO THIS EITHER:
```jsx
const component = <div>Hello</div>;
```
**WRONG** ❌ - OR THIS:
\`\`\`html
<div>Hello</div>
\`\`\`

**RIGHT** ✅ - EXPLAIN CONCEPTUALLY:
Think of a component like a recipe card. Just as a recipe card tells you the ingredients and steps to make a dish, a React component describes what should appear on the screen. When you use the component, React "cooks" the UI by following the component's instructions. The component doesn't contain the actual UI—it's just a blueprint for creating it.

For example, a "UserProfile" component blueprint might specify: show the user's name in large text, display their avatar image in a circle, and list their bio below. When React uses this blueprint, it actually creates the HTML elements. But the blueprint itself is just a description, not the code.

**Use analogies, diagrams, and tables instead of ANY code.**
""")

    # Diagram examples
    if preferences.include_diagrams:
        examples.append("""
### DIAGRAMS - BEST PRACTICES:

**PRINCIPLE: Multiple Simple Diagrams > One Complex Diagram**

Instead of creating one giant diagram with many subgraphs, create 2-3 separate, focused diagrams that each illustrate ONE concept clearly.

**EXAMPLE 1 - Side-by-Side Comparison (Like Hardware Speedup)**
```mermaid
%%{init: {'theme':'neutral', 'themeVariables': {'lineColor': '#ffffff', 'edgeLabelBackground':'#ffffff'}}}%%
flowchart LR
    subgraph Old["🐌 Old Machine"]
        A1["10 items: 5 sec"]
        A2["100 items: 50 sec"]
        A1 -->|"10× data"| A2
    end

    subgraph New["🚀 New Machine"]
        B1["10 items: 1 sec"]
        B2["100 items: 10 sec"]
        B1 -->|"10× data"| B2
    end

    Old -->|"5× faster"| New

    classDef old fill:#f8d7da,stroke:#dc3545,stroke-width:2px,color:#721c24
    classDef new fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#155724

    class A1,A2 old
    class B1,B2 new
```

**EXAMPLE 2 - Single Focused Flow (3-4 nodes max)**
```mermaid
%%{init: {'theme':'neutral', 'themeVariables': {'lineColor': '#ffffff'}}}%%
flowchart LR
    A["🚀 Input Data"] -->|Process| B["🔄 Transform"]
    B -->|Validate| C["✅ Output"]

    classDef input fill:#e2e3e5,stroke:#6c757d,stroke-width:2px,color:#383d41
    classDef process fill:#fff3cd,stroke:#ffc107,stroke-width:2px,color:#856404
    classDef output fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#155724

    class A input
    class B process
    class C output
```

**EXAMPLE 3 - Simple Before/After Comparison**
```mermaid
%%{init: {'theme':'neutral', 'themeVariables': {'lineColor': '#ffffff'}}}%%
flowchart LR
    Before["❌ Before: O(n²)<br/>100×100 = 10,000 ops"]
    After["✅ After: O(n)<br/>100 + 100 = 200 ops"]

    Before -->|"Optimize"| After

    classDef bad fill:#f8d7da,stroke:#dc3545,stroke-width:2px,color:#721c24
    classDef good fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#155724

    class Before bad
    class After good
```

**CRITICAL RULES:**

1. **Keep Labels SHORT** - Max 5-7 words per label
   - Use emojis: 🚀 ✅ ❌ 🔄 📊 🎯 🧠
   - Use line breaks with <br/> sparingly (max 2 breaks)
   - WRONG: A["This is a very long label that explains too much and makes the diagram hard to read"]
   - RIGHT: A["🚀 Input<br/>10 items"]

2. **Multiple Diagrams Strategy** - Instead of ONE complex diagram:
   - Create 2-3 simple diagrams showing different aspects
   - Each diagram focuses on ONE concept
   - Space them out with text explanations
   - Example: First diagram shows concept, second shows example, third shows comparison

3. **Subgraphs ONLY for Side-by-Side Comparison**:
   - Use when comparing TWO things (old vs new, before vs after)
   - Each subgraph should have 2-3 nodes MAX
   - Connect subgraphs with ONE clear relationship arrow

4. **AVOID Complex Nested Structures**:
   - NO deeply nested subgraphs
   - NO more than 6 nodes per diagram
   - NO crossing arrows
   - If it's getting complex, split into 2 diagrams

5. **Color Coding** (use sparingly for emphasis):
   - Green: Success, fast, good, new, optimized
   - Red: Error, slow, bad, old, inefficient
   - Yellow: Warning, processing, transforming
   - Blue: Info, data, input, neutral
   - Gray: Base, default, neutral

6. **Quote ALL labels with special chars**:
   - Special chars: [] () {} <> : = + - * /
   - WRONG: A[dp[1]] or B[F(5)]
   - RIGHT: A["dp[1]"] or B["F(5)"]

7. **Horizontal layout ONLY**:
   - WRONG: flowchart TD
   - RIGHT: flowchart LR

8. **Complete ALL classDef**:
   - WRONG: classDef child
   - RIGHT: classDef child fill:#cce5ff,stroke:#0066cc,stroke-width:2px,color:#004085
""")

    # Table examples
    if preferences.include_tables:
        examples.append("""
### TABLES - WHAT TO INCLUDE:
**RIGHT** ✅:
| Feature | Props | State |
|---------|-------|-------|
| Source | Passed from parent | Managed internally |
| Can Change | No | Yes |
| Purpose | Configuration | Dynamic data |

Use tables to compare concepts, list variations, or summarize key differences.
""")

    # Analogy examples for beginners
    if preferences.include_analogies and preferences.audience_level == "beginner":
        examples.append("""
### ANALOGIES - HOW TO USE THEM:
**RIGHT** ✅:
"Think of React components like kitchen appliances in a restaurant. Just as a blender, oven, and refrigerator each have one specific job, each React component handles one piece of your interface. The blender doesn't tell the oven what to cook—it just blends. Similarly, components stay focused on their own responsibility."

Start every major concept with an everyday analogy before introducing technical terms.
""")

    # Advanced audience examples
    if preferences.audience_level == "advanced" and not preferences.include_analogies:
        examples.append("""
### ADVANCED CONTENT - HOW TO APPROACH:
**RIGHT** ✅:
"React's component model follows the Single Responsibility Principle. Each component encapsulates its own state management and rendering logic, enabling composition patterns that scale to complex applications. The virtual DOM diffing algorithm optimizes updates by..."

Use formal terminology, discuss architecture patterns, and focus on production considerations.
""")

    if examples:
        return "## EXAMPLES: WHAT'S RIGHT vs WHAT'S WRONG\n" + "".join(examples)
    else:
        return ""


def build_review_prompt_with_preferences(
    content: str,
    title: str,
    preferences: ContentPreferences,
) -> str:
    """Build review prompt that checks against user preferences."""
    # Build checklist based on preferences
    checklist = []

    if preferences.audience_level == "beginner":
        checklist.extend([
            "1. Starts from ZERO prior knowledge? (no assumptions)",
            "2. Builds mental models concretely?",
        ])
        if preferences.include_analogies:
            checklist.append("3. Uses everyday analogies before technical terms?")
    elif preferences.audience_level == "intermediate":
        checklist.extend([
            "1. Bridges from known concepts?",
            "2. Appropriate technical depth?",
        ])
    else:  # advanced
        checklist.extend([
            "1. Assumes appropriate prior knowledge?",
            "2. Sufficient technical depth?",
        ])

    if preferences.include_code:
        checklist.extend([
            f"{len(checklist) + 1}. Real, working code (not pseudocode)?",
            f"{len(checklist) + 2}. {preferences.code_examples_per_section}+ concrete examples?",
        ])

    if preferences.include_diagrams:
        checklist.append(f"{len(checklist) + 1}. Mermaid diagrams included?")

    if preferences.include_tables:
        checklist.append(f"{len(checklist) + 1}. Comparison tables included?")

    checklist.extend([
        f"{len(checklist) + 1}. 100+ lines of content?",
        f"{len(checklist) + 1}. Progressive complexity maintained?",
        f"{len(checklist) + 1}. No layer headers?",
    ])

    checklist_text = "\n".join(checklist)

    return f"""Review this tutorial section for quality.

**Section**: {title}

**Content Preview**:
```
{content[:3000]}
```

**Configuration**:
- Audience: {preferences.audience_level}
- Style: {preferences.teaching_style}
- Analogies: {preferences.include_analogies}
- Code: {preferences.include_code}
- Diagrams: {preferences.include_diagrams}
- Tables: {preferences.include_tables}

**Quality Checklist**:
{checklist_text}

Response JSON:
```json
{{
  "passed": true/false,
  "issues": ["Missing code examples", "No diagrams included", "Too advanced for beginner"],
  "suggestions": ["Add 3 code examples", "Include mermaid flowchart", "Simplify technical language"]
}}
```

Be strict - ensure content matches the requested configuration.
"""


def build_improve_prompt_with_preferences(
    content: str,
    issues: list[str],
    suggestions: list[str],
    preferences: ContentPreferences,
) -> str:
    """Build improve prompt that respects user preferences."""
    issues_text = "\n".join(f"- {i}" for i in issues)
    suggestions_text = "\n".join(f"- {s}" for s in suggestions)

    improvement_framework = []
    improvement_framework.append("## IMPROVEMENT FRAMEWORK")
    improvement_framework.append("")

    if preferences.audience_level == "beginner":
        improvement_framework.append("### For Beginner Audience:")
        improvement_framework.append("- Start from absolute zero")
        if preferences.include_analogies:
            improvement_framework.append("- Add everyday analogies")
        improvement_framework.append("- Explain all jargon")
        improvement_framework.append("")

    improvement_framework.append("### Based on Issues:")
    if "code" in " ".join(issues).lower() and preferences.include_code:
        improvement_framework.append(f"- Add {preferences.code_examples_per_section} runnable code examples")
        if preferences.code_language:
            improvement_framework.append(f"- Use {preferences.code_language} for examples")
    if "diagram" in " ".join(issues).lower() and preferences.include_diagrams:
        improvement_framework.append("- Add mermaid diagrams")
    if "table" in " ".join(issues).lower() and preferences.include_tables:
        improvement_framework.append("- Add comparison tables")

    framework_text = "\n".join(improvement_framework)

    return f"""Improve this tutorial section to meet quality standards.

**Original Section**:
```
{content[:4000]}
```

**Issues to Fix**:
{issues_text}

**Suggestions**:
{suggestions_text}

**Target Configuration**:
- Audience: {preferences.audience_level}
- Style: {preferences.teaching_style}
- Code: {preferences.include_code} (examples: {preferences.code_examples_per_section})
- Diagrams: {preferences.include_diagrams}
- Tables: {preferences.include_tables}

---

{framework_text}

**Important**: Keep the expanded structure but DO NOT include layer headers.
Transition naturally between sections.

Rewrite to address all issues. Respond ONLY with improved markdown.
"""


def build_summary_prompt(
    content: str,
    title: str,
    preferences: ContentPreferences | None = None,
) -> str:
    """Build prompt for generating section summary.

    Args:
        content: Section content to summarize
        title: Section title
        preferences: Optional content preferences for context

    Returns:
        Formatted prompt string
    """
    # Truncate content if too long (keep first 3000 chars for context)
    content_preview = content[:3000] if len(content) > 3000 else content

    preferences_hint = ""
    if preferences:
        if preferences.audience_level == "beginner":
            preferences_hint = "\nFocus on key concepts and foundational understanding."
        elif preferences.audience_level == "advanced":
            preferences_hint = "\nFocus on technical details, patterns, and implementation insights."

    return f"""Create a concise summary for this tutorial section.

**Section**: {title}

**Content Preview**:
```
{content_preview}
```
{preferences_hint}

**Requirements**:
1. Generate exactly 3-5 bullet points
2. Each bullet should start with "- "
3. Focus on the MOST important concepts covered
4. Keep each bullet point concise (max 20 words)
5. Capture the "what" and "why" (not just "how")
6. Think ahead: What should the NEXT section know about this one?

**Format**:
Respond ONLY with the bullet points, no preamble or explanation.

Example output:
- Explained how React components manage state internally
- Introduced useState hook for functional components
- Covered the difference between props and state
- Demonstrated state updates trigger re-renders
- Showed common state management pitfalls

Create the summary now:
"""


def build_enhanced_context(
    tasks: list,
    current_index: int,
    recent_content: str,
    num_summaries: int = 3,
) -> str:
    """Build enhanced context from summaries + recent content.

    Args:
        tasks: List of all tasks (BlockTask objects)
        current_index: Index of current task being generated
        recent_content: Last N characters of immediate previous content
        num_summaries: Number of previous summaries to include (default: 3)

    Returns:
        Formatted context string with summaries + content
    """
    from preciz.agents.teaching import BlockTask

    sections = []

    # Add section summaries from previous tasks
    if current_index > 0:
        start_index = max(0, current_index - num_summaries)
        previous_tasks = tasks[start_index:current_index]
        tasks_with_summaries = [t for t in previous_tasks if t.summary]

        if tasks_with_summaries:
            sections.append("**Previous Section Summaries**:")
            sections.append("")

            for task in tasks_with_summaries:
                sections.append(f"### {task.title}")
                sections.append(task.summary)
                sections.append("")

    # Add immediate previous content for continuity
    if recent_content:
        sections.append("**Immediate Previous Content** (for continuity):")
        sections.append("```")
        sections.append(recent_content[-500:] if len(recent_content) > 500 else recent_content)
        sections.append("```")
        sections.append("")

    return "\n".join(sections)
