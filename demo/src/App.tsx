// SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
import { useEffect, useState } from "react";
import { ContrastChart, FrontierChart, LatencyStrip } from "./charts";
import { Energy } from "./Energy";
import { fmtEstimate, fmtInterval, loadResults, ResultsError, type Estimate, type Experiment, type Results } from "./results";
import { Sandbox } from "./Sandbox";

type State = { kind: "loading" } | { kind: "error"; message: string } | { kind: "ready"; results: Results };

const OUTCOME_TEXT: Record<Experiment["outcome"], string> = {
  failed: "failed, no result",
  null: "null result",
  positive: "result",
  "not run": "not run",
  exploratory: "exploratory",
};

function kindTag(kind: string) {
  if (kind.startsWith("exploratory")) return <span className="tag tag-exploratory">exploratory</span>;
  if (kind.includes("failed")) return <span className="tag tag-failed">no result</span>;
  return <span className="tag tag-measured">measured</span>;
}

export function App() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    loadResults()
      .then((results) => setState({ kind: "ready", results }))
      .catch((e: unknown) =>
        setState({ kind: "error", message: e instanceof ResultsError ? e.message : "results could not be loaded" }),
      );
  }, []);

  return (
    <>
      <a className="skip" href="#main">Skip to content</a>
      <header className="site">
        <div className="wrap">
          <p className="kicker">TOKEN · a preregistered measurement study on one laptop</p>
          <h1>How do local model configurations trade off quality, latency and resource use?</h1>
          <nav aria-label="Sections">
            <a href="#overview">Overview</a>
            <a href="#results">Results</a>
            <a href="#frontier">Frontier</a>
            <a href="#assumptions">Assumptions</a>
            <a href="#method">Method and limitations</a>
            <a href="#pending">Pending decisions</a>
            <a href="#energy">Modelled energy</a>
            <a href="#sandbox">Sandbox</a>
          </nav>
        </div>
      </header>
      <main id="main" className="wrap">
        {state.kind === "loading" && <p role="status">Loading the published results.</p>}
        {state.kind === "error" && (
          <div role="alert" className="panel error">
            <h2>Results unavailable</h2>
            <p>The published results file failed validation, so no numbers are shown.</p>
            <p><code>{state.message}</code></p>
          </div>
        )}
        {state.kind === "ready" && <Published r={state.results} />}
        <Sandbox results={state.kind === "ready" ? state.results : null} />
      </main>
      <footer className="site">
        <div className="wrap">
          <p>
            Runs offline after the first load. No data about visitors is collected, stored or sent anywhere, and the page
            contacts no model runtime or other service.
          </p>
          <p>
            Author line: [OWNER PLACEHOLDER: author line]. Repository and demo URL: [OWNER PLACEHOLDER: repository URL, not
            published]. Licence: TOKEN Source-Available Non-Commercial Research License v1.0.
          </p>
        </div>
      </footer>
    </>
  );
}

function EstimateTable({ e }: { e: Experiment }) {
  return (
    <div id={`table-${e.id}`} className="table-scroll" role="region" aria-label={`${e.id} estimates`} tabIndex={0}>
      <table className="stack">
        <thead>
          <tr>
            <th scope="col">Quantity</th>
            <th scope="col">Label</th>
            <th scope="col">Estimate</th>
            <th scope="col">Uncertainty or spread</th>
          </tr>
        </thead>
        <tbody>
          {e.estimates.map((x) => (
            <tr key={x.label}>
              <th scope="row">{x.label}</th>
              <td data-label="Label">{kindTag(x.kind)}</td>
              <td data-label="Estimate" className="num">{fmtEstimate(x)} <span className="meta">{x.unit}</span></td>
              <td data-label="Uncertainty or spread">
                {x.ci_low !== null ? <span className="num">{fmtInterval(x)}</span> : null}{" "}
                <span className="meta">{x.interval_kind ?? ""}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Published({ r }: { r: Results }) {
  const exp003 = r.experiments.find((e) => e.id === "EXP-003");
  const contrast = exp003
    ? exp003.estimates.filter((x) => x.ci_level !== null && x.unit === "percentage points")
    : [];
  const contrastRows = contrast.map((e: Estimate) => ({
    name: e.label.startsWith("Lenient") ? "Lenient extraction (S2)" : "Strict extraction (primary)",
    e,
  }));
  return (
    <>
      <section id="overview" aria-labelledby="h-overview">
        <h2 id="h-overview">Overview</h2>
        <p className="status-label"><strong>Status:</strong> {r.status_label}</p>
        <p>
          Three experiments were preregistered and frozen by the owner before any model output was seen. Two failed before
          sending any request, because the installed runtime (Ollama 0.9.6) cannot render the chat template of one required
          model. The third compared Llama 3.1 8B at Q8_0 and Q4_K_M on 300 ARC-Challenge items and detected no accuracy
          difference; it is not evidence of equivalence.
        </p>
        <ul className="legend" aria-label="Labels used on this page">
          <li><span className="tag tag-measured">measured</span> committed confirmatory results of RUN-EXP-003-0001</li>
          <li><span className="tag tag-exploratory">exploratory</span> re-analysis of committed records (JRN-0009), no confirmatory weight</li>
          <li><span className="tag tag-failed">no result</span> a registered experiment that produced no data</li>
          <li><span className="tag tag-modelled">modelled, illustrative</span> computed from a value you enter, not a measurement</li>
          <li><span className="tag tag-sandbox">sandbox, illustrative</span> produced in your browser, not a research result</li>
        </ul>
        <p className="pending-banner">
          <strong>Pending owner decisions:</strong> the next step for EXP-001 and EXP-002, and the reading of the frozen
          latency-ratio interval. Both are listed under <a href="#pending">Pending decisions</a> with every reading; this
          page chooses none.
        </p>
      </section>

      <section id="results" aria-labelledby="h-results">
        <h2 id="h-results">Published results</h2>
        <p className="note">
          These numbers come from the committed results (export revision <code>{r.code_revision.slice(0, 7)}</code>; the
          run used code revision <code>{r.run_code_revision.slice(0, 7)}</code>) and are printed exactly as in the
          manuscript. They are separate from the modelled-energy panel and the sandbox below. Failed experiments are shown
          with the same weight as the completed one.
        </p>
        <div className="exp-grid">
          {r.experiments.map((e) => (
            <article key={e.id} className={`panel outcome-${e.outcome.replace(" ", "-")}`} aria-labelledby={`h-${e.id}`}>
              <h3 id={`h-${e.id}`}>
                {e.id}: {e.title}
              </h3>
              <p>
                <span className="badge">{OUTCOME_TEXT[e.outcome]}</span> <span className="meta">{e.status}</span>
              </p>
              <p><strong>Verdict under the frozen rule:</strong> {e.verdict}</p>
              {e.id !== "EXP-003" &&
                e.estimates.map((x) => (
                  <p key={x.label} className="failed-line">
                    {kindTag(x.kind)} {x.label}: <strong>{fmtEstimate(x)}</strong>{" "}
                    <span className="meta">({x.interval_kind ?? "no interval"})</span>
                  </p>
                ))}
              {e.notes.map((n, i) => (
                <p key={i} className={n.startsWith("Pending owner decision") ? "pending-note" : "note"}>{n}</p>
              ))}
              <p className="meta">
                Report: <code>{e.report_path}</code>
                {e.claim_ids.length > 0 && <> · Claims: {e.claim_ids.join(", ")}</>}
              </p>
            </article>
          ))}
        </div>
        {exp003 && (
          <>
            <h3>EXP-003 in detail</h3>
            {contrastRows.length > 0 && <ContrastChart rows={contrastRows} />}
            <EstimateTable e={exp003} />
          </>
        )}
      </section>

      <section id="frontier" aria-labelledby="h-frontier">
        <h2 id="h-frontier">Resource frontier explorer</h2>
        <p className="note">
          Choose the cost on the horizontal axis. Only the two EXP-003 arms were measured; the three EXP-001 arms are listed
          without a point because their experiment produced no data. {r.frontier.note}
        </p>
        <FrontierChart arms={r.frontier.arms} notMeasured={r.frontier.not_measured} />
        <LatencyStrip items={r.items} arms={r.frontier.arms} />
      </section>

      <section id="assumptions" aria-labelledby="h-assumptions">
        <h2 id="h-assumptions">Assumptions and settings</h2>
        <dl className="assumptions">
          {r.assumptions.map((a) => (
            <div key={a.name}>
              <dt>{a.name}</dt>
              <dd>
                {a.value} <span className="meta">({a.source})</span>
              </dd>
            </div>
          ))}
        </dl>
      </section>

      <section id="method" aria-labelledby="h-method">
        <h2 id="h-method">Method and limitations</h2>
        <p>
          Each of 300 ARC-Challenge test items was asked five times per arm with greedy decoding; accuracy is the per-item
          mean over repetitions, and the paired difference is tested with a bootstrap over items (10,000 resamples, seed 7)
          and the exact McNemar test. Timing is client wall-clock on the streamed response; memory is the runtime's own
          report. The full method is in <code>research/paper/manuscript.md</code>, section 4.
        </p>
        <h3>Sensitivity analyses and exploratory checks</h3>
        <div id="table-sensitivity" className="table-scroll" role="region" aria-label="Sensitivity analyses" tabIndex={0}>
          <table className="stack">
            <thead>
              <tr>
                <th scope="col">Check</th>
                <th scope="col">Status</th>
                <th scope="col">Result (as in the manuscript, Table 4)</th>
              </tr>
            </thead>
            <tbody>
              {r.sensitivity.map((s) => (
                <tr key={s.check}>
                  <th scope="row">{s.check}</th>
                  <td data-label="Status">{s.status}</td>
                  <td data-label="Result">{s.result}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <h3>Limitations</h3>
        <ul>
          {r.limitations.map((l, i) => (
            <li key={i}>{l}</li>
          ))}
        </ul>
        <details>
          <summary>Source files and hashes</summary>
          <ul className="meta">
            {r.sources.map((s) => (
              <li key={s.path}>
                <code>{s.path}</code> <code>{s.sha256.slice(0, 12)}</code>
              </li>
            ))}
          </ul>
        </details>
      </section>

      <section id="pending" aria-labelledby="h-pending">
        <h2 id="h-pending">Pending owner decisions</h2>
        <p className="note">Each item below is a pending owner decision. Every reading is shown; none is chosen here.</p>
        {r.pending_owner_decisions.map((p) => (
          <article key={p.id} className="panel pending" aria-labelledby={`h-${p.id}`}>
            <h3 id={`h-${p.id}`}>{p.title}</h3>
            <p><span className="badge">{p.status}</span> <span className="meta">{p.source}</span></p>
            <ul>
              {p.readings.map((x) => (
                <li key={x}>{x}</li>
              ))}
            </ul>
          </article>
        ))}
      </section>

      <Energy arms={r.frontier.arms} />
    </>
  );
}
