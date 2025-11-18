# DCE Website Automation Research

## Target URL
`http://www.dce.com.cn/dceg/channel/list/471.html`

## Objective
Click the "Text(.txt)" button to download data from the Dalian Commodity Exchange website.

---

## Findings

### 1. Anti-Bot Protection Detected

The website uses **JavaScript-based anti-bot protection**:

- **Status Code**: 412 (Precondition Failed)
- **WAF/Proxy**: Envoy
- **Protection System**: Custom JavaScript challenge (`$_ts` system)

### 2. Protection Mechanism

The challenge works as follows:

```
1. Initial request returns 412 with challenge HTML
2. Challenge HTML contains:
   - Obfuscated JavaScript code in $_ts.cd variable
   - External JS file: /7Q0VMJNkEpeQ/SkblPG4BwpES.cfd114a.js
   - Execution trigger: _$_v() function
3. JavaScript executes and computes challenge response
4. Sets verification cookies
5. Redirects/reloads to actual page
```

**Challenge HTML structure:**
```html
<meta id="9wq7NOeAWkjr" content="[obfuscated data]" r='m'>
<script>
  $_ts=window['$_ts'];
  $_ts.nsd=28627;
  $_ts.cd="[large obfuscated string]";
  if($_ts.lcd)$_ts.lcd();
</script>
<script src="/7Q0VMJNkEpeQ/SkblPG4BwpES.cfd114a.js"></script>
<script>_$_v();</script>
```

**Cookies set:**
```
hNUS9DnJtejwS=607DkcGUvCQuGBVsUbhHXkRTxD6Dsj...
```

### 3. HTTP Approaches Tested (All Failed)

#### ❌ curl_cffi with Chrome impersonation
- Result: 412 error
- Reason: Cannot execute JavaScript

#### ❌ httpx with browser-like headers
- Result: 412 error
- Reason: Cannot execute JavaScript

---

## Conclusion

**HTTP-only solutions will NOT work** because:
1. The site requires JavaScript execution to solve the challenge
2. The challenge response is computed client-side
3. Cookies are set dynamically based on JavaScript execution
4. Simple header spoofing is insufficient

---

## Recommended Solution: Browser Automation

### Option A: Playwright (Python) ⭐ **RECOMMENDED**

**Advantages:**
- Modern, fast, and reliable
- Better stealth capabilities
- Excellent documentation
- Can handle JavaScript challenges automatically

**Setup:**
```bash
pip install playwright playwright-stealth
playwright install chromium
```

**Sample code:**
```python
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

def access_dce_and_download():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Use headless=True in production
        page = browser.new_page()

        # Apply stealth
        stealth_sync(page)

        # Navigate (will handle JavaScript challenge automatically)
        page.goto('http://www.dce.com.cn/dceg/channel/list/471.html')

        # Wait for page to load after challenge
        page.wait_for_load_state('networkidle')

        # Find and click the Text(.txt) button
        txt_button = page.locator('text=/.*txt.*/i').first
        txt_button.click()

        # Handle download
        with page.expect_download() as download_info:
            download = download_info.value
            download.save_as('/path/to/save/file.txt')

        browser.close()
```

### Option B: Selenium with Undetected ChromeDriver

**Setup:**
```bash
pip install undetected-chromedriver
```

**Note:** Less recommended as it's easier to detect than Playwright.

---

## Next Steps

1. Install Playwright with stealth plugin
2. Write script to navigate to page (handles challenge automatically)
3. Locate the "Text(.txt)" button
4. Click and handle download
5. Test and refine

---

## Files Generated

- `requirements.txt` - Python dependencies for HTTP testing
- `research_dce.py` - Initial HTTP research script
- `analyze_challenge.py` - Challenge analysis script
- `challenge.html` - Raw challenge page HTML
- `FINDINGS.md` - This document
