<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Limitations (M0, anticipated; no results exist yet)

1. **One machine, one runtime.** All measurements come from one Apple M1 Pro laptop (16 GB) and one Ollama version. Nothing generalises to other hardware, runtimes or hosted services.
2. **Confounded configurations.** EXP-001 arms differ in parameter count, architecture, training data and tokenizer at once. Differences are attributable to the configurations, not to size alone.
3. **Benchmark validity.** ARC-Challenge multiple-choice accuracy is a narrow proxy for "quality". Possible training-data contamination cannot be ruled out for any model.
4. **Statistical power.** With 300 items the minimum detectable accuracy difference is about 9 percentage points (under an assumed discordance of 0.25). Undetected differences are not equivalence.
5. **Prompt sensitivity.** Results may depend on the prompt template (sclar2023format); S1 tests this but cannot cover all formats.
6. **Shared laptop.** Background load from the owner's other work and a shared Ollama runtime can perturb timing; controls reduce but cannot remove this.
7. **Cold start.** "Cold" is runtime-cold only; the OS page cache is not purged.
8. **Energy is modelled.** No energy is measured; modelled energy depends on an assumed power range.
9. **Tokens are tokenizer-specific.** Tokens per second are not comparable in information content across models.
10. **Quantization axis.** Only one quantization is installed; EXP-003 depends on an owner-approved download.

## Added in M3 (2026-11-25)

11. **Runtime incompatibility.** The installed Ollama 0.9.6 cannot run ministral-3:8b (template function `currentDate` undefined), so EXP-001 and EXP-002 produced no results (DL-011). The study currently has no evidence on A0 versus A1 versus A2.
12. **EXP-003 power.** The observed Q8_0 minus Q4_K_M difference (+1.7 pp, CI -1.0 to +4.3) lies well inside the stated minimum detectable difference of about 9 pp; only 17 of 300 items were discordant.
13. **Latency is prefill-dominated.** With num_predict 8 and outputs of about two tokens, end-to-end latency mostly reflects prefill; the Q8_0 arm was faster end to end despite slower decoding. This does not transfer to long generations.
14. **Latency ratio intervals missing.** The frozen bootstrap interval for the median latency ratio is not implemented (DL-011 gap 1); latency comparisons are descriptive.
15. **Swap state.** About 3 GiB of swap was already in use before the confirmatory run (from the owner's other applications and the smoke run); swap growth per block stayed at or below 61 MiB.
