"""
A deliberately dumb, fully deterministic stand-in for a coding agent.

It does exactly one thing: build the part of the task that's genuinely
new (e.g. "add a Monitoring section"), and otherwise reflect back
whatever was in its supplied context. It has no way to know about a
requirement that wasn't handed to it - which is the entire point of the
experiment. Nothing here is an LLM call.
"""

from typing import Dict, Any
from .data_model import Task, Implementation

DEFAULTS: Dict[str, Any] = {
    "auth_method": "basic",
    "hides_internal_ids": False,
    "database_engine": "unspecified",
    "default_theme": "light",
    "dashboard_sections": (),
    "uses_small_model": False,
    "has_integration_tests": False,
    "requires_staging_validation": False,
    "preserves_old_fields": False,
    "rate_limited": False,
}


def implement_task(task: Task, context: Dict[str, Any]) -> Implementation:
    fields = dict(DEFAULTS)
    fields.update(context)

    if task.id == "T2":
        # The "new work" itself: the task explicitly asks for a Monitoring
        # section. Whether the pre-existing Overview/Performance/Errors
        # sections survive depends entirely on whether dashboard_sections
        # was in the supplied context.
        base = set(fields.get("dashboard_sections") or ())
        base.add("Monitoring")
        fields["dashboard_sections"] = tuple(sorted(base))

    return Implementation(fields=fields)
