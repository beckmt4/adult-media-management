# Phase 4: n8n Scene Lifecycle Automation

**Status:** Ready to implement  
**Priority:** Core scene automation workflow  
**Timeline:** Week 2-3

---

## Overview

Replace manual Phase 2-3 operations with fully automated scene processing via n8n. This workflow triggers automatically when scenes are created/updated in Stash and orchestrates all downstream enrichment, analysis, and metadata operations.

---

## Core Workflow: Scene Lifecycle Automation

### Trigger: Stash Webhook

**Event:** `scene.create` or `scene.update`  
**Endpoint:** n8n webhook URL (configure in Stash → Settings → Integrations)

```graphql
# Stash webhook payload structure
{
  "id": "scene-123",
  "title": "Scene Title",
  "path": "/path/to/scene.mp4",
  "performers": [],
  "studios": [],
  "tags": [],
  "created_at": "2026-05-15T...",
  "updated_at": "2026-05-15T..."
}
```

---

## Workflow Nodes (Sequential)

### 1. **Webhook Trigger** (Start)
- **Type:** Webhook (POST)
- **Description:** Listen for Stash scene create/update events
- **Config:** Accept raw payload from Stash

### 2. **Wait Node** (Delay)
- **Type:** Wait
- **Duration:** 2 minutes
- **Reason:** Allow file to settle on disk, handle async writes

### 3. **Get Scene Details** (Stash GraphQL)
- **Type:** HTTP Request (POST)
- **URL:** `http://192.168.1.147:9999/graphql`
- **Headers:**
  ```
  Authorization: Basic [base64(root:qlx9_adM)]
  Content-Type: application/json
  ```
- **Body:**
  ```graphql
  query GetSceneDetails($id: ID!) {
    findScene(id: $id) {
      id
      title
      path
      stash_ids
      performers { id name images }
      studios { id name }
      tags { id name }
      rating
      duration
      file_mod_time
      date
      details
    }
  }
  ```
- **Variables:** `{ "id": "{{ $json.id }}" }`

### 4. **Check for StashDB ID** (Conditional)
- **Type:** If statement
- **Condition:** `stash_ids.length === 0`
- **True branch:** Proceed to Step 5 (Scrape metadata)
- **False branch:** Skip to Step 7

### 5. **Scrape Scene Metadata** (Stash GraphQL - IF no StashID)
- **Type:** HTTP Request (POST)
- **URL:** `http://192.168.1.147:9999/graphql`
- **Body:**
  ```graphql
  mutation ScrapeScene($id: ID!, $url: String) {
    scrapeScene(input: { scene_id: $id, url: $url }) {
      title
      details
      date
      duration
      rating
    }
  }
  ```
- **Variables:** Extract scene ID and infer scraper URL

### 6. **Auto-Tag Metadata** (Stash GraphQL)
- **Type:** HTTP Request (POST)
- **Body:**
  ```graphql
  mutation AutoTag($sceneIDs: [ID!]!) {
    metadataAutoTag(input: { scenes: $sceneIDs, performers: [], studios: [] }) {
      job { id status }
    }
  }
  ```
- **Note:** Returns job ID; caller is responsible for polling

### 7. **Check Performer Images** (Conditional)
- **Type:** If statement
- **Condition:** Scene has performers AND any performer has 0 images
- **True branch:** Trigger actress_library scraping for those performers
- **False branch:** Skip to Step 8

### 8. **Trigger Actress Library Image Scraping** (Stash GraphQL - IF needed)
- **Type:** HTTP Request (POST) — Loop over each performer
- **Body:**
  ```graphql
  mutation EnrichPerformer($performerId: ID!) {
    runPluginTask(
      plugin_id: "actress_library"
      task_name: "Scrape Images for Performer"
      args: { performer_id: $performerId }
    )
  }
  ```

### 9. **Transcribe Audio** (Faster-Whisper API)
- **Type:** HTTP Request (POST)
- **URL:** `http://192.168.1.147:10300/api/transcribe`
- **Body:**
  ```json
  {
    "audio_path": "{{ $json.path }}",
    "language": "ja",  // Japanese priority for JAV
    "format": "srt"
  }
  ```
- **Output:** Transcript text or SRT file path

### 10. **Store Transcript** (Stash GraphQL - IF transcription succeeded)
- **Type:** HTTP Request (POST)
- **Body:**
  ```graphql
  mutation UpdateScene($id: ID!, $details: String!) {
    sceneUpdate(input: { id: $id, details: $details }) {
      id
    }
  }
  ```

### 11. **Vision Analysis** (Ollama LLM)
- **Type:** HTTP Request (POST)
- **URL:** `http://192.168.1.182:11434/api/generate`  // Workstation RTX 4090
- **Headers:**
  ```
  Content-Type: application/json
  ```
- **Body:**
  ```json
  {
    "model": "llava:13b",
    "prompt": "Analyze this video scene thumbnail and generate content tags...",
    "images": ["{{ base64(thumbnail_path) }}"],
    "stream": false
  }
  ```
- **Output:** Tag suggestions (solo, couples, group, acts, setting, attributes)

### 12. **Apply AI Tags** (Stash GraphQL)
- **Type:** HTTP Request (POST)
- **Body:**
  ```graphql
  mutation AddTags($sceneId: ID!, $tagNames: [String!]!) {
    sceneUpdate(
      input: { 
        id: $sceneId 
        tag_ids: {{ look_up_tag_ids_from_names($tagNames) }}
      }
    ) { id }
  }
  ```
- **Note:** May need tag creation if they don't exist

### 13. **Queue for Transcode Check** (tdarr API)
- **Type:** HTTP Request (POST)
- **URL:** `http://192.168.1.147:8265/api/v2/queue`  // tdarr port
- **Body:**
  ```json
  {
    "file_path": "{{ $json.path }}",
    "library_id": "adult",
    "priority": "high"
  }
  ```

### 14. **Generate NFO** (mcMetadata)
- **Type:** HTTP Request (POST)
- **URL:** `http://localhost:6500/api/generate-nfo`  // mcMetadata container
- **Body:**
  ```json
  {
    "scene_id": "{{ $json.id }}",
    "output_path": "/mnt/nfo/{{ $json.id }}.nfo"
  }
  ```

### 15. **Log Success & Notify** (Slack/Discord)
- **Type:** Webhook (to notification service)
- **Message:**
  ```
  ✅ Scene processed: {{ $json.title }}
  - Performers: {{ $json.performers.length }}
  - Tags applied: {{ tags_count }}
  - Transcript: {{ transcript ? '✓' : '✗' }}
  - AI Analysis: ✓
  ```

### 16. **Error Handler** (Catch errors throughout)
- **Type:** Error handler block
- **Actions:**
  - Log error details
  - Notify admin with scene ID and error message
  - Mark job as failed (don't retry indefinitely)

---

## Workflow Nodes: Daily Maintenance

**Separate workflow** — Runs on cron schedule (e.g., 2 AM daily)

### Maintenance Tasks
1. **Scan for unprocessed scenes** — Find `stash_ids: null`
2. **Batch Auto-Tag** — Run `metadataAutoTag` on 10-50 scenes
3. **Check job queue** — Poll Stash for stuck/failed jobs
4. **Refresh cookies** — Update JavDB/JavLibrary session cookies if needed
5. **Consolidate duplicates** — Find & merge duplicate performers
6. **Report metrics** — Count scenes processed, tags applied, success rate

---

## Configuration & Authentication

### Stash API
- **Endpoint:** `http://192.168.1.147:9999/graphql`
- **Auth:** Basic (`root:qlx9_adM`)
- **Cookie:** Session-based (login first via curl, store in n8n credentials)

### Ollama (Workstation)
- **Endpoint:** `http://192.168.1.182:11434`
- **Model:** `llava:13b` (vision) + `nomic-embed-text` (embeddings)
- **Auth:** None (LAN-only)

### Faster-Whisper
- **Endpoint:** `http://192.168.1.147:10300`
- **Languages:** Japanese primary, English secondary
- **Output formats:** SRT, plain text

### Qdrant (Semantic Search)
- **Endpoint:** `http://192.168.1.147:6333`
- **Collection:** `stash_scenes` (768-dim, Cosine distance)
- **Auth:** None (internal network)

### tdarr (Transcode Queue)
- **Endpoint:** `http://192.168.1.147:8265/api/v2`
- **Auth:** API key (if configured)

---

## n8n Setup Steps

### 1. Create Credentials
In n8n UI → Credentials:
- **Stash API:** Type=HTTP, Auth=Basic, User=root, Pass=qlx9_adM
- **Ollama:** Type=HTTP, URL=http://192.168.1.182:11434
- **Qdrant:** Type=HTTP, URL=http://192.168.1.147:6333

### 2. Create Webhook
In n8n → Workflows → Add node → Webhook:
- **URL:** (n8n will generate) → Copy to Stash Settings
- **Method:** POST
- **Auth:** None (assume Stash is trusted LAN)

### 3. Import Workflow
- Download or create JSON workflow definition
- Import into n8n
- Enable production mode

### 4. Configure Stash Webhook
Stash → Settings → Integrations → Webhooks:
- **URL:** (paste n8n webhook URL)
- **Events:** `scene.create`, `scene.update`
- **Test:** Create a dummy scene, verify webhook fires

### 5. Test Execution
- Trigger manually with sample scene data
- Check n8n logs for errors
- Verify Stash was updated with tags/metadata

---

## Deployment Checklist

- [ ] All n8n credentials created and tested
- [ ] Webhook URL added to Stash
- [ ] Workflow JSON validated (no syntax errors)
- [ ] Test scene processed end-to-end
- [ ] Error handlers configured (alerts to admin)
- [ ] Logging enabled (n8n debug mode)
- [ ] Maintenance workflow scheduled
- [ ] Performance baseline (check Unraid CPU/GPU usage)
- [ ] Rollback plan documented

---

## Performance Expectations

**Per-scene processing time:**
- Wait: 2 min
- Metadata scrape (if needed): 5-30 sec
- Performer image scrape (if needed): varies (1-5 min per performer)
- Vision analysis (llava:13b on RTX 4090): 8-12 sec
- Transcode check: <1 sec
- **Total:** ~3-10 min per scene (depending on scraping needs)

**Throughput:**
- 1 scene per minute in ideal case
- 2,930 scenes ÷ 1/min = ~49 hours one-time bulk
- But with daily incremental (10-20 new scenes/day), negligible overhead

**Concurrency:**
- n8n: Run up to 5 workflows in parallel (configurable)
- Ollama: Serialize on single RTX 4090 (sequential inference)
- Stash: Handles concurrent GraphQL queries

---

## Next Steps

1. **Copy workflow JSON** below, import into n8n
2. **Test with 1 scene** — verify all nodes execute
3. **Check Stash logs** for any GraphQL errors
4. **Scale to production** — enable auto-trigger on all scenes
5. **Monitor for 24 hours** — verify stable operation
6. **Iterate on error handling** — add retries, notifications

---

## Workflow JSON Template

```json
{
  "name": "Scene Lifecycle Automation",
  "nodes": [
    {
      "parameters": {
        "path": "{{ $json.id }}",
        "body": "raw",
        "method": "POST"
      },
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [250, 300]
    },
    {
      "parameters": {
        "amount": 2,
        "unit": "minutes"
      },
      "name": "Wait 2 Minutes",
      "type": "n8n-nodes-base.wait",
      "typeVersion": 1,
      "position": [450, 300]
    }
  ],
  "connections": {
    "Webhook": {
      "main": [[{ "node": "Wait 2 Minutes", "type": "main", "index": 0 }]]
    }
  },
  "active": false,
  "nodeTypes": []
}
```

---

## Commands for Manual Testing

```bash
# Test Stash GraphQL endpoint
curl -X POST http://192.168.1.147:9999/graphql \
  -H "Authorization: Basic $(echo -n 'root:qlx9_adM' | base64)" \
  -H "Content-Type: application/json" \
  -d '{"query":"query { findScenes(input: {size: 1}) { scenes { id title } } }"}'

# Test Ollama
curl -X POST http://192.168.1.182:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"llava:13b", "prompt":"test", "stream":false}'

# Test Faster-Whisper
curl -X POST http://192.168.1.147:10300/api/transcribe \
  -H "Content-Type: application/json" \
  -d '{"audio_path":"/path/to/audio.m4a", "language":"ja"}'
```

---

## Known Issues & Workarounds

| Issue | Cause | Workaround |
|-------|-------|-----------|
| Stash webhook timeout | Slow scene scraping | Increase wait time (Step 2) to 5 min |
| Performer image scrape fails | External API rate limits | Add exponential backoff, retry after 5 min |
| Vision analysis hangs | GPU memory pressure | Monitor GPU from workstation, reduce batch size |
| Transcript storage fails | Path encoding issues | Sanitize file paths, use URL encoding |

---

## Success Metrics (Week 1-2)

- ✅ Workflow executes without errors for 10 consecutive scenes
- ✅ Average scene processing time < 5 min (excluding performer scraping)
- ✅ 100% metadata tag application (no scenes with 0 tags)
- ✅ Zero failed jobs (all errors logged + handled gracefully)
- ✅ Transcripts generated for 90%+ of scenes
- ✅ Admin notifications working (success/error alerts)

---

**Status:** Ready for implementation  
**Owner:** Tom Beck  
**Last Updated:** 2026-05-15
