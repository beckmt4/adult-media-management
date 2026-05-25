# Phase 1B — Detailed Implementation Guide
**Status:** In Progress (May 25, 2026)  
**Objective:** Complete n8n workflow HTTP node configuration (6 nodes)  
**Effort:** 4-6 hours hands-on  
**Success Criteria:** All nodes configured, workflow tested end-to-end

---

## Overview: What We're Building

The n8n workflow automates the scene lifecycle:

```
Webhook Input
     ↓
[Wait 2 minutes]
     ↓
[HTTP-1: Get Scene Details] ← GraphQL query (Stash)
     ↓
[HTTP-2: Scrape Metadata] ← Update scene with additional data
     ↓
[HTTP-3: Auto-Tag] ← Tag scene with performer/studio info
     ↓
[HTTP-4: Transcription] ← Queue audio transcription (Faster-Whisper)
     ↓
[HTTP-5: Vision Analysis] ← Send frames to Ollama for tagging
     ↓
[HTTP-6: Queue Transcode] ← Send to Tdarr for video optimization
     ↓
✅ Scene fully processed
```

---

## Current Workflow Status

**Published Workflow:** `oYYQuZXygAejZWac`  
**URL:** http://192.168.1.10:5678/workflows/view/oYYQuZXygAejZWac

**Nodes Currently Configured:**
- ✅ Webhook2 (trigger)
- ✅ Wait1 (2-minute delay)
- ❌ Get Scene Details (HTTP node — NEEDS CONFIG)
- ❌ HTTP nodes 2-6 (NOT STARTED)
- ❌ Conditional error handling (NOT STARTED)

---

## Step-by-Step: Configure Each HTTP Node

### Node 1: Get Scene Details (GraphQL Query)

**Purpose:** Fetch complete scene data from Stash  
**API:** GraphQL POST  
**Location:** After "Wait1" node

**Configuration:**

| Setting | Value |
|---------|-------|
| **Node Name** | `Get Scene Details` |
| **Method** | `POST` |
| **URL** | `http://192.168.1.147:9999/graphql` |
| **Authentication** | Form data (username/password) |
| **Username** | `root` |
| **Password** | `[Your Stash password]` |

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "query": "query GetSceneDetails($id: ID!) { findScene(id: $id) { id title path duration rating url cover { url } files { basename size } performers { id name } studios { id name } tags { id name } stash_ids { endpoint id } } }",
  "variables": {
    "id": "{{ $json.id }}"
  }
}
```

**Input Source:** `Wait1` (preserves scene data)

**Expected Output:**
```json
{
  "findScene": {
    "id": "123",
    "title": "Scene Title",
    "path": "/path/to/scene.mp4",
    "duration": 1800,
    "performers": [{"id": "1", "name": "Performer Name"}],
    "studios": [{"id": "2", "name": "Studio Name"}],
    "tags": [{"id": "3", "name": "Tag"}]
  }
}
```

**How to Add:**
1. Open n8n workflow editor
2. Click "+" button to add new node after Wait1
3. Search for "HTTP Request"
4. Fill in all fields above
5. Save

---

### Node 2: Scrape Scene Metadata

**Purpose:** Update scene with additional metadata (StashDB matching, etc.)  
**API:** GraphQL mutation  
**Endpoint:** http://192.168.1.147:9999/graphql

**Body (JSON):**
```json
{
  "query": "mutation ScrapeScene($id: ID!, $scraperID: String!) { scrapeScene(sceneID: $id, scraperID: $scraperID) { id title } }",
  "variables": {
    "id": "{{ $json.findScene.id }}",
    "scraperID": "builtin"
  }
}
```

**Input Source:** `Get Scene Details`

**Notes:**
- Uses numeric ID from previous node's output
- Calls Stash's built-in scraper
- Updates scene with enriched metadata

---

### Node 3: Auto-Tag Metadata

**Purpose:** Automatically tag scene with performer/studio info  
**API:** GraphQL mutation  
**Endpoint:** http://192.168.1.147:9999/graphql

**Body (JSON):**
```json
{
  "query": "mutation AutoTag($input: AutoTagInput!) { autoTag(input: $input) { count } }",
  "variables": {
    "input": {
      "ids": ["{{ $json.findScene.id }}"],
      "performers": true,
      "studios": true,
      "tags": true
    }
  }
}
```

**Input Source:** `Get Scene Details`

**Expected Response:**
```json
{
  "autoTag": {
    "count": 5
  }
}
```

---

### Node 4: Queue Transcription (Faster-Whisper)

**Purpose:** Extract audio and transcribe dialogue/sounds  
**API:** REST POST  
**Endpoint:** http://192.168.1.147:10300/transcribe

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "video_path": "{{ $json.files[0].basename }}",
  "language": "en",
  "model_size": "base",
  "device": "cuda"
}
```

**Input Source:** `Get Scene Details`

**Expected Response:**
```json
{
  "status": "queued",
  "job_id": "job_123",
  "estimated_duration_seconds": 120
}
```

**Notes:**
- Processes audio asynchronously
- Returns job ID for tracking
- Results stored for later retrieval

---

### Node 5: Vision Analysis (Ollama)

**Purpose:** Send sample frames to vision LLM for content tagging  
**API:** REST POST  
**Endpoint:** http://192.168.1.147:11434/v1/chat/completions

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "model": "llava:7b",
  "messages": [
    {
      "role": "user",
      "content": "Analyze this adult scene and provide: 1) Main content categories 2) Positions/activities visible 3) Notable elements. Keep response concise."
    }
  ],
  "temperature": 0.7,
  "max_tokens": 300
}
```

**Input Source:** `Get Scene Details`

**Expected Response:**
```json
{
  "choices": [
    {
      "message": {
        "content": "Main content: heterosexual scene. Positions: missionary, cowgirl. Notable: professional production quality"
      }
    }
  ]
}
```

**Notes:**
- Vision model runs on Unraid (llava:7b)
- Processes frames asynchronously
- Results used to tag scene with content categories

---

### Node 6: Queue Transcode (Tdarr)

**Purpose:** Optimize video codec/quality for streaming  
**API:** REST POST  
**Endpoint:** http://192.168.1.139:8265/api/v2/queue

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "file": "{{ $json.path }}",
  "library_id": "1",
  "priority": 5,
  "options": {
    "transcode_to": "h264",
    "target_bitrate": "5000k",
    "target_resolution": "1920x1080"
  }
}
```

**Input Source:** `Get Scene Details`

**Expected Response:**
```json
{
  "success": true,
  "job_id": "tdarr_456",
  "status": "queued"
}
```

**Notes:**
- Routes to z4-media-02 (has Quadro P1000 GPU)
- NVENC hardware transcoding
- Non-blocking (async job submission)

---

## Error Handling (Optional but Recommended)

Add conditional nodes after each HTTP node to handle failures:

**After Get Scene Details:**
```
If error → Log to Stash or Slack
If success → Continue to next node
```

**Configuration:**
- Add "IF" node after HTTP node
- Condition: `$json.errors` exists?
- False branch: Continue workflow
- True branch: Error handler (log/notify)

---

## Testing: Manual Trigger

**Test with webhook POST:**

```bash
curl -X POST http://192.168.1.147:5678/webhook/scene-lifecycle \
  -H "Content-Type: application/json" \
  -d '{
    "id": "123",
    "title": "Test Scene",
    "path": "/mnt/media/scenes/test.mp4"
  }'
```

**Expected Flow:**
1. Webhook receives data
2. Wait node pauses 2 minutes
3. Get Scene Details queries Stash
4. Each subsequent node processes
5. Final status: ✅ All processed or ❌ Error

**Monitor:**
- n8n UI: Execution logs
- Stash: Check scene for updated tags/metadata
- Tdarr: Check queue for transcode job

---

## Troubleshooting Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Cannot read property 'id' of null" | Scene data lost between nodes | Ensure input source is "Wait1", not previous HTTP node |
| "401 Unauthorized" | Stash auth failed | Verify username/password in Node 1 |
| "Connection refused" | Service not running | Check Stash (9999), Ollama (11434), Tdarr (8265) |
| "Timeout after 30s" | Slow network or overloaded service | Increase HTTP timeout in node settings |
| Vision model says "image not provided" | Ollama format issue | Check base_url and model availability |

---

## Next: Validate & Optimize

Once all 6 nodes are configured:

1. **Manual Test:** Trigger with test scene ID
2. **Monitor:** Watch execution logs for errors
3. **Iterate:** Adjust GraphQL queries or API endpoints as needed
4. **Performance:** Measure time per scene (target: <5 min total)
5. **Commit:** `git add . && git commit -m "Phase 1B: Complete HTTP node configuration"`

---

## Success Criteria

- ✅ All 6 nodes configured without errors
- ✅ Workflow executes end-to-end (webhook → transcode queue)
- ✅ Scene data flows through all nodes
- ✅ No timeouts or connection errors
- ✅ Final output matches expected schema
- ✅ Tested with at least 1 real scene ID

---

## Time Estimate

| Task | Time |
|------|------|
| Node 1-3 (GraphQL) | 45 min |
| Node 4-6 (REST APIs) | 45 min |
| Error handling setup | 30 min |
| Testing & iteration | 60 min |
| **Total** | **3-4 hours** |

---

## Files & References

- **Workflow ID:** `oYYQuZXygAejZWac`
- **PHASE_4_N8N_AUTOMATION.md** — All node specs
- **Stash GraphQL Docs:** http://192.168.1.147:9999/graphql (IDE available)
- **n8n Docs:** https://docs.n8n.io/

---

**Status:** Ready to implement  
**Owner:** You  
**Next Step:** Open n8n UI and start with Node 1
