"""Tests for block-based content generator."""

import json
from unittest.mock import MagicMock, patch

import pytest

from preciz.generator_v2 import (
    BlockContentGenerator,
    OutlineNode,
    GenerationState,
    BlockContent,
    generate_long_document,
)
from preciz.config import Config
from preciz.llm import LLMResponse, Message


@pytest.fixture
def mock_config():
    """Create a mock config."""
    return Config(
        api_key="test-key",
        model="test-model",
        provider="openrouter",
        base_url="https://test.api/v1",
    )


@pytest.fixture
def generator(mock_config):
    """Create a generator with mock config."""
    return BlockContentGenerator(mock_config)


class TestOutlineNode:
    """Test OutlineNode dataclass."""

    def test_create_node(self):
        """Test creating an outline node."""
        node = OutlineNode(
            title="Introduction",
            level=1,
            description="Intro to the topic",
        )
        assert node.title == "Introduction"
        assert node.level == 1
        assert len(node.children) == 0

    def test_node_with_children(self):
        """Test node with child nodes."""
        parent = OutlineNode(title="Parent", level=1, description="Parent section")
        child = OutlineNode(title="Child", level=2, description="Child section")
        parent.children.append(child)

        assert len(parent.children) == 1
        assert parent.children[0].title == "Child"


class TestBlockContentGenerator:
    """Test BlockContentGenerator class."""

    def test_init(self, generator):
        """Test generator initialization."""
        assert generator.config is not None
        assert generator.agent is not None
        assert generator.state is None

    def test_build_outline_prompt(self, generator):
        """Test outline prompt building."""
        prompt = generator._build_outline_prompt("Python Basics", 5000)

        assert "Python Basics" in prompt
        assert "5000" in prompt
        assert "hierarchical" in prompt.lower()
        assert "JSON" in prompt

    def test_parse_outline_response(self, generator):
        """Test parsing outline from LLM response."""
        response = """
```json
{
  "title": "Python Tutorial",
  "sections": [
    {
      "title": "Introduction",
      "level": 1,
      "description": "Basic intro",
      "subsections": []
    }
  ]
}
```
"""
        outline = generator._parse_outline_response(response)

        assert outline.title == "Python Tutorial"
        assert len(outline.children) == 1
        assert outline.children[0].title == "Introduction"

    def test_parse_outline_raw_json(self, generator):
        """Test parsing raw JSON without code blocks."""
        response = '{"title": "Test", "sections": []}'
        outline = generator._parse_outline_response(response)
        assert outline.title == "Test"

    def test_build_outline_tree(self, generator):
        """Test building outline tree from dict."""
        data = {
            "title": "Root",
            "sections": [
                {
                    "title": "Section 1",
                    "level": 1,
                    "description": "First section",
                    "subsections": [
                        {
                            "title": "Subsection 1.1",
                            "level": 2,
                            "description": "Sub",
                            "subsections": [],
                        }
                    ],
                }
            ],
        }

        tree = generator._build_outline_tree(data)

        assert tree.title == "Root"
        assert len(tree.children) == 1
        assert tree.children[0].title == "Section 1"
        assert len(tree.children[0].children) == 1
        assert tree.children[0].children[0].title == "Subsection 1.1"

    def test_count_outline_nodes(self, generator):
        """Test counting nodes in outline."""
        outline = OutlineNode(title="Root", level=0, description="")
        outline.children = [
            OutlineNode(title="C1", level=1, description=""),
            OutlineNode(title="C2", level=1, description=""),
        ]
        outline.children[1].children = [
            OutlineNode(title="C2.1", level=2, description="")
        ]

        count = generator._count_outline_nodes(outline)
        assert count == 4  # Root + C1 + C2 + C2.1

    def test_build_block_generation_prompt(self, generator):
        """Test block generation prompt."""
        prompt = generator._build_block_generation_prompt(
            title="Functions",
            description="All about functions",
            context="Previous content here",
            require_mermaid=True,
            require_table=True,
            require_examples=True,
        )

        assert "Functions" in prompt
        assert "mermaid" in prompt.lower()
        assert "table" in prompt.lower()

    def test_build_review_prompt(self, generator):
        """Test review prompt building."""
        prompt = generator._build_review_prompt("Content here", "Test Section")

        assert "Test Section" in prompt
        assert "Content here" in prompt
        assert "Review Checklist" in prompt

    def test_review_block_parse_json(self, generator):
        """Test parsing review response."""
        response = """
```json
{
  "passed": false,
  "issues": ["Too short"],
  "suggestions": ["Add more examples"],
  "missing_elements": ["examples"]
}
```
"""
        # Mock the LLM call
        with patch.object(generator.agent.llm, "complete") as mock_complete:
            mock_complete.return_value = LLMResponse(
                content=response,
                model="test-model",
            )

            result = generator.review_block("content", "Test")

            assert result["passed"] is False
            assert "Too short" in result["issues"]

    def test_improve_block(self, generator):
        """Test block improvement."""
        original = "# Title\n\nBrief content"

        with patch.object(generator.agent.llm, "complete") as mock_complete:
            mock_complete.return_value = LLMResponse(
                content="# Title\n\nMuch improved content with examples",
                model="test-model",
            )

            improved = generator.improve_block(
                original,
                "Title",
                {"passed": False, "issues": ["Too short"], "suggestions": []},
            )

            assert "improved" in improved.lower()

    @patch("preciz.generator_v2.BlockContentGenerator.create_outline")
    @patch("preciz.generator_v2.BlockContentGenerator.generate_block")
    @patch("preciz.generator_v2.BlockContentGenerator.review_block")
    def test_generate_document(
        self, mock_review, mock_generate, mock_outline, generator, tmp_path
    ):
        """Test full document generation."""
        # Setup mocks
        outline = OutlineNode(title="Test", level=0, description="")
        outline.children = [
            OutlineNode(title="Section 1", level=1, description="First section")
        ]
        mock_outline.return_value = outline

        mock_generate.return_value = "# Section 1\n\nContent here"
        mock_review.return_value = {"passed": True, "issues": [], "suggestions": []}

        output = tmp_path / "output.md"

        result = generator.generate_document("Test Topic", str(output), target_lines=100)

        assert result == str(output)
        assert output.exists()
        mock_generate.assert_called_once()

    def test_assemble_document(self, generator):
        """Test document assembly."""
        node1 = OutlineNode(title="Section 1", level=1, description="")
        node2 = OutlineNode(title="Section 2", level=1, description="")

        blocks = [
            (node1, "Content for section 1"),
            (node2, "Content for section 2"),
        ]

        result = generator._assemble_document(blocks, "Test Topic")

        assert "# Test Topic" in result
        assert "# Section 1" in result
        assert "# Section 2" in result
        assert "Content for section 1" in result
        assert "Content for section 2" in result


class TestGenerateLongDocument:
    """Test generate_long_document convenience function."""

    @patch("preciz.generator_v2.BlockContentGenerator")
    def test_generate_long_document(self, mock_generator_class):
        """Test the convenience function."""
        mock_generator = MagicMock()
        mock_generator.generate_document.return_value = "output.md"
        mock_generator_class.return_value = mock_generator

        result = generate_long_document("Python", "python.md", 5000)

        assert result == "output.md"
        mock_generator.generate_document.assert_called_once_with(
            "Python", "python.md", 5000
        )
