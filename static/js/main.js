const $ = (s) => document.querySelector(s);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const pct = (x) => Math.round(x * 100);
const kind = (v) => (v === "SUPPORTED" ? "sup" : v === "CONTRADICTED" ? "con" : "unv");
const LABEL = { sup: "Supported", con: "Contradicted", unv: "Not enough info" };

let report = null;
let filter = "all";
let pdfFile = null;
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

// live value + filled track for each slider
document.querySelectorAll("input[type=range]").forEach((r) => {
  const out = r.parentElement.querySelector("output");
  const update = () => {
    out.textContent = r.value;
    r.style.setProperty("--p", ((r.value - r.min) / (r.max - r.min)) * 100 + "%");
  };
  r.addEventListener("input", update);
  update();
});

$("#run").addEventListener("click", async () => {
  const btn = $("#run");
  $("#error").hidden = true;
  $("#results").hidden = true;
  $("#busy").hidden = false;
  btn.disabled = true;
  btn.classList.add("loading");
  btn.textContent = "Checking claims…";
  try {
    const fd = new FormData();
    fd.append("text", $("#text").value);
    fd.append("top_k", $("#top_k").value);
    fd.append("pages", $("#pages").value);
    fd.append("sup_thr", $("#sup_thr").value);
    fd.append("con_thr", $("#con_thr").value);
    if (pdfFile) fd.append("pdf", pdfFile);
    const res = await fetch("/api/check", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Something went wrong. Try again.");
    report = data;
    filter = "all";
    render(true);
  } catch (e) {
    $("#error").textContent = e.message;
    $("#error").hidden = false;
  } finally {
    btn.disabled = false;
    btn.classList.remove("loading");
    btn.textContent = "Check for hallucinations";
    $("#busy").hidden = true;
  }
});

function render(fresh = false) {
  const claims = report.claims;
  const count = { sup: 0, con: 0, unv: 0 };
  claims.forEach((c) => count[kind(c.verdict)]++);

  const top = count.con ? "con" : report.overall === "FACTUALLY CONSISTENT" ? "sup" : "unv";
  $(".summary").className = "summary v-" + top;
  $("#overall").textContent = report.overall;
  $("#gauge").className = "gauge";
  fresh ? countUp($("#score"), pct(report.score)) : setScore(pct(report.score));
  $("#meta").textContent = `${claims.length} claims from ${report.source}, split by ${report.extraction_method}` +
    (report.truncated ? `. Only the first ${report.chars.toLocaleString()} characters were checked.` : "");

  const chips = [["all", `All (${claims.length})`], ["sup", `Supported (${count.sup})`], ["con", `Contradicted (${count.con})`], ["unv", `Not enough info (${count.unv})`]];
  const ratio = claims.length
    ? `<div class="ratio">${["sup", "unv", "con"].map((k) => `<i class="${k}" style="flex:${count[k]}"></i>`).join("")}</div>`
    : "";
  $("#filters").innerHTML = ratio + chips.map(([k, t]) => `<button data-k="${k}" aria-pressed="${k === filter}">${t}</button>`).join("");
  $("#filters").querySelectorAll("button").forEach((b) =>
    b.addEventListener("click", () => { filter = b.dataset.k; render(); })
  );

  const shown = claims.filter((c) => filter === "all" || kind(c.verdict) === filter);
  $("#claims").innerHTML = shown.length
    ? shown.map((c, i) => claimHTML(c, i)).join("")
    : '<li><p class="body" style="border:0">No claims in this group.</p></li>';
  $("#results").hidden = false;
  if (fresh) {
    const r = $("#results");
    r.classList.remove("show");
    void r.offsetWidth; // restart the entrance animation
    r.classList.add("show");
    r.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
  }
}

function claimHTML(c, i = 0) {
  const k = kind(c.verdict);
  const ev = c.evidence.length
    ? c.evidence.map((e, i) => {
        const p = c.nli[i] || {};
        const ent = p.entailment || 0, con = p.contradiction || 0;
        return `<div class="ev">
          <a href="${esc(e.url)}" target="_blank" rel="noopener">${esc(e.title)}</a>
          <small> · similarity ${e.similarity.toFixed(2)}</small>
          <blockquote>${esc(e.sentence)}</blockquote>
          <div class="bar e"><span>Entailment</span><div class="track"><div class="fill" style="--w:${pct(ent)}%"></div></div><span>${ent.toFixed(2)}</span></div>
          <div class="bar c"><span>Contradiction</span><div class="track"><div class="fill" style="--w:${pct(con)}%"></div></div><span>${con.toFixed(2)}</span></div>
        </div>`;
      }).join("")
    : '<p class="nums">No evidence found on Wikipedia for this claim.</p>';
  return `<li class="${k}" style="--i:${Math.min(i, 10)}"><details>
    <summary><span class="tag">${LABEL[k]}</span><span class="claim-text">${esc(c.claim)}</span><span class="chev">▸</span></summary>
    <div class="body"><p class="nums">Best entailment ${c.entailment.toFixed(2)} · Best contradiction ${c.contradiction.toFixed(2)}</p>${ev}</div>
  </details></li>`;
}

$("#download").addEventListener("click", () => {
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "hdlr-report.json";
  a.click();
  URL.revokeObjectURL(a.href);
});

function setScore(v) {
  $("#score").textContent = v + "%";
  $("#gauge").style.setProperty("--p", v);
}

function countUp(el, to) {
  if (reduce) { setScore(to); return; }
  const t0 = performance.now(), dur = 900;
  const step = (t) => {
    const p = Math.min((t - t0) / dur, 1);
    setScore(Math.round(to * (1 - Math.pow(1 - p, 3))));
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

// PDF upload: click, or drag and drop
const drop = $("#drop"), picker = $("#pdf");
function setFile(f) {
  if (f && !/\.pdf$/i.test(f.name)) {
    $("#error").textContent = "Upload a .pdf file.";
    $("#error").hidden = false;
    return;
  }
  $("#error").hidden = true;
  pdfFile = f;
  $("#fname").textContent = f ? f.name : "";
  drop.classList.toggle("has-file", !!f);
  $("#text").disabled = !!f; // the PDF takes priority over pasted text
}
picker.addEventListener("change", () => setFile(picker.files[0] || null));
$("#clear").addEventListener("click", () => { picker.value = ""; setFile(null); });
["dragenter", "dragover"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", (e) => setFile(e.dataTransfer.files[0] || null));