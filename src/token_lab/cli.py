# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Command line: ``token-lab {smoke,run,report,test}``.

- ``smoke``: run an exploratory config (refuses any confirmatory config).
- ``run``: run a config; refuses a confirmatory config while its protocol is not frozen.
- ``report``: build tables, figure and optional PDF from a result file.
- ``repeat-blocks``: re-execute named blocks of an existing matrix run (frozen block
  rules, protocol section 9; DL-017) into a new run id; the source run is untouched.
- ``combine``: write the frozen-analysis input in which the repeated blocks replace
  the excluded ones (a result file that ``report`` accepts).
- ``test``: run the test suite with pytest.
Exit codes: 0 success, 2 refused or invalid input, 3 runtime unavailable,
4 the run ended under the memory-exhaustion stopping rule (reported as a failure;
the result file is written).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .config import ConfigError, ProtocolNotFrozen, load_config
from .items import ItemFormatError
from .runtime import BackendError, RuntimeUnavailable
from .schema import ResultValidationError

REPO = Path(__file__).resolve().parents[2]


def _execute(config_path: str, require_exploratory: bool, source: str | None = None,
             blocks: list[int] | None = None) -> int:
    from .runner import execute, execute_block_repeat

    try:
        cfg = load_config(config_path)
        if require_exploratory and cfg.mode != "exploratory":
            print("refused: smoke only accepts exploratory configs", file=sys.stderr)
            return 2
        if source is not None:
            src = Path(source)
            doc, path = execute_block_repeat(cfg, REPO, src if src.is_absolute() else REPO / src, blocks or [])
        else:
            doc, path = execute(cfg, REPO)
    except ProtocolNotFrozen as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    except (ConfigError, ItemFormatError, ResultValidationError, ValueError) as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2
    except RuntimeUnavailable as exc:
        print(f"runtime unavailable: {exc}", file=sys.stderr)
        return 3
    except BackendError as exc:
        print(f"backend error: {exc}", file=sys.stderr)
        return 3
    m = doc["manifest"]
    status = m.get("block_rules", {}).get("status")
    print(json.dumps({"run_id": doc["run_id"], "label": doc["label"], "result": str(path),
                      "requests": m["n_requests"], "failures": m["n_failures"],
                      "runtime_s": round(m["runtime_s"], 4), "simulated": doc["backend"]["simulated"],
                      "block_rules_status": status,
                      "exclusions": m.get("block_rules", {}).get("exclusions")}))
    return 4 if status == "failure" else 0


def _combine(source: str, repeat: str, out: str) -> int:
    from .runner import combine_repeat
    from .schema import export_result, import_result

    try:
        doc = combine_repeat(import_result(Path(source) / "result.json"), import_result(Path(repeat) / "result.json"))
        path = export_result(doc, Path(out) / "result.json")
    except (ResultValidationError, ValueError, OSError) as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2
    c = doc["manifest"]["combination"]
    print(json.dumps({"result": str(path), "requests": len(doc["records"]), "blocks": c["n_blocks"],
                      "status": c["status"], "blocks_missing": c["blocks_missing"]}))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="token-lab")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("smoke", help="exploratory smoke run")
    s.add_argument("--config", default="experiments/smoke-simulated.json")
    r = sub.add_parser("run", help="run a config (confirmatory requires a frozen protocol)")
    r.add_argument("--config", required=True)
    rp = sub.add_parser("report", help="build a report from a result file")
    rp.add_argument("--result", required=True)
    rp.add_argument("--out")
    rp.add_argument("--pdf", action="store_true")
    rb = sub.add_parser("repeat-blocks", help="repeat named blocks of an existing matrix run (new run id)")
    rb.add_argument("--config", required=True)
    rb.add_argument("--source", required=True, help="run folder of the source run, e.g. results/confirmatory/RUN-EXP-001-0001")
    rb.add_argument("--blocks", required=True, help="comma-separated 1-based block numbers in execution order")
    cb = sub.add_parser("combine", help="replace repeated blocks for the frozen analysis")
    cb.add_argument("--source", required=True)
    cb.add_argument("--repeat", required=True)
    cb.add_argument("--out", required=True)
    t = sub.add_parser("test", help="run the test suite")
    a, extra = ap.parse_known_args(argv)
    if extra and a.cmd != "test":
        ap.error(f"unrecognized arguments: {' '.join(extra)}")

    if a.cmd == "smoke":
        return _execute(a.config, require_exploratory=True)
    if a.cmd == "run":
        return _execute(a.config, require_exploratory=False)
    if a.cmd == "repeat-blocks":
        try:
            blocks = [int(x) for x in a.blocks.split(",") if x.strip()]
        except ValueError:
            print("invalid input: --blocks takes comma-separated integers", file=sys.stderr)
            return 2
        return _execute(a.config, require_exploratory=False, source=a.source, blocks=blocks)
    if a.cmd == "combine":
        return _combine(a.source, a.repeat, a.out)
    if a.cmd == "report":
        from .report import build_report

        try:
            info = build_report(a.result, a.out, a.pdf)
        except (ResultValidationError, OSError) as exc:
            print(f"invalid result: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(info))
        return 0 if (not a.pdf or info["pdf"]) else 2
    if a.cmd == "test":
        return subprocess.call([sys.executable, "-m", "pytest", *extra], cwd=REPO)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
