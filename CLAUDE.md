<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# CLAUDE.md: how every session works in TOKEN

TOKEN studies local inference economics: how local model configurations trade off quality, latency and resource use on the owner's own hardware. `master_prompt.md` is the authority. It is never edited. If this file and `master_prompt.md` conflict, `master_prompt.md` wins; record the conflict in `progress.md`.

## 1. Reading order (every session, before modifying anything)

1. `master_prompt.md`
2. `roadmap.md`
3. `progress.md`
4. `research/protocol.md`
5. `research/claims_register.csv`

Then run `git status` and inspect existing files. Never overwrite the owner's changes. State the current milestone and the next bounded task before working.

## 2. Mandatory requirements (master prompt section 11)

- Maintain the section 11.1 tree: `research/experiment_registry.csv`, `research/protocol.md`, `research/claims_register.csv`, `research/paper/` (manuscript.md canonical, manuscript.tex generated, references.bib, figures/, supplementary.md), `research/experiments/EXP-NNN/` (protocol.md, report.md, config.json, run_manifest.json, metrics.csv, figures/, reproduction.md) and `research/publication/` (artifact_manifest.json, claims_audit.md, reproducibility_report.md, author_review.md, release_checklist.md).
- Stable identifiers: EXP-NNN for experiments, RUN-EXP-NNN-NNNN for runs, FIG-NNN for figures, CLM-NNN for claims.
- Register every experiment in `research/experiment_registry.csv` before confirmatory execution. A seed or replicate is a run, not a new experiment. A new question or materially different protocol gets a new ID.
- Before each experiment, `EXP-NNN/protocol.md` follows section 11.2. Freezing it (version and SHA-256 recorded) is the owner's decision.
- Every registered experiment gets a standalone report following the twelve-part structure of section 11.3, including failed, null, abandoned and exploratory ones, visibly labelled.
- One integrated manuscript (section 11.4). Markdown is canonical. LaTeX and PDF are generated with the zero-cost toolchain (section 5 below). Never claim a PDF exists unless it was generated and inspected.
- Evidence pipeline (section 11.5): tables and figures are generated once from versioned results and reused everywhere; a manifest maps every number to experiment ID, run IDs, metric definition, result path, generator script, config or protocol hash and code revision. A second review pass challenges the preferred hypothesis.
- Extended milestones (section 11.6): M0/M1 registry, manuscript skeleton and experiment protocols; M2 output schemas, reproducibility manifests and report generators with the core; M3 reports as experiments finish; M4 evidence audit and synthesis; M5 identical results across demo, paper, reports and articles; M6 compile and inspect PDFs, clean-clone reproduction, owner review checklist.
- Update `roadmap.md` and append to `progress.md` after every milestone and before the session ends. Never mark incomplete work done.

## 3. Rules (all sessions)

### Gates
- Never push, add a remote, create a GitHub repository or publish anything (G-PUBLIC). The repository is public at https://github.com/mohamedbechirkefi/token-local-inference-costs since 2026-11-25; pushes and the demo deployment are done by the coordinator on the owner's recorded word, never by a session.
- No paid service of any kind. No paid APIs, inference, data, compute or hosting. The coding subscription is never an inference backend.
- Never freeze a protocol yourself. Freezing is the owner's decision (G-FREEZE). Until the owner freezes a protocol, every run is exploratory and labelled as such.
- No confirmatory experiments before the owner freezes the protocol. A tiny exploratory toolchain smoke check is allowed and labelled exploratory.

### Scope
- Work only inside this repository. Tools outside it are used read-only: `/usr/local/bin/python3`, `../.tools/py/bin/` (uv, typst, pypdf, pillow), `../.tools/pandoc`, `../../helix/.tools/node/bin` (paths relative to the repository root; never modify that folder), git.
- Do not touch any other folder under the research root (hive, helix, cogkt, trading, the other labs).
- Ollama on this machine serves the owner's other projects. Do not start, stop, pull, remove or reconfigure Ollama or its models unless the owner explicitly authorises it for a given session. Confirmatory timing runs need an owner-scheduled exclusive window.
- Never kill processes you did not start. Never delete anything you did not create in the current session.

### Truthfulness
- Never fabricate results, citations, test counts or PDFs.
- Record the commands you ran and their actual outputs in `progress.md`.
- A source not actually opened is labelled unverified and is not cited as read.
- Measured quantities (runtime, tokens, memory) are kept separate from modelled ones (electricity, cost). Modelled values are labelled modelled.

### Files and style
- New text and code files start with `SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0` as a comment where the format allows. JSON and CSV files are covered by `NOTICE.md`.
- English. No em dashes. Plain, formal register.
- No e-mail address, personal identifier or secret in any committed file (git author metadata excepted).
- Refer to the owner as "the owner" (they/them).
- Large generated outputs stay out of git (`results/raw/` is ignored); provide deterministic regeneration scripts and small fixtures.

### Commits
- Local commits only: `git -c user.name=mohamedbechirkefi -c user.email=<the owner's git e-mail, kept out of committed files> commit`, message ending with a blank line and `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Run `git status` before and after.

## 4. Development commands

Run from the repository root.


- Lock dependencies: `../.tools/py/bin/uv lock`
- Create the environment: `../.tools/py/bin/uv sync`
- Tests: `../.tools/py/bin/uv run pytest` (or `uv run token-lab test`)
- Smoke (exploratory only): `uv run token-lab smoke --config experiments/smoke-simulated.json`; against a running, idle Ollama: `--config experiments/smoke-ollama.json`
- Run: `uv run token-lab run --config experiments/EXP-001.json` (refused until the owner freezes the protocol)
- Report: `uv run token-lab report --result results/<label>/<RUN-ID>/result.json [--pdf]`

## 5. Zero-cost publication toolchain (decision DL-002)

There is no TeX distribution on this machine. PDFs are produced as Markdown to Typst with pandoc 3.6.3, compiled with the `typst` Python package (0.15.0). `manuscript.tex` is generated from Markdown with pandoc for venues that need LaTeX source; it is not compiled locally.

Build commands (verified on the M0 skeleton):

```
../.tools/pandoc research/paper/manuscript.md -s -t typst -V mainfont="Libertinus Serif" -o <scratch>/manuscript.typ
../.tools/py/bin/python -c "import typst; typst.compile('<scratch>/manuscript.typ', output='research/paper/manuscript.pdf')"
../.tools/pandoc research/paper/manuscript.md -s -t latex -o research/paper/manuscript.tex
```

A PDF is committed only after it is generated from validated content and visually inspected.
