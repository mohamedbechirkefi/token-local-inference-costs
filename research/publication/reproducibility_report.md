<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Reproducibility report (M6, 2026-11-25)

Actual commands and outputs of the M6 session (DL-014). No inference was run and Ollama was not contacted (timing addendum: the machine is shared, so no new timing is compared with the frozen results). `<scratch>` is the session's scratch folder outside the repository; it is deleted at the end.

- [x] Clean clone into a separate directory
- [x] `uv sync` from `uv.lock`
- [x] Tests run (actual count and outcome below)
- [x] Smoke reproduction: analysis and report generation re-run from committed results, compared byte for byte
- [x] Demo build, tests and accessibility checker
- [x] Data manifest, artifact manifest and links verified
- [x] Secret and licence scan
- Known blocker, disclosed: `manuscript.tex` is generated but not compiled (no TeX distribution, DL-002).

## 1. Clean clone (HEAD 26eede9, before any M6 change)

| Step | Command | Actual output |
|---|---|---|
| Clone | `git clone -q <repo> <scratch>/clone` (local, no network) | HEAD `26eede9` |
| Environment | `../.tools/py/bin/uv sync --frozen --all-groups --all-extras` | success; last lines `+ token-lab==0.1.0 (from file://<scratch>/clone)` and `+ typing-extensions==4.16.0` |
| Tests | `.venv/bin/python -m pytest -q` | `151 passed in 10.83s` |
| Report regeneration (smoke reproduction) | `.venv/bin/token-lab report --result <run>/result.json --out <scratch>/regen/<run>` for RUN-EXP-003-0001 and RUN-SMOKE-0001 to 0006, then `cmp` of every generated file with the committed one | 29 of 29 files byte-identical (`report.md`, `metrics.csv`, `latency.svg`, plus `contrasts.csv` for the six matrix runs and `cold_warm.csv`, `cold_warm.svg` for RUN-SMOKE-0006) |
| M4 exploratory re-analysis | `.venv/bin/python -I scripts/m4_exploratory_exp003.py --repo .` | rewrote `results/exploratory/M4-EXPL-0001/exploratory_exp003.json`; `git status --short` empty (byte-identical) |
| Copies in `research/experiments/EXP-003/` | `cmp` of `metrics.csv`, `contrasts.csv`, `config.json`, `run_manifest.json` with the run folder | 4 of 4 identical |
| Harness smoke (exploratory, simulated backend) | `.venv/bin/token-lab smoke --config experiments/smoke-simulated.json` | RUN-SMOKE-0007: 150 requests, 0 failures, `simulated: true`; load average 2.08 1.96 1.69. It shows only that the harness executes; its timing is not compared with any published number. The output folder was deleted with the clone. |
| Demo install | `npm ci --prefer-offline` (Node 22.23.3, npm cache in scratch) | `added 53 packages in 679ms` |
| Demo tests | `npm test` | `Test Files 2 passed (2)`, `Tests 21 passed (21)` |
| Demo build | `npm run build` | `built in 271ms` (index 252.55 kB, worker 2.02 kB, CSS 5.95 kB) |
| Accessibility checker | `node tools/a11y_check.mjs dist` | 9 PASS lines, then `A11Y-CHECK PASS` |
| Export determinism | `.venv/bin/python scripts/export_demo_data.py`; `.venv/bin/python scripts/export_sandbox_fixture.py`; `git status --short` | `wrote demo/public/data/results.json (87092 bytes)`; `wrote demo/src/engine.fixture.json`; 0 status lines |

Checker output in the clone:

```
PASS results render (no fail-closed panel): 3 experiment panels
PASS text contrast, light scheme (WCAG AA)
PASS text contrast, dark scheme (WCAG AA)
PASS keyboard reaches every focusable element: 24 reached of 24
PASS visible focus indicator
PASS no horizontal page scroll at 360 px: overflow 0px
PASS reduced motion: no running animations: 0 running
PASS no request leaves the local origin
PASS offline after first load: results stay, sandbox runs: Sandbox output (illustrative, not a measurement; seed 1, 10,000 resamples, stric
A11Y-CHECK PASS
```

No step failed in the clean clone. The confirmatory timing values themselves cannot be reproduced without the owner's exclusive machine window and the runtime; that is by design (frozen protocol) and is not attempted.

## 2. Findings of this session and their fixes (working repository)

1. **PDF builder: wrapped lines read as list items.** pandoc wraps Typst output at 72 columns, and a wrapped line starting with "2018." was read by Typst as a numbered list item, leaving gaps in the reference list. Fixed by `--wrap=none` in `token_lab.report.build_pdf` (test `test_builder_disables_pandoc_line_wrapping`).
2. **PDF builder: figure outside the Typst root.** The manuscript references FIG-001 as `../experiments/...`; `build_pdf` now takes a Typst root (`research/` for the manuscript), sets the PDF title from the first heading when there is no YAML title, allows long tables to break across pages, and sets table text to 9 pt. `scripts/build_pdfs.py` builds all five PDFs and regenerates `manuscript.tex`.
3. **Supplementary tables overlapped** (64-character hashes and an eight-column matrix in equal-width columns). Fixed with relative column widths in `supplementary.md` and the 9 pt table text.
4. **Experiment reports: three lists rendered as raw Markdown** (no blank line before the list). Blank lines added in the EXP-001, EXP-002 and EXP-003 reports; no wording changed.
5. **FIG-001 clips the start of the lower arm label** ("Q8 llama3.1:8b-instruct-q8_0"). The figure is a committed result (hash in the artifact manifest), so it is not edited; the manuscript caption now names both rows.
6. **Absolute home-directory paths** in README, demo README, feasibility audit and the builder's tool defaults replaced by `~/research/...` or a path relative to the repository; see section 4.

The repository after these fixes was re-checked in a second fresh clone; see section 5.

## 3. Manifests and links

- `data/manifest.json`: 5 SHA-256 values checked against local files: the synthetic fixture (committed) and the four ARC files in the ignored `results/raw/arc/` of the working repository (test and validation, parquet and JSONL): 5 of 5 match. The ARC texts are not committed (owner decision of 2026-11-24) and are regenerated with `scripts/fetch_arc.py`, which needs network access and was not run.
- `research/publication/artifact_manifest.json`: 20 distinct repository paths named in it; 20 of 20 exist. FIG-001 SHA-256 matches.
- `results/confirmatory/RUN-EXP-003-0001/sha256_manifest.json`: 7 of 7 file hashes match.
- Frozen protocol hashes unchanged: ea86d0bb..., 1997317c..., 54d46696..., 8196740a....
- Relative Markdown links: `scripts/check_links.py` (new; test `tests/test_m6_release.py`): `relative links checked: 14; broken: 0`.
- Numbers: every decimal or thousands-separated number in README, `articles/*.md`, `demo/README.md` and `CITATION.cff` (except the CFF and package version fields) is printed in the manuscript (new parametrized test); the demo is covered by `tests/test_demo_export.py`.

## 4. Secret, identifier and licence scan

Scope: the 168 tracked or new files (`git ls-files` plus untracked, not ignored), PDFs and PNGs excluded from the text scan; the PDFs were checked with pypdf.

- E-mail addresses: 0 (the only address-like string is the AI co-author trailer `noreply@anthropic.com` in `CLAUDE.md`, a fixed non-personal address).
- Tokens, keys, private-key headers: 0. `.env` files: 0.
- Absolute home-directory paths: 21 hits in 7 files before the fixes; after: 0 in current README, demo README, feasibility audit and source code. Remaining: 8 in `CLAUDE.md` (session instructions that name the shared tool locations; kept because they are operating instructions for this machine) and 3 in the append-only `progress.md` and `research/decision_log.md` (not edited; a note is appended).
- Personal identifiers: the owner's name appears where the freeze decision C3 recorded it (author line placeholder, report identification sections, `CITATION.cff`). The final author line is an open owner decision.
- PDF metadata: title set in all five PDFs; no e-mail address and no local path in metadata or text.
- Dependency licences: `research/publication/dependency_licences.md` (14 Python distributions, 53 npm packages). Flags: numpy's wheel bundles libgfortran (GPL-3.0-or-later WITH GCC-exception-3.1); lightningcss is MPL-2.0 (build only). Nothing unknown.
- SPDX headers: every text file added since M0 carries the repository identifier where the format allows, except generated result SVGs (frozen results, not edited) and `demo/.npmrc` (template file kept unchanged). `.gitignore` and the generated `manuscript.tex` gained the header in this session.

## 5. Second fresh clone (after the M6 commit)

Recorded in `progress.md` (M6 session, "Second fresh clone").
