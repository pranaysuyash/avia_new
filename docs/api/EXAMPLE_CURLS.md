# Example cURL Requests — Key APIs

These examples assume `API_URL=http://localhost:8000`.

## Pipeline — Compile
```bash
curl -sS -X POST "$API_URL/api/v1/pipelines/compile" \
  -H 'Content-Type: application/json' \
  -d '{
    "template_id": "tpl_qc_pack_v1",
    "version": "1.0.0",
    "parameters": {
      "max_flash_threshold": 3,
      "min_black_duration_s": 1.0,
      "pse_check": true,
      "loudness_target_lufs": -23
    }
  }'
```

## Pipeline — Run
```bash
curl -sS -X POST "$API_URL/api/v1/pipelines/run" \
  -H 'Content-Type: application/json' \
  -d '{
    "template_id": "tpl_creator_pack_v1",
    "version": "1.0.0",
    "parameters": {
      "target_platforms": ["youtube_shorts", "instagram_reels"],
      "caption_burn_in": true,
      "thumbnail_style": "bold_text_center",
      "hashtags_count": 8
    }
  }'
```

## Frame OCR — Start Job
```bash
curl -sS -X POST "$API_URL/api/v1/ocr/index/med_123" \
  -H 'Content-Type: application/json' \
  -d '{"sampling_mode":"interval","interval_s":1.0,"lang":"en"}'
```

## Frame OCR — Job Status
```bash
curl -sS "$API_URL/api/v1/ocr/index/job_01ABC/status"
```

## Frame OCR — Query Results
```bash
curl -sS "$API_URL/api/v1/ocr/results?media_id=med_123&q=Breaking&limit=25"
```

## Caption QC — Validate SRT (file upload)
```bash
curl -sS -X POST "$API_URL/api/v1/captions/qc/validate" \
  -F "file=@/path/to/file.srt" -F "format=srt" \
  -F "options={\"reading_speed_max_cps\":20,\"min_duration_ms\":800,\"max_lines\":2}"
```

## Caption QC — Validate Segments (JSON)
```bash
curl -sS -X POST "$API_URL/api/v1/captions/qc/validate" \
  -H 'Content-Type: application/json' \
  -d '{
    "segments":[{"start_ms":0,"end_ms":2000,"text":"Hello world"}],
    "options":{"reading_speed_max_cps":20,"min_duration_ms":800,"max_lines":2}
  }'
```

## Study Packs — Create
```bash
curl -sS -X POST "$API_URL/api/v1/education/study-packs" \
  -H 'Content-Type: application/json' \
  -d '{"media_id":"med_lecture_1","quiz_count":15,"flashcard_format":"anki","slide_ocr":true}'
```

## Creator Publish Pack — Create
```bash
curl -sS -X POST "$API_URL/api/v1/publish/packs/creator" \
  -H 'Content-Type: application/json' \
  -d '{
    "media_id":"med_creator_1",
    "platforms":["youtube_shorts","instagram_reels"],
    "caption_burn_in":true,
    "thumbnail_style":"bold_text_center",
    "hashtags_count":10
  }'
```

## Live/SSAI — Start Highlights Detection
```bash
curl -sS -X POST "$API_URL/api/v1/live/streams/stream_123/highlights/detect" \
  -H 'Content-Type: application/json' \
  -d '{"rules":["goal","score"],"clip_length_s":12}'
```

