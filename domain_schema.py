"""
A single, disclosed domain schema: which components structurally entangle
with which others, in a typical backend service project. Authored ONCE from
generic software-architecture reasoning - not reverse-engineered from any
task's expected answer - and applied UNIFORMLY to every task's primary
component, whether or not that particular task happens to benefit from it.

This is the one place the intent-aware system is told, in general, that
(for example) authentication work has security and API implications. It is
not told, per task, which specific historical records it needs to find.

See README "Honest Design Decisions" for why this replaced an earlier,
per-task version of this idea that was closer to an oracle.
"""

COMPONENT_RELATIONSHIPS = {
    "auth": ["security", "api"],
    "api": ["security", "testing"],
    "security": ["auth", "api"],
    "database": ["deployment"],
    "deployment": ["database"],
    "testing": ["api"],
    "ui": [],
    "performance": [],
}


def related_components(component: str):
    return set(COMPONENT_RELATIONSHIPS.get(component, []))
