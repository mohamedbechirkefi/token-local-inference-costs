<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# demo/: resource frontier explorer (M5)

A static, offline page that shows TOKEN's published results exactly as the manuscript prints them, with measured, exploratory, modelled and sandbox values labelled distinctly and never mixed.

## What the page shows

- **Overview** with the status label: one confirmatory experiment complete (EXP-003, null result: +1.67 pp, 95 % CI [-1.00, +4.33], exact McNemar p = 0.332; no detected difference, not equivalence) and EXP-001 and EXP-002, which failed before any request on Ollama 0.9.6 and were rerun on Ollama 0.40.6 (EXP-002 complete; EXP-001 complete under the frozen rules after two blocks that met frozen memory criteria were repeated on the owner's instruction), shown with the same weight.
- **Published results** for every registered experiment, with status, verdict under the frozen rule, claim ids, and each number's interval or spread (or a statement that none is published).
- **Resource frontier explorer:** strict accuracy of the two measured EXP-003 arms against runtime-reported memory, median latency (with the interquartile range over items) or decode throughput; the three EXP-001 arms are listed without a point because they were measured on a different runtime version (no cross-runtime comparison). A per-item latency strip chart (as FIG-001).
- **Assumptions, method, sensitivity table (manuscript Table 4) and limitations** (manuscript section 7).
- **Pending owner decisions,** each with every reading the manuscript reports: configs for the sensitivity analyses S1 and S4, and the definition of the latency-ratio interval. The page chooses none. Both readings of the latency-ratio interval stay shown, as the owner decided.
- **Modelled energy (illustrative, not a measurement):** the measured median latency times a power value the visitor enters. The page proposes no value; S4 was not run.
- **Sandbox (illustrative, not the research engine):** a Web Worker re-runs the paired bootstrap and the exact McNemar test on the published per-item correctness, with seed, resample count, extraction and item-set controls, cancel and reset. No model runs and nothing is timed.

No visitor data is collected or stored, and the page makes no request to any host other than its own origin; it never contacts Ollama or any local service.

## Commands

Node from `helix/.tools/node/bin` under the research root (`../../../helix/.tools/node/bin` from `demo/`); Python from the repository's `.venv`.

    ../.venv/bin/python ../scripts/export_demo_data.py        # writes public/data/results.json from committed results
    ../.venv/bin/python ../scripts/export_sandbox_fixture.py  # writes src/engine.fixture.json (Python engine output)
    npm ci && npm test && npm run build && npm run preview
    node tools/a11y_check.mjs dist --screenshots <dir>

`npm run preview` serves the built `dist/` folder on 127.0.0.1. The built folder can also be opened from any static file server.

## Hosting

The built page is hosted at <https://token-local-inference-costs.kefimohamedbechir.workers.dev> as Cloudflare Workers static assets on the free plan (owner, 2026-11-26, decision sheet, B2). `wrangler.jsonc` declares assets only (the `dist/` folder written by `npm run build`), with no Worker script. The deployment is done by the coordinator, not by any script of this repository.

## Provenance

Started from the shared lab demo template (`labs/_shared/demo-template/`, CC0-1.0, verified 2026-11-25), including `tools/a11y_check.mjs`. On 2026-11-26 the page received its own brand identity, motion and layout at the owner's request; the design plan is `DESIGN.md` and the brand files (logo, favicon, Open Graph image) are in `public/brand/`, drawn for this repository and covered by its licence. The only dependencies added are the two font packages below; the other pinned versions are unchanged.

## Third-party notes

- **Chakra Petch** by Cadson Demak: package `@fontsource/chakra-petch`, version v5.3.0, pinned exactly; only the latin subset at weight 600 is bundled. Licence: SIL Open Font License (OFL-1.1).
- **IBM Plex Sans** by IBM: package `@fontsource-variable/ibm-plex-sans`, version v5.3.0, pinned exactly; only the latin subset of the variable weight axis is bundled. Licence: SIL Open Font License (OFL-1.1).

Both are self-hosted in the built page; nothing is loaded from another origin.
