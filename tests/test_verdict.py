from hdlr.claims import split_rule_based
from hdlr.verdict import (CONTRADICTED, SUPPORTED, UNVERIFIABLE,
                          claim_verdict, overall_verdict)


def test_supported():
    assert claim_verdict([{"entailment": 0.9, "contradiction": 0.05}])[0] == SUPPORTED


def test_contradicted():
    assert claim_verdict([{"entailment": 0.1, "contradiction": 0.85}])[0] == CONTRADICTED


def test_no_evidence():
    assert claim_verdict([])[0] == UNVERIFIABLE


def test_overall():
    assert overall_verdict([SUPPORTED, CONTRADICTED])[0] == "HALLUCINATION DETECTED"
    assert overall_verdict([SUPPORTED, SUPPORTED])[0] == "FACTUALLY CONSISTENT"
    assert overall_verdict([SUPPORTED, UNVERIFIABLE])[0] == "PARTIALLY UNVERIFIED"


def test_split():
    out = split_rule_based("Paris is in France. It is big; it has a tower. Hi.")
    assert len(out) == 2
