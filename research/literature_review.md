<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Literature and source review (M0, preliminary)

Status: preliminary, not a systematic review. Every entry marked **opened** was actually opened on 2026-11-24 with WebFetch; only the page shown (arXiv abstract page, dataset card or documentation page) was read, not the full paper, unless stated. Entries marked **unverified** have not been opened and must not be cited as read.

## 1. Sources opened

| Key | Source | Accessed | What was verified | Relevance |
|---|---|---|---|---|
| clark2018arc | P. Clark, I. Cowhey, O. Etzioni, T. Khot, A. Sabharwal, C. Schoenick, O. Tafjord. "Think you have Solved Question Answering? Try ARC, the AI2 Reasoning Challenge." arXiv:1803.05457, 2018. https://arxiv.org/abs/1803.05457 | 2026-11-24 (abstract page) | Title, authors, date; 7,787 science questions split into Challenge and Easy sets. | Candidate benchmark (DL-004). |
| arc-hf | AI2 ARC dataset card, https://huggingface.co/datasets/allenai/ai2_arc | 2026-11-24 | Licence cc-by-sa-4.0; ARC-Challenge splits train 1,119, validation 299, test 1,172; fields id, question, choices (text, label), answerKey. | Data licence and schema. |
| cobbe2021gsm8k | K. Cobbe et al. "Training Verifiers to Solve Math Word Problems." arXiv:2110.14168, 2021. https://arxiv.org/abs/2110.14168 | 2026-11-24 (abstract page) | Title, authors, date; GSM8K, about 8,500 grade-school math problems. | Optional extension benchmark. |
| gsm8k-hf | GSM8K dataset card, https://huggingface.co/datasets/openai/gsm8k | 2026-11-24 | Licence MIT; main config train 7,473 and test 1,319. | Data licence. |
| dettmers2022kbit | T. Dettmers, L. Zettlemoyer. "The case for 4-bit precision: k-bit Inference Scaling Laws." arXiv:2212.09720, 2022. https://arxiv.org/abs/2212.09720 | 2026-11-24 (abstract page) | Over 35,000 experiments, 19M to 176B parameters; 4-bit precision is generally optimal for the trade-off between total model bits and zero-shot accuracy. | Prior evidence for the size versus precision trade-off; motivates EXP-003. |
| dettmers2022int8 | T. Dettmers, M. Lewis, Y. Belkada, L. Zettlemoyer. "LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale." arXiv:2208.07339, NeurIPS 2022. https://arxiv.org/abs/2208.07339 | 2026-11-24 (abstract page) | 8-bit inference roughly halves memory without performance degradation (as stated in the abstract). | Background on quantization. |
| lin2023awq | J. Lin et al. "AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration." arXiv:2306.00978, 2023 (v6 revised 2026-04-25). https://arxiv.org/abs/2306.00978 | 2026-11-24 (abstract page) | Weight-only low-bit quantization guided by activation statistics. | Background; not used directly (GGUF k-quants are used here). |
| llamacpp-quantize | llama.cpp quantize README, https://github.com/ggml-org/llama.cpp/blob/master/tools/quantize/README.md | 2026-11-24 | Table for Llama-3.1-8B: Q4_K_M 4.8944 bits/weight, 4.58 GiB, text generation 71.93 t/s; Q8_0 8.5008 bits/weight, 7.95 GiB, 50.93 t/s. Hardware for that table not recorded in our note. | External reference values for comparison only; never mixed with our measurements. |
| ollama-api | Ollama API documentation, https://raw.githubusercontent.com/ollama/ollama/main/docs/api.md | 2026-11-24 | Response fields total_duration, load_duration, prompt_eval_duration, eval_duration in nanoseconds; prompt_eval_count and eval_count in tokens; tokens/s = eval_count / eval_duration x 1e9; options seed, temperature, num_predict; keep_alive 0 unloads. Main-branch docs; the installed client is 0.9.6, so field semantics must be re-checked against the installed version. | Measurement definitions. |
| liang2022helm | P. Liang, R. Bommasani, T. Lee, D. Tsipras, D. Soylu et al. "Holistic Evaluation of Language Models." arXiv:2211.09110, 2022. https://arxiv.org/abs/2211.09110 | 2026-11-24 (abstract page) | Efficiency is among the measured dimensions with accuracy and others. | Related work: multi-metric evaluation. |
| samsi2023watts | S. Samsi et al. "From Words to Watts: Benchmarking the Energy Costs of Large Language Model Inference." arXiv:2310.03003, 2023. https://arxiv.org/abs/2310.03003 | 2026-11-24 (abstract page) | Energy and performance of LLaMA sizes on V100/A100 GPUs. | Related work on energy; datacentre GPUs, not consumer laptops. |
| sclar2023format | M. Sclar, Y. Choi, Y. Tsvetkov, A. Suhr. "Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design." arXiv:2310.11324, 2023. https://arxiv.org/abs/2310.11324 | 2026-11-24 (abstract page) | Formatting changes alone produced accuracy differences up to 76 points (LLaMA-2-13B, few-shot); authors recommend reporting a range across formats. | Motivates sensitivity analysis S1 (prompt template), which could invalidate the main interpretation. |

## 2. Model licences (read from the locally installed Ollama licence layers, read-only)

| Model tag | Licence layer text (first lines) | Notes |
|---|---|---|
| phi4-mini:3.8b | MIT License, Copyright (c) Microsoft Corporation | Permissive. |
| llama3.1:8b | Llama 3.1 Community License Agreement, release date July 23, 2024 | Custom licence with use conditions and an acceptable use policy; weights are not redistributed here. Full terms to be read by the owner. |
| ministral-3:8b | Apache License 2.0 | Permissive. |
| qwen3.5:4b | Apache License 2.0 | Permissive; runtime compatibility unverified (see feasibility). |
| nomic-embed-text | Apache License 2.0 | Embedding model; out of scope. |

## 3. Unverified (not opened; do not cite as read)

- Model cards and technical reports for Phi-4-mini, Llama 3.1, Ministral 3 and Qwen3.5.
- MLPerf Inference and any consumer-hardware benchmark suites.
- Apple documentation on unified memory and `powermetrics` semantics.
- Studies of laptop-scale LLM energy measurement.

## 4. Gap and narrow contribution (draft)

Published quantization and efficiency studies (dettmers2022kbit, samsi2023watts, liang2022helm) mostly report datacentre hardware or aggregate scaling. Tool documentation (llamacpp-quantize) reports throughput but not task accuracy alongside it. The narrow contribution proposed here is a small, fully reproducible, paired measurement of accuracy, latency and memory for installed off-the-shelf local model configurations on one consumer laptop, with uncertainty at the item level and an explicit test of prompt-format sensitivity. No novelty is claimed beyond that scope, and the literature search above is not systematic.

## 5. Full-text check of the cited arXiv papers (M6, 2026-11-25)

At M6 the free arXiv PDF of every cited arXiv paper was downloaded from arxiv.org (open access; no login, no paid access) and its text extracted with pypdf. Each statement the manuscript makes about the paper was searched for and checked against the body text. The papers were not read cover to cover: the label is "full text checked for the cited statement", which is stronger than "abstract only" and weaker than "read in full". Page numbers refer to the PDF of the version named.

| Key | Version opened | Statement in the manuscript | Where it is in the full text | Result |
|---|---|---|---|---|
| clark2018arc | 1803.05457v1 | Challenge set of grade-school science multiple-choice questions; test split 1,172 items | p. 1 (Challenge Set: questions answered incorrectly by both a retrieval-based and a word co-occurrence algorithm; natural grade-school science questions); p. 3, set-size table (Challenge test 1172) | confirmed |
| dettmers2022kbit | 2212.09720v2 | More than 35,000 experiments, models from 19M to 176B parameters, 4-bit precision generally optimal for total model bits against zero-shot accuracy | p. 2, Introduction ("more than 35,000 zero-shot experiments", "19M to 176B parameters"); p. 8, Discussion ("almost universally optimal") | confirmed; the paper's own wording is "almost universally optimal" |
| dettmers2022int8 | 2208.07339v2 | 8-bit inference roughly halves memory without performance degradation | p. 1 ("reduces the memory needed for inference by half while retaining full precision performance"); p. 2 ("without any performance degradation"); p. 4 (BLOOM-176B memory footprint reduced by 1.96x) | confirmed |
| lin2023awq | 2306.00978v5 | Activation-aware weight-only quantization | p. 2, Introduction ("hardware-friendly low-bit weight-only quantization"); p. 3, Section 3 (weight-only quantization method) | confirmed; v5 is titled "AWQ: Activation-aware Weight Quantization for On-Device LLM Compression and Acceleration", while the bibliography keeps the earlier title |
| liang2022helm | 2211.09110v2 | Efficiency is among the measured dimensions | pp. 3 and 4, Introduction (seven metrics: accuracy, calibration, robustness, fairness, bias, toxicity, efficiency) | confirmed |
| samsi2023watts | 2310.03003v1 | Energy and performance of LLaMA models on V100 and A100 GPUs | p. 2 (LLaMA studied); pp. 3 and 4 (V100 and A100 nodes, experiment setup) | confirmed |
| sclar2023format | 2310.11324v2 | Up to 76 accuracy points from formatting changes; recommends reporting a range over formats | p. 1 (up to 76 accuracy points for LLaMA-2-13B between equivalent formats); p. 9, Conclusion ("we recommend that work evaluating LLMs with prompting-based methods would benefit from reporting a range of performance") | confirmed; the 76-point figure is for one model (LLaMA-2-13B), and the manuscript now says so |

No statement had to be weakened; one (sclar2023format) was made more precise. The non-arXiv sources (arc-hf, llamacpp-quantize, ollama-api) are web pages and were opened in full on 2026-11-24.
