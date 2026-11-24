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
