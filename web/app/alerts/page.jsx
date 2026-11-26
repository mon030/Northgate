import Link from "next/link";
import { data } from "../../lib/data";
export const dynamic = "force-dynamic";
export default async function Alerts({ searchParams }) {
  const p = await searchParams,
    q = p.q || "",
    kind = p.kind || "All";
  const d = await data("alerts", { q, kind, page: p.page || 1 });
  const link = (page) => "/alerts?" + new URLSearchParams({ q, kind, page });
  return (
    <>
      <header>
        <div>
          <p className="kicker">Case selection</p>
          <h1>Browse alerts</h1>
        </div>
      </header>
      <form action="/alerts" className="panel filters">
        <label>
          Alert, transaction or rule
          <input
            className="input"
            type="search"
            name="q"
            defaultValue={q}
            placeholder="e.g. AL000071 or R07"
          />
        </label>
        <label>
          Evidence
          <select className="select" name="kind" defaultValue={kind}>
            {d.kinds.map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </label>
        <button className="btn btn-primary">Find alerts</button>
        <Link href="/alerts" className="textlink">
          Reset
        </Link>
      </form>
      <section className="panel">
        <div className="section-head">
          <h2>{d.total.toLocaleString()} matching alerts</h2>
          <small>
            Page {d.page} of {d.pages}
          </small>
        </div>
        <p className="caption">Select an alert ID to prepare its case.</p>
        <div className="scroll">
          <table className="table">
            <thead>
              <tr>
                {[
                  "Alert ID",
                  "Alert date",
                  "Rule",
                  "Transaction",
                  "Channel",
                  "Timestamp",
                  "Note",
                ].map((x) => (
                  <th key={x}>{x}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {d.items.map((r) => (
                <tr key={r.alert_id}>
                  <th>
                    <Link
                      className="textlink"
                      href={"/cases?alert=" + r.alert_id}
                    >
                      {r.alert_id}
                    </Link>
                  </th>
                  <td>{r.alert_dt}</td>
                  <td>{r.rule_id}</td>
                  <td>{r.txn_id}</td>
                  <td>{r.channel}</td>
                  <td>{r.ts_convention}</td>
                  <td>{r.has_note ? "Supplied" : "Missing"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!d.total && (
          <p>No matching alerts. Try a shorter ID or reset the filter.</p>
        )}
        <div className="controls">
          {d.page > 1 && (
            <Link className="btn" href={link(d.page - 1)}>
              Previous page
            </Link>
          )}
          {d.page < d.pages && (
            <Link className="btn" href={link(d.page + 1)}>
              Next page
            </Link>
          )}
        </div>
      </section>
    </>
  );
}
