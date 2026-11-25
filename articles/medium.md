<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Draft (not published): What a higher-precision model file cost on one laptop, and two experiments that never started

*Draft title, pending owner approval. Working title in the master prompt: "The local cost of intelligence". Every number below is printed in `research/paper/manuscript.md`; nothing here is peer-reviewed.*

Running a language model on your own laptop has no per-request fee. The cost moves to your machine: memory, waiting time and electricity. I set out to measure that trade on one consumer laptop, with the analysis fixed in advance.

## The question

How do local model configurations trade off quality, latency and resource use? Three experiments were preregistered, and the owner froze the protocol on 2026-11-24, before any model output was seen.

## What happened to the main experiment

The primary experiment (EXP-001) was to compare three installed models of different sizes. It never sent a request. The installed runtime, Ollama 0.9.6, cannot render the chat template of one of the models (ministral-3:8b), and the frozen protocol aborts a run when a model cannot be described. The cold-start experiment (EXP-002) failed at the same step. Both are reported as failed: 0 of 4,500 requests and 0 of 60 requests. There is no result on the primary question. What happens next (upgrading the runtime, a new freeze without that model, or keeping both as failed) is a pending owner decision.

## What did run: Q8_0 versus Q4_K_M

EXP-003 compared Llama 3.1 8B at two quantization levels on a fixed random subset of 300 ARC-Challenge test items, five greedy repetitions each (3,000 requests, no failures).

- Strict accuracy was 0.733 for Q8_0 and 0.717 for Q4_K_M: a difference of +1.67 percentage points, 95 % paired bootstrap interval [-1.00, +4.33], exact McNemar p = 0.332. No difference was detected. Because no equivalence margin was frozen, this is not evidence that the two are equally accurate.
- Q8_0 used 9,162.4 MiB of runtime-reported model memory against 5,872.0 MiB, and decoded at 40.1 against 53.9 tokens/s.
- Yet its median end-to-end latency was lower: 437.7 against 477.5 ms. The answers were about two tokens long, so latency was dominated by prefill, and Q8_0's prefill was faster. That ordering is not expected to hold for long generations, which were not measured.

## Visual explanation

The interactive page in `demo/` plots strict accuracy against memory, latency or decode throughput for the two measured configurations, lists the three unmeasured ones as "no result", and shows each item's latency. Figure: per-item median latency per arm (FIG-001, `research/experiments/EXP-003/figures/FIG-001-exp003-latency.svg`). Alt text: two rows of 300 dots each, one per item, showing per-item median latency for Q4_K_M and Q8_0, with a bar at each arm's median (477.5 ms and 437.7 ms).

## Limitations

One laptop (Apple M1 Pro, 16 GB), one runtime version, one benchmark subset, one prompt template, short answers. The prompt-template sensitivity analysis was not run. No energy was measured, and no modelled energy figure is reported because the frozen protocol states no power range. Memory is the runtime's own accounting.

## Reproducibility

Code, protocols, item IDs, results, the manuscript and the reports: `[OWNER PLACEHOLDER: repository URL, not published]`.

*AI assistance: an AI system was used as a research and development assistant under the owner's direction; it is not an author. Author line: [OWNER PLACEHOLDER: author line].*
