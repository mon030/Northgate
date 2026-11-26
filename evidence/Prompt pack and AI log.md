# Prompt pack and AI use record

## Production prompt

The literal, versioned instruction is INSTRUCTION in models.py, version case-review-1.0. The full prompt, permitted sentences, exact output, model and token counts from a real generation are in example_run.json. Subsequent runs store the same fields in reviews.db. The role is case preparation assistant. The context is a list of permitted statements derived from validated evidence. The task is to choose a lead and follow-up. The format is a JSON object with lead and follow_up. Both values must equal an allowed sentence. The app adds every required source fact and limitation, irrespective of the model's choice. A provider failure or unsupported selection withholds the draft.

For AL000029, a verified lead reads “The note describes a wire and the linked transaction records another channel.” The selected follow-up asks the analyst to reconcile the channel before acceptance. The team can check the claim at T0000426 and analyst_notes.jsonl line 11. The original note stays attributed in the analyst's view. The model receives only the allowed sentences.

## Development interactions that shaped this build

This is a record of AI-assisted work in this chat. Automated checks below do not imply a student personally performed them.

| User request or feedback | AI-assisted output | Verification and resulting change |
| --- | --- | --- |
| Read non-draft documents, prioritize the Agent Builder role and check the teammate data. | Extracted the rubric, final outline and tool dictionary. Rebuilt missing evidence tables and compared the five exports. | Joined all 1,613 alerts and 1,500 disputes by stable IDs. Confirmed all exported values, including all 12 rule summaries. Reused the source records. |
| Teacher asked for quarantined records to be cleansed and processed. | Added explicit correction rules, keyed exception history and downstream checks. | First ISO parser failed. Added the local format, retained its clock convention and revalidated 9,376 rows. Preserved 45 conflicting narratives with an analyst review requirement. |
| “If you see the issue, fix it.” | Added conflict-comment enforcement and a test for repeat approval. | The stricter check initially returned the wrong reason for an already-decided note. Changed validation order and reran the suite. See test_results.csv. |
| Teacher requested the cost side, the working app and project learning. | Built three scenarios, a costed funding ask, a pilot capture form and a demonstration script. | Reconciled historical minutes to Bronze and measured local inference tokens. Kept wages, adoption and human timing explicit assumptions. |
| User identified Google AI Pro, AI Studio and monthly credits. | Checked AI Studio and official benefit documentation. Added an optional constrained Gemini adapter. | The account showed Pro and a free-tier project. The external case test was blocked by automatic approval review. Used measured local-model runs for costs. |
| User requested a web app using Next.js, daisyUI and existing npm packages. | Built a Next.js dashboard, case workflow, business case and review history. Used daisyUI, Recharts and Lucide React. | Production build passed. Opened the dashboard and prepared the conflict case through Edge. Resolved a hydration warning caused by an installed browser extension adding body attributes. |
| User asked which free database fits, including MongoDB. | Compared local SQLite with hosted PostgreSQL and MongoDB Atlas against the outlined relational data model. | Preserved the verified SQLite warehouse and its alert/dispute grains. Porter can develop against the dashboard endpoint and a copy of the same project. |

## Stakeholder communication

### Public deployment QA, November 26

The hosted test used fictional AL000029 with permission to send four approved candidate sentences to Gemini. Google returned HTTP 402. Run 1 retained the failure trace and an empty draft. On the same alert, run 2 used Rules only, stopped at Pending, and saved a revision request under Deployment QA. A separate read returned that decision. Neither run supplied manual or assisted pilot timings. The team can demonstrate provider failure handling and show how production review storage survives a later deployment. The local model tests remain the evidence for measured generative token usage.

**To the fraud operations manager — pilot funding request**

Our six-month sample contains 1,613 alerts and 885.1 hours of recorded analyst work. The proposed pilot will test how much of the preparation step we can safely shorten. One demonstration case links an $11.68 card purchase to a note describing a wire. The assistant brings both records to the reviewer and records the reviewer’s decision. We request $6,040 for build and training under the base assumptions. We will compare manual and assisted preparation on the same alerts before recommending rollout. At the assumed level of adoption, the pilot needs to release about 2.56 minutes per assisted case to break even over three years.

Checked against dashboard_checks.csv, Bronze T0000426, note line 11 and business.py. Removed any claim of measured savings. The team should log later AI interactions with the prompt, actual output, checks and changes.

