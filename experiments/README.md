<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# experiments/

Runnable configurations. Protocols and reports live in `research/experiments/EXP-NNN/`.

- `smoke-simulated.json`: exploratory harness smoke run on the simulated backend and the synthetic fixture (no model).
- `smoke-ollama.json`: exploratory smoke run against an already running, idle Ollama server. Not run in M2 (server down).
- `EXP-001.json`: the confirmatory EXP-001 matrix. `token-lab run` refuses it until the owner freezes the protocol; its item path is a placeholder until the ARC-Challenge test file is obtained with owner approval.
