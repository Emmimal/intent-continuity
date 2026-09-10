"""
Turns whatever a retrieval strategy produced into the flat key/value
context the agent template consumes.

Resolution rule (applied identically for every condition): sort the
supplied records chronologically and let the latest one win per
effect_key. For intent_aware, verification.py has already dropped
superseded/out-of-scope records before this point, so resolution here
is usually a no-op. For semantic_naive, nothing has been dropped yet,
so this is where a stale or out-of-scope record can still win simply
by being the most recent thing mentioned - which is exactly the
failure mode the article is about.

Also returns provenance (effect_key -> the IntentRecord that supplied
it) and a token estimate, both used by metrics.py.
"""

from typing import List, Tuple, Dict, Optional
from .data_model import IntentRecord


def compile_context(context_records: List[IntentRecord]) -> Tuple[Dict[str, object], Dict[str, Optional[IntentRecord]], int]:
    provenance: Dict[str, IntentRecord] = {}
    for record in sorted(context_records, key=lambda r: r.index):
        provenance[record.effect_key] = record  # later overwrites earlier

    fields = {key: record.effect_value for key, record in provenance.items()}
    token_estimate = sum(len(r.text.split()) for r in context_records)
    return fields, provenance, token_estimate
