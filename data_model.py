"""
Core data structures for the intent-continuity prototype.

Everything here is a plain dataclass. No external dependencies.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class Interaction:
    """One turn in the synthetic conversation history."""
    id: str
    index: int              # position in the chronological history (0 = oldest)
    text: str
    is_requirement_bearing: bool = False   # ground truth, used only to score the extractor


@dataclass
class IntentRecord:
    """
    A structured requirement/decision/preference pulled out of an Interaction
    by the extractor. This is what retrieval and verification actually operate on.
    """
    id: str
    source_interaction_id: str
    index: int               # inherited from the source interaction (chronological position)
    req_type: str             # "constraint" | "decision" | "preference"
    component: str            # e.g. "auth", "api", "database", "ui", "security", "performance", "testing", "deployment"
    scope: Optional[str]      # None (applies everywhere) | "prototype" | "production"
    text: str
    effect_key: str           # the field on Implementation this record governs
    effect_value: Any         # the value it sets
    supersedes: Optional[str] = None   # id of an earlier IntentRecord this one replaces (same effect_key)


@dataclass
class Task:
    """A later coding request that may depend on earlier, unstated requirements."""
    id: str
    index: int
    text: str
    component: str
    scope: Optional[str]                 # scope the task itself operates in, e.g. "production" / "prototype" / None
    expected_requirement_ids: List[str]  # ground truth: which planted IntentRecords should apply
    checker_name: str                    # which function in checkers.py grades this task
    # NOTE: component-to-component relationships (e.g. "auth work also
    # touches security") are NOT declared here per task. They come from the
    # single global schema in domain_schema.py, applied uniformly to every
    # task's primary component - see retrieval.py and README "Honest Design
    # Decisions" for why a per-task version of this was replaced.


@dataclass
class RetrievalResult:
    """What a retrieval strategy handed back for a given task."""
    condition: str                       # "baseline" | "semantic_naive" | "intent_aware"
    task_id: str
    raw_candidates: List[IntentRecord] = field(default_factory=list)   # everything retrieved, pre-resolution
    recovered: List[IntentRecord] = field(default_factory=list)        # after any resolution step (dedup/supersession/scope)
    retrieved_noise_ids: List[str] = field(default_factory=list)       # non-requirement interactions pulled in (semantic_naive only)


@dataclass
class Implementation:
    """
    The deterministic 'thing the agent built', expressed purely as a set of
    fields it decided on. No LLM is involved: this is a template that reacts
    only to whatever ended up in its supplied context.
    """
    fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckOutcome:
    task_id: str
    condition: str
    passed: bool
    violations: List[str] = field(default_factory=list)
