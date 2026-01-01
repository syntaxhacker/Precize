# Extending Preciz

Extend and customize Preciz for your needs.

## Custom Tools

### Create Custom Tool

```python
from preciz.orchestrator import GenerateTool
from preciz.llm import LLMClient

class MyGenerateTool(GenerateTool):
    def generate(
        self,
        topic: str,
        section_title: str,
        description: str,
        context: str,
        **kwargs
    ) -> str:
        # Custom prompt
        prompt = f"""
        Write a section about {section_title}.
        Topic: {topic}
        Description: {description}
        Context: {context}

        Your custom requirements here...
        """

        # Custom LLM call
        response = self.llm.complete(
            [Message(role="user", content=prompt)],
            temperature=0.8,  # Custom temperature
            max_tokens=4000,
        )

        # Custom post-processing
        return self._format(response.content)

    def _format(self, content: str) -> str:
        # Add custom formatting
        return content + "\n\n---\n"
```

### Use Custom Tool

```python
from preciz.orchestrator import DocumentOrchestrator

class MyOrchestrator(DocumentOrchestrator):
    def __init__(self, config):
        super().__init__(config)
        # Replace with custom tool
        self.generate_tool = MyGenerateTool(self.llm)
```

## Custom Review Criteria

```python
from preciz.orchestrator import ReviewTool

class StrictReviewTool(ReviewTool):
    def review(self, content: str, title: str) -> dict:
        # Get base feedback
        feedback = super().review(content, title)

        # Add strict checks
        issues = feedback.get("issues", [])

        # Check for TODO markers
        if "TODO" in content:
            issues.append("Contains TODO markers")

        # Check minimum length
        if len(content.split("\n")) < 150:
            issues.append("Too short (minimum 150 lines)")

        # Check for code examples
        if "```" not in content:
            issues.append("No code examples")

        # Check for diagrams
        if "```mermaid" not in content:
            issues.append("No mermaid diagram")

        feedback["issues"] = issues
        feedback["passed"] = len(issues) == 0

        return feedback
```

## Custom Todo List Source

```python
from preciz.orchestrator import BlockTask

def create_todo_from_api(topic: str) -> list[BlockTask]:
    """Create todo list from external API."""

    # Fetch from API
    sections = fetch_sections_from_api(topic)

    # Convert to BlockTask
    tasks = []
    for section in sections:
        tasks.append(BlockTask(
            title=section["title"],
            description=section["description"],
            level=section["level"],
            require_mermaid=section.get("needs_diagram", False),
            require_table=section.get("needs_table", False),
            require_examples=section.get("needs_examples", True),
        ))

    return tasks

def create_todo_from_database(topic: str) -> list[BlockTask]:
    """Create todo list from database."""

    # Query database
    import sqlite3
    conn = sqlite3.connect("curriculum.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT title, description, level, needs_diagram, needs_table
        FROM sections
        WHERE topic = ?
        ORDER BY order
    """, (topic,))

    tasks = []
    for row in cursor.fetchall():
        tasks.append(BlockTask(
            title=row[0],
            description=row[1],
            level=row[2],
            require_mermaid=row[3],
            require_table=row[4],
            require_examples=True,
        ))

    return tasks
```

## Custom Output Formats

### PDF Output

```python
from preciz.orchestrator import AppendTool

class PDFAppendTool(AppendTool):
    def __init__(self, output_file: str):
        super().__init__(output_file)
        self.pdf_pages = []

    def append(self, content: str) -> int:
        # Convert markdown to PDF
        import markdown
        from weasyprint import HTML

        html = markdown.markdown(content)
        pdf = HTML(string=html).write_pdf()

        # Append to PDF
        self.pdf_pages.append(pdf)

        # Also save markdown
        return super().append(content)

    def save_pdf(self, pdf_path: str):
        """Save combined PDF."""
        import PyPDF2

        merger = PyPDF2.PdfMerger()
        for page in self.pdf_pages:
            merger.append(page)

        merger.write(pdf_path)
        merger.close()
```

### HTML Output

```python
class HTMLAppendTool(AppendTool):
    def __init__(self, output_file: str):
        super().__init__(output_file)
        self.html_file = output_file.replace(".md", ".html")

        # Write HTML header
        with open(self.html_file, "w") as f:
            f.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <link rel="stylesheet" href="style.css">
            </head>
            <body>
            """)

    def append(self, content: str) -> int:
        # Convert markdown to HTML
        import markdown
        html = markdown.markdown(content)

        # Append to HTML file
        with open(self.html_file, "a") as f:
            f.write(html)

        # Also append to markdown
        return super().append(content)
```

## Custom LLM Providers

### Add New Provider

```python
# In config.py
@dataclass(frozen=True)
class Config:
    api_key: str
    model: str
    provider: Literal["openrouter", "openai", "anthropic"]  # Add new
    base_url: str | None = None

    @classmethod
    def from_env(cls) -> "Config":
        provider = os.getenv("API_PROVIDER", "openrouter")

        if provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY", "")
            base_url = "https://api.anthropic.com"
            model = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022")
        # ... existing providers
```

### Use Custom Endpoint

```python
from preciz.llm import LLMClient
from preciz.config import Config

# Custom endpoint
config = Config(
    api_key="custom-key",
    model="custom-model",
    provider="openrouter",
    base_url="https://my-custom-endpoint.com/v1",
)

client = LLMClient(config)
```

## Plugins

### Create Plugin

```python
# preciz_plugins/my_plugin.py
from preciz.orchestrator import DocumentOrchestrator

class MyOrchestrator(DocumentOrchestrator):
    """Custom orchestrator with my features."""

    def __init__(self, config):
        super().__init__(config)
        # Add custom initialization
        self.metadata = {}

    def generate_document(self, *args, **kwargs):
        # Add custom behavior
        result = super().generate_document(*args, **kwargs)

        # Add metadata
        self._save_metadata()

        return result

    def _save_metadata(self):
        """Save generation metadata."""
        import json

        with open("metadata.json", "w") as f:
            json.dump({
                "sections": len(self.state.tasks),
                "lines": self.state.total_lines,
                "time": time.time() - self.state.start_time,
            }, f)
```

### Use Plugin

```python
from preciz_plugins.my_plugin import MyOrchestrator
from preciz.config import Config

config = Config.from_env()
orchestrator = MyOrchestrator(config)

orchestrator.generate_document("Topic", "output.md")
```

## Hooks

### Pre/Post Generation Hooks

```python
class HookedOrchestrator(DocumentOrchestrator):

    def pre_generate(self):
        """Called before generation starts."""
        print("Starting generation...")
        # Setup logging, metrics, etc.

    def pre_section(self, task: BlockTask):
        """Called before each section."""
        print(f"Generating: {task.title}")
        # Track progress

    def post_section(self, task: BlockTask, content: str):
        """Called after each section."""
        print(f"Completed: {task.title} ({len(content)} lines)")
        # Update metrics

    def post_generate(self):
        """Called after generation completes."""
        print("Generation complete!")
        # Cleanup, notifications, etc.
```

## Middlewares

### Content Filter Middleware

```python
class ContentFilterMiddleware:
    """Filter or transform content before appending."""

    def __init__(self, append_tool):
        self.append_tool = append_tool

    def append(self, content: str) -> int:
        # Filter content
        filtered = self._filter(content)

        # Transform content
        transformed = self._transform(filtered)

        # Append
        return self.append_tool.append(transformed)

    def _filter(self, content: str) -> str:
        # Remove unwanted content
        lines = content.split("\n")
        filtered = [l for l in lines if "TODO" not in l]
        return "\n".join(filtered)

    def _transform(self, content: str) -> str:
        # Add custom formatting
        return f"\n<!-- Generated at {time.time()} -->\n{content}"
```

## Examples

### Add Bibliography Generation

```python
class BibliographyOrchestrator(DocumentOrchestrator):

    def generate_document(self, *args, **kwargs):
        # Generate main content
        result = super().generate_document(*args, **kwargs)

        # Add bibliography
        self._add_bibliography(result)

        return result

    def _add_bibliography(self, output_file: str):
        """Generate and append bibliography."""

        # Extract citations from document
        import re
        content = Path(output_file).read_text()
        citations = set(re.findall(r'\[@([^\]]+)\]', content))

        # Generate bibliography entries
        bib_content = self._generate_bibliography(citations)

        # Append
        with open(output_file, "a") as f:
            f.write("\n## References\n\n")
            f.write(bib_content)

    def _generate_bibliography(self, citations: set) -> str:
        """Generate bibliography from citations."""
        # Use LLM to generate bibliography
        prompt = f"Generate bibliography entries for: {', '.join(citations)}"

        response = self.llm.complete([
            Message(role="user", content=prompt)
        ])

        return response.content
```

### Add Index Generation

```python
class IndexOrchestrator(DocumentOrchestrator):

    def generate_document(self, *args, **kwargs):
        result = super().generate_document(*args, **kwargs)

        # Generate index
        self._generate_index(result)

        return result

    def _generate_index(self, output_file: str):
        """Generate index and prepend to file."""

        # Read document
        content = Path(output_file).read_text()

        # Extract headings
        import re
        headings = re.findall(r'^(#{1,3}) (.+)$', content, re.MULTILINE)

        # Generate index
        index = "# Index\n\n"
        for level, title in headings:
            indent = "  " * (len(level) - 1)
            slug = title.lower().replace(" ", "-")
            index += f"{indent}- [{title}](#{slug})\n"

        # Prepend index
        Path(output_file).write_text(index + "\n" + content)
```

## See Also

- [Architecture](architecture.md)
- [API Reference](api.md)
- [Orchestrator Pattern](orchestrator.md)
