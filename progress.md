<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Progress journal (append-only)

## 2026-11-24: M0 session (bootstrap and feasibility) and M1 drafts

**Milestone:** M0. **Next bounded task:** owner review of the M0 gate and decisions D1 to D6; then M2 implementation (may start before the freeze, exploratory only).

### Starting state

`git status`: "On branch main, nothing to commit, working tree clean". One commit, `195a564` (master prompt and the owner's licence package).

### Commands run and actual outputs (abridged where long)

- `sysctl -n machdep.cpu.brand_string hw.ncpu hw.memsize hw.perflevel0.physicalcpu hw.perflevel1.physicalcpu`: `Apple M1 Pro`, `10`, `17179869184`, `8`, `2`.
- `sw_vers`: macOS 15.3.1, build 24D70.
- `df -h /Users/bechir`: 460Gi size, 311Gi used, 129Gi available.
- `system_profiler SPHardwareDataType SPDisplaysDataType`: MacBook Pro MacBookPro18,1, Apple M1 Pro, 10 cores (8 performance, 2 efficiency), 16 GB, GPU 16 cores, Metal 3.
- `pmset -g batt`: battery power, 97 %, discharging.
- `/usr/local/bin/python3 --version`: Python 3.12.1. `uv --version`: uv 0.9.5 (2025-10-21). `pandoc --version`: pandoc 3.6.3. Node: v22.23.3. `git --version`: 2.42.1.
- `ls /Users/bechir/research/labs/.tools/py/bin/`: no `typst` executable. Import check in that environment: typst 0.15.0, pypdf 6.20.0, pillow 11.3.0.
- `which tex pdflatex xelatex tectonic`: none found.
- `which powermetrics`: `/usr/bin/powermetrics` (requires elevated privileges; not run).
- Ollama, read-only: `which ollama` `/opt/homebrew/bin/ollama`; `ollama --version` "Warning: could not connect to a running Ollama instance / client version is 0.9.6"; `ollama list` "Error: ollama server not responding". Manifest directory lists llama3.1, ministral-3, nomic-embed-text, phi4-mini, qwen3.5. Parsed manifests and config blobs: phi4-mini:3.8b GGUF Q4_K_M 2.49 GB; llama3.1:8b (= latest) GGUF Q4_K_M 4.92 GB; ministral-3:8b GGUF Q4_K_M 6.02 GB (8.9B); nomic-embed-text F16 0.27 GB; qwen3.5:4b safetensors nvfp4 3.97 GB. Licence layers: Llama 3.1 Community License; Apache-2.0 (ministral-3, qwen3.5, nomic-embed-text); MIT (phi4-mini). `du -sh ~/.ollama/models/blobs`: 16G. Nothing was started, stopped or pulled.
- WebFetch (2026-11-24), opened: arXiv abstract pages 1803.05457, 2110.14168, 2212.09720, 2208.07339, 2306.00978, 2211.09110, 2310.03003, 2310.11324; dataset cards allenai/ai2_arc (cc-by-sa-4.0; ARC-Challenge test 1,172) and openai/gsm8k (MIT); Ollama API docs; llama.cpp quantize README. Details in `research/literature_review.md`.
- `uv lock` (with `exclude-newer = 2026-11-10`): "Resolved 15 packages in 302ms"; numpy 2.3.4, psutil 7.1.0, jsonschema 4.25.1, pytest 8.4.2.
- `uv sync`: installed 15 packages including token-lab 0.0.0 into `.venv/` (ignored by git).
- `uv run pytest -q`: "no tests ran in 0.00s", exit 5 (no tests exist yet; this is not a pass).
- Toolchain smoke (exploratory, JRN-0001): pandoc to Typst then `typst.compile` failed with "font fallback list must not be empty"; with `-V mainfont="Libertinus Serif"` it succeeded, 3-page skeleton PDF in the session scratchpad (not committed). `pandoc -t latex` produced `research/paper/manuscript.tex` (116 lines before the SPDX header was added).

### Changed files

Created: `CLAUDE.md`, `roadmap.md`, `progress.md`, `README.md`, `CITATION.cff`, `pyproject.toml`, `uv.lock`, `src/token_lab/__init__.py`, `data/manifest.json`, `research/{decision_log.md, literature_review.md, protocol.md, feasibility.md, limitations.md, claims_register.csv, experiment_journal.jsonl, experiment_registry.csv}`, `research/experiments/EXP-00{1,2,3}/protocol.md`, `research/paper/{manuscript.md, manuscript.tex, references.bib, supplementary.md, figures/README.md}`, `research/publication/{artifact_manifest.json, claims_audit.md, reproducibility_report.md, author_review.md, release_checklist.md}`, READMEs in `results/`, `tests/`, `experiments/`, `demo/`, `articles/`. Appended: section 6 (development commands) to `CONTRIBUTING.md`. Licence files unchanged.

### Decisions

DL-001 (owner: protective licence), DL-002 (toolchain), DL-003 to DL-005 proposed. See `research/decision_log.md`.

### Decisions the owner must make

- **D1, freeze:** approve or amend `research/protocol.md` and the EXP-001 to EXP-003 protocols (G-FREEZE), including n = 300 versus the full 1,172-item test set.
- **D2, runtime window:** schedule an exclusive Ollama window on AC power for EXP-001 and EXP-002 (EXP-002 unloads models from the shared runtime).
- **D3, download:** approve or decline a free download of a Q8_0 Llama 3.1 8B variant (about 8 GB) for EXP-003.
- **D4, qwen3.5:4b:** include it after a smoke check, or exclude it (format nvfp4, runtime compatibility unverified).
- **D5, fixture rights:** bundle the ARC subset under its CC BY-SA 4.0 terms, or commit item IDs only and regenerate.
- **D6, energy:** keep energy modelled only, or authorise `sudo powermetrics` for measured power.
- Also: review the Llama 3.1 Community License terms for this use.

### Outstanding risks

Shared runtime interference; battery and thermal state; memory pressure for Q8_0; Ollama server version unknown (client 0.9.6); cold start is runtime-cold only; arms confound size with architecture. See `research/feasibility.md`.

### Not done, and why

- No experiments, no smoke inference run: the Ollama server was not running and this session may not start it.
- No dataset downloaded (brief: metadata only). Subset IDs and SHA-256 are therefore not yet fixed.
- No tests: no implementation exists yet (M2).
- No PDF committed: only the skeleton exists.
