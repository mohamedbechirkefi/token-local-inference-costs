<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Owner review checklist (prepared at M6; awaiting the owner)

- [ ] Authorship and affiliation metadata approved (no affiliation)
- [ ] Protocols frozen by the owner, with hashes recorded
- [ ] Claims register reviewed
- [ ] AI assistance disclosure reviewed and accurate
- [ ] Data and model licence statements reviewed (Llama 3.1 Community License terms; ARC CC BY-SA 4.0)
- [ ] Publication approved (G-PUBLIC); nothing is pushed or published before this

Only the owner ticks these boxes. At M6 no box was ticked, so no box had to be unticked.

## Prepared for the owner (M6, 2026-11-25)

### What to read for each item

1. **Authorship and affiliation.** `research/paper/manuscript.md` front matter (line 3, author placeholder); `CITATION.cff` (`authors`, no affiliation); report identification sections (`research/experiments/EXP-00N/report.md`, section 1).
2. **Protocols frozen.** `research/freeze.json` and `research/protocol.md`; the four SHA-256 values in `research/paper/supplementary.md` section S2 (unchanged at M6: ea86d0bb..., 1997317c..., 54d46696..., 8196740a...).
3. **Claims register.** `research/claims_register.csv` (CLM-001 to CLM-015), with `research/publication/claims_audit.md` and `research/publication/evidence_audit.md` (section 7 gives the M6 reference labels).
4. **AI assistance disclosure.** `research/paper/manuscript.md` section 11 ("AI assistance"); `articles/medium.md` last line; `CITATION.cff` comment.
5. **Data and model licences.** `data/manifest.json`; `research/literature_review.md` section 2; manuscript section 8; `research/publication/dependency_licences.md` (two notes: numpy's bundled libgfortran, MPL-2.0 lightningcss).
6. **Publication.** `research/publication/release_checklist.md`, `research/publication/reproducibility_report.md`, the PDFs `research/paper/manuscript.pdf` (13 pages), `research/paper/supplementary.pdf` (4), `research/experiments/EXP-001/report.pdf` (3), `EXP-002/report.pdf` (3), `EXP-003/report.pdf` (5), and the demo (`demo/`, `cd demo && npm ci && npm run build && npm run preview`).

### Open decisions for this repository (none is chosen here)

- **EXP-001 and EXP-002** (DL-011; `owner-approvals-2026-11-25e.md`): choose (a) upgrade Ollama and run the frozen matrices unchanged with the new runtime version recorded, (b) a new freeze without A2 or with another arm, or (c) keep both recorded as failed; the manuscript reports both experiments as failed before any request, with no results.
- **Latency-ratio interval reading** (DL-011 gap 1; `owner-approvals-2026-11-25e.md`): choose between the ratio of medians, 0.917 [0.916, 0.918], and the median of per-item ratios, 0.916 [0.916, 0.917], both exploratory as reported in manuscript section 5.4 and Table 4.
- **S4 power range and S1 config** (DL-012 decision 4; `progress.md`): decide whether to supply a power range for the modelled energy analysis and a config for the template-sensitivity analysis, which the manuscript reports as not run.
- **Manuscript title** (DL-013): approve or change "Quantization cost and accuracy of a local 8B model on one laptop: a preregistered study with two failed experiments", which is not owner-approved.
- **Funding statement** (manuscript section 11): supply the text that replaces the placeholder.
- **Competing-interests statement** (manuscript section 11): supply the text that replaces the placeholder.
- **AI-use statement** (manuscript section 11; DL-013): approve or change the wording, which is not owner-approved.
- **Author line and affiliation**: confirm the final author line (freeze decision C3 recorded a name and no affiliation).
- **Repository and demo URL**: supply the URL that replaces the placeholders.
- **CITATION.cff title**: keep "TOKEN: local inference economics" (software title, different from the manuscript title) or align it with the manuscript title; the M6 session kept it unchanged as instructed.
- **CITATION.cff version and release date**: the version now reads `0.1.0-rc1`; `date-released` stays absent until a release exists, and re-adding it is part of the owner's publication step.
- **Article draft titles**: approve or change the titles of `articles/medium.md` and `articles/linkedin.md`, which are drafts.
- **Publication (G-PUBLIC)**: decide whether and when to release, tag, deposit or publish anything; M6 releases nothing.

### Remaining owner placeholders (file and line)

- `research/paper/manuscript.md:3`: author line.
- `research/paper/manuscript.md:226`: repository URL.
- `research/paper/manuscript.md:230`: funding statement.
- `research/paper/manuscript.md:232`: competing interests statement.
- `README.md:6`: repository URL.
- `CITATION.cff:13`: repository URL (in the abstract).
- `articles/medium.md:34`: repository URL.
- `articles/medium.md:36`: author line.
- `articles/linkedin.md:14`: repository URL.
- `demo/src/App.tsx:73`: author line and repository URL (page footer).
- The generated `research/paper/manuscript.tex` and the PDFs carry the manuscript's placeholders.
