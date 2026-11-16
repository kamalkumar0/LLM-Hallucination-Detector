from dataclasses import dataclass


@dataclass
class Config:
    # Models (both run locally via Hugging Face)
    nli_model: str = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Retrieval
    wiki_lang: str = "en"
    pages_per_claim: int = 3
    top_k_evidence: int = 3
    max_sentences_per_page: int = 400
    user_agent: str = "HDLR-student-project/0.1 (educational use)"

    # Verdict thresholds
    support_threshold: float = 0.5
    contradict_threshold: float = 0.5
    unverified_tolerance: float = 0.3  # >30% unverifiable claims => "partially unverified"