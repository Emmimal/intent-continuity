"""
The later coding requests. None of these restate the historical
requirements they depend on - that's the whole point.

expected_requirement_ids is ground truth we control (since we planted
the requirements ourselves) and is used only for scoring, never fed to
any retrieval strategy.
"""

from .data_model import Task

TASKS = [
    Task(
        id="T1", index=71,
        text="Implement the new authentication flow.",
        component="auth", scope=None,
        expected_requirement_ids=["R7", "R1", "R3"],
        checker_name="generic",
    ),
    Task(
        id="T2", index=72,
        text="Add the new monitoring metrics to the dashboard.",
        component="ui", scope=None,
        expected_requirement_ids=["R6", "R11"],
        checker_name="generic",
    ),
    Task(
        id="T3", index=73,
        text="Set up the production database configuration.",
        component="database", scope="production",
        expected_requirement_ids=["R4"],
        checker_name="generic",
    ),
    Task(
        id="T4", index=74,
        text="Add a new public search endpoint.",
        component="api", scope=None,
        expected_requirement_ids=["R1", "R10", "R9", "R3"],
        checker_name="generic",
    ),
    Task(
        id="T5", index=75,
        text="Optimize the inference pipeline.",
        component="performance", scope=None,
        expected_requirement_ids=["R8"],
        checker_name="generic",
    ),
    Task(
        id="T6", index=76,
        text="Prepare the deployment pipeline for the new release.",
        component="deployment", scope="production",
        expected_requirement_ids=["R12"],
        checker_name="generic",
    ),
    Task(
        id="T7", index=77,
        text="Add tests for the new payment endpoint.",
        component="testing", scope=None,
        expected_requirement_ids=["R9"],
        checker_name="generic",
    ),
    Task(
        id="T8", index=78,
        text="Set up the prototype branch database for the experimental feature.",
        component="database", scope="prototype",
        expected_requirement_ids=["R5"],
        checker_name="generic",
    ),
]
