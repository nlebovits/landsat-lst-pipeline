"""Pick the docs notebooks a change has to execute, and keep their inputs on record.

A notebook is any tracked `.qmd` under `docs/` with a ```{python} cell.
Quarto's `freeze: auto` executes a notebook again only when its own source
changes. Each notebook also reads inputs outside its source:

- every notebook reads `docs/_plotting.py` and the fonts in `docs/fonts/`;
- a notebook in a subdirectory of `docs/` reads the other files in that
  directory, such as `docs/tutorials/data/`. A notebook directly in `docs/`
  owns no directory, because `docs/` holds the whole site.

A change to one of those inputs leaves the committed freeze stale while
`freeze: auto` still reuses it. `docs/_notebook_inputs.json` records one
SHA-256 hash over each notebook's inputs, and `check` fails when a hash no
longer matches. Execution cannot settle the question instead: the tutorial
records its own run time and downloads basemap tiles, so two runs never
produce the same bytes.

`uv.lock` is not an input here. A dependency bump executes every notebook in
the docs workflow, which proves the code still runs, but it does not force a
fresh freeze on every lock maintenance pull request.

    python3 .github/scripts/docs_notebooks.py pick --event pull_request
    python3 .github/scripts/docs_notebooks.py check
    python3 .github/scripts/docs_notebooks.py record

Run `record` after you execute a notebook whose inputs changed, and commit
the manifest with the refreshed freeze. The script uses only the standard
library, because the `detect` job runs it before any environment exists.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path, PurePosixPath

DOCS = PurePosixPath("docs")
SHARED_INPUTS = (PurePosixPath("docs/_plotting.py"), PurePosixPath("docs/fonts"))
MANIFEST = "docs/_notebook_inputs.json"
#: Files in a notebook's directory that change how the page renders, not what
#: its cells compute.
RENDER_ONLY = {"_metadata.yml"}


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout


def tracked(root: Path) -> list[str]:
    return git(root, "ls-files").splitlines()


def notebooks(root: Path, files: list[str]) -> list[str]:
    found = []
    for path in files:
        pure = PurePosixPath(path)
        if pure.suffix != ".qmd" or not pure.is_relative_to(DOCS):
            continue
        text = (root / path).read_text(encoding="utf-8")
        if any(line.strip().startswith("```{python") for line in text.splitlines()):
            found.append(path)
    return sorted(found)


def is_shared_input(path: str) -> bool:
    pure = PurePosixPath(path)
    return any(pure == s or pure.is_relative_to(s) for s in SHARED_INPUTS)


def owns(notebook: str, path: str) -> bool:
    """Whether `path` is an input of `notebook` through the notebook's directory."""
    directory = PurePosixPath(notebook).parent
    pure = PurePosixPath(path)
    return (
        directory != DOCS
        and pure.is_relative_to(directory)
        and pure.suffix != ".qmd"
        and pure.name not in RENDER_ONLY
        and not pure.is_relative_to(DOCS / "_freeze")
    )


def inputs(notebook: str, files: list[str]) -> list[str]:
    return sorted(p for p in files if is_shared_input(p) or owns(notebook, p))


def fingerprint(root: Path, paths: list[str]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.encode() + b"\0")
        digest.update((root / path).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def current(root: Path) -> dict[str, str]:
    files = tracked(root)
    return {nb: fingerprint(root, inputs(nb, files)) for nb in notebooks(root, files)}


def stale(root: Path) -> list[str]:
    """Notebooks whose inputs differ from the hash on record, or have none."""
    path = root / MANIFEST
    recorded = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return [nb for nb, digest in current(root).items() if recorded.get(nb) != digest]


def record(root: Path) -> None:
    text = json.dumps(current(root), indent=2, sort_keys=True) + "\n"
    (root / MANIFEST).write_text(text, encoding="utf-8")


def docs_group(root: Path, rev: str) -> list[str]:
    try:
        text = git(root, "show", f"{rev}:pyproject.toml")
    except subprocess.CalledProcessError:
        return []
    return tomllib.loads(text).get("dependency-groups", {}).get("docs", [])


def pick(root: Path, event: str, base: str = "HEAD^1") -> tuple[list[str], str]:
    """The notebooks to execute, and why.

    On a pull request the checkout is the merge commit, so `HEAD^1` is the
    tip of the base branch and the diff is exactly the change.
    """
    files = tracked(root)
    every = notebooks(root, files)
    if event != "pull_request":
        return every, "every notebook, on a scheduled or manual run"

    changed = set(git(root, "diff", "--name-only", base, "HEAD").splitlines())
    shared = {p for p in changed if p == "uv.lock" or is_shared_input(p)}
    if "pyproject.toml" in changed and docs_group(root, base) != docs_group(
        root, "HEAD"
    ):
        shared.add("the docs dependency group")
    if shared:
        return every, "every notebook, because these changed: " + ", ".join(
            sorted(shared)
        )
    picked = [nb for nb in every if nb in changed or any(owns(nb, p) for p in changed)]
    return picked, "the notebooks this pull request changed"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    pick_parser = sub.add_parser(
        "pick", help="Write the notebook matrix for the docs workflow."
    )
    pick_parser.add_argument("--event", required=True)
    sub.add_parser(
        "check", help="Fail when a notebook's inputs differ from the record."
    )
    sub.add_parser("record", help=f"Write {MANIFEST} from the current inputs.")
    args = parser.parse_args(argv)
    root = Path(git(Path.cwd(), "rev-parse", "--show-toplevel").strip())

    if args.command == "pick":
        picked, reason = pick(root, args.event)
        print(f"Selected {len(picked)} notebooks: {reason}.")
        for nb in picked:
            print(f"  {nb}")
        output = os.environ.get("GITHUB_OUTPUT")
        if output:
            with open(output, "a", encoding="utf-8") as out:
                out.write(f"matrix={json.dumps({'notebook': picked})}\n")
                out.write(f"any={'true' if picked else 'false'}\n")
        return 0

    if args.command == "record":
        record(root)
        print(f"Wrote {MANIFEST}.")
        return 0

    out_of_date = stale(root)
    for nb in out_of_date:
        print(
            f"::error file={nb}::The inputs of {nb} changed since its freeze was "
            f"recorded. Run 'uv run --group docs quarto render {nb} --execute', "
            f"then 'python3 .github/scripts/docs_notebooks.py record', and commit "
            f"docs/_freeze/ and {MANIFEST}."
        )
    return 1 if out_of_date else 0


if __name__ == "__main__":
    sys.exit(main())
