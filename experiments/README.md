<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# experiments/

Runnable configurations. Protocols and reports live in `research/experiments/EXP-NNN/`.

- `smoke-simulated.json`: exploratory harness smoke run on the simulated backend and the synthetic fixture (no model).
- `smoke-ollama.json`: exploratory smoke run (10 ARC-Challenge validation items x 3 arms x 2 repetitions) against an already running, idle Ollama server, in the coordinator's exclusive window.
- `EXP-001.json`, `EXP-003.json`: the confirmatory matrices, frozen by the owner on 2026-11-24 (`research/freeze.json`). `token-lab run` accepts them only while they, their protocols and `research/protocol.md` match the freeze record. Fetch the items first with `/usr/local/bin/python3 -I scripts/fetch_arc.py --repo .`.
- `EXP-002.json`: the confirmatory cold/warm trials (runner design `cold_warm`), added 2026-11-24 under the owner's second-round approval and recorded in `research/freeze.json` as implementing the frozen EXP-002 protocol (DL-009). It unloads models from the shared runtime, so it runs only in the coordinator's exclusive window.
