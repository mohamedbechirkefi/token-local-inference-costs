<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Draft (not published): LinkedIn post

*Draft, pending owner approval. Numbers as printed in `research/paper/manuscript.md`.*

Does a higher-precision model file buy accuracy on a laptop?

I preregistered three experiments on local inference costs and ran them on one Apple M1 Pro laptop. Two never started: the installed runtime (Ollama 0.9.6) cannot render one model's chat template, so the primary comparison has no result, and I report that as a failure.

The one that ran: Llama 3.1 8B at Q8_0 versus Q4_K_M on 300 ARC-Challenge items. Accuracy difference +1.67 percentage points, 95 % CI [-1.00, +4.33], exact McNemar p = 0.332: no detected difference, and not evidence of equivalence. Q8_0 used 9,162.4 MiB of runtime-reported memory against 5,872.0 MiB.

Caveat: one machine, one runtime, one benchmark subset, short answers.

Repository and interactive page: [OWNER PLACEHOLDER: repository URL, not published]
