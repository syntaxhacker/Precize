"""Tests for content generator module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from preciz.generator import (
    ContentGenerator,
    ContentSpec,
    SectionBlock,
    QualityChecklist,
    ReviewFeedback,
    generate_tutorial,
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
    return ContentGenerator(mock_config)


class TestContentSpec:
    """Test ContentSpec dataclass."""

    def test_create_spec(self):
        """Test creating content specification."""
        spec = ContentSpec(topic="Python Basics")
        assert spec.topic == "Python Basics"
        assert spec.target_length == "comprehensive"
        assert spec.target_audience == "intermediate"

    def test_spec_with_options(self):
        """Test spec with custom options."""
        spec = ContentSpec(
            topic="Advanced ML",
            target_length="brief",
            target_audience="advanced",
            include_practical=False,
        )
        assert spec.target_length == "brief"
        assert spec.target_audience == "advanced"
        assert spec.include_practical is False


class TestSectionBlock:
    """Test SectionBlock dataclass."""

    def test_create_block(self):
        """Test creating a section block."""
        block = SectionBlock(
            content="Some content",
            line_start=0,
            line_end=5,
            heading="Introduction",
            level=1,
        )
        assert block.heading == "Introduction"
        assert block.level == 1
        assert block.line_start == 0


class TestQualityChecklist:
    """Test QualityChecklist dataclass."""

    def test_default_checklist(self):
        """Test default checklist values."""
        checklist = QualityChecklist()
        assert checklist.require_mermaid_diagrams is True
        assert checklist.require_tables is True
        assert checklist.min_examples_per_section == 2


class TestReviewFeedback:
    """Test ReviewFeedback dataclass."""

    def test_passed_feedback(self):
        """Test feedback that passed."""
        feedback = ReviewFeedback(passed=True)
        assert feedback.passed is True
        assert len(feedback.issues) == 0

    def test_failed_feedback(self):
        """Test feedback that failed."""
        feedback = ReviewFeedback(
            passed=False,
            issues=["Missing examples", "No diagram"],
            suggestions=["Add code examples", "Add flowchart"],
        )
        assert feedback.passed is False
        assert len(feedback.issues) == 2


class TestContentGenerator:
    """Test ContentGenerator class."""

    def test_init_generator(self, generator):
        """Test initializing generator."""
        assert generator.config is not None
        assert generator.agent is not None
        assert generator.checklist is not None

    def test_build_generation_prompt(self, generator):
        """Test generation prompt building."""
        spec = ContentSpec(topic="Calculus", target_audience="beginner")
        prompt = generator._build_generation_prompt(spec)

        assert "Calculus" in prompt
        assert "beginner" in prompt
        assert "Mermaid" in prompt
        assert "diagram" in prompt.lower()

    def test_build_review_prompt(self, generator):
        """Test review prompt building."""
        block = SectionBlock(
            content="Test content here",
            line_start=0,
            line_end=5,
            heading="Overview",
            level=2,
        )
        prompt = generator._build_review_prompt(block, "full content")

        assert "Overview" in prompt
        assert "Test content here" in prompt
        assert "Quality Checklist" in prompt

    def test_split_into_blocks(self, generator):
        """Test splitting content into blocks."""
        content = """# Main Title

Introduction paragraph.

## Section 1

Content here.

### Subsection 1.1

More content.

## Section 2

Final content.
"""
        blocks = generator._split_into_blocks(content)

        assert len(blocks) >= 3
        assert blocks[0].heading == "Main Title"
        assert blocks[0].level == 1

    def test_split_preserves_content(self, generator):
        """Test that splitting preserves all content."""
        content = """# Title

Some content.

## Section

More content.
"""
        blocks = generator._split_into_blocks(content)

        # Reconstruct and check
        reconstructed = "\n\n".join(b.content for b in blocks)
        assert "Some content" in reconstructed
        assert "More content" in reconstructed

    def test_parse_review_response_passed(self, generator):
        """Test parsing passed review response."""
        response = """
```json
{
  "passed": true,
  "issues": [],
  "suggestions": []
}
```
"""
        feedback = generator._parse_review_response(response)
        assert feedback.passed is True

    def test_parse_review_response_failed(self, generator):
        """Test parsing failed review response."""
        response = """
```json
{
  "passed": false,
  "issues": ["Missing mermaid diagram"],
  "suggestions": ["Add flowchart"]
}
```
"""
        feedback = generator._parse_review_response(response)
        assert feedback.passed is False
        assert "Missing mermaid diagram" in feedback.issues

    def test_parse_review_raw_json(self, generator):
        """Test parsing raw JSON without code blocks."""
        response = '{"passed": true, "issues": []}'
        feedback = generator._parse_review_response(response)
        assert feedback.passed is True

    def test_parse_improve_response(self, generator):
        """Test parsing improvement response."""
        response = """
```json
{
  "new_content": "# Improved Heading\\n\\nNew content with examples."
}
```
"""
        new_content = generator._parse_improve_response(response)
        assert "Improved Heading" in new_content
        assert "New content" in new_content

    @patch("preciz.generator.PrecizAgent")
    def test_generate_content(self, mock_agent_class, generator):
        """Test content generation."""
        mock_agent = MagicMock()
        mock_agent.llm.complete.return_value = LLMResponse(
            content="# Generated Content\\n\\nSome content here.",
            model="test-model",
        )
        mock_agent_class.return_value = mock_agent

        spec = ContentSpec(topic="Test Topic")
        content = generator.generate_content(spec)

        assert "Generated Content" in content
        mock_agent.llm.complete.assert_called_once()

    @patch("preciz.generator.PrecizAgent")
    def test_review_section(self, mock_agent_class, generator):
        """Test section review."""
        mock_agent = MagicMock()
        mock_agent.llm.complete.return_value = LLMResponse(
            content='{"passed": true, "issues": [], "suggestions": []}',
            model="test-model",
        )
        mock_agent_class.return_value = mock_agent

        block = SectionBlock(
            content="Test content",
            line_start=0,
            line_end=5,
            heading="Test",
            level=2,
        )

        feedback = generator.review_section(block, "full content")

        assert feedback.passed is True

    @patch("preciz.generator.PrecizAgent")
    def test_improve_section(self, mock_agent_class, generator):
        """Test section improvement."""
        mock_agent = MagicMock()
        mock_agent.llm.complete.return_value = LLMResponse(
            content='{"new_content": "# Improved\\n\\nBetter content"}',
            model="test-model",
        )
        mock_agent_class.return_value = mock_agent

        block = SectionBlock(
            content="Original content",
            line_start=0,
            line_end=5,
            heading="Test",
            level=2,
        )
        feedback = ReviewFeedback(
            passed=False, issues=["Too short"], suggestions=["Expand"]
        )

        improved = generator.improve_section(block, feedback)

        assert "Improved" in improved


class TestGenerateTutorial:
    """Test generate_tutorial convenience function."""

    @patch("preciz.generator.ContentGenerator")
    def test_generate_tutorial(self, mock_generator_class):
        """Test the convenience function."""
        mock_generator = MagicMock()
        mock_generator.generate_with_review.return_value = "# Tutorial\\n\\nContent"
        mock_generator_class.return_value = mock_generator

        result = generate_tutorial("Python", output_file="python.md")

        assert "Tutorial" in result
        mock_generator.generate_with_review.assert_called_once()
