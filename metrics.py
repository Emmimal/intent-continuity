"""
Turns raw run artifacts (retrieval results, provenance, check outcomes)
into the simplified, non-academic metric set described in the article:

  - relevant requirements recovered   (recall against ground truth)
  - irrelevant retrieved               (retrieved but not on that task's
                                        graded checklist) - broken down into:
        noise_chatter    - filler interactions with no requirement content
                            at all (only possible for semantic_naive, which
                            searches the raw interaction stream)
        dropped_in_verification - real requirement records that WERE
                            retrieved as candidates but got filtered out
                            before reaching the agent (superseded / wrong
                            scope) - true noise that never influenced output
        extra_beyond_checklist  - a record that reached the agent but isn't
                            on that task's graded checklist. For
                            intent_aware this is guaranteed currently valid
                            (verification already resolved conflicts before
                            this point) - real, untested context, not an
                            error. For semantic_naive this bucket is NOT
                            guaranteed valid: naive retrieval never resolves
                            conflicts, so it can include a record that is
                            actually stale/wrong but simply didn't happen to
                            win the one field this task's checker tests
                            (see README for a concrete example).
  - stale/invalid decisions applied   (a superseded or out-of-scope
                                        record actually won a field)
  - requirement violations            (from the deterministic checker)
  - tokens supplied to the agent
  - task outcome (pass/fail)

The noise/dropped/extra split matters because "irrelevant retrieved" alone
conflates two very different things: junk that never reached the agent, and
real, valid context that reached the agent but wasn't on the narrow graded
checklist for that specific task. Collapsing them into one number makes a
system that supplies extra-but-legitimate context look worse than one that
supplies actual wrong or unrelated information. See README "Honest design
decisions" for the audited breakdown this produces on the 8-task run.
"""

from typing import List, Dict, Optional
from .data_model import Task, IntentRecord, RetrievalResult, CheckOutcome


def compute_task_metrics(task: Task, retrieval_result: RetrievalResult,
                          provenance: Dict[str, IntentRecord], token_estimate: int,
                          check_outcome: CheckOutcome, superseded_ids_global: set) -> dict:
    expected_ids = set(task.expected_requirement_ids)

    raw_ids = {r.id for r in retrieval_result.raw_candidates}
    recovered_ids = {r.id for r in retrieval_result.recovered}

    relevant_recovered = len(raw_ids & expected_ids)
    recall = relevant_recovered / len(expected_ids) if expected_ids else 1.0

    noise_chatter = len(retrieval_result.retrieved_noise_ids)
    dropped_in_verification = len(raw_ids - recovered_ids)  # candidates seen, filtered before the agent
    extra_beyond_checklist = len(recovered_ids - expected_ids)      # reached the agent, not on this task's checklist

    irrelevant_retrieved = noise_chatter + dropped_in_verification + extra_beyond_checklist

    stale_applied = 0
    for effect_key, record in provenance.items():
        is_superseded = record.id in superseded_ids_global
        is_out_of_scope = record.scope is not None and record.scope != task.scope
        if is_superseded or is_out_of_scope:
            stale_applied += 1

    return {
        "task_id": task.id,
        "condition": retrieval_result.condition,
        "relevant_recovered": relevant_recovered,
        "expected_count": len(expected_ids),
        "recall": recall,
        "irrelevant_retrieved": irrelevant_retrieved,
        "noise_chatter": noise_chatter,
        "dropped_in_verification": dropped_in_verification,
        "extra_beyond_checklist": extra_beyond_checklist,
        "stale_applied": stale_applied,
        "violations": len(check_outcome.violations),
        "violation_details": check_outcome.violations,
        "tokens_supplied": token_estimate,
        "passed": check_outcome.passed,
    }


def aggregate(condition_task_metrics: List[dict]) -> dict:
    n = len(condition_task_metrics)
    total_expected = sum(m["expected_count"] for m in condition_task_metrics)
    total_recovered = sum(m["relevant_recovered"] for m in condition_task_metrics)
    return {
        "tasks": n,
        "avg_recall": total_recovered / total_expected if total_expected else 1.0,
        "total_irrelevant_retrieved": sum(m["irrelevant_retrieved"] for m in condition_task_metrics),
        "total_noise_chatter": sum(m["noise_chatter"] for m in condition_task_metrics),
        "total_dropped_in_verification": sum(m["dropped_in_verification"] for m in condition_task_metrics),
        "total_extra_beyond_checklist": sum(m["extra_beyond_checklist"] for m in condition_task_metrics),
        "total_stale_applied": sum(m["stale_applied"] for m in condition_task_metrics),
        "total_violations": sum(m["violations"] for m in condition_task_metrics),
        "total_tokens_supplied": sum(m["tokens_supplied"] for m in condition_task_metrics),
        "tasks_passed": sum(1 for m in condition_task_metrics if m["passed"]),
    }
