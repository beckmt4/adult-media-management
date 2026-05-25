# Phase 1C — VLM Execution Validation & Monitoring
**Status:** Queued, awaiting execution  
**Objective:** Monitor vision LLM task, verify scene markers, validate tagging accuracy  
**Duration:** 2-4 hours monitoring + analysis  
**Success Criteria:** Scene markers created with >80% tag accuracy

---

## Current State

**Task Status:** Queued on Unraid (since May 16)
- **VLM Model:** llava:7b (4.7 GB)
- **Expected Processing Rate:** ~18 frames per minute
- **Expected Total Time:** 2,964 scenes × (varied frame counts) ≈ 8-12 hours total
- **Target Completion:** May 28-29, 2026

---

## Step 1: SSH to Unraid & Check Status

```bash
ssh -i ~/.codex-ssh/claude_cowork_ed25519 root@192.168.1.147

# Check if Stash container is running
docker ps | grep stash

# List running containers
docker ps | grep -E "stash|ollama"
```

**Expected Output:**
```
stash         /stash                    Up X hours
stash-cdp     /app/chromedp             Up X days
ollama        (Ollama service)          Up X days
```

---

## Step 2: Monitor VLM Task in Stash

### Option A: Via Stash UI

1. Open http://192.168.1.147:9999
2. Go to **Settings** → **Tasks**
3. Look for task named: **"VLM Tag Videos"** or **"Tag Videos"**
4. Check status:
   - `Running` — Task actively processing
   - `Queued` — Waiting to start
   - `Failed` — Error occurred

**Note down:**
- Current progress (frames processed / total)
- Time elapsed
- Processing rate (FPM)
- Any errors in log

### Option B: Via Stash API (GraphQL)

```bash
curl -X POST http://192.168.1.147:9999/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ jobs(status: RUNNING) { id name status progress } }"
  }'
```

**Expected Response:**
```json
{
  "data": {
    "jobs": [
      {
        "id": "job_123",
        "name": "VLM Tag Videos",
        "status": "RUNNING",
        "progress": 45.5
      }
    ]
  }
}
```

### Option C: Via Stash Logs

```bash
# SSH to Unraid
ssh root@192.168.1.147

# View Stash logs
docker logs -f stash 2>&1 | grep -i "vlm\|ollama\|tag"
```

**Look for lines like:**
```
[VLM] Processing scene 123/2964: 78 frames
[VLM] Model llava:7b ready, inference queue depth: 5
[Ollama] http://127.0.0.1:11434/v1 responding
[Plugin] ahavenvlmconnector: Frame 1234/5000 at 18.2 FPM
```

---

## Step 3: Performance Validation

### Baseline Metrics

From prior successful run (May 16):
- **Processing Rate:** 18.3 FPM (frames per minute)
- **Sample Size:** 78 frames in 255.94 seconds
- **Model:** llava:7b
- **GPU:** GTX 1660 Ti (6GB)
- **Expected Total Time:** 2,964 scenes ÷ (avg frames/scene) = ?

### Calculate Expected Completion

```bash
# Example calculation
# If 78 frames took 255.94 sec = 18.3 FPM
# Assume 2,964 scenes × 50 avg frames = 148,200 total frames
# 148,200 ÷ 18.3 FPM = 8,100 minutes = 135 hours ≈ 5.6 days

# Use this formula:
echo "Total frames / 18.3 FPM = minutes to completion"
echo "Scenes: 2964, Est. frames/scene: 50-100"
echo "Low end: (2964 * 50) / 18.3 = $(echo "scale=0; (2964 * 50) / 18.3" | bc) minutes"
echo "High end: (2964 * 100) / 18.3 = $(echo "scale=0; (2964 * 100) / 18.3" | bc) minutes"
```

### Monitor Unraid Resources

```bash
# SSH to Unraid
ssh root@192.168.1.147

# Check GPU usage
nvidia-smi

# Check CPU/Memory
free -h
top -b -n 1 | head -20

# Check Ollama API responsiveness
curl -s http://127.0.0.1:11434/api/tags | jq .
```

**Expected GPU Stats:**
```
GPU Memory:    4.7 GB / 6.0 GB (llava:7b loaded)
GPU Utilization: 85-95% (while processing)
GPU Temp: 65-75°C (normal range)
```

---

## Step 4: Validate Tag Accuracy

Once VLM task completes, validate that scene markers were created correctly.

### Check Scene Markers

```bash
# Via API
curl -X POST http://192.168.1.147:9999/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ findScene(id: \"123\") { scene_markers { title start_time primary_tag { name } } } }"
  }'
```

**Expected Response:**
```json
{
  "findScene": {
    "scene_markers": [
      {
        "title": "Fellatio",
        "start_time": 120,
        "primary_tag": {"name": "Blowjob"}
      },
      {
        "title": "Penetration",
        "start_time": 480,
        "primary_tag": {"name": "Vaginal"}
      }
    ]
  }
}
```

### Manual Validation (Sample 10 Scenes)

1. Pick 10 random scenes with markers
2. Watch 30-60 seconds at marker timestamps
3. Verify tag accuracy:
   - ✅ Accurate (matches video content)
   - ⚠️ Partially accurate (close enough)
   - ❌ Inaccurate (wrong tag)

**Scoring:**
```
Accurate: 8/10 = 80% accuracy ✅ Good
Partially: 1/10 = 10%
Inaccurate: 1/10 = 10%
```

### Sample Validation Script

```bash
#!/bin/bash
# validate_vlm_tags.sh

SAMPLE_SIZE=10
ACCURATE=0
PARTIAL=0
INACCURATE=0

# Get 10 random scene IDs with markers
SCENE_IDS=$(curl -s -X POST http://192.168.1.147:9999/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ findScenes { scenes { id } } }"}' \
  | jq -r '.data.findScenes.scenes[].id' | shuf | head -$SAMPLE_SIZE)

for SCENE_ID in $SCENE_IDS; do
  echo "Checking scene $SCENE_ID..."
  
  # Get markers
  curl -s -X POST http://192.168.1.147:9999/graphql \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"{ findScene(id: \\\"$SCENE_ID\\\") { title scene_markers { title } } }\"}" \
    | jq '.data.findScene'
  
  # Prompt for validation
  read -p "Accuracy? (a=accurate, p=partial, i=inaccurate): " response
  
  case $response in
    a) ((ACCURATE++)) ;;
    p) ((PARTIAL++)) ;;
    i) ((INACCURATE++)) ;;
  esac
done

echo ""
echo "=== Validation Results ==="
echo "Accurate: $ACCURATE/$SAMPLE_SIZE"
echo "Partial: $PARTIAL/$SAMPLE_SIZE"
echo "Inaccurate: $INACCURATE/$SAMPLE_SIZE"
echo "Overall Accuracy: $((ACCURATE * 100 / SAMPLE_SIZE))%"
```

---

## Step 5: Troubleshooting Common Issues

### Issue: Task Not Running

**Symptoms:** Status shows "Queued" after 24+ hours

**Diagnosis:**
```bash
# Check Stash logs for errors
docker logs stash 2>&1 | grep -i "error\|fail\|exception" | tail -20

# Check Ollama availability
curl -s http://127.0.0.1:11434/api/tags

# Check Haven VLM plugin config
cat /mnt/container/appdata/stash/plugins/community/ahavenvlmconnector/haven_vlm_config.py | grep -E "model|base_url"
```

**Solutions:**
1. Restart Stash: `docker restart stash`
2. Verify Ollama running: `docker ps | grep ollama`
3. Check config syntax (no typos in model name)

### Issue: Task Running but No Progress

**Symptoms:** Progress stuck at 0% or very slow (<1 FPM)

**Diagnosis:**
```bash
# Monitor Ollama inference queue
while true; do
  curl -s http://127.0.0.1:11434/api/tags
  sleep 5
done

# Check network between Stash and Ollama
docker exec stash curl -s http://127.0.0.1:11434/api/tags
```

**Solutions:**
1. Check network connectivity: `docker network ls`
2. Increase Ollama timeout: Add `OLLAMA_KEEP_ALIVE=300` to Ollama container
3. Check GPU VRAM: `nvidia-smi` (ensure 4.7+ GB free)

### Issue: "Model not found" Error

**Symptoms:** Logs show `llava:7b not found` or `connection refused`

**Diagnosis:**
```bash
# Check available models
docker exec ollama ollama list

# Check model is loaded
curl http://127.0.0.1:11434/api/tags | jq '.models[] | .name'
```

**Expected Models:**
```
llava:7b
llava:7b-v1.5-q4_K_M
llama3.2:3b
moondream
qwen3.5:4b
```

**Solutions:**
1. Pull model: `docker exec ollama ollama pull llava:7b`
2. Wait for download (2-3 GB, 10-20 min)
3. Restart Stash: `docker restart stash`

### Issue: GPU Memory Errors

**Symptoms:** `CUDA out of memory` or `Out of VRAM`

**Diagnosis:**
```bash
nvidia-smi
# Check: llava:7b needs 4.7 GB, should have 6 GB total
# If used > 5 GB, something else is consuming memory
```

**Solutions:**
1. Close Opera GX (browser GPU usage)
2. Stop competing containers: `docker ps`
3. Limit Ollama load: `export OLLAMA_MAX_LOADED_MODELS=1`

---

## Step 6: Performance Optimization

Once validation passes, optimize for speed:

### Increase Model Batch Size

Edit Haven VLM config:
```python
# /mnt/container/appdata/stash/plugins/community/ahavenvlmconnector/haven_vlm_config.py

"batch_size": 4,  # Process 4 frames simultaneously
"num_workers": 4,  # Use 4 CPU workers
"gpu_queue_depth": 10,  # Queue up to 10 requests
```

### Monitor Final Metrics

Once task completes:
```bash
# Get final statistics
curl -X POST http://192.168.1.147:9999/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{
      sceneCount: findScenes { count }
      scenesWithMarkers: findScenes(filter: {has_markers: true}) { count }
    }"
  }'
```

**Expected Output:**
```json
{
  "sceneCount": 2964,
  "scenesWithMarkers": 2500+  // >80% coverage
}
```

---

## Success Checklist

- ✅ VLM task starts and shows progress
- ✅ Processing rate ≥ 15 FPM
- ✅ No CUDA memory errors
- ✅ Scene markers created automatically
- ✅ Manual validation: 80%+ accuracy
- ✅ Completion time <72 hours
- ✅ GPU stays <75°C (thermal safe)

---

## Next Phase (After Validation)

Once VLM completes with >80% accuracy:
1. Move to Phase 1 Final: Media server integration
2. Test NFO generation
3. Validate Jellyfin/Plex metadata import
4. Release v0.2.0 (Phase 2 start)

---

## Monitoring Commands Quick Reference

```bash
# SSH to Unraid
ssh -i ~/.codex-ssh/claude_cowork_ed25519 root@192.168.1.147

# Check task status
curl -s http://192.168.1.147:9999/graphql -H "Content-Type: application/json" \
  -d '{"query":"{jobs(status:RUNNING){name status progress}}"}' | jq .

# Monitor GPU in real-time
watch -n 1 nvidia-smi

# Monitor Stash logs
docker logs -f stash 2>&1 | grep vlm

# Check Ollama queue
curl -s http://127.0.0.1:11434/api/tags | jq .

# Final scene count with markers
curl -s http://192.168.1.147:9999/graphql -H "Content-Type: application/json" \
  -d '{"query":"{sceneCount:findScenes{count} withMarkers:findScenes(filter:{has_markers:true}){count}}"}' | jq .
```

---

**Timeline:** May 25-29, 2026  
**Owner:** You  
**Next Action:** Monitor task daily, validate completion by May 29
