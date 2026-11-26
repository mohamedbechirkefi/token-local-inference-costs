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

## Added after the 0.40.6 rerun (2026-11-26)

Items 11 and 16 describe the state before the rerun and are kept as written. The owner chose option (a) (DL-015): EXP-001 and EXP-002 were run again, unchanged, on Ollama 0.40.6.

23. **Two runtime versions.** EXP-003 ran on Ollama 0.9.6 and EXP-001 and EXP-002 on 0.40.6. No latency, throughput or memory comparison is made across these experiments; A1 llama3.1:8b appears in both EXP-001 and EXP-003, but its two sets of timings come from different runtimes.
24. **EXP-001 frozen criteria not enforced.** The runner does not implement the block exclusion rule or the memory-exhaustion stopping rule (DL-011 gap 2). In RUN-EXP-001-0001, block 3 and block 11 met the exclusion criterion (swap growth 734.1 and 2,778.1 MiB) and block 11 also met the stopping rule (above 2 GiB). The run continued and no block was repeated. Accuracy was identical in all five repetitions of every arm, so no accuracy value depends on these blocks; timing and memory readings of the two blocks were taken under memory pressure. Whether EXP-001 counts as confirmatory is the owner's decision (DL-016).
25. **Format compliance drives the A1 versus A0 contrast.** A0 phi4-mini:3.8b answered with a label plus text in 520 of 1,500 records (104 items), which strict extraction counts as incorrect. Under lenient extraction (S2) the A1 minus A0 difference changes sign (-9.33 pp), so the strict A1 result reflects format compliance rather than knowledge. The A2 versus A0 difference keeps its sign under both rules.
26. **A2 receives a longer prompt.** On 0.40.6 the ministral-3:8b chat template adds a default system text, so its rendered prompt is about seven times longer than A0's and A1's (median 636 against 84 and 91.5 tokens). Its prefill, latency and cold-start penalty include this text, and EXP-002's ordering by file size is confounded with prompt length. The system text calls `currentDate`, so A2's rendered prompt also depends on the date of the run.
27. **Peak RSS does not cover the runner on 0.40.6.** The model runner runs as `llama-server`, which the frozen process filter (`ollama`) does not match; peak RSS in EXP-001 and EXP-002 (26.5 to 29.2 MiB per block) measures the server process only. The named memory metric (`/api/ps` size) is unaffected.
28. **Prompt reuse between blocks.** The A0 block of repetition 2 ran right after the A0 block of repetition 1 and had a median prefill of 22.0 ms against about 191 ms in the other A0 blocks, consistent with prompt reuse in the runtime. Per-item medians over five repetitions limit its effect on the reported latency, but the raw distribution contains this block.
29. **EXP-002 trial count and page cache.** Ten trials per cell; the first cold trial of A0 and A1 was the slowest in its arm; "cold" remains runtime-cold only (item 7).
