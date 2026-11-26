"use client";
import { useState } from "react";
import { FileSearch, ShieldCheck } from "lucide-react";
const requests = [
  "Prepare a case summary",
  "Review account activity",
  "Check linked disputes",
];
export default function Workspace({ initial, initialAlert }) {
  const [run, setRun] = useState(initial),
    [alert, setAlert] = useState(initial?.alert || initialAlert),
    [intent, setIntent] = useState(initial?.request || requests[0]),
    [mode, setMode] = useState("Local model");
  const [body, setBody] = useState(
      initial?.decision?.final_text || initial?.draft || "",
    ),
    [note, setNote] = useState(""),
    [who, setWho] = useState(""),
    [secret, setSecret] = useState(""),
    [consent, setConsent] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function action(op, payload) {
    setBusy(true);
    setError("");
    try {
      const res = await fetch("/api/" + op, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const value = await res.json();
      if (!res.ok) throw new Error(value.error || "Request failed");
      setRun(value);
      setBody(value.decision?.final_text || value.draft);
      if (op === "prepare") {
        setNote("");
        setWho("");
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  const pending = run?.status === "Pending";
  return (
    <>
      <section className="panel">
        <h2>Gather evidence</h2>
        <form
          className="controls"
          onSubmit={(e) => {
            e.preventDefault();
            setRun(null);
            action("prepare", {
              alert,
              request: intent,
              mode,
              apiKey: mode === "Gemini API" ? secret : undefined,
              cloudConsent: consent,
            });
          }}
        >
          <label>
            Alert ID
            <input
              className="input"
              value={alert}
              onChange={(e) => setAlert(e.target.value)}
              required
              pattern="[aA][lL][0-9]{6}"
            />
          </label>
          <label>
            Analyst request
            <select
              className="select"
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
            >
              {requests.map((x) => (
                <option key={x}>{x}</option>
              ))}
            </select>
          </label>
          <label>
            Drafting engine
            <select
              className="select"
              value={mode}
              onChange={(e) => setMode(e.target.value)}
            >
              {["Local model", "Gemini API", "Rules only"].map((x) => (
                <option key={x}>{x}</option>
              ))}
            </select>
          </label>
          {mode === "Gemini API" && (
            <div className="cloud">
              <label>
                Free-tier API key (or configured environment key)
                <input
                  type="password"
                  className="input"
                  value={secret}
                  onChange={(e) => setSecret(e.target.value)}
                  autoComplete="off"
                />
              </label>
              <label>
                <input
                  type="checkbox"
                  required
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                />{" "}
                Send the permitted review sentences, which can disclose a
                missing note or channel conflict, to the Google Gemini API for
                this draft. Source notes and identifiers stay local.
              </label>
            </div>
          )}
          <button disabled={busy} className="btn btn-primary">
            {busy ? "Working…" : "Prepare draft"}
          </button>
        </form>
      </section>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {run ? (
        <section className="panel">
          <div className="section-head">
            <div>
              <p className="kicker">
                {run.alert} · Run {run.id}
              </p>
              <h2>Case note</h2>
            </div>
            <span className="pill">{run.status}</span>
          </div>
          <label className="sr-only" htmlFor="draft">
            Case note for review
          </label>
          <textarea
            id="draft"
            className="textarea draft"
            value={body}
            readOnly={!pending}
            onChange={(e) => setBody(e.target.value)}
          />
          <details>
            <summary>Tool trace and token usage</summary>
            <ol>
              {run.trace.map((x, i) => (
                <li key={i}>{x}</li>
              ))}
            </ol>
            <p>
              {run.usage.model || run.usage.provider} ·{" "}
              {run.usage.input ?? "Unknown"} input /{" "}
              {run.usage.output ?? "unknown"} output tokens ·{" "}
              {run.elapsed.toFixed(2)} seconds
            </p>
          </details>
          {pending && (
            <form
              className="controls"
              onSubmit={(e) => {
                e.preventDefault();
                const decision = e.nativeEvent.submitter?.value;
                action("review", {
                  id: run.id,
                  decision,
                  reviewer: who,
                  comment: note,
                  text: body,
                });
              }}
            >
              <label>
                Reviewer initials
                <input
                  className="input"
                  required
                  maxLength={40}
                  value={who}
                  onChange={(e) => setWho(e.target.value)}
                />
              </label>
              <label className="grow">
                Review comment
                <input
                  className="input"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                />
              </label>
              <button
                disabled={busy}
                className="btn btn-primary"
                value="Approved"
              >
                Approve note
              </button>
              <button
                disabled={busy}
                className="btn"
                value="Revision requested"
              >
                Request revision
              </button>
            </form>
          )}
          {run.decision && (
            <p>
              Reviewed by <b>{run.decision.reviewer}</b> ·{" "}
              {run.decision.comment || run.decision.decision}
            </p>
          )}
          {run.status === "Approved" && !run.timing && (
            <details>
              <summary>Record paired pilot timings</summary>
              <form
                className="controls"
                onSubmit={(e) => {
                  e.preventDefault();
                  const f = new FormData(e.currentTarget);
                  action("timing", {
                    id: run.id,
                    manual: f.get("manual"),
                    assisted: f.get("assisted"),
                  });
                }}
              >
                {[
                  ["manual", "Manual minutes on this alert"],
                  ["assisted", "Assisted minutes including review"],
                ].map(([key, label]) => (
                  <label key={key}>
                    {label}
                    <input
                      className="input"
                      name={key}
                      type="number"
                      min=".001"
                      step="any"
                      required
                    />
                  </label>
                ))}
                <button disabled={busy} className="btn">
                  Save timings
                </button>
              </form>
            </details>
          )}
          {run.timing && (
            <p>
              Paired timing saved · {run.timing.manual} manual minutes /{" "}
              {run.timing.assisted} assisted minutes
            </p>
          )}
        </section>
      ) : (
        <section className="panel empty">
          <FileSearch size={35} />
          <h2>Evidence and draft</h2>
          <p>
            Prepare an alert to see the source records, evidence limits and
            proposed next step.
          </p>
          <span className="subline">
            <ShieldCheck size={16} /> Analyst approval required
          </span>
        </section>
      )}
    </>
  );
}
