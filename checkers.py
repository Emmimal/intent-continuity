"""
Grades an Implementation against ground truth. The checker is IDENTICAL
for every condition (baseline / semantic_naive / intent_aware) - only the
context supplied to the agent differs between conditions. That's what
makes the comparison fair.
"""

from typing import List, Dict
from .data_model import Task, Implementation, IntentRecord, CheckOutcome


def canonical_expected_fields(task: Task, canonical_by_id: Dict[str, IntentRecord]):
    fields = {}
    for rid in task.expected_requirement_ids:
        record = canonical_by_id[rid]
        fields[record.effect_key] = record.effect_value
    return fields


def check_task(task: Task, implementation: Implementation,
               canonical_by_id: Dict[str, IntentRecord], condition: str) -> CheckOutcome:
    expected_fields = canonical_expected_fields(task, canonical_by_id)
    violations: List[str] = []

    for key, expected_value in expected_fields.items():
        actual = implementation.fields.get(key)
        if key == "dashboard_sections":
            required = set(expected_value)
            actual_set = set(actual) if actual else set()
            missing = required - actual_set
            if missing:
                violations.append(f"missing required dashboard sections: {sorted(missing)}")
        else:
            if actual != expected_value:
                violations.append(f"{key}: expected {expected_value!r}, got {actual!r}")

    return CheckOutcome(task_id=task.id, condition=condition,
                         passed=(len(violations) == 0), violations=violations)
