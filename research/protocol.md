<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# TOKEN research protocol

**Status: FROZEN v1.0 (owner-approved 2026-11-24, G-FREEZE).** Draft v0.1 plus the owner-approved amendments listed in the section "Amendments before freeze (owner-approved 2026-11-24)" at the end. The SHA-256 of this file is recorded in `research/freeze.json`, `research/experiment_registry.csv` and `research/decision_log.md` (DL-008). Any edit to this file after the freeze makes `token-lab run` refuse confirmatory configs and constitutes a new protocol version that needs a new owner freeze.

Feasibility audit: `research/feasibility.md`. Sources: `research/literature_review.md`. Proposed decisions: DL-003 to DL-005 in `research/decision_log.md`.

## 1. Research question

Section 10 question: how do local model configurations trade off quality, latency and resource use?

Operational question (draft): on one Apple M1 Pro laptop with 16 GB unified memory, running the Ollama runtime with fixed prompts and greedy decoding, do the installed, freely licensed 8B-class instruction models (llama3.1:8b, ministral-3:8b, both Q4_K_M) differ in accuracy on a fixed public benchmark subset from the smallest installed instruction model (phi4-mini:3.8b, Q4_K_M), and what latency and memory cost accompanies any difference?

Excluded model: qwen3.5:4b (installed, safetensors nvfp4) is excluded from every experiment by the owner's decision (amendment F4).

Scope: these configurations on this machine and runtime. No claim about other hardware, other runtimes, model internals, hosted providers or real-world task quality.

## 2. Hypotheses (primary, EXP-001)

For each candidate arm k in {A1 llama3.1:8b, A2 ministral-3:8b}:

- **H0_k:** the item-level accuracy of arm k on the fixed subset equals that of the baseline A0 (Delta_k = 0).
- **H1_k (nondirectional):** Delta_k != 0.

Nondirectional because the baseline is a recent small model and there is no verified source predicting the sign for these exact configurations. The hypothesis is contradicted, for a given arm, if the 95 % confidence interval of Delta_k contains 0 and the Holm-adjusted exact McNemar test does not reject; that outcome is reported as "no detected difference", never as equivalence.

## 3. Baseline

A0 = phi4-mini:3.8b, Q4_K_M, the smallest and cheapest installed general instruction model. It is the primary comparator for every contrast. A chance-level reference (expected accuracy of uniform guessing over each item's options) is reported as a floor, not as a comparator.

## 4. Primary metric

**Accuracy**: the proportion of items whose extracted answer label equals `answerKey`, on the fixed ARC-Challenge subset. Direction: higher is better. Estimand: the paired difference

Delta_k = (1/n) sum_i (c_ik - c_i0),

where c_ik in {0, 1} is the correctness of arm k on item i (with c_ik averaged over the five repetitions if, unexpectedly, greedy outputs differ between repetitions).

Justification: quality is the only outcome that cannot be predicted from model size or file size alone; latency and memory follow largely from size and are the cost side of the trade-off. Making quality primary keeps a single confirmatory test, and the costs are reported in full as secondary metrics.

## 5. Secondary metrics (all reported, none confirmatory)

| Metric | Definition | Unit | Source |
|---|---|---|---|
| End-to-end latency | client wall-clock from request send to response complete | ms | measured, `time.perf_counter_ns` |
| Time to first token | client wall-clock to first streamed chunk | ms | measured (streaming) |
| Decode throughput | eval_count / eval_duration x 1e9 | tokens/s (model's own tokenizer) | runtime counters |
| Prefill throughput | prompt_eval_count / prompt_eval_duration x 1e9 | tokens/s | runtime counters |
| Load time | load_duration | ms | runtime counter |
| Runtime-reported model memory (the named memory metric, amendment F7) | largest `size` that `/api/ps` reports for the arm's model at the end of its blocks; includes weights, KV cache and Metal allocations as the runtime accounts for them | MiB | runtime-reported (not sampled by the harness) |
| Peak resident memory (secondary) | max summed RSS of processes whose name contains `ollama` during the arm, sampled at 10 Hz; may undercount Metal allocations on Apple silicon | MiB | measured, psutil |
| Peak system memory used (secondary) | max system-wide used memory during the arm, sampled at 10 Hz | MiB | measured, psutil |
| Swap delta | change in system swap used during the arm | MiB | measured |
| Model file size | sum of manifest layer sizes | GB | measured on disk |
| Format failure rate | proportion of responses with no extractable label | proportion | measured |
| Accuracy per second | accuracy / median per-item latency | 1/s | derived |
| Modelled energy | wall-clock x assumed power P, P in a stated range | Wh | **modelled**, never mixed with measured values; no `sudo powermetrics` (amendment F5) |

Token counts come from the runtime's own counters and are tested against hand-counted fixtures (section 11).

## 6. Experimental unit, sampling and seeds

- **Benchmark:** ARC-Challenge, test split (1,172 items, CC BY-SA 4.0). Fixed subset of n = 300 items, simple random sample without replacement, seed 20261124, drawn once; item IDs and the SHA-256 of the source file are committed before any model sees the subset. No tuning on these items. Prompt development uses the ARC-Challenge validation split only.
- **Unit for accuracy:** the item (n = 300). **Unit for timing:** the item; each item's five timed repetitions are reduced to their median before analysis, so repetitions are not treated as independent.
- **Seeds and repetitions (amendment F9):** five repetitions per arm with runtime seeds {0, 1, 2, 3, 4}. Decoding is greedy (temperature 0), so outputs should be identical; the five repetitions serve the timing distribution (each item's five latencies are reduced to their median) and a determinism check (the proportion of items whose response text is identical across the five repetitions, reported per arm). They are not independent accuracy samples. Accuracy uses c_ik = the mean correctness of item i over the five repetitions. The exact McNemar test uses majority correctness: item i counts as correct for arm k if c_ik >= 0.5; with five repetitions no tie can occur. Item order within an arm and arm order within a repetition are shuffled with seed 1000 + repetition index, identical across arms (common random numbers).
- **Fixed decoding:** temperature 0, num_predict 8, num_ctx 2048, a single fixed zero-shot prompt template T1 (answer with the label only), no system prompt beyond the template.
- **Chat templates (amendment F8):** `/api/generate` applies each model's own chat template and any default system prompt from its Modelfile. Before the first request of every run, the harness records for each arm the SHA-256 of the chat template, default system prompt, default parameters and Modelfile reported by `/api/show` in the run manifest (`arm_runtime`). A confirmatory run aborts before any request if a model cannot be described. A change of any of these hashes between runs of the same experiment is reported as a deviation.
- **Data (amendment F2):** ARC-Challenge was downloaded on 2026-11-24 from the Hugging Face `allenai/ai2_arc` repository at revision 210d026faf9955653af8916fad021475a3f00453 (CC BY-SA 4.0). Only item IDs and SHA-256 values are committed (`data/arc_challenge_test_subset_ids.json`, `data/manifest.json`); question texts stay out of git and are regenerated with `scripts/fetch_arc.py`. The runner refuses a confirmatory run if the item file or the drawn subset differs from the committed SHA-256 and item IDs.
- **Model licences (amendment F6):** the owner accepts the Llama 3.1 Community License for llama3.1:8b and its Q8_0 variant in this study.

## 7. Sample-size rationale

With n = 300 paired items and an assumed discordant-pair proportion of about 0.25 (assumption, not measured), the standard error of Delta is about sqrt(0.25 / 300) = 0.029. The 95 % interval half-width is then about 5.7 percentage points, and the minimum detectable difference at 80 % power with a Holm-first alpha of 0.025 is about 9 points. Smaller real differences may go undetected; that is a stated limitation. If the smoke run shows that the full 1,172-item test set fits the compute cap, the owner may choose n = 1,172 at the freeze (minimum detectable difference about 4.5 points under the same assumption).

## 8. Uncertainty and inference

- Paired bootstrap over items, 10,000 resamples, percentile 95 % intervals, fixed bootstrap seed 7.
- Exact McNemar test per contrast; Holm correction over the two primary contrasts, family-wise alpha 0.05.
- Effect sizes: Delta in percentage points, discordant-pair counts, and relative accuracy ratio.
- Timing: median and interquartile range of per-item medians, bootstrap intervals over items for the median latency ratio of each arm to the baseline.
- Raw per-item, per-repetition results are retained and plotted as distributions.

## 9. Controls, exclusion and stopping rules

**Controls.** AC power required; Low Power Mode off; no other Ollama client active and no foreign model loaded (`ollama ps` checked before and after each arm); runtime version, OS, CPU, git revision, config hash and package versions recorded per run; one discarded warm-up request per arm block.

**Exclusion rules (decided before any run).**
- A run (arm x repetition block) is excluded and repeated once if: a foreign model was loaded, the machine was on battery, swap grew by more than 512 MiB, or the runtime version changed. Exclusions are logged with the reason and never silently dropped.
- An item is never excluded after seeing outputs. A request error is retried up to 2 times; a persistent error counts as incorrect and is reported separately.
- A response with no extractable label counts as incorrect (format failure), reported separately.

**Stopping rules.**
- Wall-clock cap of 4 hours per experiment. If reached, the run stops, the completed blocks are kept and reported, and the experiment is marked incomplete.
- Abort on any sign of memory exhaustion (runner killed or swap growth above 2 GiB); report as a failure.
- No optional stopping on results: the analysis runs only once the full matrix (or the cap) is reached.

## 10. Matrices

**Smoke matrix (exploratory; amendment F1).** 10 items from the ARC-Challenge *validation* split (seed 20261124, IDs in `data/arc_challenge_validation_smoke_ids.json`) x 3 arms x 2 repetitions, plus 5 cold and 5 warm trials for one arm. Purpose: verify the runner, parsing, counters, memory sampler and timing projection. It runs as a real smoke run in an exclusive Ollama window on mains power, scheduled separately by the coordinator, after this freeze and before any confirmatory run. Its results are never used for confirmatory analysis and do not change any frozen value; if it shows that a frozen experiment cannot fit its wall-clock cap or cannot run as specified, that is recorded as a deviation and any change needs a new owner freeze.

**Full matrix (confirmatory, after the freeze).**

| Exp | Arms | Items | Repetitions | Requests |
|---|---|---|---|---|
| EXP-001 | A0 phi4-mini:3.8b, A1 llama3.1:8b, A2 ministral-3:8b (all Q4_K_M) | 300 | 5 | 4,500 |
| EXP-002 | A0, A1, A2, cold vs warm | 1 fixed prompt | 10 cold + 10 warm per arm | 60 |
| EXP-003 (download approved, amendment F3) | llama3.1:8b Q4_K_M vs Q8_0 | same 300 | 5 | 3,000 |

## 11. Sensitivity analyses

- **S1, prompt template (can invalidate the main interpretation).** Rerun all EXP-001 arms with two alternative templates (T2: "Answer: X" format; T3: choices numbered rather than lettered, answer mapped back), one repetition each. If the sign of Delta_k changes, or the ordering of arms by accuracy changes, between templates, the primary result is reported as template-dependent and no general statement about the configurations' relative quality is made (motivated by sclar2023format).
- **S2, answer extraction.** Strict extraction (the response must be a single label) versus lenient extraction (first standalone label). If conclusions differ, format compliance rather than knowledge is driving accuracy differences.
- **S3, order and thermal drift.** Compare first versus last repetition latency within each arm; a drift above 10 % triggers a report of thermal or background effects.
- **S4, modelled energy.** Vary assumed power P across its stated range; report whether the energy ordering of arms depends on P.

## 12. Competing explanations to discuss

Training data contamination of ARC in any model; instruction-following and format compliance differences; tokenizer effects on token counts; runtime scheduling and caching; background load on a shared laptop.

## 13. Reproducibility commands (to be implemented in M2)

- `uv run token-lab smoke --config experiments/smoke.json`
- `uv run token-lab run --exp EXP-001`
- `uv run token-lab report --exp EXP-001`
- `uv run pytest`

## 14. Verification required before the freeze (project-specific)

Scoring tested with known answers; token-count handling tested on fixtures; hardware logging tested; error handling tested (runtime down, malformed response, timeout).

## Amendments before freeze (owner-approved 2026-11-24)

The owner approved these amendments on 2026-11-24 (`_shared/owner-approvals-2026-11-24.md`, TOKEN section; decisions DL-007 and DL-008). Nothing else changed from draft v0.1.

- **F1, real smoke run.** The smoke matrix (section 10) runs as a real smoke run in an exclusive Ollama window on mains power, scheduled separately by the coordinator. It is exploratory and cannot change frozen values. (DL-007 A1.)
- **F2, ARC-Challenge data.** Downloaded (CC BY-SA 4.0); item IDs and SHA-256 committed, question texts not committed (section 6). Owner answer to D5: commit item IDs only.
- **F3, EXP-003 stays in.** The free Q8_0 download of Llama 3.1 8B is approved; EXP-003 is no longer conditional (section 10). The pull happens later, in the exclusive window.
- **F4, qwen3.5:4b excluded** (section 1). Owner answer to D4.
- **F5, energy stays modelled;** no `sudo powermetrics` (section 5). Owner answer to D6.
- **F6, Llama 3.1 Community License accepted** by the owner (section 6).
- **F7, memory metric named:** runtime-reported model memory from `/api/ps` (section 5); peak RSS and peak system memory used are secondary. (DL-007 A2.)
- **F8, chat template hashed** per arm and per run (section 6). (DL-007 A5.)
- **F9, repetition use and McNemar majority rule stated** (section 6). (DL-007 A4.) The repetition count stays at five.

DL-007 A3 (10 Hz sampler with PID caching) is an implementation detail already in the code; it is not a protocol amendment. Section 13 lists the commands as planned in draft v0.1; the implemented commands are `uv run token-lab run --config experiments/EXP-001.json` and `uv run token-lab report --result <result.json>` (see `research/freeze.json`); the text was left unchanged because the correction was not among the approved amendments.
