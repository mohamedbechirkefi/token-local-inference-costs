// SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
// Modelled energy from a power value the visitor enters. Nothing is measured and the
// page supplies no default power: the frozen protocol states no power range (S4 not run).
import { useState } from "react";
import type { FrontierArm } from "./results";

function sig3(x: number): string {
  return Number(x.toPrecision(3)).toLocaleString("en-US");
}

export function Energy({ arms }: { arms: FrontierArm[] }) {
  const [raw, setRaw] = useState("");
  const watts = Number(raw);
  const valid = raw.trim() !== "" && Number.isFinite(watts) && watts > 0 && watts <= 500;
  return (
    <section id="energy" aria-labelledby="h-energy" className="modelled">
      <h2 id="h-energy">
        Modelled energy from your assumption <span className="tag tag-modelled">modelled, illustrative</span>
      </h2>
      <p className="note">
        <strong>Illustrative, not a measurement.</strong> No energy was measured in this study, and the frozen protocol
        states no power range, so the sensitivity analysis S4 was not run and no energy figure is a result. This panel
        multiplies the measured median per-item latency by a whole-machine power draw that you enter. The page proposes no
        value. The output is a hypothetical calculation and is never shown among the published results.
      </p>
      <div className="controls">
        <label>
          Assumed power draw (W, 1 to 500){" "}
          <input id="energy-watts" type="number" inputMode="decimal" min={1} max={500} value={raw} placeholder="enter a value"
            onChange={(e) => setRaw(e.target.value)} />
        </label>
      </div>
      <div aria-live="polite">
        {!valid && <p className="meta">Enter a power between 1 and 500 W to see a modelled value.</p>}
        {valid && (
          <ul className="modelled-out">
            {arms.map((a) => {
              const joules = (a.latency_ms / 1000) * watts;
              return (
                <li key={a.arm}>
                  {a.quantization}: about {sig3(joules)} J per two-token answer, or {sig3((joules * 1000) / 3600)} Wh per 1,000
                  answers (modelled: {a.latency_display} ms measured median latency times your {sig3(watts)} W).
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}
