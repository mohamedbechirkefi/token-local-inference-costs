<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Progress journal (append-only)

## 2026-11-24: M0 session (bootstrap and feasibility) and M1 drafts

**Milestone:** M0. **Next bounded task:** owner review of the M0 gate and decisions D1 to D6; then M2 implementation (may start before the freeze, exploratory only).

### Starting state

`git status`: "On branch main, nothing to commit, working tree clean". One commit, `195a564` (master prompt and the owner's licence package).

### Commands run and actual outputs (abridged where long)

- `sysctl -n machdep.cpu.brand_string hw.ncpu hw.memsize hw.perflevel0.physicalcpu hw.perflevel1.physicalcpu`: `Apple M1 Pro`, `10`, `17179869184`, `8`, `2`.
- `sw_vers`: macOS 15.3.1, build 24D70.
- `df -h /Users/bechir`: 460Gi size, 311Gi used, 129Gi available.
- `system_profiler SPHardwareDataType SPDisplaysDataType`: MacBook Pro MacBookPro18,1, Apple M1 Pro, 10 cores (8 performance, 2 efficiency), 16 GB, GPU 16 cores, Metal 3.
- `pmset -g batt`: battery power, 97 %, discharging.
- `/usr/local/bin/python3 --version`: Python 3.12.1. `uv --version`: uv 0.9.5 (2025-10-21). `pandoc --version`: pandoc 3.6.3. Node: v22.23.3. `git --version`: 2.42.1.
- `ls /Users/bechir/research/labs/.tools/py/bin/`: no `typst` executable. Import check in that environment: typst 0.15.0, pypdf 6.20.0, pillow 11.3.0.
- `which tex pdflatex xelatex tectonic`: none found.
- `which powermetrics`: `/usr/bin/powermetrics` (requires elevated privileges; not run).
- Ollama, read-only: `which ollama` `/opt/homebrew/bin/ollama`; `ollama --version` "Warning: could not connect to a running Ollama instance / client version is 0.9.6"; `ollama list` "Error: ollama server not responding". Manifest directory lists llama3.1, ministral-3, nomic-embed-text, phi4-mini, qwen3.5. Parsed manifests and config blobs: phi4-mini:3.8b GGUF Q4_K_M 2.49 GB; llama3.1:8b (= latest) GGUF Q4_K_M 4.92 GB; ministral-3:8b GGUF Q4_K_M 6.02 GB (8.9B); nomic-embed-text F16 0.27 GB; qwen3.5:4b safetensors nvfp4 3.97 GB. Licence layers: Llama 3.1 Community License; Apache-2.0 (ministral-3, qwen3.5, nomic-embed-text); MIT (phi4-mini). `du -sh ~/.ollama/models/blobs`: 16G. Nothing was started, stopped or pulled.
- WebFetch (2026-11-24), opened: arXiv abstract pages 1803.05457, 2110.14168, 2212.09720, 2208.07339, 2306.00978, 2211.09110, 2310.03003, 2310.11324; dataset cards allenai/ai2_arc (cc-by-sa-4.0; ARC-Challenge test 1,172) and openai/gsm8k (MIT); Ollama API docs; llama.cpp quantize README. Details in `research/literature_review.md`.
- `uv lock` (with `exclude-newer = 2026-11-10`): "Resolved 15 packages in 302ms"; numpy 2.3.4, psutil 7.1.0, jsonschema 4.25.1, pytest 8.4.2.
- `uv sync`: installed 15 packages including token-lab 0.0.0 into `.venv/` (ignored by git).
- `uv run pytest -q`: "no tests ran in 0.00s", exit 5 (no tests exist yet; this is not a pass).
- Toolchain smoke (exploratory, JRN-0001): pandoc to Typst then `typst.compile` failed with "font fallback list must not be empty"; with `-V mainfont="Libertinus Serif"` it succeeded, 3-page skeleton PDF in the session scratchpad (not committed). `pandoc -t latex` produced `research/paper/manuscript.tex` (116 lines before the SPDX header was added).

### Changed files

Created: `CLAUDE.md`, `roadmap.md`, `progress.md`, `README.md`, `CITATION.cff`, `pyproject.toml`, `uv.lock`, `src/token_lab/__init__.py`, `data/manifest.json`, `research/{decision_log.md, literature_review.md, protocol.md, feasibility.md, limitations.md, claims_register.csv, experiment_journal.jsonl, experiment_registry.csv}`, `research/experiments/EXP-00{1,2,3}/protocol.md`, `research/paper/{manuscript.md, manuscript.tex, references.bib, supplementary.md, figures/README.md}`, `research/publication/{artifact_manifest.json, claims_audit.md, reproducibility_report.md, author_review.md, release_checklist.md}`, READMEs in `results/`, `tests/`, `experiments/`, `demo/`, `articles/`. Appended: section 6 (development commands) to `CONTRIBUTING.md`. Licence files unchanged.

### Decisions

DL-001 (owner: protective licence), DL-002 (toolchain), DL-003 to DL-005 proposed. See `research/decision_log.md`.

### Decisions the owner must make

- **D1, freeze:** approve or amend `research/protocol.md` and the EXP-001 to EXP-003 protocols (G-FREEZE), including n = 300 versus the full 1,172-item test set.
- **D2, runtime window:** schedule an exclusive Ollama window on AC power for EXP-001 and EXP-002 (EXP-002 unloads models from the shared runtime).
- **D3, download:** approve or decline a free download of a Q8_0 Llama 3.1 8B variant (about 8 GB) for EXP-003.
- **D4, qwen3.5:4b:** include it after a smoke check, or exclude it (format nvfp4, runtime compatibility unverified).
- **D5, fixture rights:** bundle the ARC subset under its CC BY-SA 4.0 terms, or commit item IDs only and regenerate.
- **D6, energy:** keep energy modelled only, or authorise `sudo powermetrics` for measured power.
- Also: review the Llama 3.1 Community License terms for this use.

### Outstanding risks

Shared runtime interference; battery and thermal state; memory pressure for Q8_0; Ollama server version unknown (client 0.9.6); cold start is runtime-cold only; arms confound size with architecture. See `research/feasibility.md`.

### Not done, and why

- No experiments, no smoke inference run: the Ollama server was not running and this session may not start it.
- No dataset downloaded (brief: metadata only). Subset IDs and SHA-256 are therefore not yet fixed.
- No tests: no implementation exists yet (M2).
- No PDF committed: only the skeleton exists.

## 2026-11-24: M2 session (core implementation while the freeze is pending)

**Milestone:** M2. **Next bounded task:** the owner's decisions D1 to D6 plus DL-007; then an exploratory real-runtime smoke in an exclusive window before the freeze.

### Starting state

`git status`: "On branch main, nothing to commit, working tree clean" at `10af340`. Control files read in the order of the M2 brief. The existing `.venv` still pointed at the repository's former path (`token-research`); `uv sync --reinstall` rewrote its scripts in place (nothing deleted).

### What was implemented

`src/token_lab/`: `items` (hf-arc-jsonl ingestion, SHA-256, seeded subset), `prompts` (T1, T2, T3 with label map), `scoring` (strict and lenient extraction), `tokens` (runtime counters, throughput), `runtime` (Ollama stdlib streaming client with client-side TTFT; deterministic `SimulatedBackend` labelled simulated), `hardware` (host log, power state, git state, package versions, memory sampler), `stats` (paired bootstrap, exact McNemar, Holm), `schema` (result schema 1.0.0 validated at export and import), `config` (validation, canonical SHA-256, protocol-freeze guard), `runner`, `analysis`, `report` (Markdown, CSV, SVG, PDF via pandoc and Typst with `-V mainfont="Libertinus Serif"`), `cli` (`token-lab smoke|run|report|test`). Fixture `data/fixtures/synthetic_mc.jsonl` (10 items written here, not ARC). Configs `experiments/smoke-simulated.json`, `experiments/smoke-ollama.json`, `experiments/EXP-001.json`. Decisions DL-006 (taken) and DL-007 (proposed amendments).

### Commands run and actual outputs (abridged)

- `uv lock`: "Resolved 15 packages"; `uv sync`: token-lab 0.0.0 to 0.1.0. No new dependency.
- `uv run pytest -q`: "90 passed" (10.40 s first run; 6 to 7 s later), 0 failed. Rerun after every change, last result "90 passed in 7.15s" via `uv run token-lab test -q`.
- `uv run token-lab run --config experiments/EXP-001.json` (in tests): exit 2, "refused: EXP-001: protocol is not frozen".
- `ollama ps` (16:00:54Z and again before the simulated runs): "Error: ollama server not responding - could not find ollama app". Nothing was started.
- `uv run token-lab smoke --config experiments/smoke-ollama.json`: "runtime unavailable: http://127.0.0.1:11434/api/version: [Errno 61] Connection refused", exit 3, no file written (JRN-0002).
- `uv run token-lab smoke --config experiments/smoke-simulated.json`, four times: RUN-SMOKE-0001 0.394 s; RUN-SMOKE-0002 0.165 s; RUN-SMOKE-0003 0.148 s; RUN-SMOKE-0004 0.167 s; each 150 requests, 0 failures (JRN-0003). `/usr/bin/time -l` on the first: 0.63 s real, 45,498,368 bytes maximum RSS.
- Memory sampler cost: 7.843 ms per full process scan (660 processes) before the fix; 0.0028 ms per cached sample after it.
- `uv run token-lab report --result ... --pdf`: RUN-SMOKE-0002 `report.pdf`, 3 pages (pypdf), visually inspected: banner, tables and figure render; first version had an overflowing table, fixed by splitting it.
- Host during the runs: AC power, 100 %; load average 4.7 to 5.2 (other agents were running on the machine). **All timings in this session are noisy and exploratory.**

### Smoke-run measurements (exploratory, simulated backend: not inference)

- Harness overhead: 0.7 to 0.8 ms per request (2.2 ms before the sampler fix). This is the only timing measured; it bounds the harness cost, not model latency.
- Runtime per real request, projected full-matrix time and seed spread of real latency: **not measured** (runtime down). The report's projection table for the simulated runs (EXP-001: 0.0010 h) is harness time only and must not be used for planning.
- Determinism: scored content identical across all four runs and across repetitions within each run (expected for the simulated backend; says nothing about the models).
- Degenerate cases found in the harness: none in the simulated runs beyond the intended format failures; persistent request errors, warm-up failures and runtime-down are handled and tested.

### Changed files

New: `src/token_lab/{items,prompts,scoring,tokens,runtime,hardware,stats,schema,config,runner,analysis,report,cli}.py`, `tests/{conftest,test_items_prompts_scoring,test_runtime_tokens,test_stats,test_pipeline}.py`, `data/fixtures/synthetic_mc.jsonl`, `experiments/{smoke-simulated,smoke-ollama,EXP-001}.json`, `results/exploratory/RUN-SMOKE-000{1..4}/`. Modified: `pyproject.toml` (version 0.1.0, `token-lab` script), `uv.lock`, `src/token_lab/__init__.py`, `CLAUDE.md` (section 4 commands), `roadmap.md`, `progress.md`, `data/manifest.json`, `research/decision_log.md`, `research/experiment_journal.jsonl`, `results/README.md`, `tests/README.md`, `experiments/README.md`. Registry statuses unchanged: no registered experiment was run, even exploratorily.

### Noted inconsistency (not changed)

`research/protocol.md` section 13 lists `token-lab run --exp EXP-001`; the implemented CLI takes `--config experiments/EXP-001.json`. The protocol is left untouched for the owner; align it at the freeze.

### Outstanding risks

Real inference timing, memory (RSS versus Metal allocations, DL-007 A2) and determinism remain unmeasured; chat templates applied by the runtime are not yet hashed (A5); the ARC loader has only been run on the fixture.

### Not done, and why

- No real-runtime smoke: Ollama was not running and the brief forbids starting it.
- No ARC data: downloads are forbidden in M2.
- No confirmatory run, no protocol hash: G-FREEZE.
- Nothing pushed (G-PUBLIC).

## 2026-11-24: freeze session (owner-approved amendments and protocol freeze v1.0)

**Milestone:** M1 freeze (G-FREEZE, owner-approved 2026-11-24). **Next bounded task:** the real smoke run (F1) in the coordinator's exclusive Ollama window on mains power, then M3. EXP-002 needs a cold/warm runner mode and an owner-recorded config hash.

### Starting state

`git status`: clean at `c96bf0a`. Read: control files, all protocols, registry, DL-007, `_shared/FREEZE-brief.md`, `_shared/owner-approvals-2026-11-24.md` (TOKEN section and C1 to C4).

### What was done

- Amendments F1 to F9 applied to `research/protocol.md` and the three EXP protocols, each recorded in an "Amendments before freeze (owner-approved 2026-11-24)" section. None could not be applied.
- ARC-Challenge test and validation downloaded with `scripts/fetch_arc.py` (JRN-0004); IDs only committed (`data/arc_challenge_test_subset_ids.json`, 300 IDs; `data/arc_challenge_validation_smoke_ids.json`, 10 IDs). `data/manifest.json` records URL, revision, licence and SHA-256.
- Code: per-arm `/api/show` fingerprint (template, system, parameters, Modelfile SHA-256) in the run manifest, confirmatory abort if missing (F8); named memory metric `runtime_model_mib` in the analysis (F7); confirmatory configs must pin the item file SHA-256 and the subset IDs, checked before any request; freeze guard extended to `research/freeze.json` (main protocol hash, experiment protocol hash, canonical config hash). New config `experiments/EXP-003.json`; `smoke-ollama.json` now targets 10 ARC validation items.
- Freeze record `research/freeze.json` (approval quotes, F1 to F9, C1 to C4 with the C4 disclosure, SHA-256 values, git revision `f99c4176c322d311aec93fd7a85b8f7fecfa7cb6`). Registry statuses "frozen (owner-approved 2026-11-24), not yet run". DL-008. CITATION.cff and manuscript metadata set to C3 authorship; `manuscript.tex` regenerated with pandoc.

### Commands run and actual outputs

- `/usr/local/bin/python3 -I scripts/fetch_arc.py --repo .` (twice): test parquet 203,808 bytes, SHA-256 62f03257...d1e9, JSONL 86ccaace...1f63, 1,172 rows; validation parquet 55,743 bytes, 395a5c88...9f05, JSONL 16b59737...151b, 299 rows. Identical on the second run.
- `.venv/bin/python -m pytest -q`: before changes "90 passed"; after the amendment commit "98 passed"; final "105 passed in 7.41s", 0 failed.
- `require_frozen_if_confirmatory` on the real repo: EXP-001 and EXP-003 accepted (returns the protocol hash). Tests show changed configs, an edited main or EXP protocol, and a missing freeze record are refused; `token-lab run` on the frozen EXP-001 config passes the guard and stops at "runtime unavailable" against a dead test port (Ollama was not contacted).

### Not done, and why

- No smoke or confirmatory run, no Ollama contact, no model pull (brief: the coordinator schedules M3 and the Q8_0 pull).
- EXP-002 has no runnable config (no cold/warm runner mode yet); its protocol is frozen.
- Protocol section 13 and EXP item 21 command texts left as drafted (not an approved amendment); correct commands are in `research/freeze.json`.
- Nothing pushed (G-PUBLIC).

## 2026-11-24: ratification session (owner's second round, "Approve all")

**Milestone:** M2 close-out before M3. **Task (RATIFY brief, TOKEN item):** implement the EXP-002 cold/warm runner mode exactly as the frozen protocol defines it, add a runnable config, record its hash in the freeze record.

### What was done

- Runner design `cold_warm` (`token_lab.runner.run_cold_warm`), `OllamaBackend.unload` (`keep_alive: 0`), simulated load tracking for tests, optional cold/warm record fields in the schema (1.0.0, additive), config validation (`design`, `cold_warm` block; one prompt, one seed, no warm-up, no retries).
- `experiments/EXP-002.json` (canonical SHA-256 6885e5f527df271897d6d2ba8f324fc73fd5135d250e92c8bd8dc94f4c3081cf) and `data/arc_challenge_validation_exp002_ids.json` (fixed item `Mercury_192290`), recorded in `research/freeze.json` with an `amendments_after_freeze` entry; DL-009. No protocol or earlier config changed; all frozen protocol hashes unchanged.
- Bug caught by the tests during implementation: unloading only the current arm's model left the previous arm's model loaded at each arm switch, so the "no model loaded" check would have failed every first cold trial after A0. Fixed before commit: a cold trial unloads every listed model.

### Commands run and actual outputs

- `.venv/bin/python -m pytest -q`: "128 passed in 8.30s", 0 failed (105 before; 22 new in `tests/test_cold_warm.py`, 1 new EXP-002 case in the freeze-guard parametrisation).
- `token-lab run --config experiments/EXP-002.json` passes the freeze guard and stops at "runtime unavailable" against a dead test port (test). Ollama was not contacted.

### Not done, and why

- No smoke or confirmatory run (coordinator schedules M3). The EXP-002 penalty analysis (protocol items 6 and 16) and the item-20 exploratory page-cache check are not implemented yet (M4 and an exploratory config respectively).
- Nothing pushed (G-PUBLIC).
