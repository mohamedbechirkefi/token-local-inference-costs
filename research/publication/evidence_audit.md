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

