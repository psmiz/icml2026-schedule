# ICML 2026 — Sumin's Personalized Schedule Map

A self-contained visualization of the **ICML 2026** (Seoul, July 5–11) program,
customized to your research interests:

- Mechanistic interpretability of LLMs
- Efficient sequence modeling — state space models & linear attention
- Representation learning & functional specialization
- Mixture-of-Experts routing & subspace learning
- Graph neural networks (over-squashing)
- Brain-inspired inductive biases
- **AI / ML in astrophysics & the physical sciences**

## Open it

```bash
open index.html        # macOS — just double-click also works
```

No server needed. `index.html` loads `data.js` (the prebuilt dataset).

## What's inside

| Tab | Contents |
|-----|----------|
| **Overview** | Your two ICML 2026 posters (Q-Delta, STAR) pinned at the top, an at-a-glance count per interest theme (click to drill into posters), and a day-by-day conference capsule. |
| **Events** | Tutorials, invited talks, orals, and workshops — grouped by **date**, then by type, sorted by time. Each card shows speakers, time, room, and which of your interests it touches. |
| **Posters** | Grouped by **date → poster session**, ordered by **poster number** (falls back to relevance until board numbers are published ~1 week out). Each card shows authors, ICML topic, theme tags, and links to the ICML page + paper. |

Shared controls (sticky bar):
- **Date page tabs** — the Events and Posters tabs open one day at a time (with an
  "All days" option); each day is effectively its own page.
- **Search** titles / authors / topics / abstracts
- **Relevant to me only** toggle (on by default — turn off to browse all 6,799 events)
- **Theme chips** — click to isolate one interest or combine several
- **Poster order** — by poster #, relevance, or title
- **Session jump bar** — the Posters view opens with a "Jump to" bar listing each poster
  session and its paper count, e.g. `Session 1 (376)`; click to scroll straight to it.
  Counts update live with the date / theme / search / starred filters.
- **★ Star posters** — click "☆ Star" on any poster to mark it. Your picks are saved in
  the browser (`localStorage`) and persist across reloads. Turn on **★ Starred only** to
  hide everything you haven't starred; "clear stars" resets them. Your own papers are
  always treated as starred.

Poster cards omit the author list to stay compact (authors are still searchable).

## How relevance is decided

Relevance is **title-reviewed, not topic-bucketed**. Every one of the ~6,600 poster
titles was read individually and judged against your specific interests; the verdicts
live in `curation.json` (`{id: {theme, conf}}`). A poster counts as "relevant" only if
it's in that file, and it carries the single reviewed theme tag. This is much stricter
than keyword/topic matching:

| Filter stage | Relevant posters / day |
|---|---|
| Whole-topic + keywords (initial) | ~1,000 |
| Tightened keywords (core only)   | ~300 |
| **Per-title review (current)**   | **~175** (599 total) |

`build.py` applies `curation.json` on top of the keyword pass, so if you delete it the
page falls back to keyword scoring. To re-review (e.g. after a data refresh), re-run the
batch screening pipeline that produced it (split titles → review each batch → aggregate),
or hand-edit `curation.json` directly.

## Refresh the data

The dataset is fetched from the official ICML virtual site and scored against your
interests. Re-run any time (e.g. once board numbers are released):

```bash
python3 build.py          # uses .cache/ if present
python3 build.py --fresh  # force re-download from icml.cc
```

The interest model (themes, keywords, weights) lives at the top of `build.py` —
edit `THEMES` to tune what counts as relevant.

## Files

- `index.html` — the visualization (open this)
- `data.js` — generated dataset (`window.ICML_DATA`)
- `build.py` — fetch + score + emit pipeline
- `.cache/` — raw ICML downloads (safe to delete)

## Notes

- Data sources: `icml.cc/static/virtual/data/icml-2026-orals-posters.json` (orals + posters)
  and the server-rendered listing pages for tutorials / workshops / orals / invited talks.
- Relevance scoring is heuristic — it's meant to surface candidates, not replace browsing.
- Poster board numbers are not yet assigned by ICML; the "By poster #" order shows a
  relevance-based stand-in and will snap to true board order once `build.py` picks them up.
