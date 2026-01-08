"""
Orchestrator-based long document generator.

Architecture:
1. Orchestrator maintains a todo list of blocks to generate
2. For each block:
   - Calls GENERATE tool to create content
   - Calls APPEND tool to add to document
   - Updates progress
3. Can resume from any point if interrupted

This is cleaner than monolithic generation.
"""

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from preciz.core import Config, LLMClient, Message, LLMResponse
from preciz.prompts.teaching import orchestrator as orch_prompts
from .preferences import ContentPreferences


# ========== TOOLS ==========

class GenerateTool:
    """Tool to generate a content block."""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def generate(
        self,
        topic: str,
        section_title: str,
        description: str,
        context: str,
        include_mermaid: bool = False,
        include_table: bool = False,
        include_examples: bool = True,
    ) -> str:
        """
        Generate a content block.

        Args:
            topic: Overall document topic
            section_title: Title of this section
            description: What this section covers
            context: What came before (for continuity)
            include_mermaid: Whether to include mermaid diagram
            include_table: Whether to include table
            include_examples: Whether to include code examples

        Returns:
            Generated markdown content
        """
        prompt = orch_prompts.build_generate_section_prompt(
            topic, section_title, description, context, include_mermaid, include_table, include_examples
        )

        messages = [
            Message(
                role="system",
                content="You are an expert technical writer creating educational content.",
            ),
            Message(role="user", content=prompt),
        ]

        response = self.llm.complete(messages, temperature=0.7, max_tokens=8000)
        return response.content

    def generate_with_preferences(
        self,
        topic: str,
        section_title: str,
        description: str,
        context: str,
        preferences: ContentPreferences,
    ) -> str:
        """
        Generate a content block using user preferences.

        Args:
            topic: Overall document topic
            section_title: Title of this section
            description: What this section covers
            context: What came before (for continuity)
            preferences: User content preferences

        Returns:
            Generated markdown content
        """
        prompt = orch_prompts.build_generate_section_prompt_with_preferences(
            topic, section_title, description, context, preferences
        )

        messages = [
            Message(
                role="system",
                content="You are an expert technical writer creating educational content.",
            ),
            Message(role="user", content=prompt),
        ]

        response = self.llm.complete(messages, temperature=0.7, max_tokens=8000)
        return response.content


class AppendTool:
    """Tool to append content to document."""

    def __init__(self, output_file: str):
        self.output_file = Path(output_file)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize file if needed
        if not self.output_file.exists():
            self.output_file.write_text("")

    def append(self, content: str) -> int:
        """
        Append content to the document.

        Args:
            content: Markdown content to append

        Returns:
            New line count in the document
        """
        # Get current line count before append
        before_count = len(self.output_file.read_text().split("\n")) if self.output_file.exists() else 0

        # Verify file exists before appending
        if not self.output_file.exists():
            raise FileNotFoundError(f"Output file {self.output_file} disappeared before append!")

        # Append content (use 'a' mode to append, not overwrite)
        with open(self.output_file, "a", encoding="utf-8") as f:
            f.write(content)
            if not content.endswith("\n"):
                f.write("\n")
            f.write("\n")  # Spacer between sections

        # Get new line count after append
        after_count = len(self.output_file.read_text().split("\n"))

        # Debug: verify append actually worked
        content_lines = len(content.split("\n"))
        expected_count = before_count + content_lines + 2  # +2 for the extra newlines

        if after_count < expected_count * 0.5:  # If significantly less than expected
            # Something went wrong - file might have been truncated
            raise IOError(
                f"Append failed: expected ~{expected_count} lines, got {after_count}. "
                f"Before: {before_count}, Content: {content_lines}, After: {after_count}. "
                f"File may have been truncated or overwritten."
            )

        return after_count

    def get_line_count(self) -> int:
        """Get current line count of document."""
        if not self.output_file.exists():
            return 0
        return len(self.output_file.read_text().split("\n"))


class ReviewTool:
    """Tool to review a content block."""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def review(self, content: str, title: str) -> dict:
        """
        Review content for quality.

        Args:
            content: Content to review
            title: Section title

        Returns:
            Dict with passed, issues, suggestions
        """
        prompt = orch_prompts.build_review_prompt(content, title)

        messages = [
            Message(role="system", content="You are a technical content reviewer."),
            Message(role="user", content=prompt),
        ]

        response = self.llm.complete(messages, temperature=0.3, max_tokens=1000)

        # Parse JSON
        json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return {"passed": True, "issues": [], "suggestions": []}

    def review_with_preferences(
        self,
        content: str,
        title: str,
        preferences: ContentPreferences,
    ) -> dict:
        """
        Review content for quality using user preferences.

        Args:
            content: Content to review
            title: Section title
            preferences: User content preferences

        Returns:
            Dict with passed, issues, suggestions
        """
        prompt = orch_prompts.build_review_prompt_with_preferences(content, title, preferences)

        messages = [
            Message(role="system", content="You are a technical content reviewer."),
            Message(role="user", content=prompt),
        ]

        response = self.llm.complete(messages, temperature=0.3, max_tokens=1000)

        # Parse JSON
        json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return {"passed": True, "issues": [], "suggestions": []}


class ImproveTool:
    """Tool to improve content based on feedback."""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def improve(self, content: str, title: str, feedback: dict) -> str:
        """
        Improve content based on review feedback.

        Args:
            content: Original content
            title: Section title
            feedback: Review feedback

        Returns:
            Improved content
        """
        if feedback.get("passed", True):
            return content

        issues = "\n".join(f"- {i}" for i in feedback.get("issues", []))
        suggestions = "\n".join(f"- {s}" for s in feedback.get("suggestions", []))

        prompt = orch_prompts.build_improve_prompt(content, issues, suggestions)

        messages = [
            Message(role="system", content="You improve technical content."),
            Message(role="user", content=prompt),
        ]

        response = self.llm.complete(messages, temperature=0.5, max_tokens=8000)
        return response.content

    def improve_with_preferences(
        self,
        content: str,
        title: str,
        feedback: dict,
        preferences: ContentPreferences,
    ) -> str:
        """
        Improve content based on review feedback using user preferences.

        Args:
            content: Original content
            title: Section title
            feedback: Review feedback
            preferences: User content preferences

        Returns:
            Improved content
        """
        if feedback.get("passed", True):
            return content

        issues = feedback.get("issues", [])
        suggestions = feedback.get("suggestions", [])

        prompt = orch_prompts.build_improve_prompt_with_preferences(
            content, issues, suggestions, preferences
        )

        messages = [
            Message(role="system", content="You improve technical content."),
            Message(role="user", content=prompt),
        ]

        response = self.llm.complete(messages, temperature=0.5, max_tokens=8000)
        return response.content


class SummaryTool:
    """Tool to generate section summaries."""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def generate_summary(
        self,
        content: str,
        title: str,
        preferences: ContentPreferences | None = None,
    ) -> str:
        """
        Generate a 3-5 bullet point summary of section content.

        Args:
            content: Section content to summarize
            title: Section title
            preferences: Optional content preferences for context-aware summarization

        Returns:
            Summary as bullet points (each starting with "- ")
        """
        prompt = orch_prompts.build_summary_prompt(content, title, preferences)

        messages = [
            Message(role="system", content="You are an expert technical writer creating educational content summaries."),
            Message(role="user", content=prompt),
        ]

        response = self.llm.complete(messages, temperature=0.3, max_tokens=500)
        return response.content


# ========== ORCHESTRATOR ==========

@dataclass
class BlockTask:
    """A task in the orchestrator's todo list."""

    title: str
    description: str
    level: int
    require_mermaid: bool = False
    require_table: bool = False
    require_examples: bool = True
    completed: bool = False
    content: str = ""
    summary: str = ""  # LLM-generated section summary (3-5 bullet points)


@dataclass
class OrchestrationState:
    """State for orchestration (can be saved/resumed)."""

    topic: str
    output_file: str
    target_lines: int
    tasks: list[BlockTask] = field(default_factory=list)
    current_task_index: int = 0
    total_lines: int = 0
    start_time: float = 0

    def save(self, path: str) -> None:
        """Save state to file for resume capability."""
        data = {
            "topic": self.topic,
            "output_file": self.output_file,
            "target_lines": self.target_lines,
            "current_task_index": self.current_task_index,
            "total_lines": self.total_lines,
            "start_time": self.start_time,
            "tasks": [
                {
                    "title": t.title,
                    "description": t.description,
                    "level": t.level,
                    "require_mermaid": t.require_mermaid,
                    "require_table": t.require_table,
                    "require_examples": t.require_examples,
                    "completed": t.completed,
                    "summary": t.summary,
                }
                for t in self.tasks
            ],
        }
        Path(path).write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: str, llm: LLMClient) -> "OrchestrationState":
        """Load state from file."""
        data = json.loads(Path(path).read_text())
        state = cls(
            topic=data["topic"],
            output_file=data["output_file"],
            target_lines=data["target_lines"],
            current_task_index=data["current_task_index"],
            total_lines=data["total_lines"],
            start_time=data["start_time"],
        )
        for t in data["tasks"]:
            state.tasks.append(
                BlockTask(
                    title=t["title"],
                    description=t["description"],
                    level=t["level"],
                    require_mermaid=t.get("require_mermaid", False),
                    require_table=t.get("require_table", False),
                    require_examples=t.get("require_examples", True),
                    completed=t["completed"],
                    summary=t.get("summary", ""),  # Load with fallback for old state files
                )
            )
        return state


class DocumentOrchestrator:
    """
    Orchestrates long document generation using tools.

    The orchestrator:
    1. Creates a todo list of sections
    2. For each section: generates -> reviews -> improves -> appends
    3. Tracks progress and can resume
    """

    def __init__(self, config: Config | None = None) -> None:
        """Initialize orchestrator with tools."""
        self.config = config or Config.from_env()
        self.llm = LLMClient(self.config)

        # Tools
        self.generate_tool = GenerateTool(self.llm)
        self.review_tool = ReviewTool(self.llm)
        self.improve_tool = ImproveTool(self.llm)
        self.summary_tool = SummaryTool(self.llm)

    def create_todo_list(self, topic: str, target_lines: int = 10000) -> list[BlockTask]:
        """
        Create a todo list of sections for the topic.

        Uses LLM to generate a detailed outline, then converts to tasks.
        """
        prompt = orch_prompts.build_create_outline_prompt(topic, target_lines)

        response = self.llm.complete(
            [Message(role="user", content=prompt)],
            temperature=0.5,
            max_tokens=2000,
        )

        # Parse outline - extract JSON from markdown code blocks
        json_match = re.search(r"```json\s*\n?(\{.*?\})\s*```", response.content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if not json_match:
                raise ValueError("Could not parse outline")
            json_str = json_match.group(0)

        # Clean up common JSON issues
        json_str = json_str.replace("\n", " ")
        data = json.loads(json_str)

        tasks = []
        for section in data.get("sections", []):
            tasks.append(
                BlockTask(
                    title=section["title"],
                    description=section.get("description", ""),
                    level=section.get("level", 1),
                    require_mermaid=section.get("require_mermaid", False),
                    require_table=section.get("require_table", False),
                    require_examples=section.get("require_examples", True),
                )
            )

        return tasks

    def generate_document(
        self,
        topic: str,
        output_file: str,
        target_lines: int = 10000,
        max_iterations: int = 2,
        state_file: str | None = None,
    ) -> str:
        """
        Generate a long document using orchestrator pattern.

        Args:
            topic: Document topic
            output_file: Output markdown file
            target_lines: Target line count
            max_iterations: Max review iterations per block
            state_file: Optional state file for resume capability

        Returns:
            Output file path
        """
        start_time = time.time()

        print(f"\n{'='*70}")
        print(f"  ORCHESTRATOR: Long Document Generator")
        print(f"{'='*70}")
        print(f"\nTopic: {topic}")
        print(f"Target: {target_lines} lines")
        print(f"Output: {output_file}")

        # Create or load state
        if state_file and Path(state_file).exists():
            print(f"\nResuming from {state_file}")
            state = OrchestrationState.load(state_file, self.llm)
        else:
            print("\nCreating todo list...")
            tasks = self.create_todo_list(topic, target_lines)
            print(f"  → Created {len(tasks)} tasks")

            state = OrchestrationState(
                topic=topic,
                output_file=output_file,
                target_lines=target_lines,
                tasks=tasks,
                start_time=start_time,
            )

            # Write header to output file
            Path(output_file).write_text(f"# {topic}\n\n*Generated by Preciz*\n\n---\n\n")

        # Initialize append tool
        append_tool = AppendTool(output_file)
        state.total_lines = append_tool.get_line_count()

        # Process each task
        print(f"\n{'='*70}")
        print(f"  GENERATING SECTIONS")
        print(f"{'='*70}\n")

        for i in range(state.current_task_index, len(state.tasks)):
            task = state.tasks[i]

            print(f"[{i+1}/{len(state.tasks)}] {task.title}")
            print("-" * 60)

            # Get context (previous content summary)
            context = ""
            if i > 0:
                prev_content = Path(output_file).read_text()
                context = prev_content[-1000:]

            # Generate
            print("  → Generating...")
            content = self.generate_tool.generate(
                topic=state.topic,
                section_title=task.title,
                description=task.description,
                context=context,
                include_mermaid=task.require_mermaid,
                include_table=task.require_table,
                include_examples=task.require_examples,
            )

            print(f"    Generated {len(content.split(chr(10)))} lines")

            # Review and improve
            for iteration in range(max_iterations):
                print(f"  → Review {iteration + 1}/{max_iterations}")
                feedback = self.review_tool.review(content, task.title)

                if feedback.get("passed", True):
                    print("    ✓ Passed")
                    break
                else:
                    issues = feedback.get("issues", [])
                    print(f"    ⚠ {len(issues)} issue(s)")
                    content = self.improve_tool.improve(content, task.title, feedback)

            # Append
            state.total_lines = append_tool.append(content)
            task.completed = True
            state.current_task_index = i + 1

            print(f"  → Appended (total: {state.total_lines} lines)\n")

            # Save state periodically
            if state_file and (i % 5 == 0 or i == len(state.tasks) - 1):
                state.save(state_file)
                print(f"  → State saved to {state_file}\n")

        elapsed = time.time() - start_time

        print(f"{'='*70}")
        print(f"  COMPLETE")
        print(f"{'='*70}")
        print(f"\nSections: {len(state.tasks)}")
        print(f"Lines: {state.total_lines}")
        print(f"Time: {elapsed:.1f}s")
        print(f"Output: {output_file}\n")

        # Clean up state file
        if state_file and Path(state_file).exists():
            Path(state_file).unlink()

        return output_file


def generate_long_document(
    topic: str,
    output_file: str,
    target_lines: int = 10000,
    config: Config | None = None,
) -> str:
    """
    Convenience function for orchestration-based generation.

    Args:
        topic: Document topic
        output_file: Output file
        target_lines: Target line count
        config: Optional config

    Returns:
        Output file path
    """
    orchestrator = DocumentOrchestrator(config)
    return orchestrator.generate_document(topic, output_file, target_lines)
