<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Decision log

Append-only. Each entry: ID, date, decision, decided by, rationale, alternatives, consequences. "Proposed" entries await the owner.

## DL-001: Protective non-commercial licence instead of a permissive code licence

- **Date:** 2026-11-24
- **Decided by:** the owner
- **Decision:** All original material in this repository is licensed under the TOKEN Source-Available Non-Commercial Research License v1.0 (SPDX `LicenseRef-TOKEN-NC-Research-1.0`), with a Contributor License Agreement (CLA v1.0). The licence package (`LICENSE`, `NOTICE.md`, `LICENSE_HISTORY.md`, `CLA.md`, `CONTRIBUTING.md`, `.github/CODEOWNERS`, `.github/workflows/cla.yml`, `.gitignore`) was committed at the first commit.
- **Rationale:** The owner's own protection. Section 2 of `master_prompt.md` asks for an "owner-approved permissive code license"; the owner chose this protective licence instead, which is within their authority.
- **Alternatives:** A permissive licence (MIT, Apache-2.0), as the master prompt suggested. Not chosen by the owner.
- **Consequences:** The project is source-available, not OSI open source. Third-party data, models and dependencies keep their own licences (recorded in `data/manifest.json` and `uv.lock`). Sessions never change the licence files. `CITATION.cff` names the licence in a comment rather than as an SPDX field.

## DL-002: Zero-cost publication toolchain (Typst, no TeX)

- **Date:** 2026-11-24
- **Decided by:** M0 session, under the shared M0 brief; owner may revise.
- **Decision:** No TeX distribution is installed (`which tex pdflatex xelatex tectonic` found none). PDFs are produced as Markdown to Typst with pandoc 3.6.3 (`/Users/bechir/research/labs/.tools/pandoc`), compiled with the `typst` Python package 0.15.0 (`/Users/bechir/research/labs/.tools/py/bin/python`). `research/paper/manuscript.tex` is generated from Markdown with pandoc and is not compiled locally.
- **Rationale:** Zero cost, already installed, no system changes. An exploratory smoke check on the manuscript skeleton succeeded after one fix (see `progress.md`): pandoc's default Typst template emits an empty font list, which the typst package rejects ("font fallback list must not be empty"); passing `-V mainfont="Libertinus Serif"` (a font bundled with Typst) resolves it.
- **Alternatives:** Installing TeX Live or Tectonic (adds a large install outside the repository; not needed).
- **Consequences:** Typst rendering may differ from LaTeX layout. The `.tex` source is untested by compilation; that is disclosed in the M6 reproducibility report.

## DL-003 (proposed): Primary comparison is model size at fixed quantization, using installed models only

- **Date:** 2026-11-24
- **Status:** proposed, awaiting the owner.
- **Proposal:** The confirmatory core (EXP-001) compares the three installed general instruction models that share the Q4_K_M quantization: phi4-mini:3.8b (baseline), llama3.1:8b and ministral-3:8b. A quantization comparison (EXP-003) requires downloading an additional free model variant and is conditional on the owner's approval.
- **Rationale:** Uses only already available hardware and freely licensed local models, as section 10 requires. No pull was made in M0 (owner instruction).
- **Alternatives:** Quantization as the primary axis (requires a download); analytical model only (unnecessary, the hardware is adequate).

## DL-004 (proposed): Benchmark is a fixed 300-item random subset of ARC-Challenge (test split)

- **Date:** 2026-11-24
- **Status:** proposed, awaiting the owner.
- **Proposal:** ARC-Challenge test (1,172 items, CC BY-SA 4.0), simple random sample of 300 items with seed 20261124, multiple-choice letter answers scored by exact match.
- **Rationale:** Short deterministic answers keep compute inside the five-day target and make scoring exact. GSM8K (MIT) needs long generations and fragile numeric extraction; it is kept as an optional extension.
- **Alternatives:** GSM8K subset; full ARC-Challenge test set (if smoke timing shows it fits).

## DL-005 (proposed): Energy is modelled, not measured

- **Date:** 2026-11-24
- **Status:** proposed, awaiting the owner.
- **Proposal:** Electricity is a modelled quantity: measured wall-clock time multiplied by an assumed power range stated as a parameter. `powermetrics` requires elevated privileges and is not used unless the owner authorises it.
- **Consequences:** No measured energy claim is made. Energy figures are labelled modelled everywhere.

## DL-006: M2 implementation choices (offline fixture, simulated backend, freeze guard)

- **Date:** 2026-11-24
- **Decided by:** M2 session, under the shared M2 brief; the owner may revise.
- **Decision:** (1) No dataset was downloaded (the M2 brief forbids downloads), so pipeline tests and the smoke run use a 10-item synthetic fixture written in this repository (`data/fixtures/synthetic_mc.jsonl`, recorded in `data/manifest.json`). (2) A deterministic `SimulatedBackend` exercises the harness without a model; results carry `simulated: true`, the schema forbids a simulated result labelled confirmatory, and reports print a SIMULATED banner. (3) `token-lab run` refuses a confirmatory config unless the registry row holds a 64-hex protocol hash equal to the SHA-256 of the protocol file; any edit after the freeze unfreezes it. (4) The memory sampler rescans processes at most once per second (a full scan measured 7.8 ms over 660 processes). (5) McNemar discordance uses per-item majority correctness over repetitions (mean >= 0.5 counts as correct); this matters only if greedy outputs differ between repetitions.
- **Rationale:** Correctness before the runtime window; fail closed on everything that could turn exploratory output into a claim.
- **Consequences:** No measured inference quantity exists after M2. Item (5) is an analysis detail the frozen protocol should state explicitly (see DL-007, A4).

## DL-007 (proposed): Amendments to the draft protocol from the M2 smoke attempt

- **Date:** 2026-11-24
- **Status:** proposed, awaiting the owner. Nothing in `research/protocol.md` was changed.
- **A1, smoke before freeze.** The section 10 smoke matrix could not run: the Ollama server was not running (JRN-0002) and the ARC validation split was not downloaded. Runtime per request, the full-matrix projection against the 4-hour cap, and the timing spread between seeds therefore remain unmeasured. Proposal: before freezing, the owner runs `uv run token-lab smoke --config experiments/smoke-ollama.json` in an exclusive window on AC power (and, if the download is approved, on 10 ARC validation items), then decides n = 300 versus 1,172 and the repetition count from measured values.
- **A2, memory metric.** On Apple silicon, Metal allocations of the runner may not be fully counted in process RSS (unverified concern). The runner now also records the runtime's reported `size` and `size_vram` from `/api/ps` per block and system-wide used memory. Proposal: the protocol names which of these is the reported memory metric, with RSS kept as secondary.
- **A3, sampler overhead.** A 10 Hz sampler that scans every process costs about 8 % of one core on this machine (measured 7.8 ms per scan, noisy). Fixed by PID caching (0.003 ms per cached sample without matching processes). Proposal: keep 10 Hz and record the sampler design in the protocol.
- **A4, repetitions and seeds.** Under temperature 0 the five repetitions are expected to give identical answers, so they inform timing and determinism, not accuracy. Proposal: state in section 4 that accuracy uses the per-item mean over repetitions, that McNemar uses majority correctness (DL-006 item 5), and that the determinism rate is reported per arm; and confirm five repetitions only once real per-item latency variance is measured.
- **A5, chat templates.** `/api/generate` applies each model's own chat template and any default system prompt from its Modelfile, so "no system prompt beyond the template" is not fully under the harness's control. Proposal: record each arm's template and system prompt hash (`/api/show`) in the run manifest before the freeze (not implemented in M2).

## DL-008: Protocol freeze v1.0 with the owner-approved amendments

- **Date:** 2026-11-24
- **Decided by:** the owner (G-FREEZE). Answers quoted in `labs/_shared/owner-approvals-2026-11-24.md`: for TOKEN "1. yes 2. yes 3. yes 4. exclude it 5. keep 6. yes".
- **Decision:** Freeze `research/protocol.md` and the EXP-001, EXP-002 and EXP-003 protocols at v1.0 after applying amendments F1 to F9 (listed in each protocol's "Amendments before freeze (owner-approved 2026-11-24)" section): real smoke run scheduled separately (F1); ARC-Challenge downloaded, IDs and SHA-256 committed (F2); EXP-003 stays in, Q8_0 download approved (F3); qwen3.5:4b excluded (F4); energy modelled, no powermetrics (F5); Llama 3.1 Community License accepted (F6); memory metric named as runtime-reported model memory from `/api/ps` (F7); chat template hashed per arm (F8); repetition use and McNemar majority rule stated (F9). DL-003, DL-004 and DL-005 are thereby accepted; DL-007 A1, A2, A4 and A5 are adopted as F1, F7, F9 and F8; A3 stays an implementation detail.
- **Hashes (SHA-256):** `research/protocol.md` ea86d0bb2d1864f69ac545bde1c8dd263276c8dbd9d1b3fee5b7a49b8dd4d2c3; EXP-001 1997317c931cf95d04c271ab2414aef82306f5976f1eea7262eb1e4d54fee8e4; EXP-002 54d46696e6b479c83235c789839ae3acaaaeeac1f38eccc6ef7c399d191c011e; EXP-003 8196740a07ce6b0d0e254a23729aa18e5866e0b72b7ac3dd97b779e23a024068. Config hashes and the git revision (f99c417) are in `research/freeze.json`.
- **Common decisions:** C1 to C4 recorded in `research/freeze.json`; authorship (C3) applied to `CITATION.cff` and the manuscript. C4: no real model output and no ARC item was seen before the freeze; the only primary-contrast values seen came from the simulated backend on the synthetic fixture (values and paths in `research/freeze.json`).
- **Consequences:** `token-lab run` accepts the frozen EXP-001 and EXP-003 configs only while the protocols, configs and item file match the freeze record; any change is refused and needs a new owner freeze. EXP-002 has no runnable config yet (no cold/warm mode in the runner); adding one needs an owner-recorded config hash. Not changed (outside the approved amendments): protocol section 13 and item 21 command texts, which differ from the implemented CLI; the correct commands are in `research/freeze.json`.

## DL-009: EXP-002 cold/warm runner mode and runnable config

- **Date:** 2026-11-24
- **Decided by:** the owner, second round: "Approve all" (2026-11-24, `labs/_shared/owner-approvals-2026-11-24b.md`), applied through the coordinator's ratification brief, which asked to implement the runner's cold/warm mode for EXP-002 exactly as the frozen protocol defines it, add a runnable config, and record its hash in the freeze record as implementing the frozen EXP-002.
- **Decision:** Add the `cold_warm` design (`token_lab.runner.run_cold_warm`) and `experiments/EXP-002.json`. It implements EXP-002 protocol items 9 to 12, 14, 17 and 18: arms A0, A1, A2; one fixed validation-split prompt; temperature 0, num_predict 8, num_ctx 2048; runtime seed 0; per arm 10 cold and 10 warm trials, alternating and starting cold; a cold trial follows an unload with `keep_alive: 0` and a `/api/ps` check that no model is loaded; a warm trial follows the completed request to the same arm; arm order from `default_rng(2002)` (A0, A1, A2); 1-hour cap.
- **Implementation choices within the frozen text:** the fixed prompt is `seeded_subset(validation, 1, seed 20261124)` = `Mercury_192290`, rendered with T1 (ID only in `data/arc_challenge_validation_exp002_ids.json`); each cold trial unloads its arm's model and any other model `/api/ps` lists (otherwise the previous arm's model would stay loaded at each arm switch); no retries and no discarded warm-up, since either would change the start state; the unload is confirmed by polling `/api/ps` every 0.25 s for up to 30 s; a cold trial whose pre-request `/api/ps` lists any model, or cannot be read, is kept and marked invalid (`state_valid` false), a warm trial after a failed request likewise; no new trial starts after the cap. The item-20 page-cache sensitivity check is exploratory and not part of this config.
- **Hashes:** `experiments/EXP-002.json` canonical SHA-256 6885e5f527df271897d6d2ba8f324fc73fd5135d250e92c8bd8dc94f4c3081cf (file cd78f2ed26697da586df68beba230750cd7ed76e2630aabee7c4a2dbbb49eac7); fixed item IDs file c1fea51fcf4a868ba547ed0c33456362344d5fcd2ff28c4fcdfc6834b37ea7ae. No protocol or earlier config changed; the main protocol and EXP-001, EXP-002 and EXP-003 hashes are unchanged.
- **Consequences:** `token-lab run --config experiments/EXP-002.json` now passes the freeze guard; changed EXP-002 configs are refused. Result records gain optional fields `start_state`, `trial_index`, `state_valid`, `state_check` (schema 1.0.0, additive). Tested with the simulated backend and the local HTTP stub only; Ollama was not contacted. The penalty analysis (item 6 and 16) is still to be written before the EXP-002 report (M4).

## DL-010: EXP-002 penalty analysis implemented before any EXP-002 data

- **Date:** 2026-11-25 (M3 session, before any confirmatory output of any experiment).
- **Decided by:** the M3 session under the coordinator's M3 briefs (owner "Start next", 2026-11-25), which asked to implement the EXP-002 penalty analysis exactly as the frozen protocol defines it, test it on the simulated backend and commit it before any confirmatory EXP-002 output exists.
- **Decision:** `token_lab.stats.bootstrap_median_diff`, `token_lab.analysis.cold_warm_penalties` and `token_lab.analysis.cold_warm_ordering`, used by `token-lab report` for cold/warm results (`cold_warm.csv`, `cold_warm.svg`, a penalty section in `report.md`). Frozen definitions implemented: Penalty_k = median cold TTFT_k minus median warm TTFT_k in ms (item 6); bootstrap over trials, 10,000 resamples, seed 7, for the medians and the penalty (item 16); percentile 95 % intervals (parent protocol section 8); a cold trial whose start state was not confirmed is excluded (item 17); H1 ordering A0 < A1 < A2 by file size 2.49 < 4.92 < 6.02 GB, H1 not supported on any reversal of the point estimates or on overlapping adjacent 95 % CIs, the latter labelled unresolved (item 5).
- **Readings of the frozen text, stated before any data:** (1) the trial is the unit (item 7), so cold and warm trials are resampled independently within each arm; (2) each arm's bootstrap starts from `default_rng(7)`, cold indices drawn before warm indices, as the EXP-001 contrasts reseed per contrast; (3) warm trials after a failed request and trials whose request failed carry no valid TTFT and are excluded, and every excluded trial is counted in the output; (4) when a reversal and an overlap occur together, both are reported; (5) an exact tie of two penalty point estimates is not defined by the frozen rule and is reported to the owner, not classified. Load duration and end-to-end latency (item 9 dependent variables) are reported as descriptive medians only.
- **Consequences:** no protocol, config or frozen hash changed. Tests: `tests/test_cold_warm_analysis.py` (simulated backend and hand-built records only).

## DL-011: M3 deviations and gaps (EXP-001 and EXP-002 failed; EXP-003 complete)

- **Date:** 2026-11-25
- **Decided by:** recorded by the M3 session; every choice below is left to the owner.
- **Deviation 1 (EXP-001, EXP-002 failed).** The installed Ollama is 0.9.6 (Homebrew). The installed ministral-3:8b (arm A2) has a chat template that calls `currentDate`, which this runtime does not define: `/api/show` and `/api/generate` return HTTP 500 "template: :10: function currentDate not defined" (exploratory smoke RUN-SMOKE-0005, JRN-0006). Run through the guard, both frozen experiments aborted before any generation request at the F8 fingerprint step (exit 3, no output; JRN-0007). M0 could not detect this because the server was not running. Not retried, not altered. Options for the owner: (a) upgrade Ollama (a download and a runtime change for the owner's other projects) and run the frozen matrices unchanged, recording the new runtime version; (b) a new freeze without A2 or with another arm; (c) record both experiments as failed.
- **Deviation 2 (records).** The EXP-003 run manifest shows `dirty: true` because the experiment journal (a tracked record file) was appended while the run was in progress. Code, configs and protocols were at revision 57f6187 throughout.
- **Gap 1 (not implemented, not chosen).** Protocol section 8 asks for bootstrap intervals over items for "the median latency ratio of each arm to the baseline". The analysis code does not compute them, and the text leaves open whether this is the ratio of the two medians or the median of per-item ratios. Latency ratios are reported as point values only, labelled descriptive.
- **Gap 2 (not implemented).** The block exclusion rule ("excluded and repeated once") and the 4-hour cap and memory-exhaustion abort for the matrix design are not implemented in the runner. In RUN-EXP-003-0001 no block met any criterion (checked after the run from the block records) and the run took 25.2 minutes, so nothing depended on them.
- **Gap 3 (scope).** Sensitivity analyses S1 to S4 have no frozen configs (S1 would need a seed and order plan for its single repetition); they are M4 work and were not run.
- **Consequences:** M3 gate: EXP-003 complete; EXP-001 and EXP-002 documented failures with no confirmatory output. CLM-001 to CLM-004 added.
