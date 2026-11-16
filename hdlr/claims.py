"""Step 1: break an LLM answer into atomic, checkable claims."""
import re


def split_rule_based(text: str) -> list[str]:
    """Sentences first, then semicolon-separated parts."""
    text = re.sub(r"\s+", " ", text.strip())
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", text)
    claims = []
    for sent in sentences:
        for part in sent.split(";"):
            part = part.strip()
            if len(part.split()) >= 4:  # skip fragments
                claims.append(part)
    return claims


def extract_claims(text: str) -> tuple[list[str], str]:
    """Returns (claims, method_used)."""
    return split_rule_based(text), "rule-based"