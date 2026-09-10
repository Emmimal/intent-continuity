"""
Pure rule-based extraction: turns raw Interaction text into structured
IntentRecords. No embeddings, no LLM calls - just trigger-phrase and
keyword-substring matching.

This step is deliberately imperfect: a few "trap" interactions use
requirement-sounding language without being real requirements, which
gives the extractor a small, honestly-reported false-positive rate
instead of a suspiciously clean 100%.
"""

from typing import List, Tuple, Optional
from .data_model import Interaction, IntentRecord

TRIGGER_PHRASES = [
    "must", "never", "required", "require", "prefer", "should",
    "always", "migrating", "let's use", "default", "for now",
]

# (keywords, component) checked in priority order - first match wins.
COMPONENT_PRIORITY = [
    (["oauth", "jwt", "authentication"], "auth"),
    (["database user id", "internal database"], "security"),
    (["postgres", "sqlite", "database"], "database"),
    (["dashboard", "theme", "sections"], "ui"),
    (["inference", "quantized", "model"], "performance"),
    (["integration test", "merge"], "testing"),
    (["deploy", "staging"], "deployment"),
    (["api response", "endpoint", "rate limiting"], "api"),
]


def _looks_like_requirement(text: str) -> bool:
    lower = text.lower()
    return any(t in lower for t in TRIGGER_PHRASES)


def _classify_component(text: str) -> Optional[str]:
    lower = text.lower()
    for keywords, component in COMPONENT_PRIORITY:
        if any(k in lower for k in keywords):
            return component
    return None


def _classify_type(text: str) -> str:
    lower = text.lower()
    if "prefer" in lower or "default" in lower:
        return "preference"
    if any(t in lower for t in ["must", "never", "required", "require"]):
        return "constraint"
    return "decision"


def _classify_scope(text: str) -> Optional[str]:
    lower = text.lower()
    if "prototype" in lower:
        return "prototype"
    if "production" in lower:
        return "production"
    return None


def _extract_effect(component: str, text: str) -> Tuple[Optional[str], Optional[object]]:
    lower = text.lower()
    if component == "auth":
        if "oauth" in lower:
            return "auth_method", "oauth2"
        if "jwt" in lower:
            return "auth_method", "jwt"
    elif component == "security":
        return "hides_internal_ids", True
    elif component == "database":
        if "sqlite" in lower:
            return "database_engine", "sqlite"
        if "postgres" in lower:
            return "database_engine", "postgresql"
    elif component == "ui":
        if "dark" in lower:
            return "default_theme", "dark"
        if "section" in lower:
            return "dashboard_sections", ("Overview", "Performance", "Errors")
    elif component == "performance":
        return "uses_small_model", True
    elif component == "testing":
        return "has_integration_tests", True
    elif component == "deployment":
        return "requires_staging_validation", True
    elif component == "api":
        if "backward compatible" in lower:
            return "preserves_old_fields", True
        if "rate limiting" in lower:
            return "rate_limited", True
    return None, None


def extract_intent_records(interactions: List[Interaction]) -> Tuple[List[IntentRecord], dict]:
    """
    Returns (records, extractor_eval) where extractor_eval reports how the
    rule-based flagging compared to the ground-truth is_requirement_bearing
    label (precision/recall on the *flagging* step, before any component
    classification).
    """
    records: List[IntentRecord] = []
    last_decision_per_key = {}  # (component, scope) -> most recent IntentRecord with an effect

    true_positive = false_positive = false_negative = 0

    for interaction in interactions:
        flagged = _looks_like_requirement(interaction.text)

        if flagged and interaction.is_requirement_bearing:
            true_positive += 1
        elif flagged and not interaction.is_requirement_bearing:
            false_positive += 1
        elif (not flagged) and interaction.is_requirement_bearing:
            false_negative += 1

        if not flagged:
            continue

        component = _classify_component(interaction.text)
        if component is None:
            # Trigger word fired but nothing recognizable to act on
            # (this is exactly what happens with the "trap" interactions).
            continue

        effect_key, effect_value = _extract_effect(component, interaction.text)
        if effect_key is None:
            continue

        req_type = _classify_type(interaction.text)
        scope = _classify_scope(interaction.text)

        record_id = f"R{len(records) + 1}"
        record = IntentRecord(
            id=record_id,
            source_interaction_id=interaction.id,
            index=interaction.index,
            req_type=req_type,
            component=component,
            scope=scope,
            text=interaction.text,
            effect_key=effect_key,
            effect_value=effect_value,
        )

        # Supersession: same (component, scope, effect_key) reappearing with a
        # different value means the new one replaces the old one.
        key = (component, scope, effect_key)
        prior = last_decision_per_key.get(key)
        if prior is not None and prior.effect_value != effect_value:
            record.supersedes = prior.id
        last_decision_per_key[key] = record

        records.append(record)

    extractor_eval = {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
    }
    return records, extractor_eval
