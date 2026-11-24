<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# EXP-003 protocol: quantization at fixed model (conditional)

**Status: FROZEN v1.0 (owner-approved 2026-11-24, G-FREEZE).** SHA-256 recorded in `research/freeze.json` and `research/experiment_registry.csv`; any edit after the freeze makes the run refused and needs a new owner freeze. Parent: `research/protocol.md` (v1.0, frozen 2026-11-24). Config: `experiments/EXP-003.json`. The owner approved the free Q8_0 download (amendment F3), so this experiment stays in; the pull happens in the exclusive window, not at the freeze. Optional: dropped first if the five-day target is threatened.

1. **Precise question.** For Llama 3.1 8B on this machine, does accuracy on the same fixed 300-item ARC-Challenge subset differ between Q4_K_M (installed, baseline) and Q8_0 (to be downloaded), and what are the latency and memory costs of the higher precision?
2. **Mechanism.** Higher precision reduces quantization error but increases bytes read per token, lowering decode throughput on bandwidth-bound hardware.
3. **Rationale from verified sources.** dettmers2022kbit (abstract opened): 4-bit precision is generally near the optimal size/accuracy trade-off. llamacpp-quantize (opened): for Llama-3.1-8B, Q4_K_M 4.58 GiB and 71.93 t/s versus Q8_0 7.95 GiB and 50.93 t/s on hardware not recorded in our notes. Gap: paired task accuracy alongside these costs on this laptop.
4. **Competing explanations.** The two files may come from different conversion pipelines or chat templates; this is checked by comparing the chat template, system prompt, parameters and Modelfile hashes that the run manifest records per arm (`/api/show`), and any difference is reported.
5. **Hypotheses.** H0: Delta (Q8_0 minus Q4_K_M accuracy) = 0. H1: Delta != 0. Contradiction: 95 % paired CI contains 0 and exact McNemar does not reject at alpha 0.05. Given dettmers2022kbit, a small or undetected difference is plausible; this is not evidence of equivalence.
6. **Estimand.** Paired accuracy difference in percentage points; secondary: ratio of median latency and of decode throughput, difference in runtime-reported model memory (the named memory metric), peak RSS difference.
7. **Experimental unit.** The benchmark item (n = 300, same subset as EXP-001).
8. **Scope.** Two quantizations of one model on this machine and runtime.
9. **Variables.** Independent: quantization (Q4_K_M, Q8_0). Dependent and fixed: as EXP-001.
10. **Treatment and control.** Treatment Q8_0; control Q4_K_M.
11. **Baseline.** llama3.1:8b Q4_K_M (A1 of EXP-001; rerun in the same session, not reused, so both arms share the session conditions).
12. **Sampling and seed plan.** As EXP-001: same subset IDs (`data/arc_challenge_test_subset_ids.json`), five repetitions, seeds 0 to 4, shuffles with seed 1000 + repetition; repetitions serve timing and determinism, accuracy uses the per-item mean and McNemar the majority rule (mean >= 0.5). Q8_0 arm: Ollama tag `llama3.1:8b-instruct-q8_0` (planned; the tag and its manifest digest are verified at the pull, and a different tag changes the frozen config and needs a new owner freeze).
13. **Sample-size rationale.** As EXP-001; quantization differences are expected to be smaller, so the 9-point minimum detectable difference is a serious limitation and is stated in advance.
14. **Fixed compute budget.** 3,000 requests; cap 4 hours; download size about 8 GB (external figure 7.95 GiB, unverified for the Ollama tag), zero cost.
15. **Metric formulas and units.** As EXP-001.
16. **Uncertainty method.** As EXP-001, single contrast, no multiplicity correction.
17. **Exclusion rules.** As EXP-001. Swap growth above 512 MiB is expected to be the main risk for Q8_0 and is logged per block.
18. **Stopping rules.** As EXP-001.
19. **Anticipated failure modes.** Memory pressure with Q8_0 on 16 GB; tag availability or naming differences; template mismatch.
20. **Sensitivity tests.** S1 prompt template, as EXP-001.
21. **Reproducibility commands (M2).** `uv run token-lab run --exp EXP-003`.
22. **Owner approval.** Given 2026-11-24 for the download and the freeze (see below).

## Amendments before freeze (owner-approved 2026-11-24)

Applied from the parent protocol's amendments: F2 (same ARC subset, IDs and SHA-256 committed), F3 (Q8_0 download approved; experiment no longer conditional), F5 (energy modelled only), F6 (Llama 3.1 Community License accepted for both quantizations), F7 (named memory metric; item 6), F8 (chat template hashes; item 4), F9 (repetition use and McNemar majority rule; item 12). F1: the real smoke run happens before this experiment and cannot change this protocol. Item 21 keeps the draft command text; the implemented command is `uv run token-lab run --config experiments/EXP-003.json`.
