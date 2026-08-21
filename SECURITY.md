# Security Policy

Bounty-Shield analyzes public GitHub issues. **Security** and
**confidentiality** are priorities: the project handles a database of
suspicious accounts stored as hashes, never in plain text.

## Scope / non-scope

- This is **not** a paid bug bounty program.
- The repository does not offer monetary rewards for reports.

## What to report

- A **private data leak**: a real account name, hunting data, or a secret
  exposed in the code, `known.json`, or the history.
- A **flaw** allowing the detection of fake bounties to be bypassed.
- An **injection** or unintended code execution via inputs (URL, `--list`
  file, `--report`).

## How to report

Open a **private issue** (select "Security" in the template, or contact the
maintainer via GitHub) **without publicly exposing** the vulnerability before
it is fixed.

Include:
- the type of problem,
- steps to reproduce,
- the potential impact,
- (if possible) a suggested fix.

## Commitment

- Acknowledgment within **48 h**.
- Analysis and response within **7 days**.
- Coordinated disclosure: the vulnerability is only made public after a fix.

## Non-disclosure note

The `known.json` database contains **SHA-256 hashes** of suspicious accounts —
never the plain-text names. Any regression toward plain-text storage is
considered a critical security issue.
