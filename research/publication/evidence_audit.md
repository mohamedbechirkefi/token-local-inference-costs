<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Evidence audit (master prompt section 11.5), M4, 2026-11-25

**Scope.** `research/paper/manuscript.md`, `research/paper/supplementary.md`, the three experiment reports, `README.md`, `research/limitations.md` and `research/claims_register.csv`, checked against the committed results. No new inference or timing measurement was run. The manifest is `research/publication/artifact_manifest.json` (entries N-001 to N-023 and FIG-001). Internal quality control by the AI assistant, not external review.

## 1. Method

1. Every decimal number and every number of three or more digits in the manuscript, supplementary file, README, limitations and claims register was extracted with a scratch script and matched against the committed sources (run CSVs and reports, `exploratory_exp003.json`, the journal, the decision log, the feasibility audit, the literature review, the protocols, the freeze record and the smoke CSVs), allowing rounding to 0 to 3 decimals. Section numbers were ignored.
2. Every unmatched value was traced by hand to its inputs.
3. Denominators, units, precision, uncertainty and sample counts were checked against `result.json` and the CSVs.
4. Every external claim was checked against `research/literature_review.md`, which records what was opened and how much of it was read.
5. Copies of artifacts were compared byte for byte with their run folder.

## 2. Number trace

| Value | Where | Source |
|---|---|---|
| 0.708 | manuscript 6 | derived: 50.93 / 71.93 from llamacpp-quantize (literature review) |
| 1.74 | manuscript 6, CLM-015 | derived: 8,540,789,934 bytes (JRN-0005) / 4.92 GB (feasibility audit) |
| 3.2 GiB | manuscript 6, 9 | derived: 3,290.4 MiB (E2) / 1,024 |
| 56 % | manuscript Abstract, 9 | derived: memory ratio 1.56 (E2) |
| "about a quarter" slower | manuscript 9 | derived: decode ratio 0.744 |
| 140.4 to 160.8 s | supplementary S3 | `result.json` blocks[].wall_s, minimum and maximum |
| 1,295 of 1,495 | claims register CLM-003 | derived: E4 bin counts 806 + 489 of 75 + 806 + 489 + 110 + 15 |
| 5,872.0 and 9,162.4 MiB | everywhere | `result.json` /api/ps sizes 6,157,232,128 and 9,607,432,192 bytes / 2^20 (reproduced by E2) |

Every other number matched a committed file directly. Result: **no untraced number** in the audited documents.

## 3. Denominators, units, precision, uncertainty and sample counts

| Check | Finding |
|---|---|
| Accuracy denominator | 300 items; per-item mean over 5 repetitions (protocol section 4). Matches `metrics.csv` (n_items 300, n_records 1,500). |
| Format failures | Counted in records (15 and 20 of 1,500), corresponding to 3 and 4 items with all 5 repetitions failing. The manuscript states records; the supplementary lists the items. |
| Latency | Per-item median over repetitions, then median and quartiles over 300 items, in ms. |
| TTFT, decode and prefill | Medians over 1,500 records, not over items. **Mismatch in presentation**: the manuscript and the EXP-003 report tables mixed the two levels without saying so. Fixed: captions and row labels state the level (finding A3). |
| Memory | MiB = 2^20 bytes throughout; GB (decimal) for file sizes only. Consistent. |
| Contrast precision | Two decimals in pp in the manuscript, reports and README; the claims register had one decimal (+1.7, -1.0, +4.3). Harmonised to two decimals (finding A1). |
| Uncertainty | Accuracy: paired percentile bootstrap, 10,000 resamples, seed 7, and exact McNemar, as frozen. Latency and memory: no frozen interval implemented; exploratory intervals labelled as such. |
| Holm column | `contrasts.csv` carries a Holm p equal to the raw p (single contrast). The manuscript states that no multiplicity correction applies to EXP-003. Not a mismatch. |
| Sample counts | 3,000 records, 10 blocks, 0 failures, 0 excluded blocks; eval_count 2 in 1,485 and 1,480 records; 17 discordant items. All match `result.json`. |

## 4. Findings and fixes

| ID | Finding | Severity | Fix |
|---|---|---|---|
| A1 | Claims register rounded the EXP-003 contrast to one decimal while all other documents use two. | low | CLM-001 text harmonised. |
| A2 | CLM-003 scope said prompts "of about 70 to 130 tokens"; the records show bins up to 192 tokens, with 1,295 of 1,495 records per arm between 65 and 128. | medium | Scope corrected from E4. |
| A3 | Per-arm tables mixed item-level and record-level summaries without labels. | medium | Labels added in the manuscript and in the EXP-003 report addendum. |
| A4 | The discarded warm-up repeats each block's first item; 10 of 3,000 records are measured on a just-processed prompt (102 to 135 ms against at least 325 ms). | medium (measurement artefact; medians unchanged) | Disclosed in manuscript 4.4, 5.4, 7, limitations 20, EXP-003 addendum, DL-012. Code not changed. |
| A5 | Peak RSS was lower for Q8_0 than for Q4_K_M, opposite to the runtime-reported memory. RSS does not capture model memory here. | low | Labelled secondary everywhere; limitation 22. |
| A6 | The frozen protocols contain no equivalence margin; the brief's question was checked and the interval cannot be read as equivalence. | n/a (confirmation) | Stated in manuscript 4.5, 7, limitation 17, DL-012. |
| A7 | Claims register lacked result id, config hash, figure or table and section. | medium | Columns added; CLM-005 to CLM-015 added for every claim the manuscript makes. |
| A8 | Stale text: README status ("M0 ... no experiments have run"), CITATION.cff abstract ("no confirmatory results yet"), limitations header ("no results exist yet"), limitation 10. | medium | Updated to the M4 state; limitation 10 qualified, not deleted. |
| A9 | The literature review describes llamacpp-quantize's table without the hardware; the manuscript could be read as comparing like with like. | low | Manuscript 6 reworded as a direction check only. |
| A10 | The M2 smoke attempt with the runtime down (JRN-0002) was missing from the supplementary matrix. | low | Added (supplementary S1). |
| A11 | Protocol section 13 and item 21 command texts differ from the implemented CLI. | low (known since DL-008) | Not changed (frozen text); correct commands in manuscript 4.6 and `research/freeze.json`. |

## 5. External claims

| Claim in the manuscript | Source key | How much was read | Status |
|---|---|---|---|
| 4-bit precision generally optimal for total bits against zero-shot accuracy; over 35,000 experiments, 19M to 176B | dettmers2022kbit | full text checked (M6; v2 pp. 2, 8) | confirmed; label updated |
| 8-bit inference roughly halves memory without degradation | dettmers2022int8 | full text checked (M6; v2 pp. 1, 2, 4) | confirmed; label updated |
| Activation-aware weight-only quantization | lin2023awq | full text checked (M6; v5 pp. 2, 3) | confirmed; label updated |
| Efficiency among HELM's dimensions | liang2022helm | full text checked (M6; v2 pp. 3, 4) | confirmed; label updated |
| Energy of LLaMA on V100/A100 | samsi2023watts | full text checked (M6; v1 pp. 2 to 4) | confirmed; label updated |
| Formatting changes up to 76 points | sclar2023format | full text checked (M6; v2 pp. 1, 9) | confirmed; manuscript now names the model (LLaMA-2-13B) |
| ARC-Challenge description | clark2018arc | full text checked (M6; v1 pp. 1 to 3) | confirmed; label updated |
| ARC licence, split sizes | arc-hf | dataset card | opened |
| Llama-3.1-8B Q4_K_M 4.58 GiB, 71.93 t/s; Q8_0 7.95 GiB, 50.93 t/s | llamacpp-quantize | page opened; hardware not recorded | stated as such |
| Counter field definitions | ollama-api | main-branch page opened; installed runtime 0.9.6 | stated as such |

Every reference in the manuscript is cited in the text, and every cited key is in `references.bib`. No source marked unverified in the literature review is cited.

## 6. Contradiction, leakage and missing-run checks

- **Contradictions:** none found between the manuscript, the three reports, the run report and the claims register after the fixes above.
- **Stale charts:** FIG-001 equals the run's `latency.svg` (SHA-256 73883986...b2b0); the four copied files in `research/experiments/EXP-003/` are byte-identical to the run folder.
- **Leakage:** none found (subset fixed before any output; prompt development on validation items only).
- **Unsupported causal statements:** the prefill and memory explanations are labelled unverified or plausible; the latency reversal for long generations is labelled an inference.
- **Missing failed runs:** all listed (supplementary S1).

## 7. Strength and scope of each conclusion

| Conclusion | Strength | Scope |
|---|---|---|
| EXP-003: no detected accuracy difference (CLM-001) | confirmatory, frozen rule; low power for small differences; not equivalence | one model, two quantizations, 300 items, T1, one machine and runtime |
| EXP-003: memory, decode, latency (CLM-002, CLM-003) | measured, descriptive, single session | two-token answers, num_ctx 2048 |
| EXP-003: latency-ratio intervals, prefill steps, warm-up artefact (CLM-007 to CLM-009) | exploratory | within-session item variation |
| EXP-001, EXP-002: failed (CLM-004, CLM-005) | observed failure | Ollama 0.9.6 with the installed ministral-3:8b |

## 8. Gate

Every numerical claim maps to a result id, config hash and table or figure (manifest and claims register), and every external claim maps to an opened source, with abstract-only reading marked. The M4 evidence gate holds.

## 7. M6 update (2026-11-25): reference labels and citation coverage

- **Labels.** Of the 10 references, 0 are read in full (cover to cover), 7 are "full text checked for the cited statement" (the free arXiv PDF was downloaded from arxiv.org, its text extracted, and every statement the manuscript makes about the paper checked against the page given in `research/literature_review.md` section 5), 3 are web pages opened in full on 2026-11-24 (arc-hf, llamacpp-quantize, ollama-api; their content may have changed since), and 0 are abstract only or unverified. The two unverified entries of the literature review (section 3) are not cited.
- **Qualified claim.** sclar2023format's 76-point figure is for one model; the manuscript now says "(for LLaMA-2-13B)". No other statement changed in substance.
- **Bibliography.** Every citation key in `manuscript.md` (10 keys, cited as bracketed keys, not pandoc citations) is in `references.bib`, and every bib entry is cited in the manuscript. lin2023awq's v5 title reads "for On-Device LLM Compression and Acceleration" where the bibliography has "for LLM Compression and Acceleration"; the bibliography keeps the earlier title (noted, not changed).


## 9. Rerun update (2026-11-26): EXP-001 and EXP-002 on Ollama 0.40.6

- **Scope.** The new and changed text: manuscript Abstract, 4.1, 4.3, 4.4, 4.6, 5.1, 5.2, Tables 1 and 5 to 8, 6, 7 and 9; supplementary S1, S2, S5, S6 and S7; limitations 23 to 29; claims CLM-016 to CLM-025 (and the CLM-005 status). Manifest entries N-024 to N-033, FIG-002 and FIG-003 were added; N-019 is relabelled as the first attempts.
- **Number trace.** Every decimal number and every number of three or more digits in that text was extracted with a scratch script and matched, allowing rounding to 0 to 3 decimals, against `RUN-EXP-001-0001` (`contrasts.csv`, `metrics.csv`, `run_manifest.json`), `RUN-EXP-002-0001` (`cold_warm.csv`, `metrics.csv`, `run_manifest.json`, per-trial TTFT and latency in `result.json`), `RERUN-EXPL-0001` (`exploratory_exp001.json`, `prompts_and_rss.json`) and the journal. Unmatched values were traced by hand: section numbers (ignored); the Holm p-values printed as 2.1e-06, 3.3e-23, 7.6e-04 and 4.9e-04 (`contrasts.csv` `holm_p`, two significant digits); 4.92 GB (feasibility audit); 718.8 and 1,313.4 MiB (`prompts_and_rss.json` S, from RUN-SMOKE-0005); the prompt lengths 84, 91.5 and 636 (`prompts_and_rss.json` L, added for this trace). Derived values: "about seven times longer" (636 / 91.5 = 7.0 and 636 / 84 = 7.6; 631 / 88 = 7.2 and 631 / 81 = 7.8); "about twice as long" (latency ratios 1.962 to 2.162); "about 1.8 to 1.9 times A0's runtime-reported memory" (4,777.5 / 2,698.6 = 1.77, 5,113.6 / 2,698.6 = 1.89). Result: **no untraced number** in the rerun text.
- **Denominators and uncertainty.** EXP-001 accuracy: n = 300 items per contrast, per-item mean over 5 repetitions, paired bootstrap 10,000 resamples seed 7, Holm over the two contrasts within each extraction rule (as `token-lab report` computes). EXP-002: 10 valid cold and 10 valid warm trials per arm, bootstrap over trials. Latency ratios: exploratory, both readings (R-TOKEN-2).
- **Status labels checked.** Every EXP-001 number on the second attempt carries the pending status (stopping criterion met after the fact, DL-016); no text calls EXP-001 a confirmatory success. EXP-002's verdict is the frozen rule's ("H1 supported"), with the prompt-length confound stated wherever the verdict appears (manuscript 5.2, Table 5, 6; claims CLM-022, CLM-023).
- **Cross-runtime statement.** The abstract, 4.3, 6 and 7 state that EXP-003 used 0.9.6 and EXP-001 and EXP-002 used 0.40.6, and no sentence compares latency, throughput or memory across those experiments.
- **Copies.** `research/experiments/EXP-001/` and `EXP-002/` `config.json`, `run_manifest.json`, `metrics.csv`, `contrasts.csv`, `cold_warm.csv` and the FIG-002 and FIG-003 files are byte-identical to their run folders (`cmp`).
- **Reports.** The EXP-001 and EXP-002 report texts were composed by the rerun session and handed to the coordinator for installation, as the brief requires; their PDFs are rebuilt after installation.

## 10. Block-repeat update (2026-11-26): EXP-001 blocks 3 and 11 (DL-017, DL-018)

- **Scope.** The new and changed text: manuscript title, status note, Abstract, 1 (contribution 2), 4.1, 4.3, 4.6, Table 1, 5.1 (heading, status paragraph, Tables 6 and 7, latency ratios, FIG-002 caption), Table 5, 6, 7 (first limitation) and 9; supplementary status line, S1, S2, S5, S6 and S7; limitations 30 and 31; claims CLM-016 to CLM-021 and CLM-025 changed, CLM-026 to CLM-028 added; manifest N-025 to N-029, N-031 and FIG-002 moved to the combined input, N-034 to N-036 added; README, CITATION.cff, demo export and page text.
- **Number trace.** Every decimal number and every number of three or more digits on the added lines of those files was extracted with a scratch script and matched, allowing rounding to 0 to 4 decimals, against `RUN-EXP-001-0002/combined` (`metrics.csv`, `contrasts.csv`, `result.json` manifest and blocks), `RUN-EXP-001-0002` (`result.json` blocks, `run_manifest.json`), `RUN-EXP-001-0001` (`metrics.csv`, `contrasts.csv`, `run_manifest.json`), `REPEAT-EXPL-0001` and `RERUN-EXPL-0001` (`exploratory_exp001.json`, `prompts_and_rss.json`), `RUN-EXP-002-0001/cold_warm.csv` and the journal (JRN-0014, JRN-0015). Unmatched values were section numbers, the model file sizes 4.92 and 6.02 GB (feasibility audit) and the significance level 0.05. Result: **no untraced number** in the block-repeat text.
- **Identity of the accuracy analysis.** `combined/contrasts.csv` is byte-identical to `RUN-EXP-001-0001/contrasts.csv` (SHA-256 bf08f26f...70b7 in both hash manifests); the 600 repeated records have the same responses, extracted labels and correctness as the 600 excluded ones (JRN-0014). Only latency, TTFT, swap and peak-RSS values of A0 and A1 changed.
- **Status labels checked.** No text calls EXP-001 pending any more; every place that states its completion also states that two blocks were repeated on the owner's instruction, and the manuscript (limitation 1), limitations 30 and the report state that block 11 had met the stopping rule and that treating it as repeatable is the owner's decision.
- **Copies.** `research/experiments/EXP-001/metrics.csv`, `contrasts.csv` and `figures/FIG-002-exp001-latency.svg` are byte-identical to `results/confirmatory/RUN-EXP-001-0002/combined/`; `run_manifest.json` there is the combined input's manifest (`combination` record included). `RUN-EXP-001-0001` is unchanged (result SHA-256 f95ee205...003c).
- **Report.** The EXP-001 report text was composed by the block-repeat session and handed to the coordinator for installation; its PDF is rebuilt after installation.
