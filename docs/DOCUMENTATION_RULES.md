# Documentation Rules

## File Naming

- Lowercase with hyphens: `my-document.md`
- No spaces, no underscores
- Descriptive names matching content

## Markdown

- Use ATX-style headings (`#`, `##`, `###`)
- One blank line between headings and content
- No trailing whitespace
- End files with single newline

## Headings

- One `#` per file (document title)
- Sequential nesting: `##` before `###`
- No skipping levels

## Mermaid

- Use fenced code blocks with `mermaid` language
- Keep diagrams under 30 nodes
- Use descriptive node labels

## Code Blocks

- Always specify language: `python`, `bash`, `yaml`
- Use inline code for short references

## Images

- Store in `docs/images/`
- Use descriptive filenames: `architecture-overview.png`
- Reference with relative paths

## Cross References

- Use relative links: `[Link Text](../path/to/doc.md)`
- Verify links resolve correctly

## Versioning

- Documentation follows semantic versioning
- Breaking changes require major version bump

## Deprecation

- Mark deprecated sections with warning
- Specify removal timeline
- Provide migration path
