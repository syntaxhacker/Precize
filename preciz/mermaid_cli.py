"""CLI for verifying and converting Mermaid diagrams in Markdown files."""

import sys
from pathlib import Path

from .config import Config
from .llm import LLMClient
from .mermaid_verifier import extract_mermaid_blocks, convert_mermaid_with_retry


def print_usage():
    """Print usage information."""
    print("Preciz Mermaid Verifier")
    print()
    print("Extract and convert Mermaid diagrams from Markdown files to PNG images.")
    print()
    print("Usage:")
    print("  preciz-mermaid-verify <input_file> [options]")
    print()
    print("Examples:")
    print("  preciz-mermaid-verify document.md")
    print("  preciz-mermaid-verify document.md --images-dir diagrams")
    print("  preciz-mermaid-verify document.md --output fixed.md")
    print("  preciz-mermaid-verify document.md --no-fix")
    print()
    print("Options:")
    print("  --images-dir <dir>   Directory to save PNG images (default: images)")
    print("  --output <file>      Output file (default: overwrite input)")
    print("  --no-fix             Skip LLM fixing, fail on conversion errors")
    print("  --dry-run            Show what would be done without converting")
    print("  -h, --help           Show this help message")
    print()


def parse_args(args: list[str]) -> dict:
    """Parse command line arguments.

    Returns:
        Dict with keys: input_file, images_dir, output_file, no_fix, dry_run
    """
    if len(args) < 1 or args[0] in ("-h", "--help", "help"):
        return None

    result = {
        "input_file": args[0],
        "images_dir": "images",
        "output_file": None,
        "no_fix": False,
        "dry_run": False,
    }

    i = 1
    while i < len(args):
        arg = args[i]

        if arg == "--images-dir" and i + 1 < len(args):
            result["images_dir"] = args[i + 1]
            i += 2
        elif arg == "--output" and i + 1 < len(args):
            result["output_file"] = args[i + 1]
            i += 2
        elif arg == "--no-fix":
            result["no_fix"] = True
            i += 1
        elif arg == "--dry-run":
            result["dry_run"] = True
            i += 1
        else:
            i += 1

    return result


def main() -> int:
    """Main CLI entry point."""
    args = parse_args(sys.argv[1:])

    if args is None:
        print_usage()
        return 0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help", "help") else 1

    input_file = Path(args["input_file"])
    if not input_file.exists():
        print(f"Error: File not found: {args['input_file']}")
        return 1

    # Read content
    content = input_file.read_text()

    # Extract mermaid blocks
    blocks = extract_mermaid_blocks(content)

    if not blocks:
        print(f"No Mermaid diagrams found in {args['input_file']}")
        return 0

    print(f"Found {len(blocks)} Mermaid diagram(s)")
    print()

    # Setup
    images_dir = Path(args["images_dir"])
    images_dir.mkdir(parents=True, exist_ok=True)

    if not args["dry_run"]:
        config = Config.from_env()
        llm = LLMClient(config)

    # Process each block
    updated_content = content
    success_count = 0
    failed_count = 0

    for block in blocks:
        print(f"[{block.index}/{len(blocks)}] Converting...")

        safe_name = f"diagram-{block.index}"
        output_path = images_dir / f"{safe_name}.png"

        if args["dry_run"]:
            print(f"  Would convert to: {output_path}")
            print(f"  Code preview: {block.code[:100]}...")
            print()
            continue

        # Try conversion
        if args["no_fix"]:
            # Single attempt, no fixing
            from .mermaid_verifier import try_convert_mermaid
            success, error = try_convert_mermaid(block.code, output_path)
            if success:
                success_count += 1
                print(f"  ✓ Converted: {output_path}")
            else:
                failed_count += 1
                print(f"  ✗ Failed: {error}")
        else:
            # With LLM fix retries
            success, _, error = convert_mermaid_with_retry(
                mermaid_code=block.code,
                output_path=output_path,
                context=f"Diagram {block.index}",
                llm=llm,
                max_retries=3
            )

            if success:
                success_count += 1
                print(f"  ✓ Converted: {output_path}")
                # Replace with image reference
                image_ref = f"![Diagram {block.index}]({args['images_dir']}/{safe_name}.png)"
                updated_content = updated_content.replace(block.full_match, image_ref)
            else:
                failed_count += 1
                print(f"  ✗ Failed to convert after 3 attempts")
                if error:
                    print(f"     Error: {error[:150]}...")

        print()

    # Write output
    if not args["dry_run"]:
        output_file = Path(args["output_file"]) if args["output_file"] else input_file
        output_file.write_text(updated_content)
        print(f"Output written to: {output_file}")

    # Summary
    print("=" * 60)
    print("Summary:")
    print(f"  Total diagrams: {len(blocks)}")
    print(f"  Successfully converted: {success_count}")
    print(f"  Failed: {failed_count}")
    print("=" * 60)

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
