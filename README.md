# intent-continuity

A pure-Python system that automatically discovers, verifies, and applies relevant historical requirements for coding agents — no embeddings, no vector database, no LLM calls anywhere in the pipeline.

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)

Retrieving related history isn't the same as knowing which of it is still true. This repo is a small, fully deterministic demonstration of the difference: a coding agent that only retrieves related history passes 4 of 8 tasks. The same agent, with a verification step added on top, passes 8 of 8 — using more tokens, not fewer, because correctness costs something that raw retrieval doesn't pay for.

**Read the full write-up on Towards Data Science →** [Coding Agents Don't Need Longer History — They Need Intent Continuity](https://towardsdatascience.com/author/emmimalp.alexander/)

---

## What It Does

```
Historical Interactions (70, chronological)
        |
        v
Rule-Based Intent Extraction     (trigger phrases -> component -> effect)
        |
        v
Intent Records                   (constraint / decision, tagged with component + scope)
        |
        v
Candidate Retrieval              (domain schema + keyword overlap)
        |
        v
Verification                     (drop superseded, drop out of scope)
        |
        v
Recovered Intent
        |
        v
Context Compiler                 -> flat fields
        |
        v
Deterministic "Agent"            -> implementation
        |
        v
Deterministic Requirement Checker
```

Nine steps, one `build()`-style call (`run_experiment.py`):

| Component | Job |
|---|---|
| Extractor | Rule-based parsing: trigger phrases → component → structured effect |
| Domain Schema | One global, task-independent component-relationship graph |
| Retrieval | Candidate generation via component match + keyword overlap (three competing strategies) |
| Verification | Drops superseded and out-of-scope candidates before they ever reach the agent |
| Compiler | Flattens surviving records into a plain key-value context, plus a token estimate |
| Agent | Deterministic template — reacts only to whatever context it's actually given |
| Checker | One identical grading function, applied the same way to every condition |

## Installation

```bash
git clone https://github.com/Emmimal/intent-continuity.git
cd intent-continuity
```

No `pip install` step. Everything runs on the Python standard library alone — Python 3.9+, zero external dependencies, zero API keys.

## Running the Experiment

```bash
python -m intent_continuity.run_experiment
```

This also works as a direct script (e.g. running it from an IDE like PyCharm, or double-clicking it) — both invocation styles are supported and produce identical output.

Real output, condensed (full run also prints an extraction sanity check and a worked example for Task T1):

```
condition       avg recall  irrelevant  stale used  violations  tokens    tasks passed
----------------------------------------------------------------------------------------
baseline        0.00        0           0           14          0         0/8
semantic_naive  0.57        17          1           7           155       4/8
intent_aware    1.00        10          0           0           199       8/8
```

| Task | Baseline | Naive Lexical Retrieval | Intent-Aware |
|---|---|---|---|
| T1 | FAIL (3) | FAIL (2) | PASS |
| T2 | FAIL (2) | PASS | PASS |
| T3 | FAIL (1) | FAIL (1) | PASS |
| T4 | FAIL (4) | FAIL (3) | PASS |
| T5 | FAIL (1) | PASS | PASS |
| T6 | FAIL (1) | FAIL (1) | PASS |
| T7 | FAIL (1) | PASS | PASS |
| T8 | FAIL (1) | PASS | PASS |

**Before you trust the 8/8** — an earlier version of the domain schema (Component 2) declared component relationships per task instead of globally, and it was, in effect, an answer key dressed up as a retrieval rule. Deleting that per-task hint dropped the result from 8/8 to 6/8, failing exactly the two tasks it had been quietly hand-fed. The fixed version in this repo applies one general schema uniformly to every task, including the six that never needed the extra reach — at the honest cost of more irrelevant retrieval and more tokens. Full story in the write-up linked above.

## Using the Pieces in Your Own Project

Nothing here is locked behind one entry point. Extraction, retrieval, and verification are separate, composable functions:

```python
from intent_continuity.history import generate_interaction_history
from intent_continuity.extractor import extract_intent_records
from intent_continuity.retrieval import retrieve_intent_aware_candidates
from intent_continuity.verification import verify_and_resolve

interactions, _ = generate_interaction_history()
records, extractor_eval = extract_intent_records(interactions)

# my_task is a Task (see data_model.py) describing a new request
candidates = retrieve_intent_aware_candidates(my_task, records)
recovered = verify_and_resolve(my_task, candidates)
# recovered now excludes anything superseded or out of scope
```

## Project Structure

```
intent_continuity/
├── __init__.py
├── data_model.py         # Interaction, IntentRecord, Task, RetrievalResult, Implementation, CheckOutcome
├── history.py             # the 70-interaction synthetic history (12 planted requirements, 3 traps, noise)
├── extractor.py             # rule-based extraction + the general supersession-inference rule
├── domain_schema.py           # the one global, task-independent component-relationship graph
├── tasks.py                     # the 8 tasks and their ground-truth answer key
├── retrieval.py                   # baseline / naive lexical / intent-aware candidate generation
├── verification.py                  # supersession + scope resolution
├── compiler.py                        # flattens recovered records into agent context + token estimate
├── agent.py                             # the deterministic rule-based "agent"
├── checkers.py                            # one identical checker used across every condition
├── metrics.py                               # recall, the noise/dropped/extra breakdown, tokens, pass/fail
└── run_experiment.py                          # runs everything end to end
```

## When to Use This

Worth adapting if you're running coding agents on long-lived projects where requirements get stated once and never repeated — a multi-week refactor, a codebase with accumulated architectural decisions, a team where the person who set a constraint isn't the person prompting the agent three weeks later.

Skip it for:
- Single-session, self-contained tasks with no history to lose
- Projects small enough that pasting the full requirements doc into every prompt is cheap and complete
- Setups where a human already restates every constraint on every request

## Known Limitations

- The component and keyword dictionaries are hand-authored for this domain, not learned. This demonstrates the verification mechanism — it isn't a general-purpose extraction system you could point at an arbitrary codebase as-is.
- Retrieval uses plain lexical word overlap, not a real embedding model or vector database, specifically so retrieval quality doesn't become a confounding variable. Swapping in a real embedding model would likely change the naive condition's recall; it wouldn't change the underlying argument, since verification is retrieval-agnostic.
- Eight tasks and twelve requirements is a demonstration, sized to be fully inspectable and reproducible, not a statistically powered study.
- The "agent" is a deterministic template on purpose, not a real coding LLM, so every result is attributable to what each retrieval strategy recovered rather than to model behavior on a given day.
- The checker only tests fields explicitly declared in each task's ground truth — a narrow rubric by design, not a general measure of code quality.
- Everything runs in-process; there's no persistence across restarts (see "What's Missing" in the write-up for a sketch of a persistent-store swap-in).

## Related Reading

- [Coding Agents Don't Need Longer History — They Need Intent Continuity](https://towardsdatascience.com/author/emmimalp.alexander/) — the full write-up this repo accompanies
- [context-engine](https://github.com/Emmimal/context-engine) — a related but distinct problem: managing what enters an LLM's context window (retrieval, re-ranking, memory decay, token budgets), rather than verifying whether retrieved history is still valid

## License

MIT — see [LICENSE](LICENSE).

## Disclosure

All code in this repository was written by the author and is original work, developed and tested on Python 3.12. All benchmark numbers reported in the linked article are from actual runs of this code, reproducible by cloning the repo and running `run_experiment.py` — none are calculated or simulated after the fact.
