<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# tests/

Run with `uv run pytest` or `uv run token-lab test`. No test contacts the real Ollama server: runtime behaviour (streaming, counters, runtime down, timeout, malformed stream, runtime error, HTTP 500) is tested against a local stub server defined in `conftest.py`.

- `test_items_prompts_scoring.py`: ingestion and invalid rows, seeded subsets, templates, extraction with known answers, scoring, a strict-implies-lenient property test.
- `test_runtime_tokens.py`: counter parsing and throughput from hand-counted values, error handling, the simulated backend.
- `test_stats.py`: McNemar and Holm against hand computations, McNemar against a brute-force reference, bootstrap invariants.
- `test_pipeline.py`: config validation, protocol-freeze guard, scheduling, runner integration (simulated and stub runtime), schema rejection of malformed results, analysis on a hand-built example, report outputs, hardware logs and the memory sampler, CLI.
