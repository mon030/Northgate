import { BlobPreconditionFailedError, get, put } from "@vercel/blob";

const needsHistory = new Set(["dashboard", "history", "run", "prepare", "review", "timing"]);

export async function hostedData(op, args) {
  const reviewFile = process.env.VERCEL_ENV === "production"
    ? "reviews/v1.sqlite.gz"
    : `preview/${process.env.VERCEL_URL || "local"}/reviews.sqlite.gz`;
  const url = new URL("/operate", process.env.NORTHGATE_EVIDENCE_URL);
  const previous = needsHistory.has(op)
    ? await get(reviewFile, { access: "private", useCache: false })
    : null;
  const state = previous
    ? Buffer.from(await new Response(previous.stream).arrayBuffer()).toString("base64")
    : undefined;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ op, args, state }),
    cache: "no-store",
  });
  if (!response.ok) throw new Error("The evidence service is unavailable.");
  const result = await response.json();
  if (result.state) {
    try {
      await put(reviewFile, Buffer.from(result.state, "base64"), {
        access: "private",
        addRandomSuffix: false,
        allowOverwrite: Boolean(previous),
        ifMatch: previous?.blob.etag,
        contentType: "application/gzip",
      });
    } catch (error) {
      if (error instanceof BlobPreconditionFailedError) {
        throw new Error("Another reviewer saved a change. Reload the case before trying again.");
      }
      throw new Error("The review log could not be saved. Reload the case before trying again.");
    }
  }
  if (result.error) throw new Error(result.error);
  return result.data;
}
