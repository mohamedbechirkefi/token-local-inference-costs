# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Fetch ARC-Challenge (CC BY-SA 4.0) at a pinned revision and convert it to JSONL.

Downloads the Hugging Face ``allenai/ai2_arc`` parquet files for the
ARC-Challenge test and validation splits at a fixed git revision, checks
their SHA-256 against the values recorded at the freeze (when given), and
writes ``results/raw/arc/ARC-Challenge-{test,validation}.jsonl`` in the
"hf-arc-jsonl" format read by ``token_lab.items``. ``results/raw/`` is not
committed: the question texts stay out of git (owner decision, 2026-11-24);
only item IDs and hashes are committed.

Reading parquet needs ``pyarrow``, which the project environment does not
carry. Run with an interpreter that has it, in isolated mode, for example::

    /usr/local/bin/python3 -I scripts/fetch_arc.py --repo .

The conversion is deterministic: rows keep file order, keys are sorted and
lines end with a newline, so the JSONL SHA-256 is reproducible.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

REVISION = "210d026faf9955653af8916fad021475a3f00453"
BASE = "https://huggingface.co/datasets/allenai/ai2_arc/resolve/" + REVISION + "/ARC-Challenge/"
SPLITS = {"test": "test-00000-of-00001.parquet", "validation": "validation-00000-of-00001.parquet"}
# Recorded at the freeze (2026-11-24); a mismatch aborts.
EXPECTED_PARQUET_SHA256: dict[str, str] = {
    "test": "62f03257e737aed263f55c6abf87c7bb0028a44a6bdd2a26eb1279eb42c1d1e9",
    "validation": "395a5c88d1580d69855fbaee9450270578df1ad5af6259771cd0a42c20e99f05",
}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def to_jsonl(parquet_path: Path) -> bytes:
    import pyarrow.parquet as pq

    rows = pq.read_table(parquet_path).to_pylist()
    out = []
    for r in rows:
        row = {"id": r["id"], "question": r["question"],
               "choices": {"text": list(r["choices"]["text"]), "label": list(r["choices"]["label"])},
               "answerKey": r["answerKey"]}
        out.append(json.dumps(row, sort_keys=True, ensure_ascii=False))
    return ("\n".join(out) + "\n").encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args(argv)
    dest = Path(a.repo) / "results" / "raw" / "arc"
    dest.mkdir(parents=True, exist_ok=True)
    info = {"revision": REVISION, "splits": {}}
    for split, fname in SPLITS.items():
        url = BASE + fname
        pq_path = dest / f"ARC-Challenge-{split}.parquet"
        with urllib.request.urlopen(url, timeout=60) as resp:
            data = resp.read()
        digest = sha256_bytes(data)
        exp = EXPECTED_PARQUET_SHA256.get(split)
        if exp and exp != digest:
            print(f"SHA-256 mismatch for {split}: {digest} != {exp}", file=sys.stderr)
            return 2
        pq_path.write_bytes(data)
        jl = to_jsonl(pq_path)
        jl_path = dest / f"ARC-Challenge-{split}.jsonl"
        jl_path.write_bytes(jl)
        info["splits"][split] = {"url": url, "parquet_sha256": digest, "parquet_bytes": len(data),
                                 "jsonl_path": str(jl_path.relative_to(a.repo)),
                                 "jsonl_sha256": sha256_bytes(jl), "n_rows": jl.count(b"\n")}
    print(json.dumps(info, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
