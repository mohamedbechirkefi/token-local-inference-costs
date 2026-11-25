<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# TOKEN: local inference economics

**Question.** How do local model configurations trade off quality, latency and resource use?

**Status: M4 (interpretation and evidence audit), 2026-11-25.** Protocol v1.0 frozen by the owner on 2026-11-24. One confirmatory experiment complete (EXP-003); two failed before any request (EXP-001, EXP-002). The manuscript draft is `research/paper/manuscript.md` (independent research manuscript / preprint draft, not peer-reviewed).

## Why it matters

Running language models locally avoids per-request fees, but the costs move to the user's own hardware: memory, waiting time and electricity. This project aims to measure, on one consumer laptop, what accuracy each installed model configuration delivers and at what latency and memory cost, with item-level uncertainty and a test of prompt-format sensitivity.

## Findings so far (verified against committed results)

- **EXP-003** (Llama 3.1 8B, Q8_0 versus Q4_K_M, 300 ARC-Challenge test items, Ollama 0.9.6, one M1 Pro laptop): no detected accuracy difference, +1.67 pp, 95 % CI [-1.00, +4.33], exact McNemar p = 0.332. This is not evidence of equivalence. Q8_0 used 9,162.4 MiB of runtime-reported model memory against 5,872.0 MiB and decoded at 40.1 against 53.9 tokens/s; its median latency for two-token answers was lower (437.7 against 477.5 ms).
- **EXP-001 and EXP-002** failed before any request: Ollama 0.9.6 cannot render the chat template of ministral-3:8b. They have no results; the owner's choice of next step is pending.

## What exists now

- Control files: `CLAUDE.md`, `roadmap.md`, `progress.md`.
- Frozen protocol: `research/protocol.md`; experiment protocols and reports in `research/experiments/EXP-001` to `EXP-003`.
- Code (`src/token_lab/`), tests, results (`results/`), claims register, evidence audit (`research/publication/`). No demo yet (M5).
- Feasibility audit: `research/feasibility.md`. Sources: `research/literature_review.md`. Data and model licences: `data/manifest.json`.

## Experiments

| ID | Question | Status |
|---|---|---|
| EXP-001 | Accuracy and cost of installed models of different sizes (phi4-mini 3.8B baseline vs llama3.1 8B, ministral-3 8B; Q4_K_M) | failed before any request (DL-011) |
| EXP-002 | Cold-start versus warm latency | failed before any request (DL-011) |
| EXP-003 | Quantization Q4_K_M vs Q8_0 for Llama 3.1 8B (download approved) | complete (RUN-EXP-003-0001) |

## Quick start (development)

```
/Users/bechir/research/labs/.tools/py/bin/uv sync
/Users/bechir/research/labs/.tools/py/bin/uv run pytest
```

## Data and licences

Benchmark candidate: ARC-Challenge (CC BY-SA 4.0). Models are used locally and never redistributed; their licences are listed in `data/manifest.json`. Third-party material keeps its own licence (see `NOTICE.md`).

## Limitations

See `research/limitations.md`. Results hold for one machine, one runtime version, one benchmark subset, one prompt template and the configurations measured.

## Licence and citation

TOKEN Source-Available Non-Commercial Research License v1.0 (`LICENSE`, SPDX `LicenseRef-TOKEN-NC-Research-1.0`). Not an OSI open-source licence. Citation metadata: `CITATION.cff`.
