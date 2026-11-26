<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Run report RUN-EXP-001-0001

**Label: CONFIRMATORY.**

## Provenance

- Experiment: EXP-001; run: RUN-EXP-001-0001; schema 1.0.0
- Config SHA-256: `355d86f1cd3bc28373bef6e3e36c32828337583b0893d2b87d4c33fa48c7913e`
- Protocol SHA-256: `1997317c931cf95d04c271ab2414aef82306f5976f1eea7262eb1e4d54fee8e4`
- Git revision: `ca3a08fb536fbb80196354b5bdc0b3c26b38aa56` (dirty: False)
- Backend: ollama (simulated: False), runtime version 0.40.6
- Items: `results/raw/arc/ARC-Challenge-test.jsonl`, 300 items, SHA-256 `86ccaace4cd159b5c02b6b3339ebe8a7022a54f1b488e433c060b3bc38ac1f63`
- Host: Apple M1 Pro, macOS-15.3.1-arm64-arm-64bit, power ac, load average at start [1.68, 2.55, 2.78]
- Start 2026-11-26T12:31:06Z, end 2026-11-26T13:01:55Z, runtime 1849.129 s, 4500 requests, 0 failures
- Harness peak RSS: 46.7 MiB

## Per-arm metrics

Accuracy: per-item mean over repetitions, then mean over items. Latency: per-item median over repetitions, then median [Q1, Q3] over items (ms).

| Arm | Model | n items | Acc. strict | Acc. lenient | Chance | Errors | Format fail strict | Format fail lenient |
|---|---|---|---|---|---|---|---|---|
| A0 | phi4-mini:3.8b | 300 | 0.560 | 0.813 | 0.251 | 0 | 520 | 0 |
| A1 | llama3.1:8b | 300 | 0.720 | 0.720 | 0.251 | 0 | 10 | 0 |
| A2 | ministral-3:8b | 300 | 0.893 | 0.897 | 0.251 | 0 | 5 | 0 |

| Arm | Latency median [Q1, Q3] (ms) | TTFT median (ms) | Decode (tok/s) | Prefill (tok/s) | Determinism | Peak RSS (MiB) | Max swap delta (MiB) |
|---|---|---|---|---|---|---|---|
| A0 | 221.62 [218.18, 307.66] | 195.23 | 88.6 | 459.2 | 1.00 | 27.5 | 2778.1 |
| A1 | 434.82 [430.86, 555.21] | 393.56 | 49.1 | 227.4 | 1.00 | 27.5 | 734.1 |
| A2 | 476.81 [470.90, 606.89] | 430.42 | 45.7 | 1502.3 | 1.00 | 28.0 | 0.0 |

## Spread between repetitions (seeds)

| Arm | Accuracy per repetition | Median latency per repetition (ms) | CV of repetition medians |
|---|---|---|---|
| A0 | 0.560, 0.560, 0.560, 0.560, 0.560 | 222.16, 222.19, 50.12, 223.78, 221.71 | 0.410 |
| A1 | 0.720, 0.720, 0.720, 0.720, 0.720 | 434.55, 434.51, 434.59, 435.92, 434.94 | 0.001 |
| A2 | 0.893, 0.893, 0.893, 0.893, 0.893 | 476.63, 476.30, 476.68, 476.96, 476.73 | 0.000499 |

## Paired contrasts against the baseline

Paired bootstrap over items (10,000 resamples, seed 7, percentile 95 % CI); exact McNemar; Holm within each extraction rule.

| Arm vs baseline | Extraction | n | Delta (pp) | 95 % CI (pp) | b | c | McNemar p | Holm p |
|---|---|---|---|---|---|---|---|---|
| A1 vs A0 | strict | 300 | 16.0 | [9.7, 22.3] | 75 | 27 | 2.15e-06 | 2.15e-06 |
| A2 vs A0 | strict | 300 | 33.3 | [27.7, 39.3] | 108 | 8 | 1.65e-23 | 3.3e-23 |
| A1 vs A0 | lenient | 300 | -9.3 | [-14.7, -4.3] | 19 | 47 | 0.000756 | 0.000756 |
| A2 vs A0 | lenient | 300 | 8.3 | [4.0, 12.7] | 35 | 10 | 0.000247 | 0.000494 |

## Projection of planned matrices

Measured seconds per request in this run (block wall time including warm-ups): 0.4095.

| Planned experiment | Planned requests | Projected hours |
|---|---|---|
| EXP-001 | 4500 | 0.5119 |
| EXP-002 | 60 | 0.0068 |
| EXP-003 | 3000 | 0.3413 |

## Figure

![RUN-EXP-001-0001: per-item latency. Dots: per-item median latency in ms; red bar: median over items. n = 300 items per arm.](latency.svg)
