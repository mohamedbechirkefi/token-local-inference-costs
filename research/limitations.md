<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Limitations

Items 1 to 10 were written at M0, before any result; items 11 to 15 at M3; items 16 to 22 at M4. Earlier items are kept as written and qualified where later evidence bears on them.

1. **One machine, one runtime.** All measurements come from one Apple M1 Pro laptop (16 GB) and one Ollama version. Nothing generalises to other hardware, runtimes or hosted services.
2. **Confounded configurations.** EXP-001 arms differ in parameter count, architecture, training data and tokenizer at once. Differences are attributable to the configurations, not to size alone.
3. **Benchmark validity.** ARC-Challenge multiple-choice accuracy is a narrow proxy for "quality". Possible training-data contamination cannot be ruled out for any model.
4. **Statistical power.** With 300 items the minimum detectable accuracy difference is about 9 percentage points (under an assumed discordance of 0.25). Undetected differences are not equivalence.
5. **Prompt sensitivity.** Results may depend on the prompt template (sclar2023format); S1 tests this but cannot cover all formats.
6. **Shared laptop.** Background load from the owner's other work and a shared Ollama runtime can perturb timing; controls reduce but cannot remove this.
7. **Cold start.** "Cold" is runtime-cold only; the OS page cache is not purged.
8. **Energy is modelled.** No energy is measured; modelled energy depends on an assumed power range.
9. **Tokens are tokenizer-specific.** Tokens per second are not comparable in information content across models.
10. **Quantization axis.** Only one quantization is installed; EXP-003 depends on an owner-approved download. (M4: the download took place and EXP-003 ran; the quantization axis covers two levels of one model only.)

## Added in M3 (2026-11-25)

11. **Runtime incompatibility.** The installed Ollama 0.9.6 cannot run ministral-3:8b (template function `currentDate` undefined), so EXP-001 and EXP-002 produced no results (DL-011). The study currently has no evidence on A0 versus A1 versus A2.
12. **EXP-003 power.** The observed Q8_0 minus Q4_K_M difference (+1.7 pp, CI -1.0 to +4.3) lies well inside the stated minimum detectable difference of about 9 pp; only 17 of 300 items were discordant.
13. **Latency is prefill-dominated.** With num_predict 8 and outputs of about two tokens, end-to-end latency mostly reflects prefill; the Q8_0 arm was faster end to end despite slower decoding. This does not transfer to long generations.
14. **Latency ratio intervals missing.** The frozen bootstrap interval for the median latency ratio is not implemented (DL-011 gap 1); latency comparisons are descriptive.
15. **Swap state.** About 3 GiB of swap was already in use before the confirmatory run (from the owner's other applications and the smoke run); swap growth per block stayed at or below 61 MiB.

## Added in M4 (2026-11-25)

16. **No result on the primary question.** The primary experiment (EXP-001, model size at fixed quantization) and EXP-002 (cold start) failed before any request. The manuscript's only confirmatory result is EXP-003, which the frozen plan called optional. The section 10 question (how configurations trade off quality, latency and resource use) is answered only for two quantizations of one model.
17. **No equivalence margin.** The frozen protocols define no equivalence margin, so the EXP-003 interval [-1.00, +4.33] pp cannot be read as equivalence of Q8_0 and Q4_K_M. Differences of up to about 4 pp in favour of Q8_0 are compatible with the data.
18. **Template sensitivity untested.** S1, the sensitivity analysis the protocol names as able to invalidate the main interpretation, was not run (no frozen config, and no new inference in M4). The EXP-003 accuracy contrast holds for template T1 only.
19. **Energy not reported.** S4 and every modelled energy figure are absent: the frozen protocol names an assumed power range but does not state one.
20. **Warm-up prompt reuse.** The discarded warm-up request of each block repeats the block's first item, so 10 of 3,000 records (one per block) were measured after a prompt the runtime had just processed; they are much faster. The per-item medians are unchanged by them (JRN-0009, E3), but the raw latency distribution contains these 10 values.
21. **Prefill throughput depends on prompt length.** Prefill duration rises in steps with prompt length (JRN-0009, E4), so a median prefill rate in tokens per second summarises this prompt-length mix and does not transfer to other prompt lengths.
22. **Peak RSS is not a memory measure here.** Peak resident memory of the Ollama processes was lower for Q8_0 (932.3 MiB) than for Q4_K_M (965.0 MiB) while the runtime-reported model memory was 56 % higher; RSS does not capture the model's Metal allocations on this machine and is reported as secondary only.
