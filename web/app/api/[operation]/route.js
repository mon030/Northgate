import { data } from "../../../lib/data";
export const dynamic = "force-dynamic";
const read = new Set([
  "dashboard",
  "history",
  "run",
  "economics",
  "alerts",
  "quality",
]);
const write = new Set(["prepare", "review", "timing"]);
async function execute(operation, params) {
  try {
    return Response.json(await data(operation, params), {
      headers: { "Cache-Control": "no-store" },
    });
  } catch (e) {
    return Response.json({ error: e.message }, { status: 400 });
  }
}
export async function GET(req, { params }) {
  const { operation } = await params;
  if (!read.has(operation)) return new Response(null, { status: 404 });
  return execute(operation, Object.fromEntries(new URL(req.url).searchParams));
}
export async function POST(req, { params }) {
  const { operation } = await params;
  if (!write.has(operation)) return new Response(null, { status: 404 });
  const origin = req.headers.get("origin");
  if (
    !origin ||
    new URL(origin).host !== req.headers.get("host") ||
    !req.headers.get("content-type")?.startsWith("application/json")
  )
    return new Response(null, { status: 403 });
  try {
    return execute(operation, await req.json());
  } catch {
    return Response.json({ error: "Invalid request." }, { status: 400 });
  }
}
