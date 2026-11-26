import { data } from "../../lib/data";
export const dynamic = "force-dynamic";
const usd = (x) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(x);
export default async function Business() {
  const rows = await data("economics"),
    base = rows.find((r) => r.scenario === "Base");
  return (
    <>
      <header>
        <div>
          <p className="kicker">Funding decision</p>
          <h1>Pilot business case</h1>
        </div>
      </header>
      <section className="panel">
        <h2>Fund a measured pilot</h2>
        <p className="caption">
          The base case assumes 75% adoption and seven minutes released per
          assisted alert. Validate these assumptions with paired analyst
          timings.
        </p>
        <div className="metrics mini">
          {[
            ["Build and training", usd(base.initial_build_training_usd)],
            ["Annual running cost", usd(base.annual_total_run_usd)],
            ["Three-year net capacity", usd(base.year3_cumulative_usd)],
          ].map(([l, v]) => (
            <div key={l} className="metric">
              <small>{l}</small>
              <strong>{v}</strong>
            </div>
          ))}
        </div>
      </section>
      <section className="panel">
        <h2>Cost and sensitivity</h2>
        <p className="caption">
          Annualized volume is twice the 1,613 alerts in the six-month extract.
          Each scenario holds volume and adoption constant for three years.
        </p>
        <div className="scroll">
          <table className="table">
            <thead>
              <tr>
                <th>USD unless stated</th>
                {rows.map((r) => (
                  <th key={r.scenario}>{r.scenario}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                ["Annual adoption", "adoption", "pct"],
                ["Manual minutes per case", "manual_min", "n"],
                [
                  "Assisted minutes incl. review",
                  "assisted_including_review_min",
                  "n",
                ],
                ["Build and training", "initial_build_training_usd"],
                ["Annual analyst review", "annual_review_usd"],
                ["Annual support and QA", "annual_support_usd"],
                ["Annual compute", "annual_compute_usd"],
                ["Annual local API fees", "annual_local_api_usd"],
                ["Annual gross capacity value", "annual_manual_capacity_usd"],
                ["Year 1 cumulative net", "year1_cumulative_usd"],
                ["Year 2 cumulative net", "year2_cumulative_usd"],
                ["Year 3 cumulative net", "year3_cumulative_usd"],
                ["Three-year economic ROI", "three_year_economic_roi", "pct"],
                ["Payback (months)", "payback_months", "mo"],
              ].map(([l, k, fmt]) => (
                <tr key={k}>
                  <th>{l}</th>
                  {rows.map((r) => (
                    <td key={r.scenario}>
                      {fmt === "pct"
                        ? (r[k] * 100).toFixed(1) + "%"
                        : fmt === "mo"
                          ? (r[k]?.toFixed(1) ?? "Unreached")
                          : fmt === "n"
                            ? r[k]
                            : usd(r[k])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="panel">
        <h2>Pilot decision gate</h2>
        <p>
          At base volume and adoption, the three-year break-even point is{" "}
          <b>{base.break_even_minutes_three_year.toFixed(2)} minutes</b> saved
          per assisted alert. Count evidence lookup, review and corrections in
          both workflows. Capacity becomes cash savings only when spending
          actually falls.
        </p>
      </section>
    </>
  );
}
