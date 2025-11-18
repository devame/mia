# Manual URL Capture Guide - DCE Website

## Objective
Capture the direct download URL for the Text(.txt) file by using a real browser.

---

## Step-by-Step Instructions

### Step 1: Open Browser DevTools

1. Open **Chrome** or **Firefox**
2. Press **F12** (or right-click → Inspect)
3. Click on the **Network** tab
4. Check the box for **Preserve log** (important!)

### Step 2: Navigate to the Target Page

Navigate to:
```
http://www.dce.com.cn/dceg/channel/list/471.html
```

**Important:** The site may challenge you with anti-bot verification. Complete any challenges (CAPTCHA, waiting, etc.)

### Step 3: Find the Text(.txt) Button

Once the page loads:
1. Look for a button or link labeled "Text(.txt)" or "文本(.txt)"
2. Do NOT click it yet!

### Step 4: Clear Network Log (Optional)

In DevTools Network tab:
- Click the 🚫 clear button to remove existing requests
- This makes it easier to find the download request

### Step 5: Click the Text(.txt) Button

1. Click the Text(.txt) button
2. Watch the Network tab - new requests will appear

### Step 6: Find the Download Request

Look for one of these patterns in the Network tab:

**Common patterns:**
- Filename ending in `.txt`
- Request type: `document` or `xhr` or `fetch`
- Status code: `200` (successful)
- Large size (the actual data file)

**It might look like:**
```
GET /download/data/YYYYMMDD.txt
GET /api/export?format=txt&date=...
GET /dceg/data/download/...
```

### Step 7: Capture Request Details

Click on the download request in Network tab, then:

1. **General tab:**
   - Copy the full **Request URL**
   - Note the **Request Method** (GET/POST)
   - Note **Status Code** (should be 200)

2. **Headers tab:**
   - Copy all **Request Headers** (important!)
   - Look for: Cookie, Authorization, Referer, X-Requested-With

3. **Payload tab** (if POST):
   - Copy any form data or JSON payload

### Step 8: Right-Click → Copy

Chrome provides shortcuts:
- Right-click the request
- Select **Copy** → **Copy as cURL**
- OR **Copy** → **Copy as fetch**

This gives you everything in one command!

---

## What to Save

Create a file with this information:

```
REQUEST URL:
[paste the full URL here]

REQUEST METHOD:
[GET or POST]

REQUEST HEADERS:
[paste all headers, especially Cookie and any X-* headers]

PAYLOAD (if POST):
[paste any form data or JSON]

CURL COMMAND:
[paste the "Copy as cURL" if you used that option]
```

---

## Example Output

Here's what it might look like:

```bash
curl 'http://www.dce.com.cn/dceg/api/download/settlement/2025-11-18.txt' \
  -H 'Accept: text/html,application/xhtml+xml' \
  -H 'Cookie: JSESSIONID=ABC123...; _jwt_token=eyJ...' \
  -H 'Referer: http://www.dce.com.cn/dceg/channel/list/471.html' \
  -H 'User-Agent: Mozilla/5.0 ...' \
  -H 'X-Requested-With: XMLHttpRequest'
```

---

## Next Steps

Once you have the URL and headers:

1. Save them to `/home/user/mia/captured_request.txt`
2. Run the testing script: `python3 test_captured_url.py`
3. The script will attempt to download using the captured info

---

## Tips

- **Cookies are often required** - make sure to copy them
- **JWT tokens** may be in cookies or Authorization header
- **Tokens may expire** - capture and test quickly
- If download fails, the URL might be:
  - Time-limited (expires after X minutes)
  - Session-specific (requires same browser session)
  - IP-restricted (must come from same IP)

---

## Alternative: Browser Extension

If manual capture is difficult, consider:
- **Tampermonkey** script to auto-capture URLs
- **ModHeader** to save/replay requests
- **Postman Interceptor** to capture automatically

---

Good luck! Once you have the information, we can automate it.
