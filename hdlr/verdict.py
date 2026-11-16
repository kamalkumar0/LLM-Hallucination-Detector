"""Step 4: turn NLI probabilities into per-claim and overall verdicts."""
from collections import Counter

SUPPORTED = "SUPPORTED"
CONTRADICTED = "CONTRADICTED"
UNVERIFIABLE = "NOT ENOUGH INFO"


def claim_verdict(nli_results: list[dict[str, float]], support_thr=0.5, contradict_thr=0.5):
    """Aggregate NLI results across evidence sentences for ONE claim.
    Returns (label, best_entailment, best_contradiction)."""
    if not nli_results:
        return UNVERIFIABLE, 0.0, 0.0
    ent = max(r.get("entailment", 0.0) for r in nli_results)
    con = max(r.get("contradiction", 0.0) for r in nli_results)
    if ent >= support_thr and ent >= con:
        return SUPPORTED, ent, con
    if con >= contradict_thr:
        return CONTRADICTED, ent, con
    return UNVERIFIABLE, ent, con


def overall_verdict(labels: list[str], unverified_tolerance=0.3):
    """Returns (verdict_text, hallucination_score in [0,1])."""
    n = len(labels)
    if n == 0:
        return "NO CLAIMS FOUND", 0.0
    c = Counter(labels)
    # contradicted counts fully, unverifiable counts half
    score = (c[CONTRADICTED] + 0.5 * c[UNVERIFIABLE]) / n
    if c[CONTRADICTED] > 0:
        return "HALLUCINATION DETECTED", score
    if c[UNVERIFIABLE] / n > unverified_tolerance:
        return "PARTIALLY UNVERIFIED", score
    return "FACTUALLY CONSISTENT", score
