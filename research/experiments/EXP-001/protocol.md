<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# EXP-001 protocol: accuracy and cost of installed local models of different sizes

**Status: DRAFT v0.1, 2026-11-24. Not frozen; awaiting the owner (G-FREEZE). Protocol hash: none until frozen.** Parent: `research/protocol.md` (draft v0.1).

1. **Precise question.** On this M1 Pro laptop (16 GB) with the Ollama runtime, greedy decoding and a fixed zero-shot template, does the accuracy on a fixed 300-item ARC-Challenge test subset of llama3.1:8b (A1) or ministral-3:8b (A2) differ from that of phi4-mini:3.8b (A0), all at Q4_K_M, and what latency and memory cost accompanies each arm?
2. **Mechanism.** Larger parameter counts generally store more knowledge, which may raise multiple-choice accuracy, while memory traffic per generated token grows with model size and lowers decode throughput on memory-bandwidth-bound hardware. Recent small models may close the gap through training.
3. **Rationale from verified sources.** dettmers2022kbit (abstract opened) reports that the trade-off between model bits and zero-shot accuracy favours more parameters at 4-bit precision over fewer parameters at higher precision. llamacpp-quantize (opened) gives reference throughput for Llama-3.1-8B quantizations on unrecorded hardware. Gap: no paired, item-level accuracy-plus-cost measurement for these installed configurations on a consumer laptop.
4. **Competing explanations.** Benchmark contamination; format compliance rather than knowledge; architecture and tokenizer differences; background load.
5. **Hypotheses.** H0_k: Delta_k = 0; H1_k: Delta_k != 0, for k in {A1, A2}. Contradiction: for a given arm, the 95 % paired bootstrap CI contains 0 and the Holm-adjusted exact McNemar test does not reject. This is reported as no detected difference, not equivalence.
6. **Estimand.** Delta_k = mean over items of (c_ik - c_i0), in percentage points.
7. **Experimental unit.** The benchmark item (n = 300).
8. **Population / scope.** The fixed subset of ARC-Challenge test (CC BY-SA 4.0), the three named model files, this machine and runtime version.
9. **Variables.** Independent: model configuration (A0, A1, A2). Dependent: correctness per item (primary); latency, time to first token, decode and prefill throughput, load time, peak RSS, swap delta (secondary). Held fixed: prompt template T1, temperature 0, num_predict 8, num_ctx 2048, runtime version, power state.
10. **Treatment and control.** Treatments A1, A2. Control/baseline A0.
11. **Baseline.** A0 phi4-mini:3.8b Q4_K_M; chance-level floor reported for reference.
12. **Sampling and seed plan.** Subset: simple random sample of 300 test IDs with seed 20261124, committed with the source SHA-256 before any model sees it. Five repetitions per arm, runtime seeds 0 to 4; item and arm order shuffled with seed 1000 + repetition, identical across arms.
13. **Sample-size rationale.** SE of Delta about 0.029 assuming a discordant proportion of 0.25 (assumption); 95 % CI half-width about 5.7 points; minimum detectable difference about 9 points at 80 % power, Holm-first alpha 0.025.
14. **Fixed compute budget.** 4,500 requests; wall-clock cap 4 hours; local hardware only; zero monetary cost.
15. **Metric formulas and units.** Accuracy = correct / n (proportion). Decode throughput = eval_count / eval_duration x 1e9 (tokens/s). Prefill throughput = prompt_eval_count / prompt_eval_duration x 1e9 (tokens/s). Latency = client wall-clock (ms). Peak RSS = max sampled RSS of runner process (MiB).
16. **Uncertainty method.** Paired bootstrap over items (10,000 resamples, seed 7, percentile 95 % CI); exact McNemar with Holm correction over two contrasts; timing reduced to per-item medians before bootstrapping latency ratios.
17. **Exclusion rules.** Block-level exclusion (foreign model loaded, battery power, swap growth above 512 MiB, runtime version change), repeated once and logged. No item exclusion after outputs are seen. Persistent request errors and unparseable responses count as incorrect and are reported separately.
18. **Stopping rules.** 4-hour cap; abort on memory exhaustion; no interim analysis.
19. **Anticipated failure modes.** Runner eviction under memory pressure; verbose answers exceeding num_predict 8; nondeterminism across seeds despite temperature 0; runtime version mismatch; shared-runtime interference.
20. **Sensitivity tests.** S1 prompt template (T2, T3; can invalidate the main interpretation if the sign of Delta or the arm ordering changes); S2 strict versus lenient extraction; S3 first versus last repetition latency drift.
21. **Reproducibility commands (M2).** `uv run token-lab run --exp EXP-001`; `uv run token-lab report --exp EXP-001`.
22. **Owner approval.** Not yet given.
