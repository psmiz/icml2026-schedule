# ICML 2026 schedule map (personal)

Live: https://psmiz.github.io/icml2026-schedule/ (repo: psmiz/icml2026-schedule)

## Update / redeploy
```bash
python3 build.py            # refresh data.js from icml.cc (add --fresh to re-download)
git add -A && git commit -m "update" && git push   # Pages redeploys automatically
```

## Files
- `index.html` — the page (loads `data.js`)
- `data.js` — generated dataset (`window.ICML_DATA`)
- `build.py` — fetch + score; tune relevance via `THEMES` at top
- `curation.json` — per-title keep-list `{id:{theme,conf}}`; relevance = membership. Hand-edit to add/drop papers.

## Push auth (SSH key registered to psmiz, passphrase-protected)
```bash
ssh-agent -a /tmp/a.sock; SSH_AUTH_SOCK=/tmp/a.sock ssh-add ~/.ssh/id_rsa   # enter passphrase
SSH_AUTH_SOCK=/tmp/a.sock git push
```
