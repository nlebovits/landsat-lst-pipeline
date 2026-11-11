"""Check that every action a workflow uses resolves on GitHub.

GitHub resolves `uses: owner/repo@ref` only when the job starts. A ref that
names nothing passes every local check and fails the job at setup, as
`astral-sh/setup-uv@v10` did on 2026-11-11: that project publishes no
floating major tags after v7.

For each `uses:` this script asks the action's repository for its refs with
`git ls-remote`:

- a tag or branch ref has to exist;
- a commit SHA has to carry a `# <tag>` comment, the form Renovate's
  `pinGitHubActionDigestsToSemver` writes, and that tag has to point to the
  SHA.

Local actions (`./path`) and container actions (`docker://`) are skipped.

    python3 .github/scripts/check_action_refs.py [workflow.yml ...]

With no arguments it checks every file in `.github/workflows/`. It needs
network access to github.com and uses only the standard library.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

USES = re.compile(
    r"^\s*(?:-\s*)?uses:\s*['\"]?(?P<action>[^@\s'\"]+)@(?P<ref>[^\s'\"#]+)['\"]?"
    r"(?:\s*#\s*(?P<comment>\S+))?"
)
SHA = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class Use:
    path: str
    line: int
    action: str
    ref: str
    comment: str | None

    @property
    def repo(self) -> str:
        """`owner/repo`, also for an action in a subdirectory of its repo."""
        return "/".join(self.action.split("/")[:2])


def uses_in(path: Path) -> list[Use]:
    found = []
    for number, text in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = USES.match(text)
        if not match:
            continue
        action = match["action"]
        if action.startswith(("./", "docker://")):
            continue
        found.append(Use(str(path), number, action, match["ref"], match["comment"]))
    return found


def remote_refs(repo: str) -> dict[str, str]:
    """Map each tag and branch name to the commit it points to."""
    output = subprocess.run(
        ["git", "ls-remote", "--tags", "--heads", f"https://github.com/{repo}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    refs: dict[str, str] = {}
    for line in output.splitlines():
        sha, name = line.split("\t")
        short = name.removeprefix("refs/tags/").removeprefix("refs/heads/")
        if short.endswith("^{}"):
            # The commit an annotated tag points to wins over the tag object.
            refs[short[:-3]] = sha
        else:
            refs.setdefault(short, sha)
    return refs


def problem(use: Use, refs: dict[str, str]) -> str | None:
    if SHA.match(use.ref):
        if not use.comment:
            return f"{use.action}@{use.ref} pins a commit with no '# <tag>' comment"
        if refs.get(use.comment) != use.ref:
            return (
                f"{use.action}@{use.ref} says '# {use.comment}', but {use.comment} "
                f"points to {refs.get(use.comment, 'nothing')}"
            )
        return None
    if use.ref not in refs:
        return f"{use.action}@{use.ref}: {use.repo} has no tag or branch '{use.ref}'"
    return None


def main(argv: list[str]) -> int:
    paths = [Path(a) for a in argv] or sorted(Path(".github/workflows").glob("*.y*ml"))
    uses = [use for path in paths for use in uses_in(path)]
    cache: dict[str, dict[str, str]] = {}
    failures = 0
    for use in uses:
        if use.repo not in cache:
            cache[use.repo] = remote_refs(use.repo)
        message = problem(use, cache[use.repo])
        if message:
            failures += 1
            print(f"{use.path}:{use.line}: {message}")
    print(f"Checked {len(uses)} action references in {len(paths)} workflows.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
