# Deep Dive — Advanced Search & Discovery Platform

- Intent: Unified, powerful retrieval across transcripts, OCR, entities, and media metadata with temporal and semantic reasoning.
- Scope: Search index, ranking, APIs, UI; excludes capture/generation of signals (handled by upstream systems).
- Stakeholders: Editors, researchers, students, compliance, support, PMs.

## Current Spec Strengths
- Clear goal of unified API with source filters and highlights.
- Recognition of hybrid search (lexical + semantic) and facets.

## MVP (Execution Outline)
- Capabilities
  - Unified search endpoint: `/api/v1/search?q=&sources=transcript,ocr,entity&filters=...`
  - Sources: transcript (segments), OCR (time-coded hits), entities (names/orgs/products)
  - Highlight/snippets; time-jump for time-coded sources.
- APIs
  - GET `/api/v1/search` (pagination; facets; source attribution)
  - GET `/api/v1/suggest?q=` (typeahead from index)
- Data model
  - Inverted index for lexical (BM25); simple vectors for semantic (optional in MVP)
  - Document: media_id + source entries (with t_start/t_end where applicable)
- UI/UX
  - Results grouped by media with source tags; jump controls; filters by source/time range/confidence
- Observability
  - Query latency P95, error rate; clickthrough & dwell time
- Acceptance
  - Functional: highlights/snippets correct; time-jump works; filters apply
  - Non-functional: P95 < 400ms for typical queries on N docs; index freshness < X hours

## Long-Term Roadmap
- Advanced capabilities
  - Hybrid ranking (BM25 + embeddings); personal/context re-ranking
  - Temporal queries (within N sec of event/entity), playlist generation
  - Query analytics; active learning from clicks; explainable ranking
- Scale & reliability
  - Sharded indices, incremental updates; backfill pipelines
- Security & compliance
  - Per-tenant RBAC filters at query time; attribute-level filtering
- Cost & FinOps
  - Index tiering (hot/warm); retention; rebuild cost tracking
- Integrations
  - Knowledge graph boosts; live WS suggestions; NLE integrations

## Architecture & Contracts
- Components: indexer (batch), search API, ranking, analytics, UI
- API: REST for search; optional GraphQL type for typed results
- Data: unified doc schema with per-source payloads

## Risks & Mitigations
- Signal inconsistency → validation and schema contracts
- Cost of vector search → hybrid with gate; cache heavy hitters

## Metrics & SLOs
- SLIs: latency (P50/P95), error rate, freshness, CTR
- SLOs: availability 99.9%, P95 < 500ms

## Sequencing & Dependencies
- Depends on upstream signals (transcript/OCR/entity); align schemas and freshness SLAs

