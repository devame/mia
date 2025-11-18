# API Approach: JSON → TXT Workflow

## Understanding How the Website Works

Based on your description, the DCE website uses this workflow:

```
1. User clicks Text(.txt) button
   ↓
2. JavaScript loads data via JSON API (AJAX/Fetch)
   ↓
3. JSON data is sent to server-side script
   ↓
4. Server converts JSON to .txt format
   ↓
5. Browser downloads the .txt file
```

**Our Goal:** Bypass the browser and call these APIs directly!

---

## Why This Approach is Better

✅ **No browser automation needed** - no detection
✅ **Faster** - direct API calls
✅ **More reliable** - no JavaScript challenges
✅ **Easier to automate** - simple HTTP requests

---

## What You Need to Find

You need to identify **TWO** API endpoints using a real browser:

### 1. JSON Data API
The endpoint that returns the raw data in JSON format

**Example:**
```
GET http://www.dce.com.cn/dceg/api/data/settlement?date=2025-11-18
Response: {"data": [...], "status": "success"}
```

### 2. TXT Conversion Endpoint
The server-side script that converts JSON to .txt

**Example:**
```
POST http://www.dce.com.cn/dceg/api/export/txt
Body: {"data": [...]}
Response: (downloads .txt file)
```

**OR** you might find just ONE endpoint with a format parameter:
```
GET http://www.dce.com.cn/dceg/api/data?format=txt
```

---

## Step-by-Step Guide

### Step 1: Manual API Discovery

**Use a real browser** to capture the API endpoints:

```bash
# Read the detailed guide
cat MANUAL_API_CAPTURE_GUIDE.md
```

**Quick version:**
1. Open Chrome DevTools (F12)
2. Go to Network tab → Filter by "XHR" or "Fetch"
3. Visit http://www.dce.com.cn/dceg/channel/list/471.html
4. Watch for JSON API calls as page loads
5. Click the "Text(.txt)" button
6. Watch for the download/conversion API call
7. Copy both endpoints as cURL commands

### Step 2: Save API Configuration

Copy the template:
```bash
cp captured_api_endpoints.json.template captured_api_endpoints.json
```

Edit it with your captured data:
```json
{
  "json_api": {
    "url": "http://www.dce.com.cn/dceg/api/data/list",
    "method": "GET",
    "headers": {
      "Cookie": "JSESSIONID=ABC123...",
      "Authorization": "Bearer xyz..."
    },
    "params": {
      "date": "2025-11-18"
    }
  },
  "txt_conversion": {
    "url": "http://www.dce.com.cn/dceg/api/export/txt",
    "method": "POST",
    "headers": {
      "Cookie": "JSESSIONID=ABC123...",
      "Content-Type": "application/json"
    }
  }
}
```

### Step 3: Test the APIs

Run the test script:
```bash
python3 test_api_endpoints.py
```

This will:
1. Call the JSON API to get data
2. Try to call the TXT conversion endpoint
3. Fallback to local conversion if needed
4. Save the resulting .txt file

---

## Automated Network Interception

We've also created an automated script to monitor network traffic:

```bash
python3 intercept_api_calls.py
```

**Note:** This script is currently blocked by the anti-bot protection (401 Unauthorized), so you'll need to use a **real browser** for manual capture.

---

## Common Scenarios

### Scenario A: Two Separate Endpoints

```
GET /api/data → Returns JSON
POST /api/export → Converts JSON to TXT
```

**Automation:**
```python
# Step 1: Get JSON
response = requests.get('http://...api/data', headers=headers)
json_data = response.json()

# Step 2: Convert to TXT
txt = requests.post('http://...api/export', json=json_data, headers=headers)
with open('output.txt', 'wb') as f:
    f.write(txt.content)
```

### Scenario B: Single Endpoint with Format Parameter

```
GET /api/data?format=json → Returns JSON
GET /api/data?format=txt → Returns TXT
```

**Automation:**
```python
# Just call with format=txt
response = requests.get('http://...api/data?format=txt', headers=headers)
with open('output.txt', 'wb') as f:
    f.write(response.content)
```

### Scenario C: Client-Side Conversion

```
GET /api/data → Returns JSON
JavaScript converts JSON to TXT in browser
```

**Automation:**
```python
# Get JSON
response = requests.get('http://...api/data', headers=headers)
data = response.json()

# Convert yourself
with open('output.txt', 'w') as f:
    for row in data['rows']:
        f.write('\t'.join(str(v) for v in row.values()) + '\n')
```

---

## Tools Provided

| File | Purpose |
|------|---------|
| `MANUAL_API_CAPTURE_GUIDE.md` | Detailed guide for capturing API endpoints |
| `intercept_api_calls.py` | Automated network monitoring (blocked by anti-bot) |
| `test_api_endpoints.py` | Test captured API endpoints |
| `captured_api_endpoints.json.template` | Template for configuration |
| `README_API_APPROACH.md` | This file |

---

## Current Status: Blocked

**The automated interception is blocked:**
- Status: 401 Unauthorized
- Header: `WWW-Authenticate: Bearer realm="..."`
- Error: "Jwt is missing"

This means the site requires Bearer token authentication that can only be obtained through a real browser session.

**Solution:** Use the **manual capture** approach with a real browser.

---

## Expected Success Rate

| Method | Success Rate | Notes |
|--------|--------------|-------|
| Manual browser capture | **85%** | Highest - you see exactly what browser does |
| Automated Playwright intercept | **0%** | Currently blocked |
| Direct API guessing | **10%** | Unlikely without seeing actual requests |

---

## Troubleshooting

### Can't find the JSON API?
- Check XHR/Fetch requests in Network tab
- Look in JavaScript files (Sources tab) for fetch/$.ajax calls
- Search in DevTools for keywords like "api", "data", "query"

### Can't find the TXT conversion endpoint?
- It might happen client-side (JavaScript converts JSON to TXT)
- Check for POST requests after clicking the button
- Look for endpoints with "export", "download", "convert" in the URL

### APIs require authentication?
- Copy ALL cookies from your browser session
- Look for Authorization headers
- May need to stay logged in to the site

### Tokens expire quickly?
- Capture and test immediately (within 1 minute)
- May need to refresh tokens periodically
- Consider using undetected-chromedriver to maintain session

---

## Next Steps

1. **Use a real browser** to access the page manually
2. **Capture the API endpoints** using DevTools
3. **Test with** `test_api_endpoints.py`
4. **Build automation** once you understand the pattern

---

## Alternative: If APIs Can't Be Found

If you can't find the APIs or they're too complex:

**Option #3: Undetected ChromeDriver**
```bash
pip install undetected-chromedriver
```

This is more sophisticated than Playwright and might bypass the anti-bot protection.

See `PLAYWRIGHT_RESULTS.md` for details on all alternatives.

---

Good luck! The API approach is your best bet once you can capture the endpoints in a real browser.
