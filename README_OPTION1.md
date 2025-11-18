# Option #1: Reverse Engineer Direct Download URL

## Overview

Since Playwright cannot bypass DCE's anti-bot protection, we're using the **Direct URL approach**:
1. You manually capture the download URL using a real browser
2. We automate downloads using that URL

---

## Quick Start

### Step 1: Capture the URL (Manual)

**Follow the guide:**
```bash
cat MANUAL_URL_CAPTURE_GUIDE.md
```

**Or in summary:**
1. Open Chrome/Firefox with DevTools (F12)
2. Go to Network tab, enable "Preserve log"
3. Visit: http://www.dce.com.cn/dceg/channel/list/471.html
4. Click the "Text(.txt)" button
5. Find the download request in Network tab
6. Right-click → Copy as cURL (or copy URL + headers)

### Step 2: Save the Captured Data

**Option A: JSON format (recommended)**

Copy `captured_request.json.template` to `captured_request.json`:
```bash
cp captured_request.json.template captured_request.json
```

Then edit it with your captured data:
```json
{
  "url": "http://www.dce.com.cn/dceg/api/download/settlement.txt",
  "method": "GET",
  "headers": {
    "Cookie": "JSESSIONID=ABC123...; jwt_token=XYZ...",
    "Referer": "http://www.dce.com.cn/dceg/channel/list/471.html",
    "User-Agent": "Mozilla/5.0 ..."
  }
}
```

**Option B: cURL command**

Paste your cURL command directly into `test_captured_url.py` (see script for details)

### Step 3: Test the URL

Run the testing script:
```bash
python3 test_captured_url.py
```

This will:
- ✅ Test if the URL works
- ✅ Download the file to `downloads/` folder
- ✅ Show you a preview of the content
- ✅ Help diagnose issues if it fails

---

## Files in This Package

| File | Purpose |
|------|---------|
| `MANUAL_URL_CAPTURE_GUIDE.md` | Step-by-step guide for capturing URLs |
| `test_captured_url.py` | Script to test captured URLs |
| `captured_request.json.template` | Template for saving request data |
| `README_OPTION1.md` | This file |

---

## Expected Results

### ✅ If Successful

```
✅ SUCCESS! Downloaded to: downloads/download_authenticated_20251118_123456.txt
File size: 15234 bytes

Preview (first 500 chars):
[Your data appears here...]
```

You can then:
- Automate daily downloads
- Schedule with cron
- Build a data pipeline

### ❌ If Failed

Common error messages:

**"401 Unauthorized" or "403 Forbidden"**
- Token expired → Capture and test within 1 minute
- Missing headers → Copy ALL headers, especially Cookie
- Session expired → Open new browser session

**"Jwt is missing"**
- Same issue as Playwright - need valid JWT token
- Make sure to copy Cookie header with JWT
- Try capturing immediately after clicking button

**"404 Not Found"**
- URL might be time-limited or contain session ID
- Pattern might change (check if date is in URL)
- Try clicking button again and capture fresh URL

---

## Automation Strategy

Once you find a working URL pattern:

### If URL is static:
```python
# Just use the same URL every time
url = "http://www.dce.com.cn/dceg/data/settlement.txt"
response = requests.get(url)
```

### If URL contains date:
```python
# Replace date portion
from datetime import datetime
date_str = datetime.now().strftime('%Y%m%d')
url = f"http://www.dce.com.cn/dceg/data/{date_str}.txt"
```

### If URL requires authentication:
```python
# Use captured headers
headers = {
    "Cookie": "...",  # Might need to refresh periodically
    "Referer": "http://www.dce.com.cn/dceg/channel/list/471.html"
}
response = requests.get(url, headers=headers)
```

---

## Troubleshooting

**Q: Headers don't work, keeps failing**
- Try capturing in incognito/private window
- Clear browser cache and try again
- Check if IP address matters (VPN/proxy)

**Q: Works once, then fails**
- Token/cookie expires → May need to refresh login
- Session-based → Might need to maintain session
- One-time URL → Each click generates new URL

**Q: Can't find the download request**
- Button might trigger JavaScript that creates URL
- Check XHR/Fetch requests, not just documents
- Look for POST requests with response downloads

---

## Next Steps

1. **Try it manually first** - capture and test one URL
2. **Understand the pattern** - does URL change? How often?
3. **Determine refresh strategy** - do tokens expire?
4. **Build automation** - create a scheduled script

---

Need help? Check:
- `PLAYWRIGHT_RESULTS.md` - Other alternatives if this doesn't work
- `FINDINGS.md` - Original research on HTTP approaches
