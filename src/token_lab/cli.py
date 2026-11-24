# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Command line: ``token-lab {smoke,run,report,test}``.

- ``smoke``: run an exploratory config (refuses any confirmatory config).
- ``run``: run a config; refuses a confirmatory config while its protocol is not frozen.
- ``report``: build tables, figure and optional PDF from a result file.
- ``test``: run the test suite with pytest.
Exit codes: 0 success, 2 refused or invalid input, 3 runtime unavailable.
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


def _execute(config_path: str, require_exploratory: bool) -> int:
    from .runner import execute

    try:
        cfg = load_config(config_path)
        if require_exploratory and cfg.mode != "exploratory":
            print("refused: smoke only accepts exploratory configs", file=sys.stderr)
            return 2
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
    print(json.dumps({"run_id": doc["run_id"], "label": doc["label"], "result": str(path),
                      "requests": m["n_requests"], "failures": m["n_failures"],
                      "runtime_s": round(m["runtime_s"], 4), "simulated": doc["backend"]["simulated"]}))
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
    t = sub.add_parser("test", help="run the test suite")
    a, extra = ap.parse_known_args(argv)
    if extra and a.cmd != "test":
        ap.error(f"unrecognized arguments: {' '.join(extra)}")

    if a.cmd == "smoke":
        return _execute(a.config, require_exploratory=True)
    if a.cmd == "run":
        return _execute(a.config, require_exploratory=False)
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
