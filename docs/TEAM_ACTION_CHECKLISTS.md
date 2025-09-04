# Team Action Checklists (Aligned to H1 Roadmap)

## Backend
- API prefix standardization (`/api/v1`) and auth refresh consistency
- WS endpoints matrix → implement or deprecate unused
- Frame OCR: jobs/hits schema, sampling, OCR worker, search integration
- Pipeline builder APIs: templates, compile, run, telemetry, policies
- Creator Packs endpoints: thumbnail, B-roll, social pack generation
- Live/SSAI: ingest hooks, WS events, SSAI metadata endpoints

## Web (React)
- Env configs (`VITE_API_URL`, `VITE_WS_URL`) and WS hardcode removal
- Search: OCR source filter and time-jump results surfacing
- Pipeline editor: canvas/palette/inspector MVP; run pane and diff viewer
- Creator Packs UI: one-click publish pack; A/B thumbnail test harness
- Caption QC panel and report export

## Mobile (RN/Expo)
- Auth path unification; presigned uploads adoption
- Read-only OCR search results and time-jump integration
- Creator pack preview (thumbnails, captions overlays)

## Infra/DevOps
- Observability baselines; cost/latency telemetry; budgets/alerts
- CI/CD gates; manifest signing; environment conventions
- GPU pools and autoscaling policy for OCR/Gen tasks

## Data/ML
- OCR evaluation sets; WER/OCR accuracy tracking; cost models
- Recommender baselines for Creator Pack titles/hashtags
- Time-aligned embeddings and segment graph prototypes

## Product/Design
- Pipeline builder UX flows and onboarding; starter templates library
- Niche packs definitions (broadcast QC, creator, education)
- Success metrics dashboards (adoption, time-to-value, quality)

