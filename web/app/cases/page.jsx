import { data } from "../../lib/data";
import Workspace from "./workspace";
import Link from "next/link";
export const dynamic = "force-dynamic";
export default async function Cases({ searchParams }) {
  const q = await searchParams;
  const run = q.run ? await data("run", { id: q.run }) : null;
  return (
    <>
      <header>
        <div>
          <p className="kicker">Analyst workspace</p>
          <h1>Case preparation</h1>
        </div>
        <Link className="btn" href="/alerts">
          Browse all alerts
        </Link>
      </header>
      <Workspace
        key={q.run || q.alert || "new"}
        initial={run}
        hosted={Boolean(process.env.VERCEL)}
        initialAlert={q.alert || "AL000029"}
      />
    </>
  );
}
