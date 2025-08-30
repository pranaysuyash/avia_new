# .kiro Tasks Audit — Gaps and Opportunities for a Media Management and Analysis Platform

- Date: 2025-08-30
- Scope: Review all `.kiro` steering and specs/task files; identify missing or under-specified capabilities for a modern media management and analysis platform. Focus on multi-industry use cases, stakeholders, personas, and niche workflows. No code changes — documentation only.

**Method**
- Scanned `.kiro/steering` and `.kiro/specs` folders to understand current coverage (architecture, requirements, tasks).
- Mapped against a reference media platform capability model (ingest → manage → analyze → collaborate → distribute → govern) and industry-specific needs.
- Highlighted additions that add clear value without duplicating existing plans.

**What’s Already Well Covered (high level)**
- Advanced analytics and topic modeling; vector search; knowledge graph concepts.
- Real-time collaboration, transcription, speech analytics; cross‑platform/mobile architectures.
- Production readiness (security, compliance), performance monitoring, DevOps.
- Video intelligence (scene/shot analysis), audio processing enhancements, internationalization.
- Marketplace, developer experience, testing/QA frameworks.

---

## Gaps by Domain (Additions to Consider)

- Rights, Licensing, and Distribution Management
  - Rights/clearance catalog: track territories, windows, exclusivity, embargo, contract terms and expirations.
  - Delivery packs and specs: support broadcaster/platform spec templates (AS-11 DPP, IMF/ST 2067) with automated validation.
  - Licensing workflows: clearance requests, approvals, redlines; revenue share and usage-based billing integration.
  - Usage tracking and “where-used”: downstream distribution registry; takedown/recall orchestration.

- Media Supply Chain and Professional Formats
  - Professional formats: MXF, BWF, ProRes/DNx, IMF CPL/OPLs parsing and validation; sidecar management.
  - Proxy generation & conform: high/low-res proxies, EDL/AAF/XML roundtrip to NLEs (Premiere, Resolve, FCP), relink and conform.
  - QC automation: loudness (EBU R128/CALM), black/freeze/flash/PSE checks, gamut, phase, silence; transcode quality (VMAF/SSIM/PSNR).

- Live and Near-live Workflows
  - Stream ingest: SRT, RTMP, HLS/DASH capture; live captioning, live translation, DVR.
  - Live clipping and highlights: instant replay, auto highlight reels (sports/news), ad markers and SCTE‑35 cue handling.
  - SSAI/DAI readiness: VMAP/VAST ad slot metadata, brand safety scoring per segment.

- Visual Enrichment Beyond Current Scope
  - Frame OCR at scale: extract burned-in text/titles/lower-thirds for search and compliance.
  - Logo/brand detection; product placement recognition; object tracking across time (ID persistence).
  - Face recognition with privacy tiers (blur/redact/consent tracking); speaker‑face linking to transcripts.

- Collaboration, Review & Approval at Enterprise Depth
  - Timeline review: frame/timecode comments, threaded discussions, mention/assign; compare versions side‑by‑side.
  - Structured approvals: stages, SLAs, gates, audit logs; policy‑driven release controls.
  - Watermarked review links (per‑viewer forensic watermark), expiry and view analytics.

- Security, Privacy, and Compliance (Beyond current generalities)
  - Forensic watermarking and leak tracing; outbound delivery traceability.
  - Content ID/fingerprinting: duplicate detection, platform takedown integrations.
  - Automated PII/PHI redaction in audio/video (faces, plates, docs) with review queues.
  - Legal hold and eDiscovery support: chain-of-custody, fixity (checksum) checks.

- Archive & Lifecycle Management
  - Storage tiers: warm/cold/archive (S3 Glacier/Deep Archive, GCS, Azure Archive, LTO); rehydrate workflows.
  - Fixity/health checks: scheduled checksum verification, self‑healing alerts, retention schedules.
  - Policy automation: per-team lifecycle rules, cost cap alerts, storage analytics.

- Distribution & Publishing
  - Multi-platform packaging: platform-specific transcodes and metadata (YouTube/Vimeo/TikTok/Instagram/OTT CMS).
  - Scheduling, embargo, territory blocks; caption/subtitle packaging (SRT/WebVTT/TTML/IMSC).
  - Brand safety checks pre‑publish; compliance gate for regions (e.g., age ratings, content advisories).

- Accessibility & Localization Depth
  - Caption authoring QA: SDH, speaker labels, positioning, timing QC, reading speed checks.
  - Audio description authoring & mix; sign-language track support and layout rules.
  - Transliteration/romanization; regional censorship edit rules and deliverables.

- Operations, Cost & Performance
  - GPU pool management: scheduling, quotas, cost policies, spot instance usage, per-team budgets.
  - Job observability: per-job traces, queue SLAs, anomaly detection for failures or cost spikes.
  - Green compute reporting: energy metrics, carbon estimates for processing.

- Data & AI Enablement
  - Multimodal RAG: time-aligned retrieval over transcripts + visual embeddings; temporal queries (“show segments where CEO appears and sentiment dips”).
  - Taxonomy/ontology tooling: editorial taxonomies, product catalogs; linking to knowledge graph with curation tools.
  - Safety & bias evals for models; explainability for moderation/analytics decisions.

---

## Persona- and Industry-Specific Needs

- Broadcast/Studios/Post
  - Delivery packs, QC reports, NLE roundtrip, conform/relink, version compare, watermarked review.
- Sports
  - Player/team/event detection; auto-highlights; sponsor logo compliance; real-time social clips.
- News/Publishing
  - Quote extraction and verification, compliance review, embargo and source management.
- Marketing/Brand/Agencies
  - Brand safety, logo/product placement analytics, multi-channel publish, campaign ROI mapping.
- Education (Students, Educators, Researchers)
  - Students: lecture transcription and summarization (topic, section, and full-course levels), time-coded bookmarks, highlights, flashcard and quiz generation, concept maps, spaced-repetition study packs, multimodal retrieval across notes/slides/video.
  - Educators: assessment item generation (MCQ/short-answer with rationales), lecture outline → video indexing, engagement analytics (drop-off points, question hotspots), content accessibility QC (captions/AD checks), content re-use and remixing (clips and compilations).
  - Researchers: seminar indexing, speaker/topic segmentation, code/formula/table extraction from screen recordings (OCR on frames), experiment log video tagging.
- Healthcare
  - PHI redaction in video, HIPAA storage modes (local-only), consent tracking; device video analytics.
- Legal/Compliance
  - Legal hold, eDiscovery chain-of-custody, certified transcripts; redaction workflows.
- Call Centers/Customer Support
  - Agent QA analytics, coaching clips, sentiment trends with privacy-preserving aggregation.
- Security/Surveillance
  - Anomaly detection, restricted zones, privacy masking, retention policies.
- Podcasts/Audio Publishers
  - Chaptering, loudness normalization, ad slot placement, auto social snippets.

---

## Cross-Cutting Capabilities

- Standards & Interop: IPTC/XMP, EBUCore, sidecar JSON/XML, IMF/AS‑11 schemas.
- Connectors: S3/GCS/Azure/NAS; MAM/DAM integrations (Iconik, Frame.io, Vimeo, etc.); Slack/Teams/Jira.
- Governance: retention schedules, approval matrices, policy audits, risk scoring.
- FinOps: per-team budgets, cost centers, budget alerts, showback/chargeback.

---

## Generative & Editing Provider Integrations (Replicate, FAL, OpenRouter, etc.)

- Provider Abstraction Layer
  - Unify access to hosted models for image/video/audio via a pluggable provider hub (Replicate, FAL, OpenRouter, together/Anyscale, etc.).
  - Policy-driven routing (cost, latency, capability), retries/fallbacks, rate-limit awareness, and caching of results.

- Common Media Editing Tasks
  - Image: background removal, inpainting/outpainting, upscaling/super-resolution, denoise/deblur, style transfer, key art/thumbnail generation.
  - Video: background removal, person/object masking, logo blurring, temporal inpainting, slow-motion/interpolation, caption burn-in, stylization.
  - Audio: denoise/dereverb, source separation, voice conversion, TTS/voice cloning (with consent and safeguards).

- Generative Content & Assistance
  - Auto B‑roll and thumbnails from prompts and transcript context; scene-aware title/description/hashtags for distribution.
  - LLM-assisted workflows via OpenRouter (multi-model access): summaries at multiple granularities, key points, meeting minutes, study notes, quizzes, and rubric-based grading assistants for educators.

- Compliance & Safety
  - Content moderation before/after edits; watermarks for AI-generated assets; consent gates for voice/image manipulation; provider attestations logging.

- Developer Notes
  - Introduce `provider-capabilities` registry (task mapping → supported models), standardized request/response schemas, cost/latency telemetry, golden tests per task across providers.

---

## Quick-Win Additions (low lift, high value)

- Frame OCR pipeline with search integration (index lower thirds/titles).
- Caption QC toolkit (reading speed, timing, overlap, positioning).
- Watermarked review links with per-viewer identifiers + expiry.
- Storage lifecycle policies UI (tiering rules and cost estimates).
- Live clipping + highlights with simple rules (per keyword/entity/time window).
- Preset delivery specs library (DPP/IMF presets) with validation reports.
- Student toolkit: note-taking with time-coded highlights, flashcard/quiz generation from transcripts, export to Anki/Notion.
- Generative assistants: one-click thumbnails/B‑roll via Replicate/FAL; multi-model summaries via OpenRouter; auto social packs (title/desc/hashtags) per platform.

## Strategic Initiatives (multi-sprint)

- Professional media supply chain (IMF/MXF/EDL/AAF) and NLE roundtrip.
- Rights/licensing and marketplace monetization with usage metering.
- Multimodal temporal RAG and knowledge graph curation tools.
- Full SSAI/DAI readiness and brand safety scoring per segment.
- Enterprise-grade legal hold, eDiscovery, and forensic watermarking.
- Provider hub for creative editing & LLMs with governance (cost controls, audit trails, model evals), plus fine-tuned education workflows (study packs, assessments, feedback loops).

---

## Suggested New Task Briefs (where to place in `.kiro/specs`)

- `professional-media-supply-chain/`
  - `design.md`: IMF/MXF parsing, EDL/AAF/XML roundtrip, proxies/conform.
  - `requirements.md`: delivery specs, QC, NLE integrations, sidecars.
  - `tasks.md`: parsers, validators, EDL export/import, QC checks, UI.

- `rights-licensing-distribution/`
  - `design.md`: rights catalog, windows/territories, usage tracking, licensing.
  - `requirements.md`: approvals, contracts, revenue share, takedown.
  - `tasks.md`: rights DB schema, workflows, reports, integrations.

- `live-streaming-and-ssai/`
  - `design.md`: ingest (SRT/RTMP), DVR, live captions, SSAI metadata.
  - `requirements.md`: VAST/VMAP, brand safety per segment, clipping.
  - `tasks.md`: ingest services, cue handling, clipper, API/WS endpoints.

- `visual-enrichment-at-scale/`
  - `design.md`: frame OCR, logo/product detection, object tracking.
  - `requirements.md`: privacy tiers, performance, storage costs.
  - `tasks.md`: pipelines, indexers, search UI, review tooling.

- `legal-hold-and-ediscovery/`
  - `design.md`: holds, chain-of-custody, fixity, exports.
  - `requirements.md`: permissions, audit logs, retention conflicts.
  - `tasks.md`: holds engine, checksum service, export tooling.

- `archive-lifecycle-and-finops/`
  - `design.md`: storage tiers, lifecycle policies, cost analytics.
  - `requirements.md`: budgets, alerts, showback/chargeback.
  - `tasks.md`: policy engine, calculators, dashboards.

- `student-learning-augmentation/`
  - `design.md`: lecture segmentation, bookmark/highlight model, study-pack generation (flashcards/quizzes), spaced repetition, education privacy (FERPA/COPPA).
  - `requirements.md`: student/educator roles, accessibility checks, LMS export (LTI/SCORM), analytics on engagement/retention.
  - `tasks.md`: transcript-to-quiz pipelines, flashcard exporters, UI for notes/highlights, progress tracking.

- `creative-editing-provider-hub/`
  - `design.md`: provider abstraction (Replicate/FAL/OpenRouter), task routing, capability registry, cost/latency telemetry, safety/compliance.
  - `requirements.md`: supported tasks (bg removal, inpaint, upscale, stylize, captioning), guardrails, watermarking, audit logs.
  - `tasks.md`: SDK adapters, job orchestration, caching, model evaluation harness, admin UI for provider configs.

---

## Next Steps

- Confirm canonical API surfaces for pro media (IMF/MXF, QC) and plan service boundaries.
- Prioritize two quick wins and one strategic initiative to seed roadmaps.
- If helpful, I can generate initial `design.md / requirements.md / tasks.md` scaffolds for the proposed new specs.
