# Phase 2 — Media Server Integration Test Suite
**Status:** Ready to test (depends on Phase 1B/1C completion)  
**Objective:** Validate NFO generation, metadata import, and Jellyfin/Plex display  
**Duration:** 2-4 hours testing  
**Success Criteria:** Metadata visible in both media servers

---

## Prerequisites

Before starting Phase 2 tests:
- ✅ Phase 1A complete (Stash auth working)
- ✅ Phase 1B complete (n8n HTTP nodes configured)
- ✅ Phase 1C complete (VLM task finished, markers created)
- ✅ mcMetadata plugin enabled in Stash
- ✅ Jellyfin & Plex running and accessible

**Verify:**
```bash
# Check mcMetadata plugin
curl -X POST http://192.168.1.147:9999/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{plugins{name version}}"}' | jq .

# Should include: mcMetadata (v1.4.0 or higher)
```

---

## Architecture: How NFO Files Flow

```
Stash Scene
    ↓
[mcMetadata Plugin] ← On scene update
    ↓
Generate NFO XML File
    ↓
Write to: /path/to/media/scene.nfo
    ↓
Jellyfin Library Scan
    ↓
Import NFO Metadata
    ↓
Display in UI with Poster, Plot, Performers
```

---

## Test 1: NFO File Generation

**Objective:** Verify mcMetadata creates NFO files when scene is updated

### Setup

1. **Select test scene:**
   ```bash
   # Pick a real scene ID from Stash
   curl -s http://192.168.1.147:9999/graphql \
     -H "Content-Type: application/json" \
     -d '{"query":"{findScenes(limit:1){scenes{id title path}}}"}' | jq .
   ```

   **Example Output:**
   ```json
   {
     "id": "42",
     "title": "Sample Scene",
     "path": "/mnt/itv/media/scene_42.mp4"
   }
   ```

2. **Find NFO path:**
   ```bash
   # NFO should be: /mnt/itv/media/scene_42.nfo
   # (same directory, same name, .nfo extension)
   ```

### Execute Test

**Option A: Trigger via n8n Workflow**

```bash
# Send scene through n8n workflow
curl -X POST http://192.168.1.147:5678/webhook/scene-lifecycle \
  -H "Content-Type: application/json" \
  -d '{
    "id": "42",
    "title": "Sample Scene",
    "path": "/mnt/itv/media/scene_42.mp4"
  }'
```

**Option B: Update Scene Directly in Stash**

1. Open http://192.168.1.147:9999
2. Edit scene #42
3. Change any field (e.g., add a tag)
4. Click "Save"
5. This triggers mcMetadata plugin

### Validation

**Check if NFO file was created:**

```bash
# SSH to Unraid
ssh root@192.168.1.147

# List directory with NFO files
ls -la /mnt/itv/media/ | grep "\.nfo"

# Check specific scene
ls -la /mnt/itv/media/scene_42.nfo
```

**Expected Output:**
```
-rw-r--r-- 1 root root 2541 May 25 10:30 scene_42.nfo
```

### Inspect NFO Content

```bash
# View NFO file
cat /mnt/itv/media/scene_42.nfo
```

**Expected Structure:**
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<movie>
  <title>Sample Scene</title>
  <plot>Scene description with tags and performers</plot>
  <year>2026</year>
  <runtime>30</runtime>
  <actor>
    <name>Performer Name 1</name>
    <role>Actor</role>
  </actor>
  <actor>
    <name>Performer Name 2</name>
    <role>Actor</role>
  </actor>
  <studio>Studio Name</studio>
  <tag>Blowjob</tag>
  <tag>Vaginal</tag>
  <rating>8.5</rating>
  <thumb aspect="poster" type="Season">http://192.168.1.147:9999/image</thumb>
</movie>
```

**Validation Checklist:**
- ✅ Title matches scene title
- ✅ Plot includes scene description
- ✅ All performers listed
- ✅ Studio included
- ✅ Tags from scene_markers included
- ✅ Rating populated
- ✅ Image URL points to valid Stash endpoint

---

## Test 2: Jellyfin Metadata Import

**Objective:** Verify Jellyfin reads NFO and displays metadata

### Setup

1. **Add library path to Jellyfin** (if not already done)
   - Open http://192.168.1.147:8096 (Jellyfin admin)
   - Settings → Libraries → Add Library
   - Library Type: "Movies"
   - Folders: `/mnt/itv/media` or `/mnt/media` (wherever scenes are stored)
   - Save

2. **Ensure NFO is in library path:**
   ```bash
   # Jellyfin must be able to read files
   # Check permissions
   ssh root@192.168.1.147
   ls -la /mnt/itv/media/scene_42.nfo
   # Should be readable by Jellyfin container user
   ```

### Execute Test

**Trigger Library Scan:**

1. Go to http://192.168.1.147:8096
2. Admin → Settings → Libraries
3. Select library with scene files
4. Click "Scan All Libraries" (or library name)
5. Wait for scan to complete (may take 5-10 min)

**Alternative: Force Scan via API**

```bash
# Jellyfin API (requires admin token)
curl -X POST http://192.168.1.147:8096/Library/Refresh \
  -H "X-MediaBrowser-Token: YOUR_JELLYFIN_API_KEY"
```

### Validation

**Check Jellyfin for Imported Metadata:**

1. Navigate to library in Jellyfin UI
2. Find scene "Sample Scene"
3. Click to view details

**Expected Display:**
- ✅ Scene title
- ✅ Plot/description
- ✅ Performers listed
- ✅ Studio name
- ✅ Genre/tags
- ✅ Rating (if applicable)
- ✅ Poster image (if URL accessible)
- ✅ Runtime (duration)

**Also check via API:**

```bash
# Search for imported scene
curl -s "http://192.168.1.147:8096/Items?searchTerm=Sample%20Scene" \
  | jq '.Items[] | {Name, Overview, RunTimeTicks, People}'
```

**Expected Output:**
```json
{
  "Name": "Sample Scene",
  "Overview": "Scene description...",
  "RunTimeTicks": 1800000000,
  "People": [
    {"Name": "Performer 1", "Role": "Actor"},
    {"Name": "Performer 2", "Role": "Actor"}
  ]
}
```

---

## Test 3: Plex Metadata Import

**Objective:** Verify Plex reads NFO and displays metadata

### Setup

1. **Add library to Plex** (if not already done)
   - Open http://192.168.1.147:32400/web
   - Settings → Manage → Libraries
   - Add Library → Movies
   - Folders: `/mnt/itv/media` or wherever scenes stored
   - Save

2. **Verify NFO location:**
   ```bash
   ssh root@192.168.1.147
   ls -la /mnt/itv/media/*.nfo | head -5
   ```

### Execute Test

**Trigger Library Refresh:**

1. Open http://192.168.1.147:32400/web
2. Settings → Libraries
3. Click library name
4. "..." menu → Scan Library Files
5. Wait for scan to complete

**Alternative: Force via API**

```bash
# Plex API (requires access token)
curl -X POST "http://192.168.1.147:32400/library/sections/ID/refresh" \
  -H "X-Plex-Token: YOUR_PLEX_TOKEN"
```

### Validation

**Check Plex for Imported Metadata:**

1. Navigate to library in Plex UI
2. Find "Sample Scene" in collection
3. Click to view details

**Expected Display:**
- ✅ Scene title
- ✅ Summary/plot
- ✅ Performers (cast list)
- ✅ Studio name
- ✅ Genres/tags
- ✅ Rating/score
- ✅ Poster art
- ✅ Duration

**Also check via Tautulli** (if available):

```bash
# Tautulli shows Plex library stats
curl -s "http://192.168.1.147:8181/api/v2/get_libraries" \
  | jq '.response.data[] | {section_name, count}'
```

---

## Test 4: End-to-End Workflow

**Objective:** Full automation test from scene creation through media server display

### Setup

1. Select an unprocessed scene from Stash
2. Ensure it's accessible in media libraries

### Execute

**Step 1: Trigger n8n Workflow**

```bash
curl -X POST http://192.168.1.147:5678/webhook/scene-lifecycle \
  -H "Content-Type: application/json" \
  -d '{
    "id": "999",
    "title": "End-to-End Test Scene",
    "path": "/mnt/itv/media/test_e2e.mp4"
  }'
```

**Step 2: Monitor Workflow Execution**

- Go to n8n UI: http://192.168.1.147:5678 (if accessible)
- View workflow execution logs
- Should see:
  - Webhook received
  - Scene details fetched
  - Metadata scraped
  - Auto-tags applied
  - NFO generated
  - Transcode queued

**Step 3: Verify NFO Creation**

```bash
# Check NFO exists within 5 minutes
ssh root@192.168.1.147
sleep 10
ls -la /mnt/itv/media/test_e2e.nfo
cat /mnt/itv/media/test_e2e.nfo | head -20
```

**Step 4: Trigger Media Server Scans**

```bash
# Jellyfin
curl -X POST http://192.168.1.147:8096/Library/Refresh

# Plex (if API key available)
curl -X POST "http://192.168.1.147:32400/library/sections/1/refresh"
```

**Step 5: Verify Display in Media Servers**

1. Open Jellyfin: http://192.168.1.147:8096
   - Library → Movies
   - Search: "End-to-End Test Scene"
   - Check metadata

2. Open Plex: http://192.168.1.147:32400/web
   - Library
   - Search: "End-to-End Test Scene"
   - Check metadata

### Expected Timeline

| Step | Time | Status |
|------|------|--------|
| Webhook → NFO | 1-2 min | ✅ Immediate |
| NFO → Jellyfin | 5-10 min | After library scan |
| NFO → Plex | 5-10 min | After library scan |
| **Total E2E** | **15-20 min** | ✅ Acceptable |

---

## Test 5: Performance & Scalability

**Objective:** Validate workflow handles multiple scenes without bottlenecks

### Test Batch Processing

```bash
#!/bin/bash
# batch_test.sh - Send 10 scenes through workflow

for i in {1..10}; do
  curl -X POST http://192.168.1.147:5678/webhook/scene-lifecycle \
    -H "Content-Type: application/json" \
    -d "{
      \"id\": \"$((1000 + i))\",
      \"title\": \"Batch Test Scene $i\",
      \"path\": \"/mnt/itv/media/batch_$i.mp4\"
    }"
  
  echo "Queued scene $i"
  sleep 2  # Stagger requests
done

echo "Batch test complete. Monitor n8n for execution status."
```

### Monitor Performance

```bash
# Check n8n queue depth
curl -s http://192.168.1.147:5678/api/v1/workflows \
  | jq '.data[] | {name, active}'

# Monitor Unraid resources
ssh root@192.168.1.147
watch -n 2 'docker stats --no-stream | grep -E "stash|ollama|n8n"'
```

**Expected Results:**
- ✅ All 10 scenes processed
- ✅ No dropped jobs
- ✅ Consistent 1-2 min per scene
- ✅ CPU/Memory/GPU stable

---

## Test 6: Error Handling

**Objective:** Verify workflow recovers from errors gracefully

### Test Invalid Scene ID

```bash
# Try with non-existent scene
curl -X POST http://192.168.1.147:5678/webhook/scene-lifecycle \
  -H "Content-Type: application/json" \
  -d '{
    "id": "99999999",
    "title": "Non-Existent Scene",
    "path": "/invalid/path.mp4"
  }'
```

**Expected Behavior:**
- ✅ Workflow logs error
- ✅ Error handler catches it
- ✅ Sends notification (if configured)
- ✅ Workflow continues (doesn't crash)

### Test with Missing Media File

```bash
# Scene doesn't exist on disk
curl -X POST http://192.168.1.147:5678/webhook/scene-lifecycle \
  -H "Content-Type: application/json" \
  -d '{
    "id": "42",
    "title": "Missing File Scene",
    "path": "/mnt/media/nonexistent_file.mp4"
  }'
```

**Expected Behavior:**
- ✅ Transcoding step fails gracefully
- ✅ Other steps still complete
- ✅ Metadata/NFO still generated
- ✅ Error logged for review

---

## Test 7: Performer Gallery Integration

**Objective:** Verify performer galleries display with rich metadata

### Setup

1. Ensure mcMetadata plugin has gallery sync enabled
2. Verify performer records have images (from Phase 1A enrichment)

### Execute

```bash
# Query performer with gallery
curl -X POST http://192.168.1.147:9999/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{
      findPerformer(id: \"1\") {
        name
        images { url }
        scenes { count }
        galleries { id title }
      }
    }"
  }'
```

**Expected Output:**
```json
{
  "findPerformer": {
    "name": "Performer Name",
    "images": [{"url": "http://...performer.jpg"}],
    "scenes": {"count": 42},
    "galleries": [{"id": "1", "title": "Gallery Name"}]
  }
}
```

### Verify in Media Servers

**Jellyfin:**
1. Browse → People
2. Click performer name
3. View gallery and scene list

**Plex:**
1. Search → Performers
2. Click performer
3. View profile, image, and related content

---

## Success Checklist

- ✅ NFO files created automatically
- ✅ Jellyfin imports and displays metadata
- ✅ Plex imports and displays metadata
- ✅ Performers display in media servers
- ✅ End-to-end workflow <20 minutes
- ✅ No data loss or corruption
- ✅ Error handling works correctly
- ✅ Performance acceptable (no timeouts)

---

## Troubleshooting Common Issues

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| NFO not created | Check mcMetadata logs | Enable plugin logging, restart Stash |
| Jellyfin can't find NFO | NFO in wrong location | Verify path matches media file location |
| Metadata not importing | Library not scanned | Manually trigger library scan |
| Performers not linked | Missing actor nodes in NFO | Check NFO `<actor>` tags |
| Image not displaying | URL invalid | Verify Stash image endpoint accessible |
| Workflow timeout | Service overloaded | Increase HTTP timeout in n8n nodes |

---

## Next Steps

After passing all tests:
1. ✅ Commit test results: `git commit -m "Phase 2: Media server integration validated"`
2. ✅ Update documentation with results
3. ✅ Tag release: `git tag v0.2.0`
4. ✅ Begin Phase 3: Performer enrichment at scale

---

**Timeline:** ~2-4 hours testing  
**Owner:** You  
**Success Criteria:** All 7 tests pass  
**Next Phase:** Phase 3 (Performer Enrichment Scale)
