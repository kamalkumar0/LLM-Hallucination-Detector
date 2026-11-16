# HDLR — Hallucination Detection in LLM Responses

Pipeline: **claim extraction → Wikipedia retrieval → NLI → verdict**, with a Flask web UI to inspect the evidence.

```
LLM answer
   │  claims.py     split into atomic claims (rule-based)
   ▼
claims ──► retrieval.py   Wikipedia search + sentence ranking (MiniLM embeddings)
   │
   ▼
(evidence, claim) ──► nli.py   DeBERTa-v3 NLI: entailment / neutral / contradiction
   │
   ▼
verdict.py   per-claim label + overall hallucination score
```

## Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py      # then open http://127.0.0.1:5000
pytest -q          # unit tests for verdict logic (no model download needed)
```
First run downloads the NLI + embedding models (~500 MB total).

## Verdict rules
- **SUPPORTED**: best entailment >= threshold and >= best contradiction
- **CONTRADICTED**: best contradiction >= threshold
- **NOT ENOUGH INFO**: otherwise
- Overall: any contradicted claim → *HALLUCINATION DETECTED*; else many unverifiable → *PARTIALLY UNVERIFIED*; else *FACTUALLY CONSISTENT*

## Known limitations (good for your report)
- Wikipedia only: true facts not on Wikipedia come out as "not enough info".
- Search uses the raw claim text; entity extraction would improve retrieval.
- Rule-based splitter does not resolve pronouns ("He was born in...").
- NLI models are sentence-level; multi-sentence reasoning can be missed.

## Ideas to extend
Evaluate on FEVER / HaluEval, add a web-search retriever, add reranking with a cross-encoder, report precision/recall per label.