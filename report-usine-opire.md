# Threat Report #1 — The "Opire $10" fake bounty factory

**Author**: Bounty-Shield (`dodz2`)
**Date**: 2026-08-21
**Confidence**: High (real URL evidence, automated + manual verification)

---

## Summary

We document a massive pattern of fake bounties on GitHub: recently created
accounts post a single issue on **forks of popular open-source repositories**,
advertise a fixed **$10** amount with the `opire` label, and a templated title
starting with **"🎯 Fix …"**. The likely goal is to get AI agents or
developers to work **for free** on code, without ever paying.

## Scale indicators (GitHub API, 2026-08-21)

- **1,176** issues carrying the `opire` + `$10` labels
- **~1,291** issues with a "🎯" title created **within the last day**
- **345** merged PRs carrying a `bounty` label (not all are traps)

## Pattern signature (how to recognize it)

| Signal | Description |
|---|---|
| Recent account | created < 30 days before the issue |
| Fork of a famous repo | caddy, traefik, kubernetes, gin, etcd, sqlc, fiber, nats.go… |
| 0 stars | the fork has no life of its own |
| Issue #1 | often the only issue of the repo |
| Fixed amount | `$10` (sometimes `$20`) |
| Templated title | starts with "🎯 Fix …" |
| No license | repository without an identifiable license |

## Verified examples (pattern-based, anonymized)

All examples below match the factory pattern and were confirmed during our
analysis. Account names are anonymized; the repositories involved are forks of
popular projects:

| Example | Pattern observed |
|---|---|
| trapuser01 | fork of `caddy`, issue #1, `$10`, "🎯 Fix" |
| trapuser02 | fork of `nats.go`, issue #1, `$10`, "🎯 Fix" |
| trapuser03 | fork of `fiber`, issue #1, `$10`, "🎯 Fix" |
| trapuser04 | fork of `argo-cd`, issue #1, `$10`, "🎯 Fix" |

> These are **throwaway GitHub accounts suspected** of belonging to fake
> bounty factories. The list is not exhaustive and does not constitute a
> definitive accusation of an identifiable person.

## Detection method

1. GitHub `search` queries (labels `opire`/`$10`, "🎯" titles, issue #1)
2. Automated verification: recent account + fork + 0 stars + issue #1 +
   amount ≤ $20 + templated title
3. Manual confirmation: reading the issue + archived URL evidence

## Recommendations for bounty hunters

- **Anti-trap filter**: NON-fork repo + stars > 0 + issue number > 1 +
  amount > $20 + descriptive title. A candidate failing any of these is
  suspicious.
- **Do not claim** these issues: the work is never paid.
- Report the account to GitHub.

## Limitations

- These signals indicate a **high probability** of a factory, not an absolute
  certainty for each case.
- The volume changes daily; these figures are a snapshot.
