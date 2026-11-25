<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# TOKEN: local inference economics

**Question.** How do local model configurations trade off quality, latency and resource use?

**Status: M6 release candidate prepared, 2026-11-25, awaiting owner review and G-PUBLIC; nothing is released.** Protocol v1.0 frozen by the owner on 2026-11-24. One confirmatory experiment complete (EXP-003, null result); two failed before any request (EXP-001, EXP-002). The manuscript draft is `research/paper/manuscript.md` (independent research manuscript / preprint draft, not peer-reviewed). Full-text owner review of the manuscript is pending (`research/publication/author_review.md`). PDFs: `research/paper/manuscript.pdf`, `research/paper/supplementary.pdf` and one report PDF per experiment, built with `.venv/bin/python -I scripts/build_pdfs.py`. Repository and demo URL: `[OWNER PLACEHOLDER: repository URL, not published]`.

![Top of the TOKEN results page: the research question, the status label, the labels used for measured, exploratory, modelled and sandbox values, the pending owner decisions banner, and the three experiment panels.](docs/demo.png)

## Why it matters

Running language models locally avoids per-request fees, but the costs move to the user's own hardware: memory, waiting time and electricity. This project aims to measure, on one consumer laptop, what accuracy each installed model configuration delivers and at what latency and memory cost, with item-level uncertainty and a test of prompt-format sensitivity.

## Findings so far (verified against committed results)

- **EXP-003** (Llama 3.1 8B, Q8_0 versus Q4_K_M, 300 ARC-Challenge test items, Ollama 0.9.6, one M1 Pro laptop): no detected accuracy difference, +1.67 pp, 95 % CI [-1.00, +4.33], exact McNemar p = 0.332. This is not evidence of equivalence. Q8_0 used 9,162.4 MiB of runtime-reported model memory against 5,872.0 MiB and decoded at 40.1 against 53.9 tokens/s; its median latency for two-token answers was lower (437.7 against 477.5 ms).
- **EXP-001 and EXP-002** failed before any request: Ollama 0.9.6 cannot render the chat template of ministral-3:8b. They have no results.

## Pending owner decisions

Each item is a pending owner decision; nothing in this repository chooses among the readings.

- **EXP-001 and EXP-002 (DL-011):** (a) upgrade Ollama and run the frozen matrices unchanged, recording the new runtime version; (b) a new freeze without A2 or with another arm; (c) keep both recorded as failed.
- **Reading of the frozen latency-ratio interval (DL-011 gap 1):** ratio of medians 0.917 [0.916, 0.918], or median of per-item ratios 0.916 [0.916, 0.917] (both exploratory, JRN-0009).

## What exists now

- Control files: `CLAUDE.md`, `roadmap.md`, `progress.md`.
- Frozen protocol: `research/protocol.md`; experiment protocols and reports in `research/experiments/EXP-001` to `EXP-003`.
- Code (`src/token_lab/`), tests, results (`results/`), claims register, evidence audit (`research/publication/`).
- Static results page (`demo/`, M5): published results with their intervals, a resource frontier explorer of the measured arms, the pending owner decisions, a modelled-energy panel driven only by a power value the visitor enters (illustrative, not a measurement), and a sandbox that re-runs the accuracy statistics in the browser (illustrative, not the research engine). Offline after the first load; no inference and no request to any runtime or service.
- Article drafts: `articles/medium.md`, `articles/linkedin.md` (drafts, not published).
- Feasibility audit: `research/feasibility.md`. Sources: `research/literature_review.md`. Data and model licences: `data/manifest.json`.

## Experiments

| ID | Question | Status |
|---|---|---|
| EXP-001 | Accuracy and cost of installed models of different sizes (phi4-mini 3.8B baseline vs llama3.1 8B, ministral-3 8B; Q4_K_M) | failed before any request (DL-011) |
| EXP-002 | Cold-start versus warm latency | failed before any request (DL-011) |
| EXP-003 | Quantization Q4_K_M vs Q8_0 for Llama 3.1 8B (download approved) | complete (RUN-EXP-003-0001) |

## Quick start (development)

```
~/research/labs/.tools/py/bin/uv sync
~/research/labs/.tools/py/bin/uv run pytest
```

## Demo quick start

```
cd demo && npm ci && npm run build && npm run preview
```

The page data is regenerated from committed results with `.venv/bin/python scripts/export_demo_data.py`; `tests/test_demo_export.py` checks that the page shows the manuscript's numbers verbatim.

## Data and licences

Benchmark candidate: ARC-Challenge (CC BY-SA 4.0). Models are used locally and never redistributed; their licences are listed in `data/manifest.json`. Third-party material keeps its own licence (see `NOTICE.md`).

## Limitations

See `research/limitations.md`. Results hold for one machine, one runtime version, one benchmark subset, one prompt template and the configurations measured.

## Licence and citation

TOKEN Source-Available Non-Commercial Research License v1.0 (`LICENSE`, SPDX `LicenseRef-TOKEN-NC-Research-1.0`). Not an OSI open-source licence. Citation metadata: `CITATION.cff`.
