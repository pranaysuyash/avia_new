# Deep Dive — Video Intelligence Production Platform

- Intent: Advanced video IQ to support editing decisions (shots/scenes, composition, motion) and NLE roundtrip.
- Scope: Analysis services, QC tie-ins, EDL/AAF/XML integration; excludes final rendering.
- Stakeholders: Editors, producers, post supervisors, QC ops.

## Current Spec Strengths
- Coverage of shot/scene detection, camera movement, composition scoring; deliverable QC linkage.

## MVP (Execution Outline)
- Capabilities: scene/shot detection, basic composition (rule-of-thirds, headroom), motion heuristics.
- APIs: `/api/v1/video-iq/analyze`, `/api/v1/video-iq/results/{media_id}`
- Data: timeline of segments with labels/scores; recommended “selects”.
- UI: timeline overlays, selects panel, export EDL/XML.
- Acceptance: accuracy baseline on golden set; export opens in NLE.

## Long-Term Roadmap
- Advanced: ML ranking for optimal shots, angle suggestions, b-roll proposals.
- Roundtrip: conform/relink for proxies → camera masters; IMF/AS-11 validation.
- QC: integrate flash/black/freeze/PSE checks; loudness cross-check.
- Integrations: micro-apps (auto-highlights), provider hub for style transfer.

## Architecture & Contracts
- Components: analyzers (shot/scene/motion/composition), aggregator, export service.
- API: REST; sidecar outputs for NLEs; schema contracts.
- Data: segments with features and scores; provenance with model/version.

## Risks & Mitigations
- Variability across genres → per-template tuning; allow heuristics profiles.
- NLE quirks → test vectors, robust import validation.

## Metrics & SLOs
- Hit-rate on editor‑accepted selects; EDL import success; processing P95.

## Sequencing & Dependencies
- Depends on video decode and proxy generation; QC pack alignment.

