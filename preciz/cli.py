"""CLI interface for Preciz agent."""

import sys
from pathlib import Path

from .agent import PrecizAgent
from .config import Config


def print_plan(plan) -> None:
    """Print edit plan summary."""
    if not plan.edits:
        print("No changes needed.")
        return

    print(f"\nPlan: {plan.reasoning}")
    print(f"Edits to apply: {len(plan.edits)}\n")

    for i, edit in enumerate(plan.edits, 1):
        preview_old = edit.old_text[:100] + "..." if len(edit.old_text) > 100 else edit.old_text
        preview_new = edit.new_text[:100] + "..." if len(edit.new_text) > 100 else edit.new_text
        print(f"{i}. Replace:")
        print(f"   '{preview_old}'")
        print(f"   with:")
        print(f"   '{preview_new}'")
        if edit.replace_all:
            print(f"   (replace_all: {edit.replace_all})")
        print()


def main() -> int:
    """Main CLI entry point."""
    if len(sys.argv) < 3:
        print("Usage: preciz <instruction> <file_path>")
        print("Example: preciz 'Fix the typo in line 5' src/main.py")
        return 1

    instruction = sys.argv[1]
    file_path = sys.argv[2]

    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}")
        return 1

    try:
        config = Config.from_env()
        agent = PrecizAgent(config)

        print(f"Preciz: Analyzing {file_path}...")
        print(f"Task: {instruction}\n")

        plan = agent.plan_edits(instruction, file_path)

        print_plan(plan)

        if plan.edits:
            confirm = input("Apply these changes? [y/N] ")
            if confirm.lower() in ("y", "yes"):
                agent.apply_plan(file_path, plan)
                print("Changes applied successfully!")
            else:
                print("Cancelled.")

        return 0

    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
