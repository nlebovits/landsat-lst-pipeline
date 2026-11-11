## What changed

<!-- What this pull request changes, and why. Link the issue it closes. -->

## How you tested it

<!-- The commands you ran and what they showed. Label each number MEASURED,
DERIVED, or UNKNOWN, as AGENTS.md describes. A rehearsal proves the
execution path, not real-data output. -->

- [ ] `uv run pytest`
- [ ] `uv run ruff check .` and `uv run ty check --extra-search-path tests --extra-search-path fleet`
- [ ] Vale at error level on every Markdown and Quarto file this pull request touches
- [ ] `uv run --group docs quarto render docs`, if the change touches `docs/`

## For a notebook

<!-- Delete this section if the pull request adds or changes no notebook. -->

- Data sources, with links:
- Run time on your machine, in minutes:
- [ ] The notebook reads only its area of interest.
- [ ] Any new package is in the `docs` dependency group, in this pull request.
- [ ] I committed the refreshed `docs/_freeze/` output.
