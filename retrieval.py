"""
Three retrieval strategies competing on the same tasks:

baseline        - no history at all.
semantic_naive  - stand-in for "plug in a vector database": broad
                  word-overlap search over the RAW interaction stream
                  (not the extracted intent records), no notion of
                  scope or supersession. Resolves conflicts by taking
                  whichever matching record is chronologically most
                  recent per effect_key.
intent_aware    - retrieves over the extracted IntentRecords using
                  component association plus keyword overlap, then
                  hands candidates to verification.py for
                  scope/supersession resolution.

No embeddings anywhere - "semantic" here is deliberately simulated with
plain lexical overlap, which is the whole point: the interesting part of
this pipeline is not the retrieval step.
"""

from typing import List, Dict
from .data_model import Interaction, IntentRecord, Task, RetrievalResult
from .utils import significant_words
from .domain_schema import related_components


def retrieve_baseline(task: Task, interactions: List[Interaction],
                       records: List[IntentRecord]) -> RetrievalResult:
    return RetrievalResult(condition="baseline", task_id=task.id,
                            raw_candidates=[], recovered=[])


def retrieve_semantic_naive(task: Task, interactions: List[Interaction],
                             records: List[IntentRecord]) -> RetrievalResult:
    task_words = significant_words(task.text)
    records_by_interaction_id = {r.source_interaction_id: r for r in records}

    matched_records: List[IntentRecord] = []
    noise_ids: List[str] = []

    for interaction in interactions:
        overlap = significant_words(interaction.text) & task_words
        if not overlap:
            continue
        record = records_by_interaction_id.get(interaction.id)
        if record is not None:
            matched_records.append(record)
        else:
            noise_ids.append(interaction.id)

    # Deliberately no resolution here: everything matched gets handed
    # downstream unfiltered. compiler.py applies the same "most recent
    # wins" rule used for every condition - this strategy just never
    # dropped the stale/out-of-scope candidates first.
    return RetrievalResult(
        condition="semantic_naive",
        task_id=task.id,
        raw_candidates=matched_records,
        recovered=matched_records,
        retrieved_noise_ids=noise_ids,
    )


def retrieve_intent_aware_candidates(task: Task, records: List[IntentRecord]) -> List[IntentRecord]:
    """
    Candidate generation only (no scope/supersession resolution yet -
    that happens in verification.py). A record is a candidate if:
      - it shares the task's primary component,
      - it belongs to a component the GLOBAL domain schema (domain_schema.py)
        says structurally relates to the task's primary component - a
        general rule applied to every task, not a per-task hint - or
      - it has strong keyword overlap with the task text regardless of component.
    """
    task_words = significant_words(task.text)
    relevant_components = {task.component} | related_components(task.component)
    candidates = []
    for record in records:
        component_match = record.component in relevant_components
        overlap = significant_words(record.text) & task_words
        if component_match or len(overlap) >= 2:
            candidates.append(record)
    return candidates
