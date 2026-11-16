from dataclasses import dataclass, field

from .claims import extract_claims
from .config import Config
from .nli import NLIClassifier
from .retrieval import Evidence, WikipediaRetriever
from .verdict import claim_verdict, overall_verdict


@dataclass
class ClaimResult:
    claim: str
    verdict: str
    entailment: float
    contradiction: float
    evidence: list[Evidence] = field(default_factory=list)
    nli: list[dict] = field(default_factory=list)


@dataclass
class Report:
    claims: list[ClaimResult]
    overall: str
    score: float
    extraction_method: str


class HDLRPipeline:
    def __init__(self, cfg: Config | None = None):
        self.cfg = cfg or Config()
        self.retriever = WikipediaRetriever(self.cfg)
        self.nli = NLIClassifier(self.cfg.nli_model)

    def run(self, text: str, progress=None) -> Report:
        claims, method = extract_claims(text)
        results = []
        for i, claim in enumerate(claims):
            if progress:
                progress(i, len(claims), claim)
            evidence = self.retriever.retrieve(claim)
            nli = self.nli.predict([e.sentence for e in evidence], claim)
            label, ent, con = claim_verdict(
                nli, self.cfg.support_threshold, self.cfg.contradict_threshold
            )
            results.append(ClaimResult(claim, label, ent, con, evidence, nli))
        overall, score = overall_verdict(
            [r.verdict for r in results], self.cfg.unverified_tolerance
        )
        return Report(results, overall, score, method)