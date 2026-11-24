<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# TOKEN: local inference economics

**Question.** How do local model configurations trade off quality, latency and resource use?

**Status: M0 (bootstrap and feasibility), 2026-11-24. No experiments have run and there are no findings.** The protocol is a draft awaiting the owner's freeze.

## Why it matters

Running language models locally avoids per-request fees, but the costs move to the user's own hardware: memory, waiting time and electricity. This project aims to measure, on one consumer laptop, what accuracy each installed model configuration delivers and at what latency and memory cost, with item-level uncertainty and a test of prompt-format sensitivity.

## What exists now

- Control files: `CLAUDE.md`, `roadmap.md`, `progress.md`.
- Draft protocol: `research/protocol.md`; experiment protocols in `research/experiments/EXP-001` to `EXP-003`.
- Feasibility audit: `research/feasibility.md`. Sources: `research/literature_review.md`. Data and model licences: `data/manifest.json`.
- No code beyond a package stub, no tests, no results, no demo.

## Experiments

| ID | Question | Status |
|---|---|---|
| EXP-001 | Accuracy and cost of installed models of different sizes (phi4-mini 3.8B baseline vs llama3.1 8B, ministral-3 8B; Q4_K_M) | planned (protocol draft, awaiting owner freeze) |
| EXP-002 | Cold-start versus warm latency | planned (protocol draft, awaiting owner freeze) |
| EXP-003 | Quantization Q4_K_M vs Q8_0 for Llama 3.1 8B (conditional on an owner-approved download) | planned (protocol draft, awaiting owner freeze) |

## Quick start (development)

```
/Users/bechir/research/labs/.tools/py/bin/uv sync
/Users/bechir/research/labs/.tools/py/bin/uv run pytest   # no tests yet
```

## Data and licences

Benchmark candidate: ARC-Challenge (CC BY-SA 4.0). Models are used locally and never redistributed; their licences are listed in `data/manifest.json`. Third-party material keeps its own licence (see `NOTICE.md`).

## Limitations

See `research/limitations.md`. Results, when they exist, will hold for one machine, one runtime and the configurations measured.

## Licence and citation

TOKEN Source-Available Non-Commercial Research License v1.0 (`LICENSE`, SPDX `LicenseRef-TOKEN-NC-Research-1.0`). Not an OSI open-source licence. Citation metadata: `CITATION.cff`.
