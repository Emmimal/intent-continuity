"""
The actual contribution of this prototype: given a raw candidate set,
decide what's still valid and what should carry forward.

Two checks, applied per effect_key:
  1. Supersession - if another candidate explicitly supersedes this one,
     drop the superseded one.
  2. Scope compatibility - a record scoped to "prototype" or "production"
     only survives if the task's own scope matches; scope-less records
     (apply everywhere) always survive.

If more than one candidate remains for the same effect_key after both
filters (shouldn't happen in this dataset, but kept as a safety net),
the most recent one wins.
"""

from typing import List
from .data_model import IntentRecord, Task, RetrievalResult


def verify_and_resolve(task: Task, raw_candidates: List[IntentRecord]) -> List[IntentRecord]:
    superseded_ids = {r.supersedes for r in raw_candidates if r.supersedes}

    survivors = []
    for record in raw_candidates:
        if record.id in superseded_ids:
            continue  # a later candidate explicitly replaced this one
        if record.scope is not None and record.scope != task.scope:
            continue  # scoped to a context this task isn't in
        survivors.append(record)

    best_per_key = {}
    for record in sorted(survivors, key=lambda r: r.index):
        best_per_key[record.effect_key] = record

    return list(best_per_key.values())


def run_intent_aware(task: Task, raw_candidates: List[IntentRecord]) -> RetrievalResult:
    recovered = verify_and_resolve(task, raw_candidates)
    return RetrievalResult(
        condition="intent_aware",
        task_id=task.id,
        raw_candidates=raw_candidates,
        recovered=recovered,
    )
