"""Main Preciz agent - coordinates editing with LLM."""

import re
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .config import Config
from .editor import Editor, EditOperation
from .file_ops import read_file
from .llm import LLMClient, Message


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
        return """You are Preciz, an expert file editing agent. Your job is to make precise, accurate edits to files.

## Edit Format
When asked to edit a file, you must respond with a JSON object containing:
- `reasoning`: Brief explanation of the changes
- `edits`: Array of edit operations, each with:
  - `old_text`: The exact text to replace (must match precisely)
  - `new_text`: The replacement text
  - `replace_all`: Set to true only if you want to replace ALL occurrences

Example response:
```json
{
  "reasoning": "Fix the typo in the function name",
  "edits": [
    {
      "old_text": "def caculate(total):",
      "new_text": "def calculate(total):",
      "replace_all": false
    }
  ]
}
```

## Critical Rules for Exact Matching
1. Copy `old_text` EXACTLY from the file content - every space, newline, tab matters
2. Use enough context to make `old_text` unique (at least 2-3 lines)
3. When adding content, include the surrounding lines in `old_text` and `new_text`
4. When deleting, include the line before/after in context
5. Set `replace_all: true` ONLY when intentionally replacing all occurrences
6. Respond ONLY with valid JSON, no other text
7. If the requested change is already applied, return empty edits array
8. For simple word/phrase replacements, use minimal but sufficient context

## Strategy for Common Edits:
- To replace a word: Include the full line containing it as context
- To add a line: Include the line before and after in old_text, add new line in new_text
- To delete content: Include surrounding lines, remove unwanted content in new_text
- To change a list item: Include the entire item with its bullet/number

## File Reading
When you need to read a file, I will provide its content in the prompt.
"""

    def _build_user_prompt(
        self,
        instruction: str,
        file_path: str,
        file_content: str | None = None,
    ) -> str:
        """Build user prompt with instruction and file content."""
        if file_content is None:
            file_content = read_file(file_path)

        return f"""# Task
{instruction}

# File: {file_path}
```
{file_content}
```

Please provide your edit plan as JSON."""

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
