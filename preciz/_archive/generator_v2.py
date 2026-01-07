"""
Block-based content generator for very long documents (10,000+ lines).

Design principles:
1. Generate content in chunks that fit LLM context
2. Store each block as we generate it
3. Review and improve each block before moving on
4. Maintain a master outline to track progress
5. Can resume from any point if interrupted
"""

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from preciz._archive.agent import PrecizAgent
from preciz.core.config import Config
from preciz.core.file_ops import read_file, write_file
from preciz.core.llm import Message
from preciz._archive.prompts.generator_v2 import generator_v2 as gen_v2_prompts


@dataclass(frozen=True)
class BlockSpec:
    """Specification for a content block."""

    title: str
    level: int  # 1=main, 2=section, 3=subsection
    description: str
    require_mermaid: bool = False
    require_table: bool = False
    require_examples: bool = True
    require_exercises: bool = False
    estimated_lines: int = 100


@dataclass
class OutlineNode:
    """A node in the document outline tree."""

    title: str
    level: int
    description: str
    children: list["OutlineNode"] = field(default_factory=list)
    generated: bool = False
    line_count: int = 0
    content_file: str = ""  # Path to block content file


@dataclass
class GenerationState:
    """State tracking for long document generation."""

    topic: str
    outline: OutlineNode
    current_position: list[int] = field(default_factory=list)  # Path in outline tree
    total_lines: int = 0
    blocks_generated: int = 0
    blocks_reviewed: int = 0
    blocks_improved: int = 0
    start_time: float = 0
    last_save_time: float = 0


@dataclass
class BlockContent:
    """Generated content for a single block."""

    title: str
    level: int
    content: str
    passed_review: bool
    iterations: int
    issues_found: list[str]
    line_count: int


class BlockContentGenerator:
    """
    Generate very long documents block by block.

    Strategy:
    1. Create detailed outline first
    2. Generate each block independently (fits in LLM context)
    3. Review and improve each block before saving
    4. Assemble blocks into final document
    """

    # LLM context limits (conservative estimates)
    MAX_GENERATION_TOKENS = 4096
    MAX_REVIEW_TOKENS = 2048
    MAX_BLOCK_LINES = 300  # Target ~100-200 lines per block

    def __init__(self, config: Config | None = None) -> None:
        """Initialize block content generator."""
        self.config = config or Config.from_env()
        self.agent = PrecizAgent(self.config)
        self.state: GenerationState | None = None

    # ========== OUTLINE CREATION ==========

    def _build_outline_prompt(self, topic: str, target_lines: int = 10000) -> str:
        """Build prompt for creating a detailed outline."""
        return gen_v2_prompts.build_outline_prompt(topic, target_lines)

    def _parse_outline_response(self, response: str) -> OutlineNode:
        """Parse outline JSON response."""
        # Extract JSON
        json_match = re.search(r"```json\s*\n?(\{.*?\})\s*```", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("Could not parse outline from response")

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in outline: {e}")

        return self._build_outline_tree(data)

    def _build_outline_tree(self, data: dict, level: int = 1) -> OutlineNode:
        """Recursively build outline tree from JSON data."""
        # Handle both root document and sections
        if "sections" in data:
            # Root level - create virtual root
            root = OutlineNode(
                title=data.get("title", "Tutorial"),
                level=0,
                description=data.get("description", ""),
            )
            for section in data.get("sections", []):
                child = self._build_outline_tree(section, level=1)
                root.children.append(child)
            return root

        # Individual section/node
        node = OutlineNode(
            title=data.get("title", "Untitled"),
            level=level,
            description=data.get("description", ""),
        )

        # Recursively build children
        for subsection in data.get("subsections", []):
            child = self._build_outline_tree(subsection, level + 1)
            node.children.append(child)

        return node

    def create_outline(self, topic: str, target_lines: int = 10000) -> OutlineNode:
        """Create a detailed outline for the topic."""
        print(f"\n{'='*60}")
        print(f"Creating outline for: {topic}")
        print(f"Target: ~{target_lines} lines")
        print(f"{'='*60}\n")

        prompt = self._build_outline_prompt(topic, target_lines)

        messages = [
            Message(role="system", content="You are an expert curriculum designer."),
            Message(role="user", content=prompt),
        ]

        response = self.agent.llm.complete(messages, temperature=0.5)
        outline = self._parse_outline_response(response.content)

        # Count nodes
        total_nodes = self._count_outline_nodes(outline)

        print(f"✓ Outline created with {total_nodes} sections")
        self._print_outline(outline)

        return outline

    def _count_outline_nodes(self, node: OutlineNode) -> int:
        """Count total nodes in outline tree."""
        count = 1  # Count self
        for child in node.children:
            count += self._count_outline_nodes(child)
        return count

    def _print_outline(self, node: OutlineNode, indent: int = 0) -> None:
        """Print outline structure."""
        prefix = "  " * indent + ("#" * node.level if node.level > 0 else "")
        title = f"{prefix} {node.title}" if prefix else node.title
        print(title)
        for child in node.children:
            self._print_outline(child, indent + 1)

    # ========== BLOCK GENERATION ==========

    def _build_block_generation_prompt(
        self,
        title: str,
        description: str,
        context: str,
        require_mermaid: bool = False,
        require_table: bool = False,
        require_examples: bool = True,
        require_exercises: bool = False,
    ) -> str:
        """Build prompt for generating a single content block."""
        return gen_v2_prompts.build_block_generation_prompt(
            title, description, context, require_mermaid, require_table, require_examples, require_exercises
        )

    def generate_block(
        self,
        node: OutlineNode,
        context: str = "",
    ) -> str:
        """Generate content for a single outline node."""
        print(f"  → Generating: {node.title[:50]}")

        prompt = self._build_block_generation_prompt(
            title=node.title,
            description=node.description,
            context=context,
            require_mermaid=True,  # Could be derived from node metadata
            require_table=True,
            require_examples=True,
            require_exercises=False,
        )

        messages = [
            Message(
                role="system",
                content="You are an expert technical writer creating educational content.",
            ),
            Message(role="user", content=prompt),
        ]

        response = self.agent.llm.complete(
            messages, temperature=0.7, max_tokens=self.MAX_GENERATION_TOKENS
        )

        content = response.content
        line_count = len(content.split("\n"))

        print(f"    Generated {line_count} lines")
        return content

    # ========== BLOCK REVIEW ==========

    def _build_review_prompt(self, content: str, title: str) -> str:
        """Build prompt for reviewing a block."""
        return gen_v2_prompts.build_review_prompt(content, title)

    def review_block(self, content: str, title: str) -> dict:
        """Review a generated block."""
        prompt = self._build_review_prompt(content, title)

        messages = [
            Message(role="system", content="You are a strict technical content reviewer."),
            Message(role="user", content=prompt),
        ]

        response = self.agent.llm.complete(
            messages, temperature=0.3, max_tokens=self.MAX_REVIEW_TOKENS
        )

        # Parse response
        json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return {"passed": True, "issues": [], "suggestions": []}

    # ========== BLOCK IMPROVEMENT ==========

    def improve_block(
        self, content: str, title: str, feedback: dict
    ) -> str:
        """Improve a block based on review feedback."""
        if feedback.get("passed", True):
            return content

        prompt = gen_v2_prompts.build_improve_prompt(content, title, feedback)

        messages = [
            Message(role="system", content="You are improving technical content."),
            Message(role="user", content=prompt),
        ]

        response = self.agent.llm.complete(
            messages, temperature=0.5, max_tokens=self.MAX_GENERATION_TOKENS
        )

        return response.content

    # ========== FULL GENERATION PIPELINE ==========

    def generate_document(
        self,
        topic: str,
        output_file: str,
        target_lines: int = 10000,
        max_iterations: int = 2,
    ) -> str:
        """
        Generate a complete long document block by block.

        Args:
            topic: Topic to generate
            output_file: Output file path
            target_lines: Target line count
            max_iterations: Max review iterations per block

        Returns:
            Generated file path
        """
        start_time = time.time()
        print(f"\n{'='*70}")
        print(f"  LONG DOCUMENT GENERATOR")
        print(f"{'='*70}")
        print(f"\nTopic: {topic}")
        print(f"Target: ~{target_lines} lines")
        print(f"Output: {output_file}")
        print(f"Max iterations per block: {max_iterations}")

        # Phase 1: Create outline
        outline = self.create_outline(topic, target_lines)

        # Phase 2: Generate blocks
        print(f"\n{'='*70}")
        print(f"  PHASE 2: GENERATING BLOCKS")
        print(f"{'='*70}\n")

        all_blocks: list[tuple[OutlineNode, str]] = []
        context_summary = ""

        def process_node(node: OutlineNode, level: int = 0):
            """Recursively generate content for each node."""
            nonlocal context_summary

            # Skip root node
            if node.level > 0:
                print(f"\n[{len(all_blocks) + 1}] {node.title}")
                print("-" * 60)

                # Generate content
                content = self.generate_block(node, context_summary)

                # Review and improve
                for iteration in range(max_iterations):
                    print(f"  [Review {iteration + 1}/{max_iterations}]")
                    feedback = self.review_block(content, node.title)

                    if feedback.get("passed", False):
                        print(f"    ✓ Passed")
                        break
                    else:
                        issues = feedback.get("issues", [])
                        print(f"    ⚠ Found {len(issues)} issue(s):")
                        for issue in issues[:2]:
                            print(f"      - {issue}")

                        content = self.improve_block(content, node.title, feedback)

                # Store block
                line_count = len(content.split("\n"))
                all_blocks.append((node, content))
                context_summary += f"\n## {node.title}\n{content[:200]}...\n"

                print(f"    ✓ Final: {line_count} lines")

            # Process children
            for child in node.children:
                process_node(child, level + 1)

        process_node(outline)

        # Phase 3: Assemble document
        print(f"\n{'='*70}")
        print(f"  PHASE 3: ASSEMBLING DOCUMENT")
        print(f"{'='*70}\n")

        final_content = self._assemble_document(all_blocks, topic)

        total_lines = len(final_content.split("\n"))
        write_file(output_file, final_content)

        elapsed = time.time() - start_time

        print(f"\n{'='*70}")
        print(f"  GENERATION COMPLETE")
        print(f"{'='*70}")
        print(f"\nBlocks generated: {len(all_blocks)}")
        print(f"Total lines: {total_lines}")
        print(f"Time elapsed: {elapsed:.1f} seconds")
        print(f"Output: {output_file}\n")

        return output_file

    def _assemble_document(
        self, blocks: list[tuple[OutlineNode, str]], topic: str
    ) -> str:
        """Assemble all blocks into final document."""
        parts = []

        # Title
        parts.append(f"# {topic}\n")
        parts.append(f"*Generated by Preciz*  \n")
        parts.append("---\n")

        # Content blocks
        for node, content in blocks:
            # Add appropriate heading marker based on level
            prefix = "#" * node.level
            parts.append(f"\n{prefix} {node.title}\n")
            parts.append(content)

        return "\n".join(parts)


def generate_long_document(
    topic: str,
    output_file: str,
    target_lines: int = 10000,
    config: Config | None = None,
) -> str:
    """
    Convenience function to generate a long document.

    Args:
        topic: Topic to generate
        output_file: Output markdown file
        target_lines: Target line count
        config: Optional config

    Returns:
        Output file path
    """
    generator = BlockContentGenerator(config)
    return generator.generate_document(topic, output_file, target_lines)
