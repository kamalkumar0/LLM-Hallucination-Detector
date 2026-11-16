"""Step 2: retrieve evidence sentences from Wikipedia for a claim."""
import re
from dataclasses import dataclass
from urllib.parse import quote

import requests
from sentence_transformers import SentenceTransformer, util

from .config import Config


@dataclass
class Evidence:
    title: str
    url: str
    sentence: str
    similarity: float


class WikipediaRetriever:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.api = f"https://{cfg.wiki_lang}.wikipedia.org/w/api.php"
        self.session = requests.Session()
        self.session.headers["User-Agent"] = cfg.user_agent
        self.embedder = SentenceTransformer(cfg.embed_model)
        self._cache: dict[str, tuple[list[str], object]] = {}

    def _search(self, query: str) -> list[str]:
        r = self.session.get(
            self.api,
            params={
                "action": "query", "list": "search", "srsearch": query,
                "srlimit": self.cfg.pages_per_claim, "format": "json",
            },
            timeout=10,
        )
        r.raise_for_status()
        return [h["title"] for h in r.json()["query"]["search"]]

    def _page(self, title: str):
        """Returns (sentences, embeddings) for a page, cached."""
        if title in self._cache:
            return self._cache[title]
        r = self.session.get(
            self.api,
            params={
                "action": "query", "prop": "extracts", "explaintext": 1,
                "titles": title, "redirects": 1, "format": "json",
            },
            timeout=15,
        )
        r.raise_for_status()
        page = next(iter(r.json()["query"]["pages"].values()))
        text = re.sub(r"=+[^=\n]+=+", " ", page.get("extract", ""))
        text = re.sub(r"\s+", " ", text)
        sents = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
        sents = [s.strip() for s in sents if len(s.strip()) >= 30]
        sents = sents[: self.cfg.max_sentences_per_page]
        emb = self.embedder.encode(sents, convert_to_tensor=True) if sents else None
        self._cache[title] = (sents, emb)
        return self._cache[title]

    def retrieve(self, claim: str) -> list[Evidence]:
        try:
            titles = self._search(claim)
        except requests.RequestException:
            return []
        claim_emb = self.embedder.encode(claim, convert_to_tensor=True)
        pool: list[Evidence] = []
        for title in titles:
            try:
                sents, emb = self._page(title)
            except requests.RequestException:
                continue
            if emb is None:
                continue
            sims = util.cos_sim(claim_emb, emb)[0]
            url = f"https://{self.cfg.wiki_lang}.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"
            for s, sim in zip(sents, sims):
                pool.append(Evidence(title, url, s, float(sim)))
        pool.sort(key=lambda e: e.similarity, reverse=True)
        return pool[: self.cfg.top_k_evidence]
