# Pipeline API — Examples

## Compile Template

Request
```http
POST /api/v1/pipelines/compile
Content-Type: application/json

{
  "template_id": "tpl_qc_pack_v1",
  "version": "1.0.0",
  "parameters": {
    "max_flash_threshold": 3,
    "min_black_duration_s": 1.0,
    "pse_check": true,
    "loudness_target_lufs": -23
  }
}
```

Response
```json
{
  "plan_id": "pln_01HXYZ...",
  "summary": {
    "nodes": 6,
    "estimated_cost": { "p50": 0.12, "p95": 0.15 },
    "estimated_time_s": { "p50": 45, "p95": 60 }
  },
  "valid": true,
  "diagnostics": []
}
```

## Run Template

Request
```http
POST /api/v1/pipelines/run
Content-Type: application/json

{
  "template_id": "tpl_creator_pack_v1",
  "version": "1.0.0",
  "parameters": {
    "target_platforms": ["youtube_shorts", "instagram_reels"],
    "caption_burn_in": true,
    "thumbnail_style": "bold_text_center",
    "hashtags_count": 8
  }
}
```

Response
```json
{ "run_id": "run_01HABC...", "status": "queued" }
```

## Get Run Detail

Request
```http
GET /api/v1/pipelines/runs/run_01HABC...
```

Response
```json
{
  "run_id": "run_01HABC...",
  "status": "running",
  "graph": { "nodes": [ ... ], "edges": [ ... ] },
  "node_execs": [
    { "node_id": "ingest", "status": "completed", "duration_ms": 2300 },
    { "node_id": "transcribe", "status": "running", "progress": 0.42 }
  ],
  "started_at": "2025-02-01T10:00:00Z"
}
```

