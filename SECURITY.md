# Security policy

## Report a vulnerability

Report a security problem privately. Do not open a public issue for it.

- Use GitHub's
  [private vulnerability reporting](https://github.com/nlebovits/landsat-lst-pipeline/security/advisories/new)
  for this repository.
- Or email [nissim@radiant.earth](mailto:nissim@radiant.earth) with a
  description, the affected files or URLs, and the steps that reproduce the
  problem.

You get an acknowledgement within five working days. The maintainer works
with you on a fix and a disclosure date, and credits you in the advisory
unless you ask for no credit.

## Scope

This policy covers:

- The code in this repository, including the fleet scripts and the GitHub
  Actions workflows.
- The catalog metadata under `catalog/` and the files it points to on
  [Source Cooperative](https://source.coop/nlebovits/landsat-lst).
- The [documentation site](https://nlebovits.github.io/landsat-lst-pipeline/).

A leaked credential in the history, a workflow that runs untrusted input, and
a catalog link that resolves to the wrong host are all in scope.

Problems in a dependency belong with that project. Report them upstream, and
open an issue here if this repository needs to pin around the problem. A
wrong or implausible temperature value is a data issue rather than a security
problem: report it with the
[data issue form](https://github.com/nlebovits/landsat-lst-pipeline/issues/new?template=data-issue.yml).

## Supported versions

Only the latest release and `main` receive fixes.
