"""Step 3: NLI — does the evidence entail / contradict / say nothing about the claim?"""
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class NLIClassifier:
    def __init__(self, model_name: str):
        self.tok = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).eval()
        cfg = self.model.config
        self.labels = [cfg.id2label[i].lower() for i in range(len(cfg.id2label))]

    @torch.no_grad()
    def predict(self, premises: list[str], hypothesis: str) -> list[dict[str, float]]:
        """premise = evidence sentence, hypothesis = claim."""
        if not premises:
            return []
        enc = self.tok(
            premises, [hypothesis] * len(premises),
            truncation=True, padding=True, max_length=256, return_tensors="pt",
        )
        probs = torch.softmax(self.model(**enc).logits, dim=-1)
        return [
            {label: float(probs[i, j]) for j, label in enumerate(self.labels)}
            for i in range(len(premises))
        ]
