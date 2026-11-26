import Link from "next/link";
import { data } from "../../lib/data";
export const dynamic = "force-dynamic";
export default async function History() {
  const rows = await data("history");
  return (
    <>
      <header>
        <div>
          <p className="kicker">Analyst workspace</p>
          <h1>Review history</h1>
        </div>
      </header>
      <section className="panel">
        <h2>Recent runs</h2>
        <p className="caption">
          Open a run to view its evidence, trace and reviewer decision.
        </p>
        <div className="scroll">
          <table className="table">
            <thead>
              <tr>
                <th>Run</th>
                <th>Alert</th>
                <th>Created (UTC)</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td>
                    <Link className="textlink" href={"/cases?run=" + r.id}>
                      Open #{r.id}
                    </Link>
                  </td>
                  <td>{r.alert}</td>
                  <td>{r.created}</td>
                  <td>{r.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!rows.length && <p>No cases prepared yet.</p>}
        </div>
      </section>
    </>
  );
}
