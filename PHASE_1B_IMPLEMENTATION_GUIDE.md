# Phase 1B Implementation Guide - Manual Setup Instructions

**Status:** Ready for manual implementation  
**Date:** 2026-05-15  
**Environment:** n8n v2.20.7 on z4-media-01 (192.168.1.10:5678)

---

## Overview

This guide provides step-by-step instructions to implement Phase 1B tasks manually in the n8n UI. All three tasks can be completed by modifying the Scene Lifecycle Automation workflow.

---

## TASK 1: Implement ID Format Conversion

### Objective
Convert webhook string IDs like "test-scene-123" to numeric IDs that Stash expects.

### Current State
The Get Scene Details node currently has:
```json
{
  "query": "query GetSceneDetails($id: ID!) { findScene(id: $id) { id title }}",
  "variables": {
    "id": 123
  }
}
```

### Implementation Steps

1. **Open n8n UI:** Navigate to http://192.168.1.10:5678/workflow/oYYQuZXygAejZWac

2. **Select Get Scene Details Node:**
   - Click on the "Get Scene Details" node to select it
   - Double-click the node, or right-click and select "Edit" to open configuration

3. **Locate the JSON Body Field:**
   - Find the "JSON Body" section in the node configuration
   - This is where the GraphQL query and variables are defined

4. **Update the Variables Section:**
   - Find the line: `"id": 123`
   - Replace it with: `"id": {{ parseInt($json.id.match(/\d+/)[0]) }}`
   
   **Full updated body should be:**
   ```json
   {
     "query": "query GetSceneDetails($id: ID!) { findScene(id: $id) { id title }}",
     "variables": {
       "id": {{ parseInt($json.id.match(/\d+/)[0]) }}
     }
   }
   ```

5. **Explanation of the expression:**
   - `$json.id` - accesses the webhook data ID field (e.g., "test-scene-123")
   - `.match(/\d+/)` - regex pattern to find all digits in the string
   - `[0]` - takes the first match (e.g., "123" from "test-scene-123")
   - `parseInt()` - converts string "123" to numeric 123
   - Result: "test-scene-123" → 123

6. **Test the change:**
   - Click "Execute Step" or run the entire workflow
   - Verify that the ID conversion works without strconv.Atoi errors
   - Check the node output to confirm the GraphQL query executes successfully

7. **Save the workflow:**
   - Press Ctrl+S or use the Publish button to save

---

## TASK 2: Expand GraphQL Query

### Objective
Extend the GraphQL query to retrieve additional scene metadata needed for downstream processing.

### Current Query
```graphql
query GetSceneDetails($id: ID!) {
  findScene(id: $id) {
    id
    title
  }
}
```

### Implementation Steps

1. **Open the Get Scene Details node configuration** (same as Task 1, step 2)

2. **Locate the GraphQL query string** in the JSON body

3. **Replace the query with the extended version:**
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

4. **Full updated JSON body:**
   ```json
   {
     "query": "query GetSceneDetails($id: ID!) { findScene(id: $id) { id title path duration rating date studio { id name } performers { id name image } tags { id name } images { url title } } }",
     "variables": {
       "id": {{ parseInt($json.id.match(/\d+/)[0]) }}
     }
   }
   ```

5. **Test the expanded query:**
   - Click "Execute Step" or run the workflow
   - Monitor the response to ensure all fields are returned
   - Check Stash schema compatibility - if any fields don't exist, you'll get field validation errors
   - Remove any fields that cause errors

6. **Expected response structure:**
   The GraphQL response should include:
   - Scene: id, title, path, duration, rating, date
   - Studio object: id, name
   - Performers array: id, name, image for each
   - Tags array: id, name for each
   - Images array: url, title for each

7. **Known potential issues:**
   - **Missing fields:** If Stash v0.31.1 doesn't have all these fields, the query will error. Remove problematic fields one at a time.
   - **Null values:** Some fields may return null for test scenes (expected)
   - **Image URLs:** May be relative paths that need URL normalization

8. **Save the workflow**

---

## TASK 3: Add Scene Data Processing Node

### Objective
Create a data processing node that normalizes and structures the GraphQL response for downstream use.

### Implementation Steps

1. **Add a new node after Get Scene Details:**
   - Click the "+" icon between Get Scene Details and the end of the workflow
   - Select "Set" node type (or "Function" for more complex logic)
   - Name it "Parse Scene Data"

2. **Configure the Set node:**
   - Input source: Select "Get Scene Details" (the GraphQL response)
   - Mode: "Using JSON" or "Using Expressions"

3. **Set the node output structure:**
   Use the following configuration to parse and normalize the response:

   **If using JSON mode, set these fields:**
   
   | Field Name | Assignment |
   |-----------|-----------|
   | sceneId | `{{ $('Get Scene Details').first().json.data.findScene.id }}` |
   | title | `{{ $('Get Scene Details').first().json.data.findScene.title }}` |
   | path | `{{ $('Get Scene Details').first().json.data.findScene.path }}` |
   | duration | `{{ $('Get Scene Details').first().json.data.findScene.duration }}` |
   | rating | `{{ $('Get Scene Details').first().json.data.findScene.rating }}` |
   | date | `{{ $('Get Scene Details').first().json.data.findScene.date }}` |
   | studio | `{{ $('Get Scene Details').first().json.data.findScene.studio }}` |
   | performerIds | `{{ $('Get Scene Details').first().json.data.findScene.performers.map(p => p.id) }}` |
   | performerNames | `{{ $('Get Scene Details').first().json.data.findScene.performers.map(p => p.name) }}` |
   | tagIds | `{{ $('Get Scene Details').first().json.data.findScene.tags.map(t => t.id) }}` |
   | tagNames | `{{ $('Get Scene Details').first().json.data.findScene.tags.map(t => t.name) }}` |
   | imageUrls | `{{ $('Get Scene Details').first().json.data.findScene.images.map(img => img.url) }}` |

4. **Alternative: Using Function node for complex processing:**
   
   If you need more control over data transformation, use a Function node with this logic:
   ```javascript
   const sceneData = $input.all()[0].json.data.findScene;
   
   return {
     sceneId: sceneData.id,
     title: sceneData.title,
     path: sceneData.path,
     durationSeconds: sceneData.duration ? parseInt(sceneData.duration) : null,
     rating: sceneData.rating,
     dateAdded: sceneData.date,
     studio: sceneData.studio,
     performers: sceneData.performers.map(p => ({
       id: p.id,
       name: p.name,
       imageUrl: p.image ? normalizeUrl(p.image) : null
     })),
     tags: sceneData.tags.map(t => ({
       id: t.id,
       name: t.name
     })),
     images: sceneData.images.map(img => ({
       url: normalizeUrl(img.url),
       title: img.title
     }))
   };
   
   function normalizeUrl(urlOrPath) {
     if (!urlOrPath) return null;
     if (urlOrPath.startsWith('http')) return urlOrPath;
     // If relative path, prepend Stash base URL
     return 'http://192.168.1.147:9999' + (urlOrPath.startsWith('/') ? '' : '/') + urlOrPath;
   }
   ```

5. **Testing the processing node:**
   - Execute the workflow
   - Check the "Parse Scene Data" node output
   - Verify all fields are properly extracted and normalized
   - Confirm no errors in data transformation

6. **Expected output structure:**
   ```json
   {
     "sceneId": "123",
     "title": "Scene Title",
     "path": "/path/to/video.mp4",
     "durationSeconds": 1234,
     "rating": 4,
     "dateAdded": "2024-01-01",
     "studio": {"id": "1", "name": "Studio Name"},
     "performers": [
       {"id": "100", "name": "Performer Name", "imageUrl": "http://..."}
     ],
     "tags": [
       {"id": "10", "name": "Tag Name"}
     ],
     "images": [
       {"url": "http://...", "title": "Cover"}
     ]
   }
   ```

7. **Save the workflow**

---

## Workflow Architecture After Phase 1B

```
Webhook2 (receive scene data)
  ↓
Wait1 (2-minute delay)
  ↓
Stash Login (authenticate, get session)
  ↓
Get Scene Details (query with ID conversion + extended fields)
  ↓
Parse Scene Data (normalize + structure response)
  ↓
[Ready for Phase 2: AI tagging + media server output]
```

---

## Testing Checklist

After implementing all three tasks:

- [ ] **Task 1 - ID Conversion:**
  - [ ] Webhook sends "test-scene-123" (string)
  - [ ] Expression converts to numeric 123
  - [ ] GraphQL query executes without strconv.Atoi error
  - [ ] Response shows findScene with id and title

- [ ] **Task 2 - Extended Query:**
  - [ ] Query returns performers array with id, name, image
  - [ ] Query returns tags array with id, name
  - [ ] Query returns images array with url, title
  - [ ] Query returns studio object with id, name
  - [ ] Query returns path, duration, rating, date fields
  - [ ] All fields populated with test data or null (expected for test IDs)

- [ ] **Task 3 - Data Processing:**
  - [ ] Parse Scene Data node receives Get Scene Details output
  - [ ] All fields correctly extracted and assigned
  - [ ] Arrays properly mapped (performerIds, tagNames, etc.)
  - [ ] URLs normalized if needed
  - [ ] Output is JSON object ready for downstream processing

- [ ] **Workflow Execution:**
  - [ ] Execute entire workflow without errors
  - [ ] Verify logs show successful execution of all nodes
  - [ ] Confirm final output contains all required fields

---

## Troubleshooting

### Issue: "strconv.Atoi: parsing ... invalid syntax"
**Solution:** Verify the ID conversion expression is correctly formatted in the variables section. The expression must be wrapped in `{{ }}` double braces and use the exact regex pattern.

### Issue: GraphQL field validation errors
**Solution:** Some fields may not exist in Stash v0.31.1. Remove problematic fields from the query and test incrementally.

### Issue: Null performer/tag arrays
**Solution:** This is expected with test scene IDs. Production data will have these arrays populated.

### Issue: Relative image URLs not working
**Solution:** Use the normalizeUrl function in the Function node to prepend the Stash base URL (http://192.168.1.147:9999).

### Issue: Parse Scene Data node not receiving data
**Solution:** Verify the input source is set to "Get Scene Details" and that the Get Scene Details node executes successfully first.

---

## Next Steps (Phase 2)

Once Phase 1B is complete:
1. Implement AI vision tagging using performer and scene metadata
2. Generate NFO files for Jellyfin/Plex media server
3. Push processed metadata to media server output
4. Set up automated publishing workflow

---

## References

- **Stash GraphQL Schema:** http://192.168.1.147:9999/graphql (interactive explorer)
- **n8n Documentation:** https://docs.n8n.io/
- **Scene Lifecycle Automation Workflow:** http://192.168.1.10:5678/workflow/oYYQuZXygAejZWac

