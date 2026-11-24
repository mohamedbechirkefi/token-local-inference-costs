<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Run report RUN-SMOKE-0001

**Label: EXPLORATORY.** Exploratory output; not a finding and not usable for confirmatory analysis. Backend is SIMULATED: no model ran. Accuracy values are artefacts of a hash function and latencies measure the harness only. Items are a synthetic fixture, not a benchmark.

## Provenance

- Experiment: SMOKE; run: RUN-SMOKE-0001; schema 1.0.0
- Config SHA-256: `837ec4d2faeac9a74ee9ea5d45e75e9974a789c6eb0fed210804d659158ae1bf`
- Protocol SHA-256: `None`
- Git revision: `f3a5b5412572b4d67430d74c5bd153c67a3b6010` (dirty: False)
- Backend: simulated (simulated: True), runtime version simulated-0
- Items: `data/fixtures/synthetic_mc.jsonl`, 10 items, SHA-256 `3f7a73ff0c3295d711d8b258ce83025d90e9ebd5ce1e23279d63d0c95bceb86f`
- Host: Apple M1 Pro, macOS-15.3.1-arm64-arm-64bit, power ac, load average at start [5.15, 3.76, 2.88]
- Start 2026-11-24T16:01:06Z, end 2026-11-24T16:01:07Z, runtime 0.394 s, 150 requests, 0 failures
- Harness peak RSS: 43.0 MiB

## Per-arm metrics

Accuracy: per-item mean over repetitions, then mean over items. Latency: per-item median over repetitions, then median [Q1, Q3] over items (ms).

| Arm | Model | n items | Acc. strict | Acc. lenient | Chance | Errors | Format fail strict | Format fail lenient |
|---|---|---|---|---|---|---|---|---|
| A0 | phi4-mini:3.8b | 10 | 0.300 | 0.300 | 0.253 | 0 | 0 | 0 |
| A1 | llama3.1:8b | 10 | 0.000 | 0.000 | 0.253 | 0 | 0 | 0 |
| A2 | ministral-3:8b | 10 | 0.400 | 0.400 | 0.253 | 0 | 5 | 5 |

| Arm | Latency median [Q1, Q3] (ms) | TTFT median (ms) | Decode (tok/s) | Prefill (tok/s) | Determinism | Peak RSS (MiB) | Max swap delta (MiB) |
|---|---|---|---|---|---|---|---|
| A0 | 0.00325 [0.00308, 0.00378] | 0.00331 | 1000000.0 | 1000000.0 | 1.00 | n/a | 0.0 |
| A1 | 0.0031 [0.003, 0.00345] | 0.00317 | 1000000.0 | 1000000.0 | 1.00 | n/a | 0.0 |
| A2 | 0.00327 [0.00301, 0.00383] | 0.00331 | 1000000.0 | 1000000.0 | 1.00 | n/a | 0.0 |

## Spread between repetitions (seeds)

| Arm | Accuracy per repetition | Median latency per repetition (ms) | CV of repetition medians |
|---|---|---|---|
| A0 | 0.300, 0.300, 0.300, 0.300, 0.300 | 0.00342, 0.00313, 0.00352, 0.00323, 0.00333 | 0.047 |
| A1 | 0.000, 0.000, 0.000, 0.000, 0.000 | 0.003, 0.00292, 0.00321, 0.00319, 0.00329 | 0.050 |
| A2 | 0.400, 0.400, 0.400, 0.400, 0.400 | 0.00327, 0.00315, 0.00348, 0.00327, 0.00362 | 0.057 |

## Paired contrasts against the baseline

Paired bootstrap over items (10,000 resamples, seed 7, percentile 95 % CI); exact McNemar; Holm within each extraction rule.

| Arm vs baseline | Extraction | n | Delta (pp) | 95 % CI (pp) | b | c | McNemar p | Holm p |
|---|---|---|---|---|---|---|---|---|
| A1 vs A0 | strict | 10 | -30.0 | [-60.0, 0.0] | 0 | 3 | 0.25 | 0.5 |
| A2 vs A0 | strict | 10 | 10.0 | [-30.0, 50.0] | 3 | 2 | 1 | 1 |
| A1 vs A0 | lenient | 10 | -30.0 | [-60.0, 0.0] | 0 | 3 | 0.25 | 0.5 |
| A2 vs A0 | lenient | 10 | 10.0 | [-30.0, 50.0] | 3 | 2 | 1 | 1 |

## Projection of planned matrices

Measured seconds per request in this run (block wall time including warm-ups): 0.0022. The backend is simulated, so this projection says nothing about inference time.

| Planned experiment | Planned requests | Projected hours |
|---|---|---|
| EXP-001 | 4500 | 0.0027 |
| EXP-002 | 60 | 3.58e-05 |
| EXP-003 | 3000 | 0.0018 |

## Figure

![RUN-SMOKE-0001: per-item latency (SIMULATED backend). Dots: per-item median latency in ms; red bar: median over items. n = 10 items per arm.](latency.svg)
