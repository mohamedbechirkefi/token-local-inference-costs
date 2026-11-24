<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# TOKEN roadmap

Question: how do local model configurations trade off quality, latency and resource use? Target: five focused development days (planning estimate). Cost: zero. Section 11.6 requirements are mandatory at every milestone.

Status values: not started, in progress, done (all acceptance criteria checked), blocked.

| ID | Milestone | Depends on | Priority | Effort (estimate) | Status | Blockers |
|---|---|---|---|---|---|---|
| M0 | Bootstrap and feasibility | none | P0 | 0.5 day | done (2026-11-24), pending owner review of the gate | none |
| M1 | Research and preregistration | M0 | P0 | 0.5 day | in progress (drafts only) | owner freeze (G-FREEZE); owner decisions D1 to D6 in `progress.md` |
| M2 | Core implementation | M1 drafts (implementation may start before the freeze) | P0 | 1.5 days | not started | none for implementation; ARC download is part of M2 |
| M3 | Experiments | M1 freeze, M2 | P0 | 1 day | not started | owner freeze; exclusive Ollama window; AC power; EXP-003 needs download approval |
| M4 | Interpretation | M3 | P0 | 0.5 day | not started | M3 |
| M5 | Interactive experience | M4 (results), M2 (schema) | P1 (cut first) | 0.5 day | not started | M4 |
| M6 | Release candidate | M4, M5 | P0 | 0.5 day | not started | owner approval for any publication (G-PUBLIC) |

## M0: Bootstrap and feasibility

- Deliverables: control files (section 2), section 11.1 tree, feasibility audit (`research/feasibility.md`), source and licence audit (`research/literature_review.md`, `data/manifest.json`), zero-cost toolchain confirmed (DL-002), lockfile (`uv.lock`), registry with EXP-001 to EXP-003.
- Acceptance: the owner can understand the question, the cost (zero) and the exclusions from README.md, `research/protocol.md` and `research/feasibility.md`. All files exist; nothing fabricated; commands and outputs in `progress.md`.

## M1: Research and preregistration (11.6: initialise registry, manuscript skeleton and experiment protocols; confirm toolchain; freeze before execution)

- Deliverables: draft protocols (done as drafts), fixture manifest for the 300-item subset (IDs plus source SHA-256), owner decisions recorded, frozen protocol hashes.
- Acceptance: owner freezes `research/protocol.md` and each `EXP-NNN/protocol.md`; SHA-256 recorded in the registry and decision log; exploratory results (smoke) visibly separated.
- Blockers: owner freeze; decisions D1 to D6.

## M2: Core implementation (11.6: versioned output schemas, reproducibility manifests and report generators alongside the core)

- Deliverables: `src/token_lab/` with ingestion (ARC loader with SHA-256 and licence record), prompt templates, answer extraction and scoring, Ollama client (stdlib HTTP, streaming TTFT), memory sampler, run manifest writer, JSON result schema (validated on export and import), analysis (paired bootstrap, exact McNemar, Holm), report generator, CLI `token-lab {smoke,run,report}`. Offline fixtures (small, licence-compliant).
- Acceptance: unit tests for scoring with known answers, extraction edge cases, token-count handling, bootstrap and McNemar against hand-computed examples, schema rejection of malformed results, error handling (runtime down, timeout, malformed response), hardware log capture; tests run and actual counts recorded. Correctness before UI.

## M3: Experiments (11.6: individual reports as experiments finish; record all failures and deviations)

- Deliverables: smoke run (exploratory), then EXP-001, EXP-002 and, if approved, EXP-003 per the frozen matrix; raw results, run manifests, metrics.csv, figures, standalone reports per 11.3.
- Acceptance: complete planned matrix or documented failure; no silently dropped runs; provenance captured at run time.
- Blockers: freeze, exclusive runtime window, AC power.

## M4: Interpretation (11.6: finish reports and evidence audit; synthesise into the manuscript with contradictory results and sensitivity analyses)

- Deliverables: sensitivity analyses S1 to S4, claims register, limitations, manuscript sections, claims audit, second review pass challenging the preferred hypothesis.
- Acceptance: every numerical claim maps to result ID, config and figure; every external claim maps to an opened source.

## M5: Interactive experience (11.6: identical results, labels and scope across demo, paper, reports and articles)

- Deliverables: static resource frontier explorer (measured versus modelled distinction), accessibility checks.
- Acceptance: offline after load, responsive, keyboard usable, no fabricated data, no runtime service. First to be cut if time is short.

## M6: Release candidate (11.6: compile and inspect PDFs; verify references and metadata; clean-clone reproduction; owner review checklist)

- Deliverables: PDFs via Typst, generated `manuscript.tex`, clean-clone reproduction, secret and licence scan, `research/publication/*` completed, Medium and LinkedIn drafts.
- Acceptance: actual command outputs recorded; publication only with owner approval.
