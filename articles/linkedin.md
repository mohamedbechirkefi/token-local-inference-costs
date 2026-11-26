<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Draft (not published): LinkedIn post

*Draft, pending owner approval. Numbers as printed in `research/paper/manuscript.md`.*

*Note (2026-11-26): this draft was written before the owner-approved rerun of EXP-001 and EXP-002 on Ollama 0.40.6 (manuscript sections 5.1 and 5.2, DL-015, DL-016). Its statements that these experiments produced no results describe the first attempts only. The draft is not revised here; revising it is left to the owner's review of the article drafts.*

Does a higher-precision model file buy accuracy on a laptop?

I preregistered three experiments on local inference costs and ran them on one Apple M1 Pro laptop. Two never started: the installed runtime (Ollama 0.9.6) cannot render one model's chat template, so the primary comparison has no result, and I report that as a failure.

The one that ran: Llama 3.1 8B at Q8_0 versus Q4_K_M on 300 ARC-Challenge items. Accuracy difference +1.67 percentage points, 95 % CI [-1.00, +4.33], exact McNemar p = 0.332: no detected difference, and not evidence of equivalence. Q8_0 used 9,162.4 MiB of runtime-reported memory against 5,872.0 MiB.

Caveat: one machine, one runtime, one benchmark subset, short answers.

Repository: https://github.com/mohamedbechirkefi/token-local-inference-costs
Interactive page: https://token-local-inference-costs.kefimohamedbechir.workers.dev

Mohamed Bechir Kefi, independent researcher
