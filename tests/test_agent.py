"""Tests for agent module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from preciz.agent import PrecizAgent, EditPlan, EditParseError
from preciz.config import Config
from preciz.llm import Message, LLMResponse


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
def agent(mock_config):
    """Create an agent with mock config."""
    return PrecizAgent(mock_config)


class TestEditPlan:
    """Test EditPlan dataclass."""

    def test_create_plan(self):
        """Test creating an edit plan."""
        from preciz.editor import EditOperation

        plan = EditPlan(
            edits=[EditOperation("old", "new")],
            reasoning="Fix typo",
        )
        assert len(plan.edits) == 1
        assert plan.reasoning == "Fix typo"


class TestPrecizAgent:
    """Test PrecizAgent class."""

    def test_init_agent(self, agent):
        """Test initializing the agent."""
        assert agent.config.model == "test-model"
        assert agent.llm is not None

    def test_build_system_prompt(self, agent):
        """Test system prompt building."""
        prompt = agent._build_system_prompt()
        assert "Preciz" in prompt
        assert "JSON" in prompt
        assert "old_text" in prompt

    def test_build_user_prompt(self, agent, tmp_path):
        """Test user prompt building."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world")

        prompt = agent._build_user_prompt("Change world to there", str(test_file))

        assert "Change world to there" in prompt
        assert "Hello world" in prompt
        assert str(test_file) in prompt

    def test_parse_valid_edit_plan(self, agent):
        """Test parsing valid JSON response."""
        response = """
```json
{
  "reasoning": "Fix the greeting",
  "edits": [
    {
      "old_text": "Hello world",
      "new_text": "Hello there"
    }
  ]
}
```
"""
        plan = agent._parse_edit_plan(response)
        assert plan.reasoning == "Fix the greeting"
        assert len(plan.edits) == 1
        assert plan.edits[0].old_text == "Hello world"
        assert plan.edits[0].new_text == "Hello there"

    def test_parse_raw_json(self, agent):
        """Test parsing raw JSON without code blocks."""
        response = '{"reasoning": "test", "edits": []}'
        plan = agent._parse_edit_plan(response)
        assert plan.reasoning == "test"
        assert len(plan.edits) == 0

    def test_parse_with_replace_all(self, agent):
        """Test parsing edit with replace_all flag."""
        response = """
```json
{
  "reasoning": "Replace all",
  "edits": [
    {
      "old_text": "foo",
      "new_text": "bar",
      "replace_all": true
    }
  ]
}
```
"""
        plan = agent._parse_edit_plan(response)
        assert plan.edits[0].replace_all is True

    def test_parse_invalid_json(self, agent):
        """Test error on invalid JSON."""
        response = "This is not JSON"
        with pytest.raises(EditParseError, match="No JSON found"):
            agent._parse_edit_plan(response)

    def test_parse_malformed_json(self, agent):
        """Test error on malformed JSON."""
        response = '```json\n{"invalid": }\n```'
        with pytest.raises(EditParseError, match="Invalid JSON"):
            agent._parse_edit_plan(response)

    @patch("preciz.agent.LLMClient.complete")
    def test_plan_edits(self, mock_complete, agent, tmp_path):
        """Test planning edits with LLM."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world")

        mock_complete.return_value = LLMResponse(
            content='''{"reasoning": "test", "edits": []}''',
            model="test-model",
        )

        plan = agent.plan_edits("Make changes", str(test_file))

        assert len(plan.edits) == 0
        mock_complete.assert_called_once()

    @patch("preciz.agent.LLMClient.complete")
    def test_apply_plan(self, mock_complete, agent, tmp_path):
        """Test applying an edit plan."""
        from preciz.editor import EditOperation

        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world")

        plan = EditPlan(
            edits=[EditOperation(old_text="world", new_text="there")],
            reasoning="Change greeting",
        )

        agent.apply_plan(str(test_file), plan)

        content = test_file.read_text()
        assert content == "Hello there"

    @patch("preciz.agent.LLMClient.complete")
    @patch.object(PrecizAgent, "apply_plan")
    def test_edit_file_full_flow(self, mock_apply, mock_complete, agent, tmp_path):
        """Test the full edit_file flow."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world")

        mock_complete.return_value = LLMResponse(
            content='''{"reasoning": "test", "edits": [
              {"old_text": "world", "new_text": "there"}
            ]}''',
            model="test-model",
        )

        plan = agent.edit_file("Change world to there", str(test_file))

        assert len(plan.edits) == 1
        mock_apply.assert_called_once()

    @patch("preciz.agent.LLMClient.complete")
    def test_edit_file_dry_run(self, mock_complete, agent, tmp_path):
        """Test edit_file with dry_run=True."""
        test_file = tmp_path / "test.txt"
        original = "Hello world"
        test_file.write_text(original)

        mock_complete.return_value = LLMResponse(
            content='''{"reasoning": "test", "edits": [
              {"old_text": "world", "new_text": "there"}
            ]}''',
            model="test-model",
        )

        plan = agent.edit_file("Change world to there", str(test_file), dry_run=True)

        # File should not be modified
        assert test_file.read_text() == original
        assert len(plan.edits) == 1
