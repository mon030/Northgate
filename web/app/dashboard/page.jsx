import { data } from "../../lib/data";
import Link from "next/link";
import Chart from "./chart";
import {
  Clock3,
  Files,
  NotebookPen,
  Timer,
  CircleCheck,
  Flag,
  ArrowUpRight,
  CalendarDays,
} from "lucide-react";
export const dynamic = "force-dynamic";
const samples = [
  ["AL000029", "Conflicting evidence", "A wire note on a card transaction"],
  ["AL000002", "Missing note", "Review the available evidence"],
  ["AL000001", "Local timestamp", "Account window needs a timezone"],
];
export default async function Dashboard({ searchParams }) {
  const q = await searchParams;
  const d = await data("dashboard", {
    month: q.month || "All",
    rule: q.rule || "All",
  });
  const t = d.totals;
  const stats = [
    ["Alerts", t.alert_count.toLocaleString(), "distinct alert IDs", Files],
    ["Analyst hours", t.total_analyst_hours ?? "—", "recorded effort", Clock3],
    [
      "False positive",
      t.false_positive_pct == null ? "—" : t.false_positive_pct + "%",
      "historical disposition",
      Flag,
    ],
    [
      "Minutes per alert",
      t.minutes_per_alert ?? "—",
      "mean recorded effort",
      Timer,
    ],
    [
      "Note coverage",
      t.note_coverage_pct == null ? "—" : t.note_coverage_pct + "%",
      "alerts with a supplied note",
      NotebookPen,
    ],
    [
      "Pilot time saved",
      t.observed_minutes_saved == null
        ? "Pending"
        : t.observed_minutes_saved + " min",
      t.pilot_pairs + " paired observations",
      CircleCheck,
    ],
  ];
  return (
    <>
      <header>
        <div>
          <p className="kicker">Fraud operations</p>
          <h1>Workload overview</h1>
        </div>
        <span className="period">
          <CalendarDays size={16} /> Jan – Jun 2026
        </span>
      </header>
      <form className="filters panel" action="/dashboard">
        <label>
          Alert month
          <select name="month" defaultValue={d.month} className="select">
            {["All", ...d.months].map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </label>
        <label>
          Rule code
          <select name="rule" defaultValue={d.rule} className="select">
            {["All", ...d.rules].map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </label>
        <button className="btn btn-neutral">Apply filters</button>
      </form>
      <section className="metrics">
        {stats.map(([label, value, unit, Icon]) => (
          <div className="metric" key={label}>
            <div className="metric-label">
              <Icon size={16} />
              {label}
            </div>
            <strong>{value}</strong>
            <small>{unit}</small>
          </div>
        ))}
      </section>
      <div className="columns">
        <section className="panel">
          <h2>Analyst hours by month</h2>
          <p className="caption">
            Recorded review time across the selected alerts
          </p>
          <Chart rows={d.by_month} />
        </section>
        <section className="panel">
          <h2>Cases for the demo</h2>
          <p className="caption">Open an alert to inspect its evidence</p>
          {samples.map(([id, title, info]) => (
            <Link href={"/cases?alert=" + id} key={id} className="case-link">
              <div>
                <small>{id}</small>
                <b>{title}</b>
                <span>{info}</span>
              </div>
              <ArrowUpRight size={18} />
            </Link>
          ))}
        </section>
      </div>
      <section className="panel">
        <h2>Workload by rule</h2>
        <p className="caption">Ranked by total recorded minutes</p>
        <div className="scroll">
          <table className="table">
            <thead>
              <tr>
                {[
                  "Rule",
                  "Alerts",
                  "Analyst hours",
                  "Min / alert",
                  "False positive",
                  "Note coverage",
                ].map((x) => (
                  <th key={x}>{x}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {d.by_rule.map((r) => (
                <tr key={r.rule_id}>
                  <th>{r.rule_id}</th>
                  <td>{r.alert_count}</td>
                  <td>{r.total_analyst_hours}</td>
                  <td>{r.minutes_per_alert}</td>
                  <td>{r.false_positive_pct}%</td>
                  <td>{r.note_coverage_pct}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
