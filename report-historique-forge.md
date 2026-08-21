# Threat Report #2 — Forged payment history

**Author**: Bounty-Shield (`dodz2`)
**Date**: 2026-08-21
**Confidence**: High (real URL evidence)

---

## Summary

Beyond the fake bounty factory pattern (report #1), we observed an
additional **luring technique**: some fake bounties **forge a payment
history**. They artificially close issues with the `💰 Reward` label to make
it look like the repository "actually pays" — an attempt to bypass the
history check that serious hunters run.

## Why it is dangerous

A hunter who only checks "has this repo ever paid?" via closed issues can be
fooled: the `payment history` signal is there, but it is **forged**. The work
is still not paid.

## Observed examples (anonymized)

| Example | Pattern observed |
|---|---|
| trapuser04 | forged history + closed `💰 Reward` labels on a `sqlc` fork |
| trapuser05 | forged history + closed `💰 Reward` labels on a `kubernetes` fork |

> These are **throwaway GitHub accounts suspected** of belonging to fake
> bounty factories. Account names are anonymized.

## Detection lesson

**A payment history alone proves nothing.** Robustness comes from the
COMBINATION of signals:

- the risk score (recent account, fork, 0 stars, issue #1) **overrides** the
  displayed history;
- a 0-star repo, fork of a big project, with a sudden "payment" history =
  contradictory signal, therefore suspicious;
- always cross-check with the real reward link (Opire/Algora page showing the
  `paid` state).

## Method

1. Never trust a single signal (here: history).
2. Check consistency: trap signals must be treated as priority over
   confidence signals.
3. Require real payment proof (reward page) to qualify a repository as a
   "reliable payer".

## Limitations

- Forged history is only detectable through **contradiction** with the other
  signals — not from the history itself.
- These two examples are representative; others may exist with variations.
