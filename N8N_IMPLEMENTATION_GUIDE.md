# Phase 4 n8n Implementation Guide

**Status:** Workflow foundation laid, ready for completion  
**Date:** 2026-05-15  
**Workflow ID:** oYYQuZXygAejZWac

---

## What's Been Completed ✅

### 1. **Webhook Trigger Node**
- ✅ HTTP Method: POST
- ✅ Path: `scene-lifecycle`
- ✅ Test URL: `http://192.168.1.147:5678/webhook-test/scene-lifecycle`
- ✅ Production URL: `http://192.168.1.147:5678/webhook/scene-lifecycle`
- ✅ Ready for Stash integration

### 2. **Wait Node**
- ✅ Duration: 2 minutes
- ✅ Unit: Minutes
- ✅ Purpose: Allow file to settle on disk before processing

### 3. **HTTP Request Node (Started)**
- ✅ Method: POST
- ✅ URL: http://192.168.1.147:9999/graphql
- ⏳ Still needs: Authentication, Headers, Body configuration

---

## Next Steps: Quick Integration Path

### Step 1: Configure Stash Webhook (5 minutes)

Navigate to **Stash → Settings → Integrations → Webhooks**

Click **Add Webhook** and configure:
- **Event:** `scene.create` and `scene.update`
- **URL:** `http://192.168.1.147:5678/webhook/scene-lifecycle`
- **Method:** POST
- **Test:** Create a new scene in Stash, verify webhook fires in n8n

### Step 2: Complete HTTP Request Node Configuration

In n8n, edit the HTTP Request node and add:

**Authentication:**
- Type: Basic
- Username: `root`
- Password: `qlx9_adM`

**Headers (toggle "Send Headers" ON):**
```
Content-Type: application/json
```

**Body (toggle "Send Body" ON):**
```json
{
  "query": "query GetSceneDetails($id: ID!) { findScene(id: $id) { id title path performers { id name } studios { id name } stash_ids rating duration } }",
  "variables": {
    "id": "{{ $json.id }}"
  }
}
```

### Step 3: Add Remaining Nodes

Refer to `PHASE_4_N8N_AUTOMATION.md` for complete specifications. The remaining 13 nodes are:

1. **Conditional Check** - Verify scene has no StashDB ID
2. **Scrape Metadata** - HTTP POST to Stash scrape mutation
3. **Auto-Tag** - HTTP POST for metadataAutoTag mutation
4. **Performer Image Check** - Conditional, check performer images
5. **Actress Library Task** - HTTP POST for plugin execution
6. **Transcription Request** - HTTP POST to Faster-Whisper API
7. **Store Transcript** - HTTP POST scene update mutation
8. **Vision Analysis** - HTTP POST to Ollama llava:13b
9. **Apply AI Tags** - HTTP POST scene update with tags
10. **Queue Transcode** - HTTP POST to tdarr API
11. **Generate NFO** - HTTP POST to mcMetadata
12. **Success Notification** - Webhook to notification service
13. **Error Handler** - Catch and log errors

---

## Alternative: API-Based Completion

For efficiency, use the n8n API to import a complete workflow definition:

```bash
# Export current workflow
curl -X GET http://192.168.1.147:5678/api/v1/workflows/oYYQuZXygAejZWac \
  -H "X-N8N-API-KEY: [your-api-key]"

# Import complete workflow (use PHASE_4_N8N_AUTOMATION.md JSON template)
curl -X POST http://192.168.1.147:5678/api/v1/workflows \
  -H "Content-Type: application/json" \
  -H "X-N8N-API-KEY: [your-api-key]" \
  -d @workflow.json
```

---

## Testing Commands

Once workflow is complete, test with:

```bash
# Test webhook trigger
curl -X POST http://192.168.1.147:5678/webhook-test/scene-lifecycle \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-scene-123",
    "title": "Test Scene",
    "path": "/mnt/data/scenes/test.mp4"
  }'

# Test Stash GraphQL endpoint directly
curl -X POST http://192.168.1.147:9999/graphql \
  -H "Authorization: Basic $(echo -n 'root:qlx9_adM' | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { findScenes(input: {size: 1}) { scenes { id title } } }"
  }'

# Test Faster-Whisper endpoint
curl -X POST http://192.168.1.147:10300/api/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "audio_path": "/path/to/audio.m4a",
    "language": "ja",
    "format": "srt"
  }'

# Test Ollama vision model
curl -X POST http://192.168.1.182:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llava:13b",
    "prompt": "Analyze this scene",
    "stream": false
  }'
```

---

## Implementation Timeline

| Phase | Task | Duration | Blocker |
|-------|------|----------|---------|
| **Now** | Webhook config in Stash | 5 min | None |
| **Phase 1** | Complete HTTP nodes (6-10) | 45 min | Basic auth patterns |
| **Phase 2** | Add conditional logic (1-2) | 30 min | GraphQL queries |
| **Phase 3** | Integration nodes (11-13) | 30 min | API endpoints |
| **Phase 4** | Error handling & testing | 30 min | None |
| **Total** | End-to-end completion | ~2 hours | None critical |

---

## Key Reference Files

- **PHASE_4_N8N_AUTOMATION.md** — Complete node-by-node specification with all GraphQL queries
- **WEEK_1_PROGRESS_2026-05-15.md** — Execution timeline and infrastructure status
- **MASTER_PLAN.md** — Overall project architecture

---

## Critical Configuration Values

| Component | Endpoint | Auth | Notes |
|-----------|----------|------|-------|
| **Stash GraphQL** | http://192.168.1.147:9999/graphql | Basic (root:qlx9_adM) | Core metadata source |
| **Ollama Vision** | http://192.168.1.182:11434/api/generate | None | Workstation RTX 4090 |
| **Faster-Whisper** | http://192.168.1.147:10300/api/transcribe | None | Japanese priority |
| **Qdrant** | http://192.168.1.147:6333 | None | Vector embeddings |
| **tdarr** | http://192.168.1.147:8265/api/v2 | Optional | Transcode queue |

---

## Success Criteria

- [ ] Webhook receives scene.create/update events from Stash
- [ ] Workflow executes without errors for 5 consecutive scenes
- [ ] Average scene processing < 5 minutes (excluding performer scraping)
- [ ] All metadata applied to scene successfully
- [ ] Transcripts generated for 90%+ of scenes
- [ ] AI tags applied and visible in Stash
- [ ] NFO files generated and stored

---

## Next Session Plan

**Monday (May 19):**
1. Configure Stash webhook (5 min) ← **Start here**
2. Complete HTTP node configurations (30 min)
3. Test single scene end-to-end (15 min)

**Remaining phase 4 implementation:** ~90 minutes

---

**Prepared by:** Claude (Cowork Mode)  
**Workflow URL:** http://192.168.1.147:5678/workflow/oYYQuZXygAejZWac  
**Next Review:** After Stash webhook configuration
