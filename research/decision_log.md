<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Decision log

Append-only. Each entry: ID, date, decision, decided by, rationale, alternatives, consequences. "Proposed" entries await the owner.

## DL-001: Protective non-commercial licence instead of a permissive code licence

- **Date:** 2026-11-24
- **Decided by:** the owner
- **Decision:** All original material in this repository is licensed under the TOKEN Source-Available Non-Commercial Research License v1.0 (SPDX `LicenseRef-TOKEN-NC-Research-1.0`), with a Contributor License Agreement (CLA v1.0). The licence package (`LICENSE`, `NOTICE.md`, `LICENSE_HISTORY.md`, `CLA.md`, `CONTRIBUTING.md`, `.github/CODEOWNERS`, `.github/workflows/cla.yml`, `.gitignore`) was committed at the first commit.
- **Rationale:** The owner's own protection. Section 2 of `master_prompt.md` asks for an "owner-approved permissive code license"; the owner chose this protective licence instead, which is within their authority.
- **Alternatives:** A permissive licence (MIT, Apache-2.0), as the master prompt suggested. Not chosen by the owner.
- **Consequences:** The project is source-available, not OSI open source. Third-party data, models and dependencies keep their own licences (recorded in `data/manifest.json` and `uv.lock`). Sessions never change the licence files. `CITATION.cff` names the licence in a comment rather than as an SPDX field.

## DL-002: Zero-cost publication toolchain (Typst, no TeX)

- **Date:** 2026-11-24
- **Decided by:** M0 session, under the shared M0 brief; owner may revise.
- **Decision:** No TeX distribution is installed (`which tex pdflatex xelatex tectonic` found none). PDFs are produced as Markdown to Typst with pandoc 3.6.3 (`/Users/bechir/research/labs/.tools/pandoc`), compiled with the `typst` Python package 0.15.0 (`/Users/bechir/research/labs/.tools/py/bin/python`). `research/paper/manuscript.tex` is generated from Markdown with pandoc and is not compiled locally.
- **Rationale:** Zero cost, already installed, no system changes. An exploratory smoke check on the manuscript skeleton succeeded after one fix (see `progress.md`): pandoc's default Typst template emits an empty font list, which the typst package rejects ("font fallback list must not be empty"); passing `-V mainfont="Libertinus Serif"` (a font bundled with Typst) resolves it.
- **Alternatives:** Installing TeX Live or Tectonic (adds a large install outside the repository; not needed).
- **Consequences:** Typst rendering may differ from LaTeX layout. The `.tex` source is untested by compilation; that is disclosed in the M6 reproducibility report.

## DL-003 (proposed): Primary comparison is model size at fixed quantization, using installed models only

- **Date:** 2026-11-24
- **Status:** proposed, awaiting the owner.
- **Proposal:** The confirmatory core (EXP-001) compares the three installed general instruction models that share the Q4_K_M quantization: phi4-mini:3.8b (baseline), llama3.1:8b and ministral-3:8b. A quantization comparison (EXP-003) requires downloading an additional free model variant and is conditional on the owner's approval.
- **Rationale:** Uses only already available hardware and freely licensed local models, as section 10 requires. No pull was made in M0 (owner instruction).
- **Alternatives:** Quantization as the primary axis (requires a download); analytical model only (unnecessary, the hardware is adequate).

## DL-004 (proposed): Benchmark is a fixed 300-item random subset of ARC-Challenge (test split)

- **Date:** 2026-11-24
- **Status:** proposed, awaiting the owner.
- **Proposal:** ARC-Challenge test (1,172 items, CC BY-SA 4.0), simple random sample of 300 items with seed 20261124, multiple-choice letter answers scored by exact match.
- **Rationale:** Short deterministic answers keep compute inside the five-day target and make scoring exact. GSM8K (MIT) needs long generations and fragile numeric extraction; it is kept as an optional extension.
- **Alternatives:** GSM8K subset; full ARC-Challenge test set (if smoke timing shows it fits).

## DL-005 (proposed): Energy is modelled, not measured

- **Date:** 2026-11-24
- **Status:** proposed, awaiting the owner.
- **Proposal:** Electricity is a modelled quantity: measured wall-clock time multiplied by an assumed power range stated as a parameter. `powermetrics` requires elevated privileges and is not used unless the owner authorises it.
- **Consequences:** No measured energy claim is made. Energy figures are labelled modelled everywhere.
