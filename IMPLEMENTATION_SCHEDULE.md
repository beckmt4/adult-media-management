# Implementation Schedule: May 25 - July 5, 2026
**Objective:** Complete Adult Media Management Platform v1.0.0  
**Timeline:** 6 weeks (42 days)  
**Target Release:** July 5, 2026

---

## Week 1: Phase 1B Completion (May 25-31)

### Monday, May 25 (Today)
- ✅ **DONE:** Project assessment completed
- ✅ **DONE:** GitHub repository created & synced
- ✅ **DONE:** Documentation & guides prepared
- **TODO:** Begin n8n Phase 1B configuration

**Time Estimate:** 6-8 hours hands-on
**Deliverables:** All 6 HTTP nodes configured

### Tuesday-Wednesday, May 26-27
**Focus:** Configure HTTP Nodes 1-3 (GraphQL Queries)

**Daily Goal:** 2 hours each day

**Node 1: Get Scene Details**
- [ ] Open n8n workflow: http://192.168.1.10:5678
- [ ] Add HTTP node after Wait1
- [ ] Configure GraphQL endpoint (http://192.168.1.147:9999/graphql)
- [ ] Add query with expanded fields (performers, studios, tags, duration, rating)
- [ ] Test with scene ID 123
- [ ] Verify response structure
- [ ] **Time:** 45 min

**Node 2: Scrape Metadata**
- [ ] Add HTTP node after Node 1
- [ ] Configure scrape mutation
- [ ] Set input source to Node 1 output
- [ ] Test execution
- [ ] **Time:** 30 min

**Node 3: Auto-Tag**
- [ ] Add HTTP node after Node 2
- [ ] Configure autoTag mutation
- [ ] Map scene ID from previous node
- [ ] Test execution
- [ ] **Time:** 30 min

### Thursday-Friday, May 28-29
**Focus:** Configure HTTP Nodes 4-6 (REST APIs)

**Node 4: Queue Transcription**
- [ ] Add HTTP node for Faster-Whisper API
- [ ] Endpoint: http://192.168.1.147:10300/transcribe
- [ ] Map file path from scene details
- [ ] Test job submission
- [ ] **Time:** 30 min

**Node 5: Vision Analysis**
- [ ] Add HTTP node for Ollama API
- [ ] Endpoint: http://192.168.1.147:11434/v1/chat/completions
- [ ] Configure llava:7b model prompt
- [ ] Map frames from scene
- [ ] Test inference
- [ ] **Time:** 45 min

**Node 6: Queue Transcode**
- [ ] Add HTTP node for Tdarr API
- [ ] Endpoint: http://192.168.1.139:8265/api/v2/queue
- [ ] Map scene file path
- [ ] Configure quality settings
- [ ] Test job submission
- [ ] **Time:** 30 min

### Saturday, May 30
**Focus:** Error Handling & Testing

- [ ] Add IF nodes after each HTTP node
- [ ] Implement error logging
- [ ] Test with valid scene ID
- [ ] Test with invalid ID (error handling)
- [ ] Monitor execution logs
- [ ] Fix any issues found
- [ ] **Time:** 2-3 hours

### Sunday, May 31
**Focus:** Documentation & Commit

- [ ] Validate all nodes working
- [ ] Document any gotchas
- [ ] Run 5 test scenes through workflow
- [ ] Measure performance (target: <5 min per scene)
- [ ] Commit to GitHub: `git commit -m "Phase 1B: Complete HTTP node configuration"`
- [ ] Create git tag: `git tag v0.2-beta`

**Week 1 Success Criteria:**
- ✅ All 6 HTTP nodes configured
- ✅ Workflow executes end-to-end
- ✅ No timeout or connection errors
- ✅ Error handling tested
- ✅ 5+ test scenes processed successfully

---

## Week 2: Phase 1C Validation (June 1-7)

### Monday-Tuesday, June 1-2
**Focus:** Monitor VLM Task Execution

- [ ] SSH to Unraid: `ssh root@192.168.1.147`
- [ ] Check Stash task status: http://192.168.1.147:9999 (Settings → Tasks)
- [ ] Record baseline metrics:
  - [ ] Scenes processed (progress %)
  - [ ] Processing rate (FPM)
  - [ ] Estimated completion time
  - [ ] GPU temp & utilization
- [ ] Create monitoring script (see PHASE_1C_VALIDATION.md)
- [ ] **Time:** 2-3 hours setup + continuous monitoring

### Wednesday-Thursday, June 3-4
**Focus:** Daily VLM Monitoring

**Daily Checklist:**
- [ ] Check task status (still running?)
- [ ] Record metrics: FPM, GPU temp, scene count
- [ ] Check for errors in logs
- [ ] Verify no CUDA memory issues
- [ ] **Time:** 30 min daily

### Friday-Saturday, June 5-6
**Focus:** Validate Tag Accuracy

Once VLM task completes (or at 50% progress):

- [ ] Pick 10 random scenes with markers
- [ ] Watch 30-60 seconds at marker timestamps
- [ ] Rate tag accuracy (accurate/partial/inaccurate)
- [ ] Calculate overall accuracy %
- [ ] Document results
- [ ] If <80% accuracy:
  - [ ] Review marker content
  - [ ] Check Ollama model output
  - [ ] Consider prompt refinement
  - [ ] Re-run on subset

**Validation Script:**
```bash
# See PHASE_1C_VALIDATION.md for full script
ACCURATE=0; PARTIAL=0; INACCURATE=0
# Test 10 scenes, rate accuracy
# Report: $((ACCURATE * 100 / 10))% overall
```

### Sunday, June 7
**Focus:** Document Results & Finalize

- [ ] Compile VLM execution metrics
- [ ] Document accuracy validation results
- [ ] Identify any model tuning needed
- [ ] Commit findings: `git commit -m "Phase 1C: VLM validation complete - 80%+ accuracy"`
- [ ] Create tag: `git tag v0.2-vlm-validated`

**Week 2 Success Criteria:**
- ✅ VLM task running/completed
- ✅ >80% tag accuracy validated
- ✅ No critical GPU/memory issues
- ✅ Scene markers created automatically
- ✅ Metrics documented

---

## Week 3: Phase 2 - Media Server Integration (June 8-14)

### Monday, June 8
**Focus:** NFO Generation Testing

**Test Suite 1: NFO File Creation**
- [ ] Trigger scene through n8n workflow
- [ ] Verify NFO file created (in same dir as MP4)
- [ ] Inspect NFO content (XML structure)
- [ ] Validate all required fields present:
  - [ ] Title, plot, runtime
  - [ ] All performers listed
  - [ ] Studio name
  - [ ] AI-generated tags
  - [ ] Cover image URL
- [ ] **Time:** 2 hours

### Tuesday, June 9
**Focus:** Jellyfin Integration

**Test Suite 2: Jellyfin Metadata Import**
- [ ] Add library path to Jellyfin (if needed)
- [ ] Trigger library scan
- [ ] Search for test scene in Jellyfin
- [ ] Verify metadata displays:
  - [ ] Title, plot, duration
  - [ ] Performers (cast list)
  - [ ] Studio, genres/tags
  - [ ] Poster image
- [ ] Document any issues
- [ ] **Time:** 2-3 hours

### Wednesday, June 10
**Focus:** Plex Integration

**Test Suite 3: Plex Metadata Import**
- [ ] Add library path to Plex (if needed)
- [ ] Trigger library refresh
- [ ] Search for test scene in Plex
- [ ] Verify metadata displays
- [ ] Check Tautulli for library stats
- [ ] Compare with Jellyfin results
- [ ] **Time:** 2-3 hours

### Thursday-Friday, June 11-12
**Focus:** End-to-End & Performance Testing

**Test Suite 4: Full Workflow**
- [ ] Batch test: Send 5 scenes through workflow
- [ ] Monitor time from webhook → NFO creation
- [ ] Monitor time from NFO → media server display
- [ ] Verify no data loss
- [ ] Check error handling
- [ ] **Time:** 3-4 hours

**Test Suite 5: Error Cases**
- [ ] Invalid scene ID
- [ ] Missing media file
- [ ] Corrupted NFO
- [ ] Verify graceful error handling
- [ ] **Time:** 1-2 hours

### Saturday-Sunday, June 12-14
**Focus:** Optimization & Documentation

- [ ] Review performance metrics
- [ ] Identify optimization opportunities
- [ ] Update documentation with results
- [ ] Run final validation: 10 full scenes
- [ ] Commit: `git commit -m "Phase 2: Media server integration complete - NFO→Jellyfin/Plex validated"`
- [ ] Tag release: `git tag v0.2.0`

**Week 3 Success Criteria:**
- ✅ NFO files generated automatically
- ✅ Jellyfin metadata imported & displayed
- ✅ Plex metadata imported & displayed
- ✅ End-to-end workflow <20 min
- ✅ All error cases handled
- ✅ v0.2.0 released

---

## Week 4-5: Phase 3 - Performer Enrichment at Scale (June 15-28)

### Monday-Tuesday, June 15-16
**Focus:** Data Source Integration

- [ ] Identify best performer image sources:
  - [ ] StashDB API
  - [ ] TMDB API
  - [ ] Web scraping (if feasible)
- [ ] Implement image fetching
- [ ] Test with 10 performers
- [ ] Validate image quality
- [ ] **Time:** 4-6 hours

### Wednesday-Thursday, June 17-18
**Focus:** Batch Enrichment Process

- [ ] Create batch enrichment script
- [ ] Implement image download & validation
- [ ] Handle duplicates/conflicts
- [ ] Add progress tracking
- [ ] **Time:** 4-5 hours

### Friday, June 19
**Focus:** Start Batch Run

- [ ] Run enrichment on 100 test performers
- [ ] Monitor for issues
- [ ] Validate image quality
- [ ] Adjust scripts as needed
- [ ] **Time:** 2-3 hours

### Weekend, June 20-22
**Focus:** Scale to Full Set

- [ ] Run enrichment on all 1,546 performers needing images
- [ ] Monitor progress continuously
- [ ] Handle any errors that arise
- [ ] **Time:** Continuous monitoring

### Monday-Tuesday, June 23-24
**Focus:** Validation & Optimization

- [ ] Verify all images downloaded
- [ ] Check for duplicates
- [ ] Validate coverage (should be close to 100%)
- [ ] Optimize process for future runs
- [ ] **Time:** 3-4 hours

### Wednesday, June 25
**Focus:** Gallery Generation

- [ ] Enable performer gallery syncing
- [ ] Test gallery display in Jellyfin/Plex
- [ ] Validate image quality in UI
- [ ] **Time:** 2 hours

### Thursday-Friday, June 26-27
**Focus:** Documentation & Testing

- [ ] Compile enrichment metrics
- [ ] Document data sources used
- [ ] Test gallery features
- [ ] Commit: `git commit -m "Phase 3: Performer enrichment complete - 1,897/1,897 with images"`
- [ ] Tag: `git tag v0.3.0`

**Week 4-5 Success Criteria:**
- ✅ 1,546+ new performer images downloaded
- ✅ Total coverage: ~100% (1,897 performers with images)
- ✅ Gallery generation working
- ✅ Performer galleries display in media servers
- ✅ v0.3.0 released

---

## Week 6: Hardening & Release (June 29 - July 5)

### Monday-Wednesday, June 29 - July 1
**Focus:** End-to-End Testing

- [ ] Full workflow test with 50 real scenes
- [ ] 48-hour continuous operation test
- [ ] Monitor for memory leaks, errors
- [ ] Validate data consistency
- [ ] **Time:** Continuous monitoring

### Thursday-Friday, July 2-3
**Focus:** Documentation & Release Prep

- [ ] Finalize all documentation
- [ ] Create user guides
- [ ] Document known limitations
- [ ] Create troubleshooting guide
- [ ] Update README with final status
- [ ] **Time:** 4-6 hours

### Saturday-Sunday, July 4-5
**Focus:** Release v1.0.0

- [ ] Final validation pass
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Final commit: `git commit -m "Release v1.0.0: Full automation platform"`
- [ ] Create release tag: `git tag v1.0.0`
- [ ] Create GitHub Release notes
- [ ] Archive final metrics
- [ ] **Time:** 2-3 hours

---

## Success Metrics (Final)

| Metric | Target | Achievement |
|--------|--------|-------------|
| **Performers with images** | 1,897/1,897 (100%) | ✅ |
| **Automated pipeline** | 100% automation | ✅ |
| **Scenes with AI tags** | 2,964/2,964 (100%) | ✅ |
| **Media server coverage** | Jellyfin + Plex | ✅ |
| **End-to-end time** | <20 min per scene | ✅ |
| **System uptime** | >99% during 48-hr test | ✅ |
| **Tag accuracy** | >80% | ✅ |

---

## Critical Path

```
Week 1: Phase 1B (HTTP nodes) ← MUST COMPLETE
   ↓
Week 2: Phase 1C (VLM validation)
   ↓
Week 3: Phase 2 (Media server integration)
   ↓
Week 4-5: Phase 3 (Performer enrichment)
   ↓
Week 6: Release v1.0.0
```

**If any week falls behind:**
- Extend that week by 2-3 days
- Prioritize core functionality over optimization
- Move optional features to v1.1.0

---

## Daily Standup Checklist

**Every morning (5 min):**
- [ ] Review yesterday's progress
- [ ] Identify blockers
- [ ] Plan today's focus
- [ ] Log any issues in GitHub

**Every evening (5 min):**
- [ ] Document what was accomplished
- [ ] Commit code if applicable
- [ ] Note any issues for next day
- [ ] Update task status

---

## Git Workflow

**Daily commits:**
```bash
# After each major task
git add .
git commit -m "Feature: Brief description of work completed"
git push origin main
```

**Weekly tags:**
```bash
# At end of each week
git tag v0.X.0-weekN
git push origin v0.X.0-weekN
```

**Release tags:**
```bash
# At phase completions
git tag v0.2.0  # Phase 2 complete
git tag v0.3.0  # Phase 3 complete
git tag v1.0.0  # Full release
git push origin v0.2.0 v0.3.0 v1.0.0
```

---

## Communication & Escalation

**If blocked for >1 hour:**
- Document issue in GitHub issue
- Check logs for root cause
- Attempt 2-3 fixes
- If still blocked: Create issue, move to next task

**If task takes >2x estimated time:**
- Adjust timeline
- Break task into smaller steps
- Consider parallel work if possible

---

**Timeline:** May 25 - July 5, 2026 (42 days)  
**Status:** Ready to begin  
**Next Action:** Start Phase 1B configuration immediately (Monday, May 25)
