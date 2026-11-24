<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# EXP-002 protocol: cold-start versus warm latency of installed local models

**Status: FROZEN v1.0 (owner-approved 2026-11-24, G-FREEZE).** SHA-256 recorded in `research/freeze.json` and `research/experiment_registry.csv`; any edit after the freeze makes the run refused and needs a new owner freeze. Parent: `research/protocol.md` (v1.0, frozen 2026-11-24).

1. **Precise question.** For A0 phi4-mini:3.8b, A1 llama3.1:8b and A2 ministral-3:8b (Q4_K_M) on this machine, how large is the latency penalty of a runtime-cold request (model unloaded from the runtime) relative to a warm request, and does it increase with model file size?
2. **Mechanism.** A cold request must map and initialise the model weights before prefill; the cost should scale with file size, moderated by the OS page cache.
3. **Rationale from verified sources.** ollama-api (opened) documents `load_duration` and unloading via `keep_alive: 0`. No verified source measures cold-start penalties for these models on this class of hardware.
4. **Competing explanations.** OS page cache (weights still in RAM after unload); disk state; background processes; runtime version.
5. **Hypotheses.** H0: the cold-start penalty (median cold time to first token minus median warm time to first token) does not increase with model file size across the three arms. H1 (directional): the penalty increases with file size, that is, penalty(A0) < penalty(A1) < penalty(A2), ordered by file size 2.49 < 4.92 < 6.02 GB. Contradiction: any reversal of this ordering in the point estimates, or overlapping 95 % CIs between adjacent arms (reported as unresolved). With three configurations this is descriptive evidence only; no scaling law is claimed.
6. **Estimand.** Penalty_k = median cold TTFT_k - median warm TTFT_k (ms), per arm.
7. **Experimental unit.** The trial (one request). 10 cold and 10 warm trials per arm.
8. **Scope.** "Cold" means runtime-cold only: the OS page cache cannot be purged without elevated privileges (feasibility risk 5).
9. **Variables.** Independent: arm, start state (cold, warm). Dependent: TTFT (ms), load_duration (ms), end-to-end latency (ms). Fixed: one fixed validation-split prompt, temperature 0, num_predict 8, num_ctx 2048.
10. **Treatment and control.** Treatment: cold request issued immediately after unloading with `keep_alive: 0` and confirming via `ollama ps` that no model is loaded. Control: warm request issued immediately after a completed request to the same arm.
11. **Baseline.** Warm state of the same arm.
12. **Sampling and seed plan.** Alternating cold and warm trials in a fixed interleaved order per arm; arm order shuffled with seed 2002; runtime seed 0.
13. **Sample-size rationale.** 10 trials per cell are cheap (60 requests in total) and allow bootstrap intervals on medians; more trials are allowed at the freeze if smoke timing shows variance is high.
14. **Fixed compute budget.** 60 requests plus unloads; cap 1 hour.
15. **Metric formulas and units.** TTFT = client wall-clock to first streamed chunk (ms). Penalty as in item 6.
16. **Uncertainty method.** Bootstrap over trials (10,000 resamples, seed 7) for medians and penalties; raw trial values plotted.
17. **Exclusion rules.** Same block-level rules as EXP-001; a cold trial is invalid if `ollama ps` shows the model loaded before the request.
18. **Stopping rules.** 1-hour cap; abort on memory exhaustion.
19. **Anticipated failure modes.** Unload not honoured; another client reloading a model; page-cache effects masking size dependence.
20. **Sensitivity tests.** Repeat the cold trials after loading a different arm in between (to displace that model from cache) as an exploratory check of page-cache influence.
21. **Reproducibility commands (M2).** `uv run token-lab run --exp EXP-002`.
22. **Owner approval.** Given 2026-11-24 (freeze with amendments; see below). Unloading models affects the shared runtime; the coordinator schedules the exclusive window.

## Amendments before freeze (owner-approved 2026-11-24)

Applied from the parent protocol's amendments: F5 (energy modelled only), F6 (Llama 3.1 Community License accepted for A1), F8 (each arm's chat template, system prompt, parameters and Modelfile hashes recorded in the run manifest). F1: the real smoke run, including its 5 cold and 5 warm trials for one arm, happens in a separate exclusive window and cannot change this protocol. F2, F3, F4, F7 and F9 do not change this experiment's design. Implementation note: the M2 runner has no cold/warm mode yet, so this experiment has no runnable config at the freeze (`research/freeze.json`); the cold/warm mode must implement exactly items 9 to 12 above, and its config is added under a new owner freeze record entry before it runs.
