# Phase 1 Container Migration Playbook
**Target:** Move n8n and Qdrant from Unraid to z4-media-01  
**Date:** 2026-05-14  
**Estimated Duration:** 90 minutes  
**Risk Level:** Low (both services have no persistent state dependencies on Unraid)

---

## Pre-Migration Checklist

- [ ] z4-media-01 (192.168.1.10) is reachable via SSH
- [ ] Backup current n8n workflow (manual export from UI)
- [ ] Backup Qdrant embeddings directory
- [ ] Document current Stash GraphQL endpoint URL
- [ ] Verify z4-media-01 has Docker installed
- [ ] Create /opt/n8n and /opt/qdrant directories on z4-media-01
- [ ] Confirm 50GB+ free space on z4-media-01

---

## Phase 1A: n8n Migration

### Step 1: Export n8n Workflow from Unraid

**On Unraid (via SSH or UI):**

```bash
# Option A: Via API (if you have n8n API key)
curl -X GET http://192.168.1.147:5678/api/v1/workflows/oYYQuZXygAejZWac \
  -H "X-N8N-API-KEY: [your-api-key]" \
  -H "Content-Type: application/json" | jq . > /tmp/n8n_workflow_backup.json

# Option B: Via UI (preferred if you don't have API key)
# 1. Go to n8n: http://192.168.1.147:5678
# 2. Open workflow "oYYQuZXygAejZWac"
# 3. Menu → Download as JSON
# 4. Save to: /tmp/n8n_workflow_backup.json
```

**Expected output:**
```json
{
  "name": "Scene Lifecycle Automation",
  "nodes": [
    { "name": "Webhook Trigger", ... },
    { "name": "Wait", ... },
    ...
  ]
}
```

### Step 2: Stop n8n on Unraid

```bash
# SSH to Unraid
ssh root@192.168.1.147

# Stop the container
docker stop n8n

# Verify it's stopped
docker ps | grep n8n
# (should return empty)
```

### Step 3: Export n8n Volume Data

```bash
# On Unraid, locate n8n volume
docker inspect n8n --format='{{json .Mounts}}' | jq .

# Look for Source path (typically /mnt/user/appdata/n8n or similar)
# Example: "Source": "/mnt/user/appdata/n8n"

# Create backup archive
docker run --rm -v /mnt/user/appdata/n8n:/n8n_data \
  -v /tmp:/backup ubuntu tar czf /backup/n8n_data.tar.gz -C /n8n_data .

# Verify backup
ls -lh /tmp/n8n_data.tar.gz
```

### Step 4: Copy n8n Data to z4-media-01

```bash
# From Unraid, SCP to z4-media-01
scp /tmp/n8n_data.tar.gz mbeck@192.168.1.10:/tmp/

# Verify transfer
ssh mbeck@192.168.1.10 "ls -lh /tmp/n8n_data.tar.gz"
```

### Step 5: Set Up n8n on z4-media-01

```bash
# SSH to z4-media-01
ssh mbeck@192.168.1.10

# Create app data directory
sudo mkdir -p /opt/n8n/data
sudo chown -R $USER:$USER /opt/n8n

# Extract backup
cd /opt/n8n && tar xzf /tmp/n8n_data.tar.gz

# Create docker-compose.yml for n8n
cat > /opt/n8n/docker-compose.yml << 'EOF'
version: '3.8'
services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=192.168.1.10
      - N8N_PORT=5678
      - NODE_ENV=production
      - WEBHOOK_URL=http://192.168.1.10:5678/
      - GENERIC_TIMEZONE=America/Los_Angeles
    volumes:
      - ./data:/home/node/.n8n
    networks:
      - n8n_net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5678/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  n8n_net:
    driver: bridge
EOF

# Start n8n
docker-compose -f /opt/n8n/docker-compose.yml up -d

# Wait 30 seconds for startup
sleep 30

# Verify health
curl http://192.168.1.10:5678/api/v1/health
# Expected: HTTP 200 with JSON response
```

### Step 6: Verify n8n on z4-media-01

```bash
# Check logs
docker logs n8n | tail -20

# Test webhook endpoint
curl -X POST http://192.168.1.10:5678/webhook/scene-lifecycle \
  -H "Content-Type: application/json" \
  -d '{
    "id": "migration-test-123",
    "title": "Migration Test",
    "path": "/mnt/data/scenes/test.mp4"
  }'

# Expected response: HTTP 200 "Workflow was started"
```

### Step 7: Update Workflow Endpoint References

If any other systems call n8n webhook, update them:

```bash
# Old endpoint: http://192.168.1.147:5678/webhook/scene-lifecycle
# New endpoint: http://192.168.1.10:5678/webhook/scene-lifecycle

# If Stash has webhook config pointing to old endpoint, update it
# (via Stash config file or manual re-entry if UI doesn't expose webhooks)
```

### Step 8: Clean Up n8n on Unraid

Once verified working on z4, remove from Unraid:

```bash
# SSH to Unraid
ssh root@192.168.1.147

# Remove container
docker rm n8n

# Remove volume (optional - keep if you want a backup)
docker volume rm n8n
# OR keep it for rollback:
# docker volume ls | grep n8n
```

---

## Phase 1B: Qdrant Migration

### Step 1: Backup Qdrant Embeddings

```bash
# On Unraid
ssh root@192.168.1.147

# Locate Qdrant volume
docker inspect qdrant --format='{{json .Mounts}}' | jq .

# Create backup (Qdrant stores vectors in /qdrant/storage)
docker run --rm -v /mnt/user/appdata/qdrant:/qdrant_data \
  -v /tmp:/backup ubuntu tar czf /backup/qdrant_data.tar.gz -C /qdrant_data .

# Verify
ls -lh /tmp/qdrant_data.tar.gz
```

### Step 2: Stop Qdrant on Unraid

```bash
# Stop container
docker stop qdrant
docker wait qdrant

# Verify stopped
docker ps | grep qdrant
```

### Step 3: Copy Qdrant Data to z4-media-01

```bash
# From Unraid
scp /tmp/qdrant_data.tar.gz mbeck@192.168.1.10:/tmp/

# Verify on z4
ssh mbeck@192.168.1.10 "ls -lh /tmp/qdrant_data.tar.gz"
```

### Step 4: Set Up Qdrant on z4-media-01

```bash
# SSH to z4-media-01
ssh mbeck@192.168.1.10

# Create directory
sudo mkdir -p /opt/qdrant/storage
sudo chown -R $USER:$USER /opt/qdrant

# Extract backup
cd /opt/qdrant && tar xzf /tmp/qdrant_data.tar.gz

# Create docker-compose entry (append to existing n8n compose, or standalone)
cat > /opt/qdrant/docker-compose.yml << 'EOF'
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    restart: always
    ports:
      - "6333:6333"
    volumes:
      - ./storage:/qdrant/storage
    environment:
      - QDRANT_API_KEY=qdrant-key-12345
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3
EOF

# Start Qdrant
docker-compose -f /opt/qdrant/docker-compose.yml up -d

# Wait 30 seconds
sleep 30

# Verify health
curl http://192.168.1.10:6333/health
# Expected: HTTP 200 with uptime info
```

### Step 5: Update n8n to Point to New Qdrant Endpoint

**In n8n Workflow:**
- Any Qdrant nodes pointing to `192.168.1.147:6333` → change to `192.168.1.10:6333`
- Test one Qdrant query node to verify connectivity

```bash
# Quick test from z4
curl -X POST http://192.168.1.10:6333/collections \
  -H "Content-Type: application/json" \
  -d '{"query": ""}'
# Expected: Collections list
```

### Step 6: Clean Up Qdrant on Unraid

```bash
# On Unraid
ssh root@192.168.1.147

# Remove container
docker rm qdrant

# Remove volume (optional - keep for rollback)
# docker volume rm qdrant
```

---

## Validation Checklist

### Immediate Tests (Right After Migration)

```bash
# Test 1: n8n webhook receives data
curl -X POST http://192.168.1.10:5678/webhook/scene-lifecycle \
  -H "Content-Type: application/json" \
  -d '{"id":"val-test-1","title":"Validation Test","path":"/test.mp4"}'
# Expected: HTTP 200 ✅

# Test 2: Qdrant responds to collection query
curl http://192.168.1.10:6333/collections
# Expected: JSON with collections ✅

# Test 3: n8n can reach Stash
curl -X POST http://192.168.1.147:9999/graphql \
  -H "Authorization: Basic $(echo -n 'root:qlx9_adM' | base64)" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ version }"}'
# Expected: Version string ✅

# Test 4: Check z4-media-01 network load
ssh mbeck@192.168.1.10 "iftop -n -t -s 5 | head -20"
# Expected: Minimal traffic (< 1 MB/s) ✅
```

### 24-Hour Validation (Run Next Day)

- [ ] Both containers still running: `docker ps | grep -E 'n8n|qdrant'`
- [ ] No restart loops: `docker ps --format "{{.Names}} {{.Status}}"` (Status should not show many restarts)
- [ ] Check Unraid logs for any references to missing n8n/Qdrant
- [ ] Verify n8n workflow executions in logs

---

## Rollback Plan (If Something Breaks)

### Rollback n8n (Back to Unraid)

```bash
# Step 1: Stop n8n on z4
ssh mbeck@192.168.1.10 "docker-compose -f /opt/n8n/docker-compose.yml down"

# Step 2: Restore n8n container on Unraid
ssh root@192.168.1.147 "docker start n8n"

# Step 3: Verify Unraid n8n is up
curl http://192.168.1.147:5678/api/v1/health

# Done - webhook endpoint reverts to .147
```

### Rollback Qdrant (Back to Unraid)

```bash
# Similar to n8n:
ssh mbeck@192.168.1.10 "docker-compose -f /opt/qdrant/docker-compose.yml down"
ssh root@192.168.1.147 "docker start qdrant"
curl http://192.168.1.147:6333/health
```

---

## Network Configuration (Optional but Recommended)

To make z4-media-01 endpoints easier to reference, you can add DNS entries:

```bash
# On your local network DNS (if available), or in /etc/hosts on machines that need it:
192.168.1.10  z4-media-01 n8n.local qdrant.local
```

Then use: `http://n8n.local:5678/webhook/scene-lifecycle` instead of IP address.

---

## Post-Migration Tasks

After Phase 1 is stable (24 hours):

1. **Consider Phase 2:** Move tdarr agent to z4-media-02 if GPU acceleration needed
2. **Monitor Unraid load:** CPU/RAM should drop noticeably
3. **Update documentation:** Point all internal references to new .10 endpoints
4. **Archive old backups:** Keep n8n/Qdrant volumes on Unraid for 1-2 weeks, then remove

---

## Timeline Estimate

| Task | Duration | Notes |
|------|----------|-------|
| Export n8n workflow + data | 10 min | Mostly waiting for docker |
| Stop n8n, backup, copy to z4 | 15 min | SCP transfer ~10 min |
| Set up n8n on z4, verify | 20 min | Docker pull, start, health check |
| Export Qdrant data, copy | 15 min | Similar to n8n |
| Set up Qdrant on z4, verify | 15 min | Smaller than n8n |
| Update n8n config + test | 10 min | Change Qdrant endpoint, test query |
| Cleanup on Unraid | 5 min | Remove containers, keep volumes |
| **Total** | **~90 min** | Most time is docker pull/startup |

---

## Success Criteria

✅ **Phase 1 is complete when:**
1. n8n webhook receives test events on 192.168.1.10:5678 (not .147)
2. Qdrant collections accessible from 192.168.1.10:6333 (not .147)
3. n8n workflow execution logs show no errors fetching from Qdrant
4. Stash can still reach both services (verify GraphQL queries work)
5. No restart loops or crashes in 24-hour observation period

---

## Emergency Contacts / Notes

**If n8n workflow endpoint breaks during migration:**
- Old URL: `http://192.168.1.147:5678/webhook/scene-lifecycle`
- New URL: `http://192.168.1.10:5678/webhook/scene-lifecycle`
- Temporary: Use curl to re-trigger webhook from z4:
  ```bash
  curl -X POST http://192.168.1.10:5678/webhook/scene-lifecycle \
    -H "Content-Type: application/json" \
    -d '{"id":"scene-id","title":"title","path":"/path"}'
  ```

**If Qdrant data doesn't restore:**
- Backup location: `/tmp/qdrant_data.tar.gz` (on z4-media-01)
- Can re-extract: `cd /opt/qdrant && tar xzf /tmp/qdrant_data.tar.gz`
- Or rollback to Unraid and retry with fresh backup

---

**Prepared by:** Claude  
**Date:** 2026-05-14  
**Next Action:** Execute Phase 1A (n8n migration) starting with workflow export  
**Estimated Completion:** 2026-05-14 Evening (or 2026-05-15 if starting tomorrow)

