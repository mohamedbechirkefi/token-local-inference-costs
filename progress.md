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

## 2026-11-25: M3 session (exclusive quiet-machine window)

**Milestone:** M3 (owner "Start next", 2026-11-25). The M3 status line is left to the coordinator.

### Starting state

`git status`: clean at `e242e86`. Every frozen hash matched (main protocol, three EXP protocols, three configs via the guard, subset and EXP-002 item ID files, both ARC JSONL files). `uv sync --frozen --all-groups --all-extras`: "Audited 14 packages"; `.venv/bin/python -m pytest -q`: "128 passed in 8.45s". Load average 1.53 at 13:02 local, AC power, Low Power Mode off, no Ollama process running.

### What was done

- EXP-002 penalty analysis implemented and committed before any EXP-002 output (`57f6187`, DL-010; 16 new tests). Provenance revision for all M3 runs: `57f6187e7b450fea05eedbbee8c663943596a699`.
- Ollama 0.9.6 started by this session (`ollama serve`, 12:03Z) and stopped again at 12:56Z, as found. Q8_0 pull: `llama3.1:8b-instruct-q8_0`, manifest digest b158ded76fa0..., 8,540,789,934 bytes, 12:03Z to 12:29Z (JRN-0005).
- Exploratory smoke RUN-SMOKE-0005 (matrix) and RUN-SMOKE-0006 (cold/warm, A0, new exploratory config `experiments/smoke-cold-warm.json`); metric validation 21 of 21 checks passed (JRN-0006). A2 ministral-3:8b fails on Ollama 0.9.6 (template function `currentDate` undefined).
- EXP-001 and EXP-002 run through the guard: both aborted before any request (exit 3, no output; JRN-0007, DL-011).
- EXP-003 RUN-EXP-003-0001: 3,000 of 3,000 requests, 0 failures, 25.2 min, no excluded block (JRN-0008). Delta Q8_0 minus Q4_K_M +1.67 pp, 95 % CI [-1.00, +4.33], McNemar p 0.332: H0 not rejected.
- Records: registry statuses, CLM-001 to CLM-004, limitations 11 to 15, DL-010, DL-011, results README, `research/experiments/EXP-003/` (config, manifest, metrics, contrasts, FIG-001). Experiment reports are written by the coordinator from the texts returned by this session.

### Not done, and why

- EXP-001 and EXP-002: runtime incompatibility; needs the owner (DL-011 options a to c).
- Latency-ratio intervals, block repeat, and S1 to S4: gaps listed in DL-011.
- `report.pdf` was generated for EXP-003 but not inspected, so it was removed and not committed.
- Nothing pushed (G-PUBLIC).

## 2026-11-25: M3 done with documented failures (coordinator, quiet window)

The owner approved the experiment reports (owner, 2026-11-25, "approve all recommendations, RIGGED A", item 4). Subagents may not write report files, so the reports were composed by the M3 session from committed results only and written by the coordinator: 3 report(s). The coordinator checked that every decimal number in them appears in a committed file. Four numbers in the EXP-003 report are derived, not copied, and were traced by hand: 5,872.0 and 9,162.4 MiB are the `/api/ps` byte sizes in `result.json` divided by 2^20; 0.744 is the ratio of the two committed decode medians; 3,073.6 MiB is the swap reading in the experiment journal. EXP-003 ran in full in an exclusive quiet-machine window (3,000 of 3,000 requests). EXP-001 and EXP-002 failed before any request: the installed Ollama 0.9.6 cannot render the chat template of arm A2 (ministral-3:8b), and the frozen F8 rule aborts the run (DL-011). Both failures are documented, so the M3 gate holds. M3 is **done** with these failures. Next: the owner chooses for EXP-001 and EXP-002 between upgrading Ollama, a new freeze without A2, or keeping them as failed; then M4.

## 2026-11-25: M4 session (interpretation, evidence audit, manuscript, review pass 2)

**Milestone:** M4, started by the owner's instruction (owner, 2026-11-25, "Next"; `labs/_shared/owner-approvals-2026-11-25d.md`). The owner-approval files of 2026-11-25, -25b and -25c have no TOKEN section. **Next bounded task:** the owner's choice for EXP-001 and EXP-002; then M5.

### Starting state

`git status`: clean at `3b6b8bf`. All four frozen protocol hashes matched. `.venv/bin/python -m pytest -q`: "144 passed in 8.37s".

### What was done

- **No new measurement.** No inference, timing measurement or runtime contact. Ollama was not started, stopped or touched.
- **Exploratory re-analysis** (JRN-0009, DL-012): `scripts/m4_exploratory_exp003.py` reads the committed `RUN-EXP-003-0001/result.json` and writes `results/exploratory/M4-EXPL-0001/exploratory_exp003.json` (run twice, identical SHA-256 65c421c4...6f). Checks E1 to E8: latency ratio under both readings of protocol section 8, decode and memory ratios, warm-up prompt reuse, prefill by prompt length, discordance and format failures, arm position, interval width, tokenizer. One worker.
- **Confounder inspection** for EXP-003 against the competing explanations named in the protocols (manuscript section 6): template and parameter hashes equal, weight provenance unaudited (partly addressed); format compliance (addressed by S2 and E5); tokenizer (addressed by E8); scheduling and caching (partly addressed by E3 and E6); background load (partly addressed); contamination (not tested, does not bias the paired contrast). **No conclusion changed.**
- **Equivalence check:** neither the main protocol nor the EXP-003 protocol defines an equivalence margin, so the EXP-003 interval is reported as no detected difference, not equivalence.
- **Evidence audit** (`research/publication/evidence_audit.md`), manifest (`artifact_manifest.json`, N-001 to N-023 and FIG-001), claims register with result id, config hash, table or figure and section columns (CLM-001 to CLM-015), claims audit checklist. Findings A1 to A11, all fixed or disclosed; among them a warm-up artefact in the runner (A4), unlabelled mixing of item-level and record-level summaries (A3), a wrong prompt-length scope in CLM-003 (A2) and stale M0 text in README, CITATION.cff and limitations (A8).
- **Manuscript** synthesised to section 11.4 (`research/paper/manuscript.md`, about 4,800 words with tables and references; `supplementary.md`); `manuscript.tex` regenerated with pandoc 3.6.3 (not compiled, DL-002). No PDF generated or committed. EXP-001 and EXP-002 are reported as failed with the same prominence as EXP-003.
- **Second review pass** (`research/publication/review_pass_2.md`): six passages rewritten to remove overreach (a non-inferiority reading of the CI lower bound, "no detected difference" drifting toward "Q4_K_M is as accurate", an unsupported claim about the literature, an unsourced motivation sentence, a replication-like comparison with the llama.cpp table, "exclusive window"), one table relabelled, one claim scope corrected, one failed attempt (JRN-0002) added. No verdict changed.
- **Records:** limitations 16 to 22, DL-012, JRN-0009, M4 addenda to the three experiment reports, references.bib completed for every cited key, README and roadmap updated.

### Commands run and actual outputs

- `shasum -a 256 research/protocol.md research/experiments/EXP-00*/protocol.md`: ea86d0bb..., 1997317c..., 54d46696..., 8196740a... (unchanged, before and after).
- `.venv/bin/python -I scripts/m4_exploratory_exp003.py --repo .` (three runs after the last edit gave the same output hash 65c421c4...6f).
- Number trace (scratch script, not committed): every unmatched number in the audited documents was traced by hand (evidence audit section 2).
- `cmp` of the four copied EXP-003 files and `shasum` of FIG-001 against the run folder: identical.
- `pandoc research/paper/manuscript.md -s -t latex`: success.
- `.venv/bin/python -m pytest -q`: "144 passed in 8.52s" after all changes (no code under `src/` changed).

### Owner placeholders for M5

- Repository URL (manuscript section 10): `[OWNER PLACEHOLDER: repository URL, not published]`.
- Funding statement (manuscript section 11): `[OWNER PLACEHOLDER: funding statement]`.
- Competing interests (manuscript section 11): `[OWNER PLACEHOLDER: competing interests statement]`.
- Author line (manuscript front matter): `[OWNER PLACEHOLDER: author line ...]`; the freeze decision C3 recorded a name and no affiliation, and the owner confirms the final line. Affiliation: none recorded; owner to confirm.

### Pending owner decisions (not decided by "Next")

- EXP-001 and EXP-002: (a) upgrade Ollama and run the frozen matrices unchanged, recording the new runtime version; (b) a new freeze without A2 or with another arm; (c) keep both recorded as failed (DL-011).
- The definition of the frozen latency-ratio interval (ratio of medians or median of per-item ratios; DL-011 gap 1).
- An S4 power range and an S1 config, if the owner wants them run.

### Not done, and why

- S1 (template sensitivity) and S4 (modelled energy): no frozen config or power range, and M4 allows no new inference.
- The warm-up artefact is disclosed, not fixed (changing the runner would alter the code used by the frozen configs).
- No PDF (M6). Nothing pushed (G-PUBLIC).

## 2026-11-25: M5 session (interactive experience)

**Milestone:** M5, started by the owner's instruction (owner, 2026-11-25, "Next" (second); `labs/_shared/owner-approvals-2026-11-25e.md`), under the M5 brief and its timing addendum. **Next bounded task:** M6 (release candidate), only on the owner's word; the owner decisions below stay pending.

### Starting state

`git status`: clean at `bfaa36b`. Frozen protocol hashes ea86d0bb..., 1997317c..., 54d46696..., 8196740a... (unchanged at the end). `.venv/bin/python -m pytest -q` after `uv sync --frozen --all-groups --all-extras`: "144 passed in 9.05s".

### What was done

- **No measurement, no inference.** Ollama was not contacted, started or stopped. No benchmark, load test or model run.
- `demo/`: copy of the shared template (pinned versions, lockfile, `.npmrc` unchanged; no dependency added). Sections: overview with status label and a labels legend (measured, exploratory, no result, modelled, sandbox); published results for EXP-001, EXP-002 (failed, same visual weight) and EXP-003 with a contrast chart and every estimate's interval or spread; resource frontier explorer (strict accuracy against memory, latency with IQR, or decode throughput; EXP-001 arms listed as "no result"); per-item latency strip chart (as FIG-001); assumptions; method, Table 4 sensitivity checks and section 7 limitations; pending owner decisions with every reading; modelled energy from a visitor-entered power only; sandbox (statistics port in a Web Worker, illustrative).
- `scripts/export_demo_data.py` (fail-closed export, DL-013 decision 2), `scripts/export_sandbox_fixture.py` (Python engine fixture), `tests/test_demo_export.py` (7 tests: exact re-export, every display string verbatim in the manuscript, exceptions absent, registry coverage, pending decisions, no timestamp, fixture re-generation).
- README (status, screenshot `docs/demo.png` with alt text, pending decisions, demo quick start), `CITATION.cff` (`date-released` removed per the coordinator default; abstract updated), `demo/README.md`, new drafts `articles/medium.md` and `articles/linkedin.md`. A script checked that every decimal number and interval in these files is printed in the manuscript (only `cff-version: 1.2.0` is not, as expected).
- No sentence of the form "the owner has not reviewed" existed; `author_review.md` has no ticked box (nothing to untick).

### Commands run and actual outputs

- `npm ci --prefer-offline` (Node 22.23.3 from helix, npm cache in the scratchpad): "added 53 packages".
- `.venv/bin/python scripts/export_demo_data.py`: "wrote demo/public/data/results.json (87092 bytes)". `.venv/bin/python scripts/export_sandbox_fixture.py`: "wrote demo/src/engine.fixture.json" (0.2 s).
- `npm test`: "Test Files 2 passed (2)", "Tests 21 passed (21)".
- `npm run build`: "built in 76ms" (index 251.51 kB, worker 2.02 kB, CSS about 6 kB).
- `node tools/a11y_check.mjs dist --screenshots <scratchpad>/token-local-inference-costs/shots` (final run):

```
PASS results render (no fail-closed panel): 3 experiment panels
PASS text contrast, light scheme (WCAG AA)
PASS text contrast, dark scheme (WCAG AA)
PASS keyboard reaches every focusable element: 24 reached of 24
PASS visible focus indicator
PASS no horizontal page scroll at 360 px: overflow 0px
PASS reduced motion: no running animations: 0 running
PASS no request leaves the local origin
PASS offline after first load: results stay, sandbox runs: Sandbox output (illustrative, not a measurement; seed 1, 10,000 resamples, stric
A11Y-CHECK PASS
```

  (The last line is truncated by the checker at 80 characters.) Earlier runs failed on two items and were fixed: keyboard keys collided for identical table regions and unnamed inputs (ids added), and a select overflowed at 360 px (label shortened, width capped). A run on a copy of `dist/` with one item value set to 2 printed "FAIL results render (no fail-closed panel): 0 experiment panels" and "A11Y-CHECK FAIL (2)": the page fails closed.
- Screenshots inspected (desktop light, desktop dark, mobile): fixed clipped failed-experiment tables (now plain lines), an overlapping contrast-chart label, small chart text and clipped tables on mobile (stacked rows below 36rem). The mobile full-page capture repeats the page top after the pending-decisions section; this is a capture artefact of the checker's beyond-viewport screenshot, and the energy and sandbox sections render on desktop.
- `.venv/bin/python -m pytest -q`: "151 passed in 8.65s".
- `shasum -a 256` of the four frozen protocols: unchanged.

### Owner placeholders that remain

- Repository and demo URL: `[OWNER PLACEHOLDER: repository URL, not published]` (manuscript section 10, README, CITATION.cff abstract, page footer, articles).
- Funding statement and competing interests: `[OWNER PLACEHOLDER: funding statement]`, `[OWNER PLACEHOLDER: competing interests statement]` (manuscript section 11).
- Author line: `[OWNER PLACEHOLDER: author line ...]` (manuscript front matter, page footer, Medium draft). Affiliation: none recorded; owner to confirm.

### Pending owner decisions (shown on the page and in the README as pending)

- EXP-001 and EXP-002: (a), (b) or (c) (DL-011).
- Reading of the frozen latency-ratio interval (DL-011 gap 1).
- Not decided by any approval so far: the TOKEN manuscript title and its funding, competing-interest and AI-use wording (the post-M4 approval predates this manuscript; DL-013); the article draft titles.

### Not done, and why

- No PDF (M6). Nothing pushed (G-PUBLIC). S1 and S4 stay not run.

## 2026-11-25: M6 session (release candidate)

**Milestone:** M6, started by the owner's instruction (owner, 2026-11-25, "Push and next"; `labs/_shared/owner-approvals-2026-11-25f.md`), under the M6 brief and its timing addendum. **Next bounded task:** none for the agent; the owner's review of `research/publication/author_review.md` and any G-PUBLIC decision.

### Starting state

`git status`: clean at `26eede9`. Frozen protocol hashes ea86d0bb..., 1997317c..., 54d46696..., 8196740a... (unchanged at the end). Ollama not contacted, started or stopped; no inference; no timing compared with frozen results.

### Commands run and actual outputs

- Clean clone `git clone -q <repo> <scratch>/clone` at `26eede9`; `uv sync --frozen --all-groups --all-extras`: success; `.venv/bin/python -m pytest -q`: "151 passed in 10.83s".
- `token-lab report --result <run>/result.json --out <scratch>/regen/<run>` for RUN-EXP-003-0001 and RUN-SMOKE-0001 to 0006, `cmp` with the committed files: 29 of 29 identical. `scripts/m4_exploratory_exp003.py --repo .`: `git status` empty. EXP-003 copies: 4 of 4 identical.
- Exploratory harness smoke, simulated backend, in the clone: RUN-SMOKE-0007, 150 requests, 0 failures; load average 2.08 1.96 1.69; timing not compared; folder deleted with the clone.
- Demo in the clone: `npm ci --prefer-offline`: "added 53 packages in 679ms"; `npm test`: "Test Files 2 passed (2)", "Tests 21 passed (21)"; `npm run build`: "built in 271ms"; `node tools/a11y_check.mjs dist`: 9 PASS lines and "A11Y-CHECK PASS". Export re-run: 0 `git status` lines.
- References: the free arXiv PDFs of the 7 cited arXiv papers fetched from arxiv.org, text extracted with pypdf in scratch, cited statements checked with page numbers (`research/literature_review.md` section 5). Result: 0 read in full, 7 full text checked for the cited statement, 3 web pages opened in full (M0), 0 abstract only, 0 unverified; 10 of 10 keys cited and in `references.bib`. One claim made more precise (sclar2023format, LLaMA-2-13B).
- `.venv/bin/python -I scripts/build_pdfs.py`: manuscript 13 pages, supplementary 4, EXP-001 3, EXP-002 3, EXP-003 5; `manuscript.tex` regenerated. Sizes 59 kB to 212 kB. pypdf: title set in all five; no e-mail address or local path in metadata or text.
- Visual inspection (PNG at 60 ppi in scratch, read page by page): every manuscript page, every supplementary page, every page of the three reports. Fixed: reference list gaps (pandoc line wrap read as a Typst list item; `--wrap=none`), overlapping supplementary tables (column widths, 9 pt table text), three raw Markdown lists in the reports (blank lines), FIG-001 clipped lower label (caption names both rows; the result figure is not edited).
- `scripts/check_links.py .`: "relative links checked: 14; broken: 0". Data manifest: 5 of 5 hashes match. Artifact manifest: 20 of 20 paths exist; FIG-001 hash matches. Run hash manifest: 7 of 7.
- Scan of 168 tracked or new files: 0 e-mail addresses (apart from the `noreply@anthropic.com` trailer in `CLAUDE.md`), 0 keys or tokens, 0 `.env`; home paths 21 in 7 files before, now only `CLAUDE.md` (8) and append-only records (this file 2, decision log 1; not edited, noted here and in DL-014).
- Licences: `research/publication/dependency_licences.md` (14 Python, 53 npm). Flags: numpy wheel bundles libgfortran (GPL-3.0-or-later WITH GCC-exception-3.1); lightningcss MPL-2.0 (build only).
- `CITATION.cff`: `version: "0.1.0-rc1"`; `date-released` absent; title kept (software title; alignment is an owner decision).
- Working repository: `.venv/bin/python -m pytest -q`: "162 passed in 8.56s" (151 plus 11 in `tests/test_m6_release.py`); demo `npm test` 21 passed, `npm run build` success, checker "A11Y-CHECK PASS"; `scripts/export_demo_data.py` updated only the two source hashes of the manuscript and claims register in `results.json`.

### Owner items

Listed in `research/publication/author_review.md` ("Prepared for the owner (M6, 2026-11-25)"): EXP-001 and EXP-002 options (a), (b), (c); the latency-ratio interval reading; S1 and S4; manuscript title; funding, competing-interest and AI-use statements; author line and affiliation; repository and demo URL; CITATION.cff title; article titles; publication. No box ticked.

### Not done, and why

- No release, tag or push (G-PUBLIC). No confirmatory or timing run. `manuscript.tex` not compiled (DL-002).

### Second and third fresh clones (M6 session, after commit)

- Second clone at e08b037: `pytest -q` "1 failed, 161 passed in 10.91s": `test_committed_results_json_is_reproduced_exactly` failed because `demo/public/data/results.json` was exported before the commit and named the previous source revision (bfaa36b) as `code_revision`. Report regeneration: 29 files, 0 differing. `scripts/build_pdfs.py` (tool paths set by environment variables): same page counts; `manuscript.tex` identical; PDFs differ only by creation date (extracted text equal). Links: 14 checked, 0 broken.
- Fix: re-exported after the commit (one line), commit e5d0801.
- Third clone at e5d0801: "162 passed in 10.81s"; export re-run leaves `git status` empty; demo `npm ci` "added 53 packages in 635ms", "Tests 21 passed (21)", build "built in 270ms", "A11Y-CHECK PASS". Clone deleted.
- Note for future sessions: after any change to the export sources (manuscript, claims register, results, registry, freeze record, artifact manifest), commit first, then re-export and commit `results.json`.
