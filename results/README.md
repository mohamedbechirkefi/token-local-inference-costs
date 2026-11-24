<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# results/

Machine-readable experiment outputs, one folder per run (`RUN-<EXP>-NNNN/`: `result.json` validated against schema 1.0.0, `run_manifest.json`, `config.json`, and the generated `report.md`, `metrics.csv`, `contrasts.csv`, `latency.svg`, optionally `report.pdf`).

- `exploratory/`: exploratory runs only. Never findings, never inputs to confirmatory analysis. As of M2 it holds RUN-SMOKE-0001 to 0004, harness smoke runs on the SIMULATED backend with a synthetic fixture (journal JRN-0003): no model ran.
- `confirmatory/`: created by the runner only for configs whose protocol the owner has frozen. Empty: nothing is frozen.
- `raw/`: large generated outputs and local copies of external data; ignored by git.
