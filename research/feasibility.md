<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Feasibility audit (M0, 2026-11-24)

All values below come from commands run in the M0 session; outputs are reproduced in `progress.md`.

## 1. Hardware

| Item | Value | Command |
|---|---|---|
| Machine | MacBook Pro, MacBookPro18,1 | `system_profiler SPHardwareDataType` |
| Chip | Apple M1 Pro, 10 CPU cores (8 performance, 2 efficiency), 16 GPU cores, Metal 3 | `sysctl -n machdep.cpu.brand_string hw.ncpu hw.perflevel0.physicalcpu hw.perflevel1.physicalcpu`, `system_profiler SPDisplaysDataType` |
| Memory | 16 GB unified (17179869184 bytes) | `sysctl -n hw.memsize` |
| OS | macOS 15.3.1 (24D70) | `sw_vers` |
| Free disk | 129 GiB available on the data volume (460 GiB) | `df -h ~` |
| Power at audit time | Battery, 97 %, discharging | `pmset -g batt` |

The brief's expected values (M1 Pro, 10 cores, 16 GB, macOS 15.3.1, about 127 GB free) are confirmed; free disk read 129 GiB.

## 2. Tools

| Tool | Version | Location | Status |
|---|---|---|---|
| Python | 3.12.1 | `/usr/local/bin/python3` | confirmed |
| uv | 0.9.5 | `../.tools/py/bin/uv` (relative to the repository) | confirmed |
| typst (Python package) | 0.15.0 | `../.tools/py/bin/python` | confirmed by import; there is no `typst` executable in that folder, the package is the compiler |
| pypdf | 6.20.0 | same environment | confirmed |
| pillow | 11.3.0 | same environment | confirmed |
| pandoc | 3.6.3 | `../.tools/pandoc` | confirmed |
| Node | 22.23.3 | `helix/.tools/node/bin` under the research root (read-only) | confirmed |
| git | 2.42.1 | system | confirmed |
| TeX | none | `which tex pdflatex xelatex tectonic` | absent; see DL-002 |
| powermetrics | present at `/usr/bin/powermetrics` | requires elevated privileges | not used (DL-005) |

## 3. Local inference runtime and models (read-only inventory)

The owner runs Ollama for other projects. This session did not start, stop or pull anything. Commands used: `which ollama`, `ollama --version`, `ollama list`, and reading the manifest JSON files under `.ollama/models/manifests/registry.ollama.ai/library/` in the owner's home folder plus their config and licence blobs.

- `ollama` binary: `/opt/homebrew/bin/ollama`, client version 0.9.6.
- Server: not running at audit time ("could not connect to a running Ollama instance"). Its version could not be read.
- Model store: 16 GiB of blobs.

| Tag | Family / parameters | Format / quantization | Size (manifest layers) | Licence | Use here |
|---|---|---|---|---|---|
| phi4-mini:3.8b | phi3, 3.8B | GGUF Q4_K_M | 2.49 GB | MIT | EXP-001 baseline |
| llama3.1:8b (same blob as llama3.1:latest) | llama, 8.0B | GGUF Q4_K_M | 4.92 GB | Llama 3.1 Community License | EXP-001 arm |
| ministral-3:8b | mistral3, 8.9B | GGUF Q4_K_M | 6.02 GB | Apache-2.0 | EXP-001 arm |
| qwen3.5:4b | not recorded in config | safetensors, nvfp4 | 3.97 GB | Apache-2.0 | excluded pending smoke check (format and runtime compatibility unverified) |
| nomic-embed-text:latest | nomic-bert, 137M | GGUF F16 | 0.27 GB | Apache-2.0 | out of scope (embedding model) |

All installed generative GGUF models share one quantization (Q4_K_M). A quantization comparison therefore needs at least one additional download (for example a Q8_0 variant of llama3.1 8B), which is an owner decision (EXP-003). External reference: llama.cpp reports Q8_0 of Llama-3.1-8B at 7.95 GiB, which fits in 16 GB but leaves little headroom.

## 4. Time and compute budget

- Five focused development days, planning estimate only.
- EXP-001: 300 items x 3 arms x 5 repetitions = 4,500 requests. Per-request time is unknown until the smoke run; the run is capped at 4 hours of wall-clock. If the smoke run projects beyond the cap, the owner chooses between fewer repetitions for timing (accuracy is deterministic under greedy decoding) and a smaller item set, before the freeze.
- EXP-002: 3 arms x 10 cold and 10 warm trials; under 1 hour expected (unmeasured).
- EXP-003 (conditional): 300 items x 2 arms x 5 repetitions.
- Cost: zero. No paid service. Electricity is not purchased by the project and is modelled only.

## 5. Risks

1. **Shared runtime.** Ollama serves other projects. Concurrent requests or loaded models would contaminate latency and memory. Confirmatory runs need an exclusive, owner-scheduled window; the runner will record `ollama ps` before and after and abort if a foreign model is loaded.
2. **Power and thermal state.** The audit found the laptop on battery. macOS may change performance on battery or in Low Power Mode. Protocol requires AC power and records `pmset -g batt` and `pmset -g` per run.
3. **Memory pressure.** 16 GB unified memory shared with the OS and the owner's applications. An 8.9B Q4_K_M model (6.02 GB) is comfortable; a Q8_0 8B model is tight. Swap use is logged and is an exclusion criterion.
4. **Version drift.** The client is 0.9.6; the server version is unknown. The qwen3.5 safetensors/nvfp4 model suggests it was pulled with a different (newer) runtime; this is an unverified inference. The server version is recorded per run, and a version change during a campaign invalidates timing comparisons.
5. **Cold start definition.** Without elevated privileges the OS page cache cannot be purged, so "cold" means "model unloaded from the runtime", not "weights absent from RAM". This limits EXP-002.
6. **Model identity confound.** EXP-001 arms differ in parameter count, architecture, training data and tokenizer at once. Size effects cannot be isolated causally; results are about these configurations.
7. **Tokenizer differences.** Tokens per second are not comparable across tokenizers in information content; latency per item is the cross-model time metric.

## 6. Fallback

If the runtime is unavailable or inadequate, the project falls back to a clearly labelled analytical resource model (memory from bits per weight and parameter count; throughput bounded by memory bandwidth), and makes no measured quality claim, as section 10 requires.
