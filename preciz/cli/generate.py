"""CLI for long document generation with multiple generation modes."""

import json
import re
import sys
import time
from pathlib import Path
from typing import Literal

from preciz.agents.teaching import DocumentOrchestrator, BlockTask, ContentPreferences
from preciz.agents.teaching.preferences import (
    prompt_interactive_preferences,
    parse_preferences_args,
)
from preciz.core import Config, Message


def print_usage():
    """Print usage information."""
    print("Preciz Long Document Generator")
    print()
    print("Generate 10,000+ line educational documents block by block.")
    print()
    print("Usage:")
    print("  preciz-gen-long <topic> <output_file> [options]")
    print()
    print("Examples:")
    print("  preciz-gen-long 'Differential Calculus' calculus.md")
    print("  preciz-gen-long 'Python Async' async.md --lines 5000 --gen-mode llm")
    print("  preciz-gen-long 'ML Basics' ml.md --gen-mode parts --lines 3000")
    print("  preciz-gen-long 'Python' python.md --gen-mode custom my_sections.json")
    print()
    print("  # With content customization (non-interactive)")
    print("  preciz-gen-long 'API Design' api.md --audience advanced --style direct")
    print("  preciz-gen-long 'Git Basics' git.md --audience beginner --no-diagrams")
    print("  preciz-gen-long 'HTTP History' http.md --style reference --no-code")
    print()
    print("Options:")
    print("  --lines <n>       Target line count (default: 10000)")
    print("  --iter <n>        Max review iterations per block (default: 2)")
    print("  --gen-mode <mode> Generation mode (default: auto)")
    print("  --parts <n>       Number of parts for 'parts' mode (default: auto)")
    print("  --approve-outline Prompt to approve outline before generation")
    print()
    print("Content Customization (optional flags, otherwise prompts interactively):")
    print("  --audience <level>     Target audience: beginner, intermediate, advanced")
    print("  --style <style>        Teaching style: progressive, direct, reference")
    print("  --no-analogies         Skip everyday analogies (direct technical)")
    print("  --no-code              Skip code examples (theory only)")
    print("  --no-diagrams          Skip mermaid diagrams (text only)")
    print("  --no-tables            Skip comparison tables")
    print("  --code-lang <lang>     Specific language for code (e.g., python)")
    print("  --code-examples <n>    Number of code examples per section (default: 3)")
    print()
    print("Generation Modes:")
    print("  auto    - Try LLM outline, fall back to parts if it fails")
    print("  llm     - Use LLM to create detailed outline (best quality)")
    print("  parts   - Simple numbered parts (most reliable)")
    print("  custom  - Use custom sections from a file")
    print()
    print("Without customization flags, you'll be prompted interactively for preferences.")


def parse_args(args: list[str]) -> tuple[str, str, int, int, str, int | None, bool]:
    """Parse command line arguments.

    Returns:
        (topic, output, target_lines, max_iterations, gen_mode, num_parts, approve_outline)
    """
    if len(args) < 2:
        return None, None, 10000, 2, "auto", None, False

    topic = args[0]
    output = args[1]
    target_lines = 10000
    max_iterations = 2
    gen_mode = "auto"
    num_parts = None  # None = auto-calculate from target_lines
    approve_outline = False  # Default: auto-proceed

    i = 2
    while i < len(args):
        if args[i] == "--lines" and i + 1 < len(args):
            target_lines = int(args[i + 1])
            i += 2
        elif args[i] == "--iter" and i + 1 < len(args):
            max_iterations = int(args[i + 1])
            i += 2
        elif args[i] == "--gen-mode" and i + 1 < len(args):
            gen_mode = args[i + 1]
            i += 2
        elif args[i] == "--parts" and i + 1 < len(args):
            num_parts = int(args[i + 1])
            i += 2
        elif args[i] == "--approve-outline":
            approve_outline = True
            i += 1
        else:
            i += 1

    return topic, output, target_lines, max_iterations, gen_mode, num_parts, approve_outline


def create_llm_todo_list(orchestrator, topic: str, target_lines: int, logger=None) -> list[BlockTask]:
    """Create todo list using LLM (best quality)."""
    if logger is None:
        # No logger - use print directly
        print("  → Asking LLM to create outline...")
    elif hasattr(logger, 'info'):
        # SessionLogger object
        logger.info("  → Asking LLM to create outline...")
    else:
        # Fallback
        print("  → Asking LLM to create outline...")

    prompt = f"""Create a detailed outline for a {target_lines}-line comprehensive tutorial on: {topic}

**Teaching Approach**: Progressive from absolute zero to advanced mastery

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

Create 20-40 sections (each ~100-200 lines when written).
Early sections: Pure analogies and intuition (no jargon).
Middle sections: Formal concepts with visual diagrams.
Later sections: Real code implementations with 3-5 examples each.
Final sections: Performance analysis, real-world use cases, interview prep.

Respond ONLY with the raw JSON object (no markdown code blocks).
"""

    start_time = time.time()
    success = True
    error_message = ""
    response_content = ""
    parsed_json = ""

    try:
        response = orchestrator.llm.complete(
            [Message(role="user", content=prompt)],
            temperature=0.5,
            max_tokens=8000,
        )
        response_time = time.time() - start_time
        response_content = response.content

        # Log the LLM call if logger is provided
        if hasattr(logger, 'log_llm_request'):
            logger.log_llm_request(
                prompt=prompt,
                response=response_content,
                model=orchestrator.config.model,
                temperature=0.5,
                max_tokens=8000,
                response_time_seconds=response_time,
                success=True,
            )

        # Parse with fallback strategies
        json_str = None

        # Strategy 1: Extract from code blocks
        for pattern in [r"```json\s*\n?(\{.*?\})\s*```", r"``(\{.*?\})```"]:
            match = re.search(pattern, response_content, re.DOTALL)
            if match:
                json_str = match.group(1)
                break

        # Strategy 2: Find raw JSON
        if not json_str:
            match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response_content, re.DOTALL)
            if match:
                json_str = match.group(0)

        # Strategy 3: Parse JSON
        if json_str:
            try:
                # Parse JSON directly (preserves newlines in strings)
                data = json.loads(json_str)
                parsed_json = json.dumps(data, indent=2)

                tasks = []
                for section in data.get("sections", []):
                    tasks.append(BlockTask(
                        title=section["title"],
                        description=section.get("description", ""),
                        level=section.get("level", 1),
                        require_mermaid=section.get("require_mermaid", False),
                        require_table=section.get("require_table", False),
                        require_examples=section.get("require_examples", True),
                    ))

                # Update log with parsed JSON
                if hasattr(logger, 'log_llm_request'):
                    logger.metadata.llm_calls[-1].parsed_json = parsed_json

                return tasks
            except json.JSONDecodeError as e:
                success = False
                error_message = f"JSON decode error: {e}"
                if hasattr(logger, 'log_llm_request'):
                    logger.metadata.llm_calls[-1].success = False
                    logger.metadata.llm_calls[-1].error_message = error_message

        success = False
        error_message = "Could not extract valid JSON from LLM response"
        if hasattr(logger, 'log_llm_request'):
            logger.metadata.llm_calls[-1].success = False
            logger.metadata.llm_calls[-1].error_message = error_message

        raise ValueError("Failed to parse LLM outline as JSON")

    except Exception as e:
        # Log failed request
        if hasattr(logger, 'log_llm_request') and not response_content:
            logger.log_llm_request(
                prompt=prompt,
                response=response_content or f"Exception: {e}",
                model=orchestrator.config.model,
                temperature=0.5,
                max_tokens=8000,
                response_time_seconds=time.time() - start_time,
                success=False,
                error_message=str(e),
            )
        raise


def create_parts_todo_list(topic: str, target_lines: int, num_parts: int | None = None) -> list[BlockTask]:
    """Create simple numbered parts (most reliable).

    Args:
        topic: Document topic
        target_lines: Target line count (used if num_parts is None)
        num_parts: Explicit number of parts, or None to auto-calculate
    """
    if num_parts is not None:
        # Use explicit number
        num_sections = max(1, num_parts)
    else:
        # Auto-calculate from target_lines
        num_sections = max(5, target_lines // 150)

    tasks = []
    for i in range(1, num_sections + 1):
        tasks.append(BlockTask(
            title=f"{topic} - Part {i}",
            description=f"Part {i} of {topic}",
            level=1,
            require_mermaid=(i % 3 == 0),
            require_table=(i % 2 == 0),
            require_examples=True,
        ))

    return tasks


def create_custom_todo_list(custom_file: str) -> list[BlockTask]:
    """Load custom sections from a file."""
    path = Path(custom_file)
    if not path.exists():
        raise FileNotFoundError(f"Custom sections file not found: {custom_file}")

    data = json.loads(path.read_text())

    tasks = []
    for section in data.get("sections", []):
        tasks.append(BlockTask(
            title=section["title"],
            description=section.get("description", ""),
            level=section.get("level", 1),
            require_mermaid=section.get("require_mermaid", False),
            require_table=section.get("require_table", False),
            require_examples=section.get("require_examples", True),
        ))

    return tasks


def main() -> int:
    """Main CLI entry point."""
    if len(sys.argv) < 3 or sys.argv[1] in ("-h", "--help", "help"):
        print_usage()
        return 0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help", "help") else 1

    args = sys.argv[1:]
    topic, output, target_lines, max_iterations, gen_mode, num_parts, approve_outline = parse_args(args)

    if topic is None:
        print_usage()
        return 1

    # Validate gen_mode
    valid_modes = ["auto", "llm", "parts", "custom"]
    if gen_mode not in valid_modes:
        print(f"Error: Invalid gen-mode '{gen_mode}'. Must be one of: {', '.join(valid_modes)}")
        return 1

    # Import logger after we have the args
    from preciz.core.logger import SessionLogger

    # Initialize logger
    logger = SessionLogger(
        topic=topic,
        output_file=output,
        target_lines=target_lines,
        mode=gen_mode,
        max_iterations=max_iterations,
        num_parts=num_parts,
    )

    # Get timestamp filename for log reference
    timestamp_filename = logger.log_file.stem if hasattr(logger, 'log_file') else "preciz-latest"

    try:
        # Collect preferences (check for flags or prompt interactively)
        preferences = parse_preferences_args(args)

        if preferences is None:
            # No flags found, prompt interactively
            # Exit logger context temporarily for interactive input
            preferences = prompt_interactive_preferences(topic)

        with logger:
            logger.info(f"{'='*60}")
            logger.info(f"  PRECIZ CONTENT GENERATOR")
            logger.info(f"{'='*60}")
            logger.info("")
            logger.info(f"Topic: {topic}")
            logger.info(f"Output: {output}")
            logger.info(f"Target: {target_lines} lines")
            logger.info(f"Mode: {gen_mode}")

            # Log preferences
            logger.info(f"")
            logger.info(f"Content Preferences:")
            logger.info(f"  Audience: {preferences.audience_level}")
            logger.info(f"  Style: {preferences.teaching_style}")
            logger.info(f"  Analogies: {'Yes' if preferences.include_analogies else 'No'}")
            logger.info(f"  Code: {'Yes' if preferences.include_code else 'No'}")
            if preferences.include_code:
                logger.info(f"    Language: {preferences.code_language or 'Auto-detect'}")
                logger.info(f"    Examples: {preferences.code_examples_per_section}/section")
            logger.info(f"  Diagrams: {'Yes' if preferences.include_diagrams else 'No'}")
            logger.info(f"  Tables: {'Yes' if preferences.include_tables else 'No'}")

            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            config = Config.from_env()
            orchestrator = DocumentOrchestrator(config)

            # Log config
            logger.debug(f"Model: {config.model}")
            logger.debug(f"Provider: {config.provider}")
            logger.debug(f"API Base: {config.base_url}")

            # Create todo list based on mode
            logger.info("")
            logger.info(f"Creating todo list (mode: {gen_mode})...")
            tasks = None

            if gen_mode == "llm":
                # LLM mode - use AI to create outline
                try:
                    tasks = create_llm_todo_list(orchestrator, topic, target_lines, logger)
                    logger.success(f"  ✓ LLM created {len(tasks)} sections")
                except Exception as e:
                    logger.error(f"  ✗ LLM outline failed: {e}")
                    return 1

            elif gen_mode == "parts":
                # Parts mode - simple numbered sections
                tasks = create_parts_todo_list(topic, target_lines, num_parts)
                if num_parts:
                    logger.success(f"  ✓ Created {len(tasks)} parts (explicit)")
                else:
                    logger.success(f"  ✓ Created {len(tasks)} parts (auto-calculated)")

            elif gen_mode == "custom":
                # Custom mode - load from file
                # Look for a .json file in the remaining args
                custom_file = "sections.json"
                for arg in args:
                    if arg.endswith(".json"):
                        custom_file = arg
                        break

                try:
                    tasks = create_custom_todo_list(custom_file)
                    logger.success(f"  ✓ Loaded {len(tasks)} sections from {custom_file}")
                except Exception as e:
                    logger.error(f"  ✗ Failed to load custom sections: {e}")
                    logger.info(f"     Create {custom_file} with section definitions")
                    logger.info(f"     Example format:")
                    logger.info(f'     {{"sections": [{{"title": "Intro", "level": 1, "description": "...", "require_mermaid": false, "require_table": false, "require_examples": true}}]}}')
                    return 1

            else:  # auto mode
                # Auto mode - try LLM first, fall back to parts
                try:
                    tasks = create_llm_todo_list(orchestrator, topic, target_lines, logger)
                    logger.success(f"  ✓ LLM created {len(tasks)} sections")
                except Exception as e:
                    logger.warning(f"  ⚠ LLM outline failed ({e})")
                    logger.info(f"  → Falling back to parts mode...")
                    tasks = create_parts_todo_list(topic, target_lines, num_parts)
                    logger.success(f"  ✓ Created {len(tasks)} parts")

            if not tasks:
                logger.error("  ✗ No tasks created")
                logger.error(f"  → LLM returned 0 sections. Check the log file for details.")
                return 1

            # Display outline and ask for confirmation
            logger.info("")
            logger.info(f"{'='*60}")
            logger.info(f"  OUTLINE PREVIEW")
            logger.info(f"{'='*60}")
            logger.info("")
            for i, task in enumerate(tasks, 1):
                logger.info(f"  {i}. {task.title}")
            logger.info("")
            logger.info(f"Total: {len(tasks)} sections planned")
            logger.info("")

            # Ask for confirmation before proceeding
            if approve_outline:
                try:
                    response = input("Proceed with this outline? [Y/n/edit]: ").strip().lower()

                    if response == 'n':
                        logger.info("Cancelled by user.")
                        return 0
                    elif response == 'edit':
                        # Save outline to JSON file for editing
                        outline_file = Path("outline.json")
                        import json
                        outline_data = {
                            "title": topic,
                            "sections": [
                                {
                                    "title": task.title,
                                    "level": task.level,
                                    "description": task.description,
                                    "require_mermaid": task.require_mermaid,
                                    "require_table": task.require_table,
                                    "require_examples": task.require_examples
                                }
                                for task in tasks
                            ]
                        }
                        outline_file.write_text(json.dumps(outline_data, indent=2))
                        logger.info("")
                        logger.success(f"✓ Outline saved to {outline_file}")
                        logger.info("")
                        logger.info("Edit the file to modify sections, then press Enter to continue...")
                        logger.info("Press Ctrl+C to cancel")

                        # Wait for user to edit and press Enter
                        input("Press Enter when ready to proceed...")

                        # Reload the outline from JSON
                        try:
                            modified_data = json.loads(outline_file.read_text())
                            tasks = []
                            for section in modified_data.get("sections", []):
                                tasks.append(BlockTask(
                                    title=section["title"],
                                    description=section.get("description", ""),
                                    level=section.get("level", 1),
                                    require_mermaid=section.get("require_mermaid", False),
                                    require_table=section.get("require_table", False),
                                    require_examples=section.get("require_examples", True),
                                ))
                            logger.success(f"✓ Loaded {len(tasks)} sections from modified outline")
                            logger.info("")
                            logger.info("Modified outline:")
                            for i, task in enumerate(tasks, 1):
                                logger.info(f"  {i}. {task.title}")
                            logger.info("")

                            # Ask for final confirmation
                            confirm = input("Proceed with modified outline? [Y/n]: ").strip().lower()
                            if confirm == 'n':
                                logger.info("Cancelled by user.")
                                return 0
                        except (json.JSONDecodeError, KeyError) as e:
                            logger.error(f"✗ Failed to load modified outline: {e}")
                            logger.info("Using original outline...")
                    elif response not in ('', 'y', 'yes'):
                        logger.info(f"Unknown response: {response}")
                        logger.info("Proceeding with outline...")
                except (EOFError, KeyboardInterrupt):
                    logger.info("")
                    logger.info("Cancelled by user.")
                    return 0

            # Generate content
            from preciz.agents.teaching.orchestrator import AppendTool

            # Write header
            Path(output).write_text(f"# {topic}\n\n*Generated by Preciz*\n\n---\n\n")

            append_tool = AppendTool(output)
            context = ""

            logger.info("")
            logger.info(f"{'='*60}")
            logger.info(f"  GENERATING SECTIONS")
            logger.info(f"{'='*60}")
            logger.info("")

            for i, task in enumerate(tasks):
                logger.info(f"[{i+1}/{len(tasks)}] {task.title}")
                logger.info("-" * 60)

                # Track LLM calls for content generation
                section_start_time = time.time()

                # Build the prompt for logging
                from preciz.prompts.teaching.orchestrator import build_generate_section_prompt_with_preferences
                generation_prompt = build_generate_section_prompt_with_preferences(
                    topic=topic,
                    section_title=task.title,
                    description=task.description,
                    context=context,
                    preferences=preferences,
                )

                # Generate with preferences
                content = orchestrator.generate_tool.generate_with_preferences(
                    topic=topic,
                    section_title=task.title,
                    description=task.description,
                    context=context,
                    preferences=preferences,
                )

                section_time = time.time() - section_start_time

                # Log generation LLM call with full prompt
                logger.log_llm_request(
                    prompt=generation_prompt,
                    response=content[:500] + "..." if len(content) > 500 else content,
                    model=config.model,
                    temperature=0.7,
                    max_tokens=3000,
                    response_time_seconds=section_time,
                    success=True,
                )

                logger.info(f"  → Generated {len(content.split(chr(10)))} lines")

                # Review with preferences
                for iteration in range(max_iterations):
                    logger.info(f"  → Review {iteration + 1}/{max_iterations}")

                    # Build review prompt for logging
                    from preciz.prompts.teaching.orchestrator import build_review_prompt_with_preferences
                    review_prompt = build_review_prompt_with_preferences(content, task.title, preferences)

                    feedback = orchestrator.review_tool.review_with_preferences(
                        content, task.title, preferences
                    )

                    if feedback.get("passed", True):
                        logger.info("    ✓ Passed")
                        break
                    else:
                        issues = feedback.get("issues", [])
                        if len(issues) <= 2:
                            logger.info(f"    ⚠ {len(issues)} issue(s):")
                            for issue in issues[:2]:
                                logger.info(f"      - {issue[:60]}")
                        else:
                            logger.info(f"    ⚠ {len(issues)} issue(s)")

                        # Build improve prompt for logging
                        from preciz.prompts.teaching.orchestrator import build_improve_prompt_with_preferences
                        issues_list = feedback.get("issues", [])
                        suggestions_list = feedback.get("suggestions", [])
                        improve_prompt = build_improve_prompt_with_preferences(
                            content, issues_list, suggestions_list, preferences
                        )

                        # Log improvement with full prompt
                        improve_start_time = time.time()
                        improved = orchestrator.improve_tool.improve_with_preferences(
                            content, task.title, feedback, preferences
                        )
                        improve_time = time.time() - improve_start_time

                        logger.log_llm_request(
                            prompt=improve_prompt,
                            response=improved[:500] + "..." if len(improved) > 500 else improved,
                            model=config.model,
                            temperature=0.5,
                            max_tokens=3000,
                            response_time_seconds=improve_time,
                            success=True,
                        )
                        content = improved

                # Generate summary after content is approved
                logger.info(f"  → Generating summary...")
                try:
                    # Build summary prompt for logging
                    from preciz.prompts.teaching.orchestrator import build_summary_prompt
                    summary_prompt_for_log = build_summary_prompt(content, task.title, preferences)

                    summary_start_time = time.time()
                    summary = orchestrator.summary_tool.generate_summary(
                        content=content,
                        title=task.title,
                        preferences=preferences,
                    )
                    summary_time = time.time() - summary_start_time

                    task.summary = summary

                    logger.log_llm_request(
                        prompt=summary_prompt_for_log,
                        response=summary,
                        model=config.model,
                        temperature=0.3,
                        max_tokens=500,
                        response_time_seconds=summary_time,
                        success=True,
                    )
                    logger.info(f"    ✓ Summary generated")
                except Exception as e:
                    logger.warning(f"    ⚠ Summary generation failed: {e}")
                    task.summary = ""

                # Verify and convert Mermaid diagrams to PNG
                if preferences.include_diagrams:
                    from preciz.tools.mermaid.verifier import verify_and_convert_mermaid
                    content = verify_and_convert_mermaid(
                        content=content,
                        section_index=i,
                        section_title=task.title,
                        llm=orchestrator.llm,
                        images_dir="images",
                        logger=logger
                    )

                # Append
                total_lines = append_tool.append(content)
                task.completed = True

                # Build enhanced context for next section
                # Combine last 3 summaries + last 500 chars of content
                context_parts = []

                # Add last 3 section summaries
                num_summaries = 3
                start_idx = max(0, i + 1 - num_summaries)
                for j in range(start_idx, i + 1):
                    if tasks[j].summary:
                        context_parts.append(f"### {tasks[j].title}\n{tasks[j].summary}\n")

                # Add immediate previous content
                recent_content = content[-500:] if len(content) > 500 else content
                context_parts.append(f"**Immediate Previous Content**:\n```\n{recent_content}\n```")

                context = "\n".join(context_parts)

                logger.info(f"  → Appended (total: {total_lines} lines)")
                logger.info("")

            # Post-generation validation: check for incomplete sections
            logger.info(f"{'='*60}")
            logger.info(f"  VALIDATING OUTPUT")
            logger.info(f"{'='*60}")
            logger.info("")

            from preciz.tools.completion.checker import detect_incomplete_sections, print_incomplete_report

            final_content = Path(output).read_text()
            issues = detect_incomplete_sections(final_content)

            if issues:
                logger.warning(f"⚠️  Found {len(issues)} incomplete section(s)!")
                print_incomplete_report(issues)

                # Ask user if they want to regenerate
                try:
                    response = input("\nRegenerate incomplete sections? [Y/n]: ").strip().lower()
                    if response not in ('n', 'no'):
                        logger.info("Regenerating incomplete sections...")
                        # TODO: Implement targeted regeneration
                        logger.warning("Targeted regeneration not yet implemented.")
                        logger.warning("Tip: Re-run generation with higher --max-tokens or split into smaller sections")
                except (KeyboardInterrupt, EOFError):
                    logger.warning("\nSkipping regeneration")
            else:
                logger.success("✅ All sections complete!")

            logger.info("")
            logger.info(f"{'='*60}")
            logger.info(f"  COMPLETE")
            logger.info(f"{'='*60}")
            logger.info("")
            logger.info(f"Sections: {len(tasks)}")
            logger.info(f"Lines: {total_lines}")
            logger.info(f"Output: {output}")
            logger.info("")
            logger.info(f"Log file: {logger.log_file}")

        return 0

    except KeyboardInterrupt:
        logger.error("")
        logger.error("Interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"")
        logger.error(f"Error: {e}")
        # Exception is automatically logged by the context manager
        return 1


if __name__ == "__main__":
    sys.exit(main())
