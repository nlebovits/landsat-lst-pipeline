# Contributing

This guide explains how to change the code in this repository and the
[documentation site](https://nlebovits.github.io/landsat-lst-pipeline/). To add
an example notebook to the site's gallery, start with
[Contribute a notebook](https://nlebovits.github.io/landsat-lst-pipeline/contribute/notebooks.html).
Everyone who takes part agrees to the
[code of conduct](https://github.com/nlebovits/landsat-lst-pipeline/blob/main/CODE_OF_CONDUCT.md).
Report a security problem privately, as the
[security policy](https://github.com/nlebovits/landsat-lst-pipeline/blob/main/SECURITY.md)
describes, and never in a public issue.

## Set up and submit a change

You need Python 3.12, 3.13, or 3.14 and [uv](https://docs.astral.sh/uv/).
[`AGENTS.md`](https://github.com/nlebovits/landsat-lst-pipeline/blob/main/AGENTS.md)
holds the rules for the pipeline itself: the package layers, the two engines,
and how to label a measurement. Read it before you change anything under
`src/lst`.

1. Install the project and its development tools from the repository root.
   Add the `docs` group when you work on the site:

   ```bash
   uv sync
   uv sync --group docs
   ```

2. Install the Git hooks with [prek](https://prek.j178.dev/). The second
   command installs the `commit-msg` hook, which runs
   [commitizen](https://commitizen-tools.github.io/commitizen/) on each commit
   message:

   ```bash
   prek install
   prek install --hook-type commit-msg
   ```

3. Make the change on a branch, and write each commit message in the
   [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) form,
   such as `fix(masks): count strict land in the coverage share`. The hook
   rejects any other form. The release workflow reads these messages to pick
   the next version and to write `CHANGELOG.md`.

4. Run the checks that CI runs:

   ```bash
   uv run ruff check .
   uv run ty check \
     --extra-search-path tests \
     --extra-search-path fleet
   uv run lint-imports --no-logo
   uv run pytest
   vale --minAlertLevel=error \
     README.md FINDINGS.md CONTRIBUTING.md docs/
   uv run --group docs quarto render docs
   ```

   The Vale gate applies the rules in
   [`docs/PROSE.md`](https://github.com/nlebovits/landsat-lst-pipeline/blob/main/docs/PROSE.md)
   to every Markdown and Quarto file. If `quarto render` re-executes a
   notebook, commit the refreshed `docs/_freeze/` directory with it.

5. Push the branch and open a pull request against `main`. Fill in the pull
   request template with what changed and how you tested it.

## Code quality

Agents write much of this repository. The CI gates apply the same standard to
their output as to hand-written code:

- Make sure the pull request passes the CI gates. A gate does not pass with
  warnings.
- Include tests that would fail without the change.
- Update the documentation the change affects, and keep the prose to what a
  reader needs.
- Run the code yourself and check that it does what the pull request says.
  Do not take an agent's report as the test.
- Run at least one adversarial review pass on the pull request, and push the
  fixes it finds.

You are responsible for every line you submit, including the lines an agent
wrote. Expect to explain any of them in review.

## Maintainer bandwidth

A small team maintains this project alongside other work. Expect a response
to an issue or a pull request within a few days. If a thread has no reply
after a week, one follow-up comment on GitHub is enough. Keep the conversation on
GitHub rather than reaching a maintainer through another channel.

A small fix arrives fastest as a pull request that carries its own
explanation. For a larger change, such as a new runtime dependency or a change
to the numeric rules, open an issue first and describe who needs it and why.
