# Phase 1B: Content Processing & Query Expansion

**Start Here for Next Session**

## Immediate Tasks (Ready to Start)

### 1. Fix ID Format Issue
**Problem:** Webhook sends `id: "test-scene-123"` (string), but Stash GraphQL expects numeric ID.

**Solution Options:**
1. Extract numeric portion: Use n8n expression to parse "123" from "test-scene-123"
   - Expression: `{{ parseInt($json.id.match(/\d+/)[0]) }}`
2. Use real Stash scene IDs: Update webhook test data to send numeric IDs directly
3. Add mapping node: Create a preprocessing node that converts string IDs to numeric

**Action:** Implement option 1 (most flexible for production)

### 2. Expand GraphQL Query
**Current Query:**
```graphql
query GetSceneDetails($id: ID!) {
  findScene(id: $id) {
    id
    title
  }
}
```

**Extended Query Needed:**
```graphql
query GetSceneDetails($id: ID!) {
  findScene(id: $id) {
    id
    title
    path
    duration
    rating
    date
    studio {
      id
      name
    }
    performers {
      id
      name
      image
    }
    tags {
      id
      name
    }
    images {
      url
      title
    }
  }
}
```

**Note:** Verify these field names exist in Stash v0.31.1 schema by testing in Stash GraphQL explorer or checking documentation.

**File to Update:** Get Scene Details node in Scene Lifecycle Automation workflow (n8n, 192.168.1.10:5678)

### 3. Add Scene Data Processing Node
**Purpose:** Parse the GraphQL response and structure data for downstream processing

**Location in Workflow:** After Get Scene Details node

**Processing Steps:**
1. Extract performer IDs and names
2. Normalize image URLs (resolve relative paths)
3. Parse duration into seconds
4. Format date fields
5. Create structured output for tagging/metadata generation

**Implementation:** Add Set/Function node to restructure response

---

## Phase 1B Architecture

```
Get Scene Details (GraphQL response)
  ↓
Parse Scene Data (restructure + normalize)
  ↓
Extract Performers
  ├→ Query performer details
  └→ Merge performer metadata
  ↓
Extract Content Tags
  ├→ Query existing tags
  └→ Prepare for AI tagging
  ↓
Generate Metadata
  ├→ Create NFO file structure
  ├→ Prepare for Jellyfin/Plex
  └→ Stage for output
```

---

## Code Location References

**n8n Workflow:** `http://192.168.1.10:5678/workflow/oYYQuZXygAejZWac`  
- Node: "Get Scene Details" → Update JSON body and test
- Add after: "Get Scene Details" node

**Related Files:**
- `PHASE_1A_COMPLETION.md` - Complete Phase 1A documentation
- `SPECS.md` - Hardware/software specifications (use to check Stash schema)

---

## Testing Checklist for Phase 1B

- [ ] ID format conversion working (test with "test-scene-123" → numeric 123)
- [ ] Extended GraphQL query returns all requested fields
- [ ] Scene data parsing node handles all field types correctly
- [ ] Performer data structured for downstream processing
- [ ] Image URLs properly formatted
- [ ] All outputs ready for Phase 2 (AI tagging + media server)

---

## Stash GraphQL Endpoint Reference

**URL:** `http://192.168.1.147:9999/graphql`  
**Auth:** Cookie header with Stash session token  
**Query Variables:** `{ "id": <numeric_id> }`  

To test queries manually:
1. Use Stash GraphQL explorer (if available)
2. Or construct curl request with session cookie

---

## Known Schema Notes

**Stash v0.31.1:**
- Scene ID type: ID (accepts numeric or string, but converts to int internally)
- Performers: Array of performer objects
- Images: Array with URL and title
- Tags: Array of tag objects
- Studios: Single studio object reference

**Not yet verified (test in Phase 1B):**
- Exact field names for images array
- Whether performers.image returns URL or ID
- Date format returned

---

## Critical Code Snippets

**n8n ID Parsing Expression:**
```
{{ parseInt($json.id.match(/\d+/)[0]) }}
```

**Alternative (if string ID works):**
```
{{ $json.id }}
```

**GraphQL Variable Substitution (n8n):**
```json
{
  "query": "...",
  "variables": {
    "id": {{ parseInt($json.id.match(/\d+/)[0]) }}
  }
}
```

---

## Expected Challenges

1. **Field Name Mismatches** - Stash v0.31.1 might use different field names than expected; be prepared to adjust query based on schema errors
2. **Null Returns** - Test scene ID 123 returns findScene: null (expected with test data); production needs real scene IDs
3. **Image URL Format** - May need URL joining/normalization depending on how Stash returns paths
4. **Large Response Payload** - Extended query might return large performer/tag arrays; may need pagination

---

## Success Criteria

✅ Phase 1B is complete when:
1. Extended GraphQL query executes without errors
2. All scene fields retrieved and structured
3. Performer data formatted for AI vision processing
4. Ready to pass to Phase 2 (AI tagging + media server output)

---

## Session Notes

- n8n is running on z4-media-01 and appears stable
- Stash endpoint responding consistently
- All auth issues resolved
- Ready to expand content processing logic
