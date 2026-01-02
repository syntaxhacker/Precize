"""Content generation module for creating long educational documents."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .agent import PrecizAgent
from .config import Config
from .file_ops import read_file, write_file
from .llm import Message
from .prompts import generator as gen_prompts

# Re-export types from prompts for backward compatibility
SectionBlock = gen_prompts.SectionBlock
ReviewFeedback = gen_prompts.ReviewFeedback
ContentSpec = gen_prompts.ContentSpec


@dataclass(frozen=True)
class QualityChecklist:
    """Checklist for validating educational content quality."""

    require_mermaid_diagrams: bool = True
    require_tables: bool = True
    require_ascii_examples: bool = True
    require_code_examples: bool = True
    require_practical_exercises: bool = True
    min_examples_per_section: int = 2
    min_section_depth: int = 2


class ContentGenerator:
    """Generate long educational content with iterative review."""

    def __init__(self, config: Config | None = None) -> None:
        """Initialize content generator."""
        self.config = config or Config.from_env()
        self.agent = PrecizAgent(self.config)
        self.checklist = QualityChecklist()

    def _build_generation_prompt(self, spec: ContentSpec) -> str:
        """Build prompt for content generation."""
        return gen_prompts.build_generation_prompt(spec)

    def _build_review_prompt(self, block: SectionBlock, full_content: str) -> str:
        """Build prompt for reviewing a content block."""
        return gen_prompts.build_review_prompt(block, self.checklist.min_examples_per_section)

    def _build_improve_prompt(
        self, block: SectionBlock, feedback: ReviewFeedback
    ) -> str:
        """Build prompt for improving a content block."""
        return gen_prompts.build_improve_prompt(block, feedback)

    def _parse_review_response(self, response: str) -> ReviewFeedback:
        """Parse review agent response."""
        # Extract JSON
        json_match = re.search(r"```json\s*\n?(\{.*?\})\s*```", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                return ReviewFeedback(passed=False, issues=["Could not parse review"])

        import json
        try:
            data = json.loads(json_str)
            return ReviewFeedback(
                passed=data.get("passed", False),
                issues=data.get("issues", []),
                suggestions=data.get("suggestions", []),
            )
        except json.JSONDecodeError:
            return ReviewFeedback(passed=False, issues=["Invalid JSON in review"])

    def _parse_improve_response(self, response: str) -> str:
        """Parse improvement response."""
        json_match = re.search(r"```json\s*\n?(\{.*?\})\s*```", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("Could not parse improvement response")

        import json
        try:
            data = json.loads(json_str)
            return data.get("new_content", "")
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in improvement response")

    def _split_into_blocks(self, content: str) -> list[SectionBlock]:
        """Split content into section blocks based on headings."""
        lines = content.split("\n")
        blocks = []
        current_block: list[str] = []
        current_heading = ""
        current_level = 1
        line_start = 0

        for i, line in enumerate(lines):
            # Check for heading
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if heading_match:
                # Save previous block
                if current_block:
                    blocks.append(
                        SectionBlock(
                            content="\n".join(current_block).strip(),
                            line_start=line_start,
                            line_end=i - 1,
                            heading=current_heading,
                            level=current_level,
                        )
                    )

                # Start new block
                current_level = len(heading_match.group(1))
                current_heading = heading_match.group(2)
                current_block = [line]
                line_start = i
            else:
                current_block.append(line)

        # Save last block
        if current_block:
            blocks.append(
                SectionBlock(
                    content="\n".join(current_block).strip(),
                    line_start=line_start,
                    line_end=len(lines) - 1,
                    heading=current_heading,
                    level=current_level,
                )
            )

        return blocks

    def generate_content(self, spec: ContentSpec) -> str:
        """Generate initial content based on specification."""
        prompt = self._build_generation_prompt(spec)

        messages = [
            Message(role="system", content="You are an expert educational content creator."),
            Message(role="user", content=prompt),
        ]

        response = self.agent.llm.complete(messages, temperature=0.7, max_tokens=8192)
        return response.content

    def review_section(self, block: SectionBlock, full_content: str) -> ReviewFeedback:
        """Review a single section against quality checklist."""
        prompt = self._build_review_prompt(block, full_content)

        messages = [
            Message(role="system", content="You are a strict educational content reviewer."),
            Message(role="user", content=prompt),
        ]

        response = self.agent.llm.complete(messages, temperature=0.3)
        return self._parse_review_response(response.content)

    def improve_section(
        self, block: SectionBlock, feedback: ReviewFeedback
    ) -> str:
        """Improve a section based on review feedback."""
        prompt = self._build_improve_prompt(block, feedback)

        messages = [
            Message(role="system", content="You are an expert content improver."),
            Message(role="user", content=prompt),
        ]

        response = self.agent.llm.complete(messages, temperature=0.5, max_tokens=4096)
        return self._parse_improve_response(response.content)

    def generate_with_review(
        self,
        spec: ContentSpec,
        max_iterations: int = 3,
        output_file: str | None = None,
    ) -> str:
        """
        Generate content with iterative review and improvement.

        Args:
            spec: Content specification
            max_iterations: Max review-improve cycles per section
            output_file: Optional file to save final content

        Returns:
            Final improved content
        """
        print(f"\n{'='*60}")
        print(f"Generating: {spec.topic}")
        print(f"{'='*60}\n")

        # Step 1: Generate initial content
        print("Step 1: Generating initial content...")
        content = self.generate_content(spec)

        if output_file:
            write_file(output_file, content)
            print(f"  → Saved to {output_file}")

        # Step 2: Split into blocks
        print("\nStep 2: Analyzing structure...")
        blocks = self._split_into_blocks(content)
        print(f"  → Found {len(blocks)} sections")

        # Step 3: Review and improve each block
        print("\nStep 3: Reviewing and improving sections...")
        improved_blocks = []

        for i, block in enumerate(blocks, 1):
            print(f"\n  [{i}/{len(blocks)}] Reviewing: {block.heading[:50]}")

            iteration = 0
            current_content = block.content

            while iteration < max_iterations:
                # Create updated block for review
                review_block = SectionBlock(
                    content=current_content,
                    line_start=block.line_start,
                    line_end=block.line_end,
                    heading=block.heading,
                    level=block.level,
                )

                # Review
                feedback = self.review_section(review_block, content)

                if feedback.passed:
                    print(f"    ✓ Passed (iteration {iteration + 1})")
                    improved_blocks.append(current_content)
                    break
                else:
                    print(f"    ⚠ Issues found: {len(feedback.issues)}")
                    for issue in feedback.issues[:2]:
                        print(f"      - {issue}")

                    # Improve
                    current_content = self.improve_section(review_block, feedback)
                    iteration += 1

                    if iteration >= max_iterations:
                        print(f"    → Max iterations reached, using current version")
                        improved_blocks.append(current_content)

        # Step 4: Assemble final content
        print("\nStep 4: Assembling final content...")
        final_content = "\n\n".join(improved_blocks)

        if output_file:
            write_file(output_file, final_content)
            print(f"  → Final version saved to {output_file}")

        print(f"\n{'='*60}")
        print("Generation complete!")
        print(f"{'='*60}\n")

        return final_content


def generate_tutorial(
    topic: str,
    output_file: str | None = None,
    **spec_kwargs,
) -> str:
    """
    Convenience function to generate a tutorial.

    Args:
        topic: Topic to generate tutorial for
        output_file: Optional file path to save output
        **spec_kwargs: Additional ContentSpec arguments

    Returns:
        Generated content
    """
    spec = ContentSpec(topic=topic, **spec_kwargs)
    generator = ContentGenerator()
    return generator.generate_with_review(spec, output_file=output_file)
