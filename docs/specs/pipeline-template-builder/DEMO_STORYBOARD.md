# Pipeline Builder — Demo Storyboard (Product Walkthrough)

1) Landing (Templates Library)
- Show starter templates: QC Pack, Creator Pack, Education Pack. CTA: “Create from template” or “Blank”.

2) Canvas (Blank)
- Narration: “Let’s build a QC pipeline.” Drag Ingest → QC Flash → QC Black → PSE → Loudness → Report.
- Show snap, connectors, validation on wrong edge.

3) Inspector (Node Properties)
- Click PSE node; toggle enabled; see cost/time estimates update.
- Set loudness target; save changes.

4) Validate & Compile
- Click Validate: schema/acyclic checks pass; policy gate added before Export.
- Click Compile: see plan summary (nodes, retries, cost/time ranges).

5) Run & Observe
- Trigger manual run; run pane opens.
- Node-by-node progress; heatmap highlights slowest node; click-through logs.

6) Failure & Rerun
- Simulate a failure; policy halts; show actionable error.
- Fix param; rerun from failed node; successful completion.

7) Save as Template & Share
- Save as “QC Pack — Custom” v1.0.0; add description and tags; share with team.

8) Trigger Setup (Schedule)
- Open scheduler; set nightly cron; add concurrency cap; dry-run preview shows expected cost/time.

9) Manifest Export & CI
- Export signed manifest; show JSON excerpt; mention CI contract lint step.

10) Wrap-up
- Recap: from blank canvas to automated, reusable pipeline with guardrails and observability.

