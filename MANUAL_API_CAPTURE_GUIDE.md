# Manual API Capture Guide - DCE Website (JSON → TXT Workflow)

## Understanding the Workflow

The DCE website uses a **two-step process**:

```
1. JSON API Call → Loads data onto page (AJAX/Fetch)
2. Server-side Script → Converts JSON to .txt and downloads
```

We need to find **BOTH** endpoints to automate this.

---

## Step-by-Step Instructions

### Step 1: Open Browser DevTools

1. Open **Chrome** (recommended for this)
2. Press **F12** (or right-click → Inspect)
3. Go to the **Network** tab
4. ✅ Check **Preserve log**
5. ✅ Filter by **XHR** or **Fetch** (to see only API calls)

### Step 2: Navigate to Target Page

Navigate to:
```
http://www.dce.com.cn/dceg/channel/list/471.html
```

Complete any anti-bot challenges that appear.

### Step 3: Watch for JSON API Calls

As the page loads, watch the Network tab for:

**Look for:**
- Requests to `/api/` endpoints
- Requests with `XHR` or `Fetch` type
- Responses with `Content-Type: application/json`
- Response size that suggests data (not just metadata)

**Common patterns:**
```
GET /api/data/list?date=2025-11-18
GET /dceg/data/settlement/query
POST /api/query with JSON body
```

### Step 4: Identify the Data API

Click on each XHR/Fetch request and check:

1. **Response tab** - Does it contain the actual data?
2. **Preview tab** - See the JSON structure
3. **Headers tab** - Check Content-Type is `application/json`

**What to look for:**
```json
{
  "data": [
    { "product": "...", "price": "...", ... },
    { "product": "...", "price": "...", ... }
  ],
  "status": "success"
}
```

### Step 5: Clear Network Log

Once you've identified the JSON API, **clear the network log** (🚫 button) to make the next step easier.

### Step 6: Click the Text(.txt) Button

Now click the "Text(.txt)" button on the page.

Watch for:
1. **New XHR/Fetch request** - might send the JSON data
2. **Download request** - the server-side .txt conversion endpoint

### Step 7: Find the TXT Conversion Endpoint

Look for a request that:
- Returns `Content-Type: text/plain` or `application/octet-stream`
- Has `Content-Disposition: attachment; filename="..."` header
- Downloads a file to your browser

**Common patterns:**
```
POST /api/export/txt with JSON body
GET /api/download/txt?id=...
POST /dceg/convert with data payload
```

### Step 8: Capture BOTH Endpoints

You need information from **TWO** requests:

#### **Request 1: JSON Data API**

```
URL: http://www.dce.com.cn/dceg/api/data/list
Method: GET (or POST)
Headers: Cookie, Referer, etc.
Parameters: date, product, etc.
Response: JSON data
```

#### **Request 2: TXT Conversion Endpoint**

```
URL: http://www.dce.com.cn/dceg/api/export/txt
Method: POST (likely)
Headers: Cookie, Content-Type, etc.
Body: The JSON data from Request 1
Response: .txt file download
```

### Step 9: Copy as cURL (Both Requests)

For **each** request:
1. Right-click in Network tab
2. **Copy → Copy as cURL**
3. Save to separate files

---

## What to Save

Create a file with this structure:

```json
{
  "json_api": {
    "url": "http://www.dce.com.cn/dceg/api/data/list",
    "method": "GET",
    "headers": {
      "Cookie": "...",
      "Referer": "..."
    },
    "params": {
      "date": "2025-11-18"
    }
  },
  "txt_conversion": {
    "url": "http://www.dce.com.cn/dceg/api/export/txt",
    "method": "POST",
    "headers": {
      "Cookie": "...",
      "Content-Type": "application/json"
    },
    "body_template": "Uses JSON from first API"
  }
}
```

---

## Alternative: Just JSON API

If you can't find the TXT conversion endpoint, that's okay!

You can:
1. Get the JSON data from the API
2. Convert it to .txt yourself with Python

**Example:**
```python
import requests
import json

# Get JSON data
response = requests.get('http://example.com/api/data')
data = response.json()

# Convert to .txt (simple example)
with open('output.txt', 'w') as f:
    for item in data['data']:
        f.write(f"{item['product']}\t{item['price']}\n")
```

---

## Tips for Finding APIs

### Use Chrome DevTools Tricks:

1. **Search in all files**: Press `Ctrl+Shift+F` in DevTools
   - Search for: `fetch(`, `$.ajax`, `XMLHttpRequest`
   - Find the JavaScript that makes the API call

2. **Check the Sources tab**: Look at JavaScript files
   - Find the click handler for the Text(.txt) button
   - Read the code to see what API it calls

3. **Use console**: Type in console:
   ```javascript
   // Override fetch to log all calls
   const originalFetch = window.fetch;
   window.fetch = function(...args) {
     console.log('Fetch called:', args);
     return originalFetch.apply(this, args);
   }
   ```

4. **Breakpoints**:
   - Find the button in Elements tab
   - Right-click → Break on → Subtree modifications
   - Click button, debugger will pause

---

## Common Scenarios

### Scenario 1: JSON API + TXT Endpoint

```
1. GET /api/data → Returns JSON
2. POST /api/export → Receives JSON, returns .txt
```

**Solution**: Call both endpoints

### Scenario 2: Single Endpoint with Format Parameter

```
GET /api/data?format=json → Returns JSON
GET /api/data?format=txt → Returns .txt
```

**Solution**: Just change the format parameter!

### Scenario 3: Client-Side Conversion

```
1. GET /api/data → Returns JSON
2. JavaScript converts JSON to .txt in browser
3. Browser downloads using Blob API
```

**Solution**: Replicate the JavaScript conversion in Python

---

## What We're Looking For

**Ideal outcome:**
```
✓ JSON API URL with parameters
✓ TXT conversion endpoint
✓ Required headers/cookies
✓ Understanding of data flow
```

**Minimum outcome:**
```
✓ JSON API URL
✓ Can convert JSON to TXT ourselves
```

---

## Next Steps

Once captured:
1. Save to `captured_api_endpoints.json`
2. Run `python3 test_api_endpoints.py`
3. Automate the full workflow

---

Good luck! This approach has a much higher success rate since we're calling APIs directly rather than automating browsers.
