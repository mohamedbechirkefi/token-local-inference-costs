<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Claims audit checklist (M4, 2026-11-25)

Full record: `research/publication/evidence_audit.md`. Manifest: `research/publication/artifact_manifest.json`. Second pass: `research/publication/review_pass_2.md`.

- [x] Every row of `research/claims_register.csv` (CLM-001 to CLM-015) has a result id or a stated "none", a config hash or "none", a table or figure, a manuscript section and an evidence path that resolves.
- [x] Every number matches the raw result file (denominator, unit, precision, sample count); mismatches A1 to A3 fixed (evidence audit section 4).
- [x] Measured and modelled values are labelled and never mixed (no modelled value is reported: S4 not run).
- [x] Every external claim maps to a source marked opened in `research/literature_review.md`; abstract-only reading is marked.
- [x] No causal or general claim beyond the configurations, machine and runtime measured (review pass 2, section 2).
- [x] Null and negative results are reported; failed runs are listed (EXP-001, EXP-002, JRN-0002, A2 smoke failures).
- [x] Second review pass challenged the preferred hypothesis (2026-11-25, `review_pass_2.md`).
- [ ] Owner review of the claims register (M6, `author_review.md`).
