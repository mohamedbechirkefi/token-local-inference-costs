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
