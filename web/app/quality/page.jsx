import { data } from "../../lib/data";
export const dynamic = "force-dynamic";
export default async function Quality() {
  const d = await data("quality");
  return (
    <>
      <header>
        <div>
          <p className="kicker">Data stewardship</p>
          <h1>Quarantine and recovery</h1>
        </div>
      </header>
      <section className="panel">
        <h2>Records returned to processing</h2>
        <p className="caption">
          Each intake key is matched to a correction and validated against
          Silver before Gold is published. Some transactions require two
          corrections.
        </p>
        <div className="scroll">
          <table className="table">
            <thead>
              <tr>
                <th>Intake reason</th>
                <th>Issue records</th>
                <th>Outcome</th>
              </tr>
            </thead>
            <tbody>
              {d.summary.map((r) => (
                <tr key={r.issue}>
                  <th>{r.issue}</th>
                  <td>{r.records.toLocaleString()}</td>
                  <td>{r.outcome}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="panel">
        <h2>Trace a source record</h2>
        {d.examples.map((r) => (
          <details key={r.source_key + r.issue}>
            <summary>
              {r.source_key} · {r.issue}
            </summary>
            <p>
              <b>Source value</b> {r.raw_value}
            </p>
            <p>
              <b>Processed value</b> {r.after_value}
            </p>
            <p>{r.rule}</p>
          </details>
        ))}
      </section>
    </>
  );
}
