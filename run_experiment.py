"""
Runs all three retrieval strategies (baseline, semantic_naive, intent_aware)
across all eight tasks, grades each with the identical deterministic
checker, and prints:

  1. Extractor precision/recall sanity check.
  2. A worked example (Task T1) showing what each strategy actually
     handed the agent.
  3. The aggregate results table.

Nothing here calls an LLM, an embedding model, or an external API.
"""

import os
import sys

# Make this file runnable two ways:
#   1) python -m intent_continuity.run_experiment   (relative imports work natively)
#   2) python run_experiment.py                     (e.g. PyCharm's default "Run",
#      double-clicking the file, or running it from inside the folder) - here
#      Python has no package context, so relative imports raise ImportError.
# The try/except below adds the project's parent folder to sys.path and falls
# back to absolute imports so both cases work without extra configuration.
try:
    from .history import generate_interaction_history
    from .extractor import extract_intent_records
    from .tasks import TASKS
    from .retrieval import retrieve_baseline, retrieve_semantic_naive, retrieve_intent_aware_candidates
    from .verification import run_intent_aware
    from .compiler import compile_context
    from .agent import implement_task
    from .checkers import check_task
    from .metrics import compute_task_metrics, aggregate
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from intent_continuity.history import generate_interaction_history
    from intent_continuity.extractor import extract_intent_records
    from intent_continuity.tasks import TASKS
    from intent_continuity.retrieval import retrieve_baseline, retrieve_semantic_naive, retrieve_intent_aware_candidates
    from intent_continuity.verification import run_intent_aware
    from intent_continuity.compiler import compile_context
    from intent_continuity.agent import implement_task
    from intent_continuity.checkers import check_task
    from intent_continuity.metrics import compute_task_metrics, aggregate


def build_canonical_index(records):
    """Map requirement id -> IntentRecord, for scoring against ground truth."""
    return {r.id: r for r in records}


def global_superseded_ids(records):
    return {r.supersedes for r in records if r.supersedes}


def run():
    interactions, planted_index_map = generate_interaction_history()
    records, extractor_eval = extract_intent_records(interactions)
    canonical_by_id = build_canonical_index(records)
    superseded_ids = global_superseded_ids(records)

    print("=" * 72)
    print("STEP 1 - EXTRACTION SANITY CHECK")
    print("=" * 72)
    tp, fp, fn = extractor_eval["true_positive"], extractor_eval["false_positive"], extractor_eval["false_negative"]
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    print(f"{len(interactions)} interactions -> {len(records)} intent records extracted")
    print(f"Trigger-word flagging vs. ground truth: TP={tp} FP={fp} FN={fn} "
          f"(precision={precision:.2f}, recall={recall:.2f})")
    print(f"Detected {len(superseded_ids)} superseded record(s): {sorted(superseded_ids)}")

    conditions = ["baseline", "semantic_naive", "intent_aware"]
    per_condition_task_metrics = {c: [] for c in conditions}
    worked_example = {}

    for task in TASKS:
        for condition in conditions:
            if condition == "baseline":
                result = retrieve_baseline(task, interactions, records)
            elif condition == "semantic_naive":
                result = retrieve_semantic_naive(task, interactions, records)
            else:
                raw_candidates = retrieve_intent_aware_candidates(task, records)
                result = run_intent_aware(task, raw_candidates)

            fields, provenance, token_estimate = compile_context(result.recovered)
            implementation = implement_task(task, fields)
            check_outcome = check_task(task, implementation, canonical_by_id, condition)
            task_metrics = compute_task_metrics(
                task, result, provenance, token_estimate, check_outcome, superseded_ids
            )
            per_condition_task_metrics[condition].append(task_metrics)

            if task.id == "T1":
                worked_example[condition] = {
                    "raw_candidate_ids": [r.id for r in result.raw_candidates],
                    "recovered_ids": [r.id for r in result.recovered],
                    "fields": fields,
                    "violations": check_outcome.violations,
                    "tokens": token_estimate,
                }

    print()
    print("=" * 72)
    print("STEP 2 - WORKED EXAMPLE: Task T1 - 'Implement the new authentication flow.'")
    print("=" * 72)
    print("Ground truth requirements this task actually depends on: "
          f"{TASKS[0].expected_requirement_ids} (none restated in the task text)")
    for condition in conditions:
        ex = worked_example[condition]
        print(f"\n[{condition}]")
        print(f"  raw candidates retrieved : {ex['raw_candidate_ids']}")
        print(f"  survived to final context: {ex['recovered_ids']}")
        print(f"  fields handed to agent   : {ex['fields']}")
        print(f"  tokens supplied          : {ex['tokens']}")
        print(f"  checker violations       : {ex['violations'] or 'none'}")

    print()
    print("=" * 72)
    print("STEP 3 - AGGREGATE RESULTS ACROSS ALL 8 TASKS")
    print("=" * 72)
    header = f"{'condition':<16}{'avg recall':<12}{'irrelevant':<12}{'stale used':<12}{'violations':<12}{'tokens':<10}{'tasks passed':<14}"
    print(header)
    print("-" * len(header))
    agg_rows = {}
    for condition in conditions:
        agg = aggregate(per_condition_task_metrics[condition])
        agg_rows[condition] = agg
        print(f"{condition:<16}{agg['avg_recall']:<12.2f}{agg['total_irrelevant_retrieved']:<12}"
              f"{agg['total_stale_applied']:<12}{agg['total_violations']:<12}"
              f"{agg['total_tokens_supplied']:<10}{agg['tasks_passed']}/{agg['tasks']}")

    print()
    print("=" * 72)
    print("STEP 3b - WHAT 'IRRELEVANT RETRIEVED' ACTUALLY CONTAINS")
    print("=" * 72)
    print("'Irrelevant' is not one kind of thing. It splits into:")
    print("  noise_chatter            - filler interactions with no requirement")
    print("                             content at all (only semantic_naive can")
    print("                             hit this - it searches the raw stream)")
    print("  dropped_in_verification  - a real candidate that was filtered out")
    print("                             before it ever reached the agent (true")
    print("                             noise, zero effect on the output)")
    print("  extra_beyond_checklist   - reached the agent, not on this task's")
    print("                             graded checklist. For intent_aware this")
    print("                             is GUARANTEED valid (verification already")
    print("                             resolved conflicts). For semantic_naive")
    print("                             it is NOT guaranteed valid - naive")
    print("                             retrieval never resolves conflicts, so")
    print("                             this bucket can include a record that is")
    print("                             actually stale but didn't happen to win")
    print("                             the one field this task's checker tests.")
    print()
    header2 = f"{'condition':<16}{'noise_chatter':<16}{'dropped_in_verif':<18}{'extra_beyond_checklist':<16}"
    print(header2)
    print("-" * len(header2))
    for condition in conditions:
        agg = agg_rows[condition]
        print(f"{condition:<16}{agg['total_noise_chatter']:<16}{agg['total_dropped_in_verification']:<18}"
              f"{agg['total_extra_beyond_checklist']:<16}")

    print()
    print("=" * 72)
    print("STEP 4 - PER-TASK PASS/FAIL BY CONDITION")
    print("=" * 72)
    print(f"{'task':<8}{'baseline':<12}{'semantic_naive':<18}{'intent_aware':<14}")
    for i, task in enumerate(TASKS):
        row = [task.id]
        for condition in conditions:
            m = per_condition_task_metrics[condition][i]
            row.append("PASS" if m["passed"] else f"FAIL ({m['violations']})")
        print(f"{row[0]:<8}{row[1]:<12}{row[2]:<18}{row[3]:<14}")

    return per_condition_task_metrics, agg_rows


if __name__ == "__main__":
    run()
