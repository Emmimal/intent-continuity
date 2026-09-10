"""
Builds the synthetic interaction history used by the whole experiment.

Design:
- ~70 interactions total, chronologically ordered (index 0 = oldest).
- 12 interactions are genuine planted requirements/decisions/preferences,
  scattered across the timeline, including one real supersession
  (custom JWT auth -> OAuth2) and one scope split that is NOT a
  supersession (production Postgres vs. prototype-only SQLite).
- 3 "trap" interactions use requirement-sounding trigger words
  ("must", "always") in a non-requirement, conversational sense, to give
  the rule-based extractor a genuine (small) precision problem worth
  discussing honestly rather than a free 100%.
- Everything else is ordinary back-and-forth noise: status updates,
  small talk, unrelated questions. This is what a naive broad-retrieval
  ("semantic_naive") strategy will end up scooping up.
"""

from .data_model import Interaction

NOISE_LINES = [
    "Can you rebase this branch on main before I review it?",
    "The CI pipeline is green again after the flaky test fix.",
    "Let's push the sprint demo to Thursday afternoon.",
    "I'll write up the meeting notes and share them later.",
    "Does anyone know why the staging environment is slow today?",
    "Nice catch on that off-by-one bug yesterday.",
    "Can we sync on the roadmap for next quarter?",
    "The design mockups are in the shared drive now.",
    "I'm going to grab coffee, back in ten minutes.",
    "Reminder: standup moved to 9:15 this week.",
    "The linter config got updated, you may need to re-run it.",
    "Thanks for reviewing that PR so quickly.",
    "Let's table the naming debate and revisit next sprint.",
    "The onboarding doc could use a diagram here.",
    "I filed a ticket for the flaky integration test.",
    "Good work on the release notes, they read well.",
    "Can someone double check the changelog before we tag it?",
    "The new intern starts Monday, can you show them around the repo?",
    "I moved the retro to a shared doc so it's easier to track.",
    "Let's keep the PR descriptions a bit more detailed going forward.",
    "The dashboard load time improved after the caching change.",
    "Is the Q3 planning doc final yet?",
    "I'll follow up with the design team about spacing tweaks.",
    "The demo went well, a few small UI nits to fix.",
    "Let's revisit the backlog grooming cadence.",
    "Can you share the load test results from last week?",
    "I added a couple of TODOs in the ingestion module.",
    "The build takes a bit long locally, might be worth profiling.",
    "Thanks for jumping on that incident so fast last night.",
    "Let's park the naming bikeshed and move on.",
    "I'll draft the postmortem doc tomorrow morning.",
    "The new logging format is much easier to grep through.",
    "Can we get an extra reviewer on the migration PR?",
    "I like the new error message copy, much clearer now.",
    "Let's schedule a short knowledge-share on the queue system.",
    "The feature flag rollout looks stable so far.",
    "Someone left a stray console.log in the last commit.",
    "I'll update the architecture diagram after this refactor lands.",
    "Good idea splitting that PR into smaller pieces.",
    "The test suite runtime dropped after parallelizing it.",
]

TRAP_LINES = [
    "I must run to a dentist appointment, back in an hour.",
    "You should always double-check your local time zone before scheduling these.",
    "I never get tired of how fast the new build pipeline is.",
]


def _mk_noise(idx: int, text: str) -> Interaction:
    return Interaction(id=f"i{idx}", index=idx, text=text, is_requirement_bearing=False)


def _mk_trap(idx: int, text: str) -> Interaction:
    # Trigger-word bait: looks requirement-shaped to a keyword scanner, isn't one.
    return Interaction(id=f"i{idx}", index=idx, text=text, is_requirement_bearing=False)


def _mk_req(idx: int, text: str) -> Interaction:
    return Interaction(id=f"i{idx}", index=idx, text=text, is_requirement_bearing=True)


# Planted requirement texts, keyed by the IntentRecord id they'll be extracted into.
# (index, text) - indices are chosen to scatter them across the ~70-turn history.
PLANTED = {
    "R1":  (4,  "All API responses must remain backward compatible with existing clients."),
    "R2":  (9,  "For now, use custom JWT-based authentication for the login service."),
    "R3":  (15, "Internal database user IDs must never be exposed in any API response."),
    "R4":  (21, "The production database must be PostgreSQL, not anything else."),
    "R5":  (26, "For the prototype branch database only, let's use SQLite instead of Postgres to move faster."),
    "R6":  (31, "The dashboard must always show three sections: Overview, Performance, and Errors."),
    "R7":  (39, "We are migrating authentication over to OAuth2, replacing the old JWT approach."),
    "R8":  (43, "Prefer smaller quantized models over large ones for the inference service."),
    "R9":  (47, "All new endpoints require integration tests before they can be merged."),
    "R10": (51, "Rate limiting must be applied to all public-facing endpoints."),
    "R11": (55, "Default the dashboard theme to dark mode going forward."),
    "R12": (59, "Never deploy directly to production without a staging validation pass."),
}


def generate_interaction_history():
    """
    Returns (interactions, planted_index_map) where planted_index_map maps
    requirement id -> the Interaction it was planted in, for downstream use
    by extractor.py and for building ground truth.
    """
    total = 70
    trap_indices = {6, 34, 62}
    planted_indices = {idx: rid for rid, (idx, _text) in PLANTED.items()}

    interactions = []
    noise_pool = iter(NOISE_LINES * 3)   # plenty of noise lines to draw from
    trap_pool = iter(TRAP_LINES)

    for idx in range(total):
        if idx in planted_indices:
            rid = planted_indices[idx]
            _, text = PLANTED[rid]
            interactions.append(_mk_req(idx, text))
        elif idx in trap_indices:
            interactions.append(_mk_trap(idx, next(trap_pool)))
        else:
            interactions.append(_mk_noise(idx, next(noise_pool)))

    planted_index_map = {rid: interactions[idx] for rid, (idx, _t) in PLANTED.items()}
    return interactions, planted_index_map
