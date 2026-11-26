# Northgate fraud operations

Northgate is a student capstone using fictional bank data. Porter’s workload dashboard and Tommy’s case-preparation agent share the same alert records. An analyst can open an alert, inspect the agent’s cited evidence, edit a draft and record a decision. The business case asks whether the time saved after human review justifies the build and operating costs.

## Porter's dashboard handoff

Porter owns Component 4, the dashboard and its source checks. Start with the [live workload dashboard](https://northgate-nu.vercel.app/dashboard). The dashboard works in a browser without setup or an API key.

1. **Verify the figures you plan to present.** These five measures were checked against the original alert and analyst-note files on November 26. The sixth measure, minutes saved per case, requires paired human timings. The app showed zero pairs and displayed **Pending**. Keep that label until the team measures a case.

   | Rule filter, all months | Alerts | Analyst hours | Minutes per alert | Recorded false positives | Alerts with notes |
   | --- | ---: | ---: | ---: | ---: | ---: |
   | All | 1,613 | 885.1 | 32.9 | 90.3% | 26.3% |
   | R07 | 829 | 414.7 | 30.0 | 94.5% | 25.2% |
   | R09 | 146 | 152.4 | 62.6 | 56.2% | 27.4% |

   The all-rules control is 53,108 recorded minutes, 1,457 alerts marked false positive and 425 alerts with notes. Round after aggregation. [Source checks by month and rule](evidence/dashboard_checks.csv)
2. **Explain the difference between volume and effort.** R07 accounts for about half the alerts. R09 has fewer alerts and takes more than twice as long per alert as R07. Use the dashboard filters live, then hand the demo to Tommy with [AL000029, an R09 case](https://northgate-nu.vercel.app/cases?alert=AL000029). The recorded minutes cover historical case work. Measuring how much of that work the agent saves requires the pilot.
3. **Coordinate with Tommy and the business-case lead.** Porter verifies each figure used on the team’s slides. Tommy demonstrates the conflicting evidence and reviewer decision. Use the [business case](https://northgate-nu.vercel.app/business) for build, training, review and support costs and the [data-quality page](https://northgate-nu.vercel.app/quality) for quarantine corrections.

**Working agreement for Porter and coding assistants.** Start with [the dashboard page](web/app/dashboard/page.jsx) and [its chart](web/app/dashboard/chart.jsx) for display changes. For a metric change, inspect `dashboard()` in [web_service.py](web_service.py) and `METRICS` in [build.py](build.py). Preserve one row per alert and count disputes by dispute ID. Check both the whole extract and a filtered slice against [dashboard controls](evidence/dashboard_checks.csv). See [web development instructions](web/AGENTS.md) before editing Next.js code. Each local copy has its own review history. Git excludes database files, credentials, installed dependencies and downloaded model binaries.

## Run the app from a clone

Install Python 3.11+ and Node.js 22.12+ with npm. From the repository root, run the following command or double-click **Open Northgate.cmd** on Windows.

```powershell
python launch.py
```

The launcher rebuilds the warehouse from the included teaching data on first use, installs the locked web dependencies, and opens the [dashboard](http://127.0.0.1:3301/dashboard). The first npm install needs internet. On a fresh clone, select **Rules only** to try a case immediately. For the offline language-model demo on Windows x64, run `python setup_model.py` once with internet access, then select **Local model**. The installer verifies the downloaded weights and engine archive.

For **AL000029**, choose **Prepare draft** and expand **Tool trace and token usage**. Compare transaction T0000426 with the note on line 11. Use your initials and record a revision request if the evidence is insufficient. The original proposal and the reviewer’s decision are kept in the local review log.

## Configure the agent prompt and Gemini

For this checkout, edit `web/.env.local`. On a fresh clone, copy [the environment template](web/.env.example) to that path first. Set the drafting instruction, for example:

```dotenv
NORTHGATE_AGENT_PROMPT="Prioritize conflicting evidence, then choose the follow-up that best addresses the missing information."
```

Restart the local web server and prepare a **new** draft using **Local model** or **Gemini API**. A blank value restores `INSTRUCTION` in [models.py](models.py). Each run saves its effective prompt and version under `usage` in the review log. Keep credentials and personal data out of the prompt. Direct Python and desktop launches read these variables from the shell environment. Next.js loads `web/.env.local` and passes the settings to the Python service.

The prompt guides the choice among evidence-supported lead sentences and follow-ups. Code validates both choices, supplies amounts and citations from the data, and requires a named reviewer for the decision. **Rules only** always chooses the first allowed options. Changing the prompt applies to future model drafts.

| Server variable | Purpose |
| --- | --- |
| `NORTHGATE_AGENT_PROMPT` | Optional drafting instruction. |
| `GEMINI_API_KEY` | Private API credential for the Gemini engine. Keep it in the ignored local file or the hosting platform’s secret store. |
| `GEMINI_MODEL` | Optional Gemini API model ID that supports structured output and is available to your project. |

## Hosted app on Vercel

The project builds from the repository root. The [service configuration](vercel.json) routes public traffic to the Next.js frontend and gives its server a private connection to the Python evidence service. The Python service rebuilds the read-only teaching warehouse from the six Bronze files on cold start. The frontend saves the compressed SQLite review log in a private Vercel Blob store. Conditional writes detect simultaneous changes. Reload the case if another reviewer saves first. The production log starts independently of each laptop and previews use separate paths.

The classroom URL is public. Use the supplied fictional alerts and reviewer initials suitable for the class. A visitor can prepare a draft, read the shared history, and record a decision. Select **Gemini API**, check the consent box and choose **Prepare draft**, or select **Rules only** for a zero-API exercise. The Windows offline model is available through the local launcher.

In **Vercel → northgate → Settings → Environment Variables**, change `NORTHGATE_AGENT_PROMPT` to edit the drafting instruction. Store `GEMINI_API_KEY` as a sensitive server variable and optionally set `GEMINI_MODEL`. Redeploy to apply changes. The private Blob connection supplies the storage credentials. [Vercel environment settings](https://vercel.com/docs/environment-variables/managing-environment-variables)

## What the assignment grades

**Agent Builder handoff.** Keep the tested prompt version `case-review-1.0` for the class demo. It sets the role, supplies the evidence-supported choices for the case, asks for a lead and follow-up, and requires JSON. The code checks each selection, adds source citations, and leaves the decision to a reviewer. The [prompt pack and AI log](evidence/Prompt%20pack%20and%20AI%20log.md) and [20 test outcomes](evidence/test_results.csv) document the broader evaluation.

**What Gemini actually produced.** In [hosted run 7](https://northgate-nu.vercel.app/cases?run=7), the model selected “The note describes a wire and the linked transaction records another channel.” It also selected “Reconcile the note with the transaction channel before accepting the case note.” Transaction T0000426 records a card transaction and analyst note line 11 mentions a wire. The saved run was Pending when verified. Gemini reported 111 input, 37 output and 200 thinking tokens, 348 total. An earlier provider failure withheld the draft, and a [separate Rules only run](https://northgate-nu.vercel.app/cases?run=2) recorded a revision request. No pilot time was entered for these QA checks.

**Tommy’s next step.** On a fresh alert, time your manual preparation and then the entire assisted workflow, including checking citations and making your own decision. Enter the pair only on a genuinely approved run. Write down one thing the agent caught or missed and what you did about it. Bring that observation to the seven-minute team rehearsal. For the live generative demo, select **Gemini API** in the engine menu and check consent before preparing the draft.

**Finding another case.** Open [Browse alerts](http://127.0.0.1:3301/alerts) to search all 1,613 alert IDs by alert, transaction, rule or evidence type. Try AL000002 for missing notes, AL000001 for local time, or AL000071 with the “Check linked disputes” request. Use [Data quality](http://127.0.0.1:3301/quality) to trace actual intake and reprocessing records.

**Materials for the live presentation.** The browser-based [team presentation](http://127.0.0.1:3301/pitch) has six slides with a timed speaker handoff and links to the live demo. The team creates its final presentation together. The local PDF exports include an offline deck, a funding brief covering all eight components and appendices, and a one-page architecture. Edit the deck content in web/app/pitch/slides.json. Run report.py with ReportLab and pypdf installed to regenerate the PDFs.

**QA evidence.** All 20 agent tests and 12 web checks passed. The web check performed one approval and one revision under the reviewer name QA demo. Neither created a human pilot observation. Run web_check.py only for a fresh QA exercise with the site running, since it adds labeled QA runs to review history.

The December 4 team deliverables are the seven-minute pitch with a live dashboard and agent demo, and the written case covering all eight components with appendices. The rubric splits the Part 2 evaluation evenly across business case, data and analytics, agent build, and communication. Tommy owns the working agent, approved tools, prompts, guardrails, at least ten tests with outcomes, and the demo. The attached funding brief and architecture are inputs to the team's final submission. The individual teammate feedback is due on the date announced in class.

| Component | Owner and evidence |
| --- | --- |
| 1 AI map | Samuel integrates rules for data and indicators, a policy-based agent planner, and constrained generative drafting. Supervised prediction needs independently verified fraud labels. |
| 2 Prompts and AI log | Actual runtime instruction in models.py. Full prompt, response and checks in evidence/example_run.json. Project log and checked stakeholder communication in the brief. Team members add their own interactions. |
| 3 Data platform | Romit reviews Architecture.pdf, build.py, northgate.db, evidence/quality_log.csv and evidence/layer_counts.csv. Each exception is keyed to Bronze in quarantine_history. |
| 4 Dashboard | Porter owns web/app/dashboard/page.jsx and chart.jsx. The six measures, filters and rule ranking use the service below. Independent checks are in evidence/dashboard_checks.csv. |
| 5 Agent | Tommy owns agent.py, models.py, web/app/cases and verify.py. Named reviewers can edit the proposed text, request revision or approve. Automated exercises use a separate test log. |
| 6 Industry fit | Samuel adapts the workflow assessment in Funding brief.pdf to the class industry map. |
| 7 Governance and unit cost | Review decisions and tool/model traces live in reviews.db. Ten real local-model usage records are in evidence/local_token_runs.csv. |
| 8 ROI | Samuel reviews business.py and evidence/cost_model.csv. Pilot time, adoption and pay rates are assumptions until the team measures or validates them. |

## Rebuild and verify

Close open app windows and the local server before replacing the database on Windows. From this folder run:

```powershell
python -B build.py
python -B audit.py
python -B verify.py
python -B business.py
cd web
npm ci
npm run build
npm run dev
```

Run `python setup_model.py` first for the local-model tests in `verify.py`. The builder stages a fresh warehouse, validates schema, foreign keys, recovered rows and all six layer counts, then replaces the release. Unrecognized schemas or unhandled invalid inputs stop publication for Data Lead review. Source hashes and loads are in lineage. Bronze is read-only. All required teaching inputs are under `data/2_Northgate_Bank/bronze/`. The audit compares every exported column in `data/teammate_exports/` by stable key and treats numeric spellings as equivalent. All five exports reconciled. See the [audit results](evidence/teammate_audit.csv) and [differences file](evidence/teammate_differences.csv).

## Gemini and local operation

The tested local engine is HuggingFaceTB SmolLM2-360M-Instruct Q8_0 served by llama.cpp b12728 on loopback. The optional setup script restores this engine and model for a new checkout. The Rules only and local-model options work without a Gemini key.

Gemini receives the permitted review sentences and the drafting instruction. The app assembles the source note, names, identifiers and amounts outside the Gemini request. Hosted credentials are configured server-side. The live case above records provider-reported usage. The bank’s costing scenario uses the local model and excludes personal subscription benefits.

## Seven-minute rehearsal

| Time | Speaker | Show |
| --- | --- | --- |
| 0:00–0:45 | Samuel | Request a limited pilot and explain who owns analyst preparation time. |
| 0:45–2:00 | Romit | Follow 9,376 two-format local clocks through quarantine and back to Silver. Explain the 45 conflicting notes. |
| 2:00–3:10 | Porter | On Workload, filter R07. It accounts for 829 alerts and 414.7 hours. Switch to R09 for 62.6 minutes per alert. |
| 3:10–4:45 | Tommy | Open AL000029, prepare the draft, expand the trace, compare T0000426 with note line 11, describe the discrepancy, and request revision. If time permits, contrast AL000001's withheld local-time window. |
| 4:45–6:15 | Samuel | Show base build, annual review and support costs, three-year result, downside case and payback. |
| 6:15–7:00 | Tommy and Samuel | Show one failed test and its fix. State the pilot timing and quality gates. Ask for the pilot decision. |

## Personal evidence to collect

Choose a mix of real alerts across rules, channels and note availability. Time manual evidence collection and writing, then the entire assisted workflow including checking references, corrections and approval. Alternate the order across reviewers to reduce practice effects. Record each matched pair once through the approved run. Keep negative savings and describe any exclusions. Replace the illustrative manual and assisted times in business.py before claiming measured ROI. Keep reviewer judgments and personal reflections in your own words.

Source materials reviewed were the root README, the submitted Team 09 outline including its architecture image, Capstone Brief and Rubric, Component 3 Data Platform Guide, Northgate DATA_DICTIONARY, the Bronze manifest and the teammate PDF. All outputs here are based on the supplied teaching data.

Runtime sources: [SmolLM2 model](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct-GGUF), [llama.cpp release](https://github.com/ggml-org/llama.cpp/releases/tag/b12728), [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing), [Google Developer Program benefits](https://developers.google.com/program/plans-and-pricing).

