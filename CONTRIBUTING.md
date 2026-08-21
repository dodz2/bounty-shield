# Contributing to Bounty-Shield

Thanks for wanting to improve Bounty-Shield. This project is designed to be
simple, reliable and dependency-free — please respect these principles in your
contributions.

## Environment

- **Python ≥ 3.9**, zero external dependency (stdlib only).
- Tests: `unittest` (no third-party framework).

```bash
cd verify-bounty
python3 -m unittest discover -s tests -q
```

## How to contribute

1. **Fork** the repository, create a dedicated branch (`git switch -c feature/...`).
2. **Code** following the existing style (docstrings, clear comments).
3. **Add tests** for any new feature or fix.
4. **Verify** the suite passes: `python3 -m unittest discover -s tests -q`.
5. **Open a Pull Request** with a clear description:
   - the problem solved,
   - the approach,
   - the tests added.

## Rules

- **Zero dependency**: do not add an external package without justification.
- **Do not disclose the database**: the `known.json` file embeds SHA-256
  hashes of accounts. Never replace it with plain-text names, and never
  publish hunting data in issues/PRs.
- **Compatibility**: the code must stay compatible with Python 3.9+.
- **Tests**: any PR must keep the suite green (CI depends on it).

## Reporting a bug

Open an issue with: the command run, the output obtained, the expected output.
For security issues, see `SECURITY.md`.
