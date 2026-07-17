# Viewing Instructions

## Local static server

```bash
bash docs/daanaa-system-audit/serve-report.sh
```

Then open:

```text
http://localhost:8088/
```

## Optional Mermaid rendering

If Mermaid CLI is already installed in your environment, render any source diagram into `docs/daanaa-system-audit/rendered/` with a command like:

```bash
mmdc -i docs/daanaa-system-audit/diagrams/01-platform-architecture.md -o docs/daanaa-system-audit/rendered/01-platform-architecture.svg
```

Repeat for the remaining diagram sources. Do not modify the Mermaid source files.

## Graphviz

If Graphviz is already installed, you can create additional dependency graphs from the repository evidence, but do not install it during this audit.

