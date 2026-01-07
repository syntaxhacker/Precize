"""Main Preciz agent - coordinates editing with LLM."""

import re
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from preciz.core.config import Config
from preciz.core.editor import Editor, EditOperation
from preciz.core.file_ops import read_file
from preciz.core.llm import LLMClient, Message
from preciz._archive.prompts.agent import agent as agent_prompts


@dataclass
class EditPlan:
    """Parsed edit plan from LLM."""

    edits: list[EditOperation]
    reasoning: str = ""


class EditParseError(Exception):
    """Exception raised when edit plan parsing fails."""

    pass


class PrecizAgent:
    """
    Preciz agent - uses LLM to plan and apply precise file edits.

    The agent reads files, consults the LLM for edit suggestions,
    parses the response into precise edit operations, and applies them.
    """

    def __init__(self, config: Config | None = None) -> None:
        """
        Initialize the agent.

        Args:
            config: Optional configuration. Uses env defaults if not provided.
        """
        self.config = config or Config.from_env()
        self.llm = LLMClient(self.config)

    def _build_system_prompt(self) -> str:
        """Build system prompt for the agent."""
        return agent_prompts.SYSTEM_PROMPT

    def _build_user_prompt(
        self,
        instruction: str,
        file_path: str,
        file_content: str | None = None,
    ) -> str:
        """Build user prompt with instruction and file content."""
        if file_content is None:
            file_content = read_file(file_path)

        return agent_prompts.build_user_prompt(instruction, file_path, file_content)

    def _parse_edit_plan(self, response: str) -> EditPlan:
        """Parse LLM response into EditPlan."""
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r"```(?:json)?\s*\n?(\{.*?\})\s*```", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise EditParseError("No JSON found in LLM response")

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise EditParseError(f"Invalid JSON: {e}")

        reasoning = data.get("reasoning", "")
        edits_data = data.get("edits", [])

        edits = []
        for e in edits_data:
            edits.append(
                EditOperation(
                    old_text=e["old_text"],
                    new_text=e["new_text"],
                    replace_all=e.get("replace_all", False),
                )
            )

        return EditPlan(edits=edits, reasoning=reasoning)

    def plan_edits(
        self,
        instruction: str,
        file_path: str,
        file_content: str | None = None,
    ) -> EditPlan:
        """
        Plan edits using LLM.

        Args:
            instruction: Natural language instruction for what to edit.
            file_path: Path to the file.
            file_content: Optional pre-read file content.

        Returns:
            EditPlan with parsed edit operations.
        """
        messages = [
            Message(role="system", content=self._build_system_prompt()),
            Message(
                role="user",
                content=self._build_user_prompt(instruction, file_path, file_content),
            ),
        ]

        response = self.llm.complete(messages, temperature=0.3)
        return self._parse_edit_plan(response.content)

    def apply_plan(self, file_path: str, plan: EditPlan) -> None:
        """
        Apply an edit plan to a file.

        Args:
            file_path: Path to the file.
            plan: Edit plan to apply.
        """
        editor = Editor(file_path)
        for edit in plan.edits:
            editor.apply_edit(edit)
        editor.save()

    def edit_file(
        self,
        instruction: str,
        file_path: str,
        dry_run: bool = False,
    ) -> EditPlan:
        """
        Edit a file based on natural language instruction.

        Args:
            instruction: What to do with the file.
            file_path: Path to the file.
            dry_run: If True, only plan without applying.

        Returns:
            The EditPlan that was (or would be) applied.
        """
        plan = self.plan_edits(instruction, file_path)

        if not dry_run and plan.edits:
            self.apply_plan(file_path, plan)

        return plan
