<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Second review pass (M4, 2026-11-25)

**Purpose.** Master prompt section 11.5: a pass that argues against the preferred reading, not one that polishes the text. This is internal quality control by the AI assistant, not peer review. Input: the M4 draft of `research/paper/manuscript.md`, `supplementary.md`, the three experiment reports, the claims register and the committed results. Every challenge below states whether it holds and what changed.

**Preferred reading under challenge.** "For Llama 3.1 8B on this laptop, Q4_K_M is the better configuration: Q8_0 costs much more memory and gains no accuracy." The frozen rule only supports "no detected difference"; the review tests how far the draft drifted toward the preferred reading.

## 1. Strongest alternative readings

| # | Challenge | Holds? | Change made |
|---|---|---|---|
| R1 | "No detected difference" is being read as "no difference". The point estimate favours Q8_0 (+1.67 pp, 11 against 6 discordant items) and the interval reaches +4.33 pp; a larger item set might detect a Q8_0 advantage. | Yes | Discussion rewritten: it now says explicitly that the result must not be read as "Q4_K_M is as accurate as Q8_0", and names the discordant split and the upper bound. |
| R2 | The draft said the interval "rules out, at the 95 % level, losses larger than 1 point". That is a non-inferiority statement without a preregistered margin. | Yes | Replaced by a statement that the lower end is a property of this subset and bootstrap and supports no non-inferiority claim. |
| R3 | The planned power analysis assumed 0.25 discordance; the observed 0.057 means the design was more precise than planned, so one could argue the null is "informative". | Partly | The manuscript reports the observed half-width (2.67 against 5.66 pp planned) in Limitations, and states that this does not create an equivalence test after the fact. No claim strengthened. |
| R4 | Q8_0's faster end-to-end latency could be an order, thermal or caching artefact rather than a property of the arm. | No, within the session | Arm position changed median latency by less than 1 ms (E6), drift was below 1 % (S3), Q8_0 was faster on 296 of 300 items (E1) and in every prompt-length bin (E4). Kept as descriptive, with the mechanism labelled unverified. Between-session variation remains unmeasured and is stated. |
| R5 | The two weight files may differ in more than precision (different conversion pipeline, GGUF metadata). | Partly | Already disclosed (Modelfile hashes differ; template and parameter hashes equal; weight provenance unaudited). No change. |
| R6 | ARC accuracy might reflect contamination rather than reasoning. | Partly | Both arms are the same weights at two precisions, so contamination does not bias the paired contrast; it limits construct validity. Stated in Discussion; no change. |
| R7 | Format compliance, not knowledge, could drive the contrast. | No | S2 gave the identical contrast; the post hoc exclusion of format-failure items left +1.36 pp (labelled exploratory and invalid as confirmatory evidence). |

## 2. Overgeneralisation

| # | Challenge | Holds? | Change made |
|---|---|---|---|
| G1 | The abstract said "published comparisons rarely report" accuracy and resource use together. The literature review is preliminary and not systematic, so this is an unsupported claim about the literature. | Yes | Rewritten as "the sources consulted for this study (a preliminary, non-systematic review) do not report ...". Same change in the Introduction. |
| G2 | The Introduction asserted that local inference is "attractive for cost, privacy and availability", with no source. | Yes | Replaced by a statement limited to what the study shows (the cost moves to the user's own memory, time and electricity; 8B quantized models run on this 16 GB laptop). |
| G3 | The decode ratio was called "close to" the llama.cpp ratio, which invites a replication reading across unrecorded hardware. | Yes | Reworded as a sanity check on direction only. |
| G4 | "Q8_0 was faster" could be read as general. | No | Already restricted to two-token answers with the reversal for long generations labelled an inference. |
| G5 | The run window was called "exclusive". The machine's load average was 2.29 at start and only the session's own server is known to have had no other client. | Yes | Reworded as an owner-scheduled quiet-machine window with the measured load and the scope of "no other client". |

## 3. Stale figures and numbers

| # | Check | Result |
|---|---|---|
| S1 | FIG-001 in `research/experiments/EXP-003/figures/` against the run's `latency.svg` | Identical SHA-256 (73883986...b2b0). Not stale. |
| S2 | `research/experiments/EXP-003/{config.json, metrics.csv, contrasts.csv, run_manifest.json}` against the run folder | Byte-identical (`cmp`). |
| S3 | README, CITATION.cff abstract, limitations header | Stale (M0 text: "no experiments have run", "no results exist yet"). Fixed in M4; see the evidence audit, finding A8. |
| S4 | Table 2 mixed summary levels without saying so (latency over 300 item medians; TTFT and throughput over 1,500 records). | Holds. Row labels and the table caption now state the level. |
| S5 | CLM-003 scope gave prompts "of about 70 to 130 tokens"; the raw records show prompt lengths up to 192 tokens, mostly 65 to 128. | Holds. Scope corrected from E4 (finding A2). |

## 4. Leakage

- The 300-item subset was drawn and committed before any model saw it (freeze record C4); prompts were developed on the validation split; both smoke runs used validation items. No leakage from outputs into the design was found.
- The M4 re-analysis was run after the confirmatory verdict was known. That is why it is labelled exploratory and cannot change the verdict. The post hoc exclusion in E5 is exactly the kind of analysis protocol section 9 forbids for confirmatory use; it is reported only to show that it does not change the sign.

## 5. Missing failed runs

| Run or attempt | In the manuscript before this pass? | Change made |
|---|---|---|
| EXP-001, EXP-002 aborted (JRN-0007) | Yes (Sections 5.1, 5.2, Table 1) | None |
| A2 failing every smoke request (RUN-SMOKE-0005) | Yes | None |
| M2 smoke attempt with the runtime down (JRN-0002) | No | Added to supplementary S1 |
| Simulated harness runs RUN-SMOKE-0001 to 0004 | Yes (supplementary S1 note) | None |
| EXP-003 `report.pdf` generated, not inspected, removed | Not a run; recorded in `sha256_manifest.json` and `progress.md` | None |
| S1 and S4 not run | Yes (Table 4) | None |

## 6. Findings that weaken the evidence and are now disclosed

- The warm-up request repeats each block's first item, so 10 records were measured on a just-processed prompt (E3). It does not move the medians but it is a measurement artefact of the frozen runner, now in Methods, Results and Limitations.
- Peak RSS ran opposite to the runtime-reported memory, which shows that RSS does not measure model memory here. Now stated in Limitations.

## 7. Net effect

No verdict changed. EXP-003 remains "H0 not rejected: no detected difference, not equivalence"; EXP-001 and EXP-002 remain failed with no results. Five passages of the manuscript were rewritten to remove overreach (R1, R2, G1, G2, G3, G5), one table relabelled (S4), one claim scope corrected (S5), and one failed attempt added to the supplementary matrix.
