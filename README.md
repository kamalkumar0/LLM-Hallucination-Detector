# LLM Hallucination Detector (HDLR)

Check whether an AI-generated answer is actually true. HDLR pulls out every factual claim, finds matching evidence on Wikipedia, and uses a Natural Language Inference (NLI) model to judge each claim as **supported**, **contradicted**, or **not enough info**.

Everything runs locally with Hugging Face models. No paid API or API key is needed.

---

## Screenshots

### Home screen
Paste an LLM response (or drop a PDF) and press **Check for hallucinations**.

![Home screen](screenshots/01_UI.png)

### Settings
Tune how much evidence is fetched and how strict the verdicts are.

![Settings panel](screenshots/02_Controls.png)

### PDF upload
Upload a PDF by browsing or drag and drop. The text inside is checked claim by claim.

![PDF upload](screenshots/03_upload_file.png)

### Overall verdict
A score ring and verdict summarise the whole response, with filters for each claim type.

![Hallucination detected](screenshots/04_hallucination_detected.png)

### Claim details
Open any claim to see the Wikipedia sentences used as evidence, with entailment and contradiction scores.

![Claim details](screenshots/05_detected_screen.png)

### Evidence breakdown
Every evidence sentence shows its source link, similarity score and NLI probabilities.

![Evidence breakdown](screenshots/06_detected_screen.png)

---

## Features

- Claim extraction: splits a response into individual checkable claims
- Wikipedia retrieval: finds the most relevant evidence sentences for each claim
- NLI verification: DeBERTa-v3 decides entailment, contradiction or neutral
- Overall hallucination score with a clear verdict
- Paste text or upload a PDF (drag and drop supported)
- Adjustable settings: evidence count, pages per claim, support and contradiction thresholds
- Filter claims by verdict and inspect the evidence for each one
- Download the full report as JSON
- Dark, responsive UI

## How it works

```
LLM answer
   |  claims.py      split into claims
   v
claims --> retrieval.py   Wikipedia search + sentence ranking (MiniLM embeddings)
   |
   v
(evidence, claim) --> nli.py   DeBERTa-v3: entailment / neutral / contradiction
   |
   v
verdict.py   per-claim label + overall hallucination score
```

### Verdict rules

| Result | Condition |
|---|---|
| **Supported** | best entailment >= support threshold and >= best contradiction |
| **Contradicted** | best contradiction >= contradiction threshold |
| **Not enough info** | anything else, or no evidence found |

**Overall verdict:** any contradicted claim gives *HALLUCINATION DETECTED*. Otherwise, too many unverifiable claims gives *PARTIALLY UNVERIFIED*. Otherwise it is *FACTUALLY CONSISTENT*.

**Score:** contradicted claims count fully and unverifiable claims count half, divided by the total number of claims.

## Tech stack

- **Backend:** Python, Flask
- **Models:** `MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli` (NLI), `all-MiniLM-L6-v2` (embeddings)
- **Libraries:** PyTorch, Transformers, Sentence-Transformers, pypdf, Requests
- **Frontend:** HTML, CSS, vanilla JavaScript
- **Evidence source:** Wikipedia API

## Project structure

```
.
├── app.py                 # Flask server and API
├── hdlr/
│   ├── claims.py          # claim extraction
│   ├── retrieval.py       # Wikipedia search and ranking
│   ├── nli.py             # NLI classifier
│   ├── verdict.py         # verdict and score logic
│   ├── pipeline.py        # ties all steps together
│   └── config.py          # models and default thresholds
├── templates/index.html
├── static/
│   ├── css/style.css
│   └── js/main.js
├── tests/test_verdict.py
├── screenshots/
└── requirements.txt
```

## Getting started

```bash
git clone https://github.com/kamalkumar0/LLM-Hallucination-Detector.git
cd LLM-Hallucination-Detector

python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

The first check downloads the NLI and embedding models (about 500 MB in total), so it can take a minute. Later checks are much faster.

### Run the tests

```bash
python -m pytest -q
```

The tests cover the verdict logic and do not download any model.

## Known limitations

- Wikipedia only: true facts that are not on Wikipedia come out as "not enough info".
- Search uses the raw claim text, so entity extraction would improve retrieval.
- The rule-based splitter does not resolve pronouns (for example "He was born in...").
- NLI works at sentence level, so reasoning across several sentences can be missed.
- Input is capped at 6,000 characters per check, because every claim triggers Wikipedia lookups.

## Future improvements

- Evaluate on FEVER and HaluEval, with precision and recall per label
- Add a web-search retriever beyond Wikipedia
- Rerank evidence with a cross-encoder
- Resolve pronouns and extract entities for better claims and search

## Author

**Kamal Kumar** · [@kamalkumar0](https://github.com/kamalkumar0)
