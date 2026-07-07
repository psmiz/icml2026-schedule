#!/usr/bin/env python3
"""
Build a personalized ICML 2026 schedule dataset for Sumin Park.

Pipeline
--------
1. Fetch ICML 2026 data:
     - orals + posters  : https://icml.cc/static/virtual/data/icml-2026-orals-posters.json
     - tutorials / workshops / orals / invited-talk listing pages (server-rendered HTML)
2. Score every event/poster against Sumin's research interests (see THEMES below).
3. Emit  data.js  -> sets  window.ICML_DATA  consumed by index.html.

Re-run any time to refresh:  python3 build.py
(Uses .cache/ if present; pass --fresh to force re-download.)
"""
import json, re, sys, os, urllib.request
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))   # ICML 2026 is in Seoul; show local Seoul time


def to_kst(iso):
    """Parse an ISO datetime (any offset ICML uses) -> (date 'YYYY-MM-DD', 'HH:MM')
    in Korea Standard Time. Handles the source switching between +09:00 and -07:00."""
    if not iso:
        return "", ""
    try:
        dt = datetime.fromisoformat(iso).astimezone(KST)
        return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
    except ValueError:
        return iso[:10], iso[11:16]   # fallback: naive slice

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, ".cache")
FRESH = "--fresh" in sys.argv

OP_URL = "https://icml.cc/static/virtual/data/icml-2026-orals-posters.json"
LIST_URLS = {
    "tutorial": "https://icml.cc/virtual/2026/events/tutorial",
    "workshop": "https://icml.cc/virtual/2026/events/workshop",
    "oral":     "https://icml.cc/virtual/2026/events/oral",
    "invited":  "https://icml.cc/virtual/2026/eventlistwithbios/invited%20talk",
}

# --------------------------------------------------------------------------
# Sumin's interest model.  Each theme has a label, color, weight, and matchers
# (substrings checked against title / topic / abstract, lowercased).
# Topics use the ICML taxonomy ("Area->Subarea").
# --------------------------------------------------------------------------
THEMES = [
    dict(key="seq", label="Sequence Modeling & Linear Attention", color="#e8590c", weight=5,
         kw=["linear attention","state space","state-space"," ssm","mamba","rwkv","retention",
             "delta rule","deltanet","associative recurr","recurren","gated linear","linear recurr",
             "long context","long-context","long sequence","s4 ","s5 ","kv cache","key-value",
             "test-time training","attention mechanism","subquadratic","sub-quadratic","gla "],
         topics=["Deep Learning->Attention Mechanisms",
                 "Deep Learning->Sequential Models, Time series"]),
    dict(key="moe", label="Mixture-of-Experts & Routing", color="#7048e8", weight=5,
         kw=["mixture of experts","mixture-of-experts"," moe ","moe)","(moe","expert routing",
             "router","routing","sparse activation","conditional computation","sparsely activated",
             "expert specialization","top-k expert"],
         topics=[]),
    dict(key="interp", label="Mechanistic Interpretability", color="#1971c2", weight=5,
         kw=["mechanistic","interpretab","circuit","sparse autoencoder"," sae ","sae)",
             "polysemantic","superposition","feature steering","activation patching","monosemantic",
             "logit lens","internal representation","concept bottleneck"],
         topics=["Social Aspects->Accountability, Transparency, and Interpretability"]),
    dict(key="repr", label="Representation Learning & Specialization", color="#0ca678", weight=4,
         kw=["representation learning","disentangl","functional specialization",
             "inductive bias","feature learning","grokking","neural collapse",
             "subspace","geometry of representation","linear representation"],
         topics=["General Machine Learning->Representation Learning",
                 "Deep Learning->Other Representation Learning"]),
    dict(key="gnn", label="Graph Neural Networks", color="#d6336c", weight=4,
         kw=["graph neural"," gnn","over-squashing","oversquashing","over-smoothing","oversmoothing",
             "message passing","graph transformer","spectral graph"],
         topics=["Deep Learning->Graph Neural Networks"]),
    dict(key="astro", label="AI for Astrophysics & Physical Sciences", color="#1098ad", weight=5,
         kw=["astro","cosmolog","galax","stellar","exoplanet","telescope","gravitational wave",
             "interstellar","supernova","spectroscop","sky survey","redshift","dark matter",
             "dark energy","simulation-based inference","physical science","physics-informed",
             "n-body","gravitation","celestial","light curve"],
         topics=["Applications->Astronomy"]),
    dict(key="neuro", label="Neuroscience & Brain-Inspired", color="#f08c00", weight=3,
         kw=["neuroscience","brain","cognitive","biologically plausible","neural coding",
             "spiking","cortex","cortical","neuro-inspired","brain-inspired"],
         topics=["Applications->Neuroscience, Cognitive Science"]),
    dict(key="tsbio", label="Time-Series & EEG Foundation Models", color="#087f5b", weight=4,
         kw=["time series foundation","time-series foundation","eeg","electroencephalo",
             "brain-computer","brain computer"," bci","physiological time","biosignal"],
         topics=[]),
    # Non-core: a broad context signal. Shown as a tag, but does NOT by itself make a
    # paper "relevant to me" (otherwise nearly every LLM paper would qualify).
    dict(key="llm", label="LLMs & Foundation Models", color="#495057", weight=2, core=False,
         kw=["large language model"," llm","foundation model","pretrain","pre-train",
             "transformer","scaling law","in-context learning","fine-tun"],
         topics=["Deep Learning->Large Language Models","Deep Learning->Foundation Models"]),
]

# Sumin's own ICML 2026 papers (highlighted specially if found in the data).
OWN_PAPERS = [
    "Q-Delta: Beyond Key", "Q-Delta", "STAR: Rethinking MoE Routing",
    "Structure-Aware Subspace",
]


def fetch(url, cache_name):
    path = os.path.join(CACHE, cache_name)
    if not FRESH and os.path.exists(path):
        return open(path, encoding="utf-8").read()
    os.makedirs(CACHE, exist_ok=True)
    print(f"  downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "replace")
    open(path, "w", encoding="utf-8").write(data)
    return data


def score(text, topic):
    """Return (total_score, [theme_keys]) for a piece of text + ICML topic."""
    t = (text or "").lower()
    topic = topic or ""
    hits, total = [], 0
    for th in THEMES:
        matched = any(k in t for k in th["kw"]) or topic in th["topics"]
        if matched:
            hits.append(th["key"])
            if th.get("core", True):        # only core interests gate relevance
                total += th["weight"]
    return total, hits


MONTHS = {m: i for i, m in enumerate(
    ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], 1)}


def norm_time(time_str):
    """'Jul 6, 9:00 AM - 11:30 AM' -> (date 'YYYY-MM-DD', sort_minutes)."""
    if not time_str:
        return "", 1 << 30
    m = re.match(r"([A-Za-z]{3})\s+(\d{1,2})", time_str)
    date = ""
    if m and m.group(1) in MONTHS:
        date = f"2026-{MONTHS[m.group(1)]:02d}-{int(m.group(2)):02d}"
    tm = re.search(r"(\d{1,2}):(\d{2})\s*([AP]M)", time_str)
    mins = 1 << 30
    if tm:
        h, mn, ap = int(tm.group(1)), int(tm.group(2)), tm.group(3)
        if ap == "PM" and h != 12:
            h += 12
        if ap == "AM" and h == 12:
            h = 0
        mins = h * 60 + mn
    return date, mins


def parse_cards(html):
    cards, parts = [], re.split(r'<span class="event-type-badge">', html)
    for p in parts[1:]:
        mt = re.match(r'\s*([^<]+)</span>', p)
        etype = mt.group(1).strip() if mt else ""
        mtitle = re.search(r'<h3 class="event-title">\s*<a href="([^"]+)">\s*(.*?)\s*</a>', p, re.S)
        if not mtitle:
            continue
        url = mtitle.group(1)
        title = re.sub(r"\s+", " ", mtitle.group(2)).strip()
        msp = re.search(r'<div class="event-speakers">\s*(.*?)\s*</div>', p, re.S)
        speakers = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", msp.group(1))).strip() if msp else ""
        mtime = re.search(r'class="touchup-time">\s*(.*?)\s*</span>', p, re.S)
        time = re.sub(r"\s+", " ", mtime.group(1)).strip() if mtime else ""
        mloc = re.search(r'fa-map-marker-alt"></i>\s*<span>(.*?)</span>', p, re.S)
        loc = mloc.group(1).strip() if mloc else ""
        mabs = re.search(r"<!-- Abstract -->(.*?)(?:<!--|</div>\s*</div>)", p, re.S)
        abstract = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", mabs.group(1))).strip() if mabs else ""
        date, mins = norm_time(time)
        cards.append(dict(type=etype, title=title, url=url, speakers=speakers,
                          time=time, date=date, mins=mins, loc=loc,
                          abstract=abstract[:700]))
    return cards


def main():
    print("Fetching ICML 2026 data...")
    op = json.loads(fetch(OP_URL, "icml_op.json"))["results"]
    listings = {k: parse_cards(fetch(v, f"ev_{k}.html")) for k, v in LIST_URLS.items()}

    # ---- Events (tutorials / invited talks / orals / workshops) ----
    events = []
    for kind, cards in listings.items():
        for c in cards:
            s, hits = score(c["title"] + " " + c["abstract"] + " " + c["speakers"], None)
            events.append({**c, "score": s, "themes": hits})

    # ---- Posters & orals from the structured feed ----
    def authors_str(a):
        names = [x.get("fullname", "") for x in (a or [])]
        return names

    def board_num(raw):
        # ICML gives board positions like "#3609"; keep the integer for clean
        # display (template adds the "#") and correct numeric sorting.
        if not raw:
            return None
        digits = re.sub(r"\D", "", str(raw))
        return int(digits) if digits else None

    posters = []
    own = []
    for x in op:
        if x["eventtype"] != "Poster":
            continue
        s, hits = score(x["name"] + " " + (x.get("topic") or ""), x.get("topic"))
        p_date, p_time = to_kst(x.get("starttime"))
        _, p_end = to_kst(x.get("endtime"))
        rec = dict(
            id=x["id"], title=x["name"], authors=authors_str(x["authors"])[:6],
            topic=x.get("topic") or "", session=x.get("session") or "",
            date=p_date, time=p_time, end=p_end,
            room=x.get("room_name") or "", url=x.get("virtualsite_url") or "",
            paper=x.get("paper_url") or "", pos=board_num(x.get("poster_position")),
            score=s, themes=hits,
        )
        if any(o.lower() in x["name"].lower() for o in OWN_PAPERS):
            rec["own"] = True
            own.append(rec["title"])
        posters.append(rec)

    # ---- apply per-paper title review (curation.json) ----
    # Built by reviewing every poster TITLE individually (see review pipeline / README).
    # Overrides the coarse keyword scoring: relevance = membership in the curated set,
    # and each kept paper gets a single, human-reviewed theme tag.
    cur_path = os.path.join(HERE, "curation.json")
    if os.path.exists(cur_path):
        curation = json.load(open(cur_path))
        wmap = {th["key"]: th["weight"] for th in THEMES}
        kept = 0
        for p in posters:
            c = curation.get(str(p["id"]))
            if c:
                p["themes"] = [c["theme"]]
                p["conf"] = c["conf"]
                p["score"] = wmap.get(c["theme"], 4) + (3 if c["conf"] == "high" else 0)
                kept += 1
            elif not p.get("own"):
                p["themes"] = []          # not a fit -> no relevance, no tags
                p["score"] = 0
        print(f"  applied curation.json — {kept} title-reviewed posters kept relevant")
    else:
        print("  (no curation.json; using keyword scoring)")

    # Session -> (date, start, end, room) lookup for the schedule map.
    sessions = {}
    for p in posters:
        if p["session"]:
            sessions.setdefault(p["session"], dict(date=p["date"], start=p["time"],
                                                   end=p["end"], room=p["room"]))

    out = dict(
        generated="2026-06-18",
        # Identity scrubbed for public sharing; the page header no longer shows it.
        person=dict(
            name="", affil="", home="",
            interests=[
                "Mechanistic interpretability of LLMs",
                "Efficient sequence modeling (state space models, linear attention)",
                "Representation learning & functional specialization",
                "Mixture-of-Experts routing & subspace learning",
                "Graph neural networks (over-squashing)",
                "Brain-inspired inductive biases",
                "AI / ML in astrophysics",
            ],
        ),
        themes=[{k: th[k] for k in ("key", "label", "color", "weight")} for th in THEMES],
        own_papers=own,
        events=events,
        posters=posters,
        sessions=sessions,
    )

    data_js = os.path.join(HERE, "data.js")
    with open(data_js, "w", encoding="utf-8") as f:
        f.write("window.ICML_DATA = ")
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";")

    # ---- summary ----
    rel_posters = [p for p in posters if p["score"] > 0]
    rel_events = [e for e in events if e["score"] > 0]
    print(f"\nWrote {data_js}  ({os.path.getsize(data_js)//1024} KB)")
    print(f"  events:  {len(events)} total, {len(rel_events)} matching your interests")
    print(f"  posters: {len(posters)} total, {len(rel_posters)} matching your interests")
    print(f"  your papers found: {own or '(none matched by title)'}")
    print("  matches per theme:")
    for th in THEMES:
        n = sum(1 for p in posters if th['key'] in p['themes']) + \
            sum(1 for e in events if th['key'] in e['themes'])
        print(f"    {th['label']:<42} {n}")


if __name__ == "__main__":
    main()
