import re
import threading
from dataclasses import asdict

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, render_template, request

from hdlr.config import Config
from hdlr.pipeline import HDLRPipeline

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024  # 15 MB upload cap

MAX_CHARS = 6000  # each claim triggers Wikipedia lookups, so cap the input
_pipe = None
_lock = threading.Lock()  # one check at a time: the pipeline config is shared

SAMPLE = (
    "The Eiffel Tower is located in Paris. It was completed in 1889. "
    "It was designed by Thomas Edison. The tower is about 330 metres tall."
)


def get_pipeline() -> HDLRPipeline:
    global _pipe
    if _pipe is None:  # models load on the first check, then stay in memory
        _pipe = HDLRPipeline(Config())
    return _pipe


def num(value, lo, hi, default):
    try:
        return min(max(float(value), lo), hi)
    except (TypeError, ValueError):
        return default


def read_pdf(file) -> str:
    from pypdf import PdfReader

    parts, total = [], 0
    for page in PdfReader(file.stream).pages:
        t = page.extract_text() or ""
        parts.append(t)
        total += len(t)
        if total >= MAX_CHARS:  # no need to read the rest
            break
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


@app.get("/")
def index():
    return render_template("index.html", d=Config(), sample=SAMPLE)


@app.post("/api/check")
def check():
    form = request.form
    pdf = request.files.get("pdf")

    if pdf and pdf.filename:
        if not pdf.filename.lower().endswith(".pdf"):
            return jsonify(error="Upload a .pdf file."), 400
        try:
            text = read_pdf(pdf)
        except Exception:
            return jsonify(error="Couldn't read this PDF. It may be corrupted or password-protected."), 400
        if not text:
            return jsonify(error="No selectable text found. Scanned PDFs need OCR first."), 400
        source = pdf.filename
    else:
        text = (form.get("text") or "").strip()
        if not text:
            return jsonify(error="Paste text or upload a PDF to check."), 400
        source = "pasted text"

    truncated = len(text) > MAX_CHARS
    text = text[:MAX_CHARS]

    try:
        with _lock:
            pipe = get_pipeline()
            c = pipe.cfg
            c.top_k_evidence = int(num(form.get("top_k"), 1, 6, c.top_k_evidence))
            c.pages_per_claim = int(num(form.get("pages"), 1, 5, c.pages_per_claim))
            c.support_threshold = num(form.get("sup_thr"), 0.3, 0.95, c.support_threshold)
            c.contradict_threshold = num(form.get("con_thr"), 0.3, 0.95, c.contradict_threshold)
            report = pipe.run(text)
    except Exception as exc:  # surface a readable message instead of a 500 page
        return jsonify(error=f"Check failed: {exc}"), 500

    out = asdict(report)
    out.update(source=source, truncated=truncated, chars=len(text))
    return jsonify(out)


@app.errorhandler(413)
def too_big(_):
    return jsonify(error="File is too large. Keep it under 15 MB."), 413


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)  # reloader off: avoids loading models twice