<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Owner review checklist (prepared at M6; awaiting the owner)

- [ ] Authorship and affiliation metadata approved ("Mohamed Bechir Kefi, independent researcher", owner, 2026-11-26, B3)
- [ ] Protocols frozen by the owner, with hashes recorded
- [ ] Claims register reviewed
- [ ] AI assistance disclosure reviewed and accurate
- [ ] Data and model licence statements reviewed (Llama 3.1 Community License terms; ARC CC BY-SA 4.0)
- [ ] Publication approved (G-PUBLIC); the repository is public since 2026-11-25 on the owner's word, and no release, tag, DOI or preprint is made before this

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

Update (2026-11-26): every placeholder below was filled from the owner's answers (section "Owner answers recorded (2026-11-26)"); none remains. The list is kept as the M6 state.

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

## Added after the EXP-001 and EXP-002 rerun (2026-11-26)

No box was ticked. The owner decided on 2026-11-26 (`labs/_shared/owner-approvals-2026-11-26.md`): R-TOKEN-1, option (a), carried out (DL-015); R-TOKEN-2, both latency-ratio readings stay shown. The first two open decisions above are therefore settled. New items for the owner:

- **EXP-001 status** (DL-016; manuscript 5.1; EXP-001 report sections 7 and 11): on the rerun, block 11 met the frozen stopping rule (swap growth above 2 GiB) and blocks 3 and 11 the exclusion criterion (above 512 MiB); the runner enforces neither. Choose: report EXP-001 as a failure under the rule as written; count the frozen accuracy analysis of the complete matrix with the criteria disclosed (accuracy was identical in every repetition); or have blocks 3 and 11, or the experiment, repeated (a further run).
- **Manuscript title** (approved as written, per the coordinator's brief): it says "two failed experiments". After the rerun, EXP-002 is complete and EXP-001's status is open; the manuscript carries a note on this under the status line. The title is unchanged; changing it is the owner's choice.
- **Runner rules** (DL-011 gap 2): implementing the exclusion and stopping rules before any further confirmatory run needs the owner's approval of a code change to the frozen code path.
- **Article drafts:** `articles/medium.md` and `articles/linkedin.md` now carry a dated note that they predate the rerun; their text is not revised.
- **PDFs:** after the coordinator installs the two report texts, `scripts/build_pdfs.py` rebuilds the five PDFs; the manuscript and supplementary PDFs in this commit were rebuilt and inspected by the rerun session.
- **Placeholder lines moved:** manuscript repository URL now at line 282, funding at 286, competing interests at 288; `articles/medium.md` repository URL at 36, author line at 38; `articles/linkedin.md` placeholder at 16.

## Added after the EXP-001 block repeat (2026-11-26)

No box was ticked. The owner decided on 2026-11-26 (follow-up answers in `labs/_shared/owner-approvals-2026-11-26.md`): "Repeat blocks 3 and 11", and the new manuscript title. Both were carried out (DL-017, DL-018): the frozen block rules were implemented in the runner and committed (c7d1ba6) before the repeat; both blocks were repeated once and met no criterion; EXP-001 is complete under the frozen rules. The EXP-001 status, manuscript title and runner-rules items of the previous addendum are therefore settled. Still open:

- **S1 and S4** configs (manuscript Table 4 and section 9) and the **latency-ratio interval** definition (both readings stay shown, R-TOKEN-2).
- **Block 11 reading:** RUN-EXP-001-0001 met the stopping rule at block 11, which as written ends the run as a failure; the repeat followed the owner's instruction, and the manuscript (limitation 1), limitations 30 and the EXP-001 report disclose this. The owner may wish to confirm the wording.
- **Article drafts** still predate the rerun and the repeat (dated note only).
- **PDFs:** after the coordinator installs the EXP-001 report text, `scripts/build_pdfs.py` rebuilds its PDF; the manuscript and supplementary PDFs in this commit were rebuilt and inspected by the block-repeat session.
- **Placeholder lines:** unchanged (manuscript repository URL at line 282, funding at 286, competing interests at 288).

## Owner answers recorded (2026-11-26)

Source: owner, 2026-11-26, decision sheet (`labs/_shared/owner-decision-sheet-2026-11-26.md`, answers in `labs/_shared/owner-approvals-2026-11-26.md`). Applied in DL-019. No box was ticked.

- **A1.** The repository is public at https://github.com/mohamedbechirkefi/token-local-inference-costs since 2026-11-25; out-of-date sentences in this file, `release_checklist.md`, the README and `CLAUDE.md` corrected. Append-only records are unchanged.
- **B1.** Repository URL filled in the manuscript (section 10), README, `CITATION.cff` (abstract and `repository-code`), the articles and the page footer.
- **B2.** Demo URL https://token-local-inference-costs.kefimohamedbechir.workers.dev filled (manuscript section 10, README, articles, page footer); `demo/wrangler.jsonc` declares the built `dist/` folder as static assets with no Worker script; deployment by the coordinator.
- **B3.** Author line "Mohamed Bechir Kefi, independent researcher" in the manuscript, the three report identification sections, README, articles and page footer; `CITATION.cff` `affiliation: "Independent researcher"`. The report sections kept as written (attempt 1 of EXP-001 and EXP-002, the pre-repeat analysis of EXP-001) keep their original wording.
- **B4.** Funding: "No funding was received." Competing interests: "The author declares no competing interests."
- **B5.** The AI-use statement (manuscript section 11) is owner-approved as drafted.
- **B6, B7.** The manuscript title is owner-approved (the follow-up answer replaced the B6 title for TOKEN); `CITATION.cff` carries it.
- **B8.** `0.1.0-rc1`, no `date-released`; at the release the version becomes `0.1.0` and `date-released` the release day (recorded in `release_checklist.md`).
- **B9.** Home paths scrubbed from editable files; what remains is listed in `reproducibility_report.md` section 7.
- **B10, B11, B13.** PDFs stay committed; FIG-001 kept with its clipped label; both noted in the release notes draft in `release_checklist.md`.
- **B14.** The source-level labels of `research/literature_review.md` are accepted.
- **R-TOKEN-1 and R-TOKEN-2.** Option (a) carried out (DL-015 to DL-018); both latency-ratio readings stay shown.
- **R-TOKEN-3.** Not decided: S1 and S4 stay "not run".

Still open for the owner: B15 (article drafts and their titles), B16 (full-text review of the manuscript and sign-off of this checklist), B18 (release, tag, optional DOI or preprint), S1 and S4 configs (R-TOKEN-3), and the block 11 wording noted above. No owner placeholder remains.
