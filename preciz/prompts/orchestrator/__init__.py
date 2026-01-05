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
- Early sections: Pure analogies and intuition (no jargon)
- Middle sections: Formal concepts with visual diagrams
- Later sections: Real code implementations with 3-5 examples each
- Final sections: Performance analysis, real-world use cases, interview prep

**Level meanings**:
- level 1: Major section heading
- level 2: Subsection
- level 3: Advanced/deep dive topic

Respond ONLY with the JSON object. No markdown, no code blocks, just the raw JSON.
"""
