# DCE Data Downloader - Ready to Use!

## Quick Start (30 seconds)

### Step 1: Get Fresh Token from Browser

1. Open http://www.dce.com.cn/dceg/channel/list/471.html in Chrome/Firefox
2. Press **F12** (open DevTools)
3. Go to **Network** tab
4. **Let the page load** (it will make the API call automatically)
5. Find the POST request to `/dailystat/dayQuotes`
6. Right-click → **Copy → Copy as cURL**

### Step 2: Download Data

```bash
python3 dce_downloader.py --curl "PASTE_YOUR_CURL_COMMAND_HERE"
```

**Done!** Files saved to `downloads/` folder:
- `dce_YYYYMMDD_timestamp.json` (raw JSON)
- `dce_YYYYMMDD_timestamp.txt` (tab-separated text)

---

## Examples

### Download Today's Data
```bash
# Get fresh cURL from browser, then:
python3 dce_downloader.py --curl "curl 'http://www.dce.com.cn/dcereport/...' ..."
```

### Download Specific Date
```bash
python3 dce_downloader.py --curl "..." --date 20251117
```

### Chinese Language
```bash
python3 dce_downloader.py --curl "..." --lang zh
```

---

## What Gets Downloaded

### Data includes:
- **All commodities**: Soybeans, Corn, Iron Ore, Eggs, Palm Oil, PVC, etc.
- **Contract details**: Contract ID, variety name
- **Price data**: Open, High, Low, Close, Clear Price
- **Volume data**: Volume, Open Interest, Turnover
- **Changes**: Daily change, difference from last clear

### Sample output:
```
variety              contractId  open   high   low    close  volume   turnover
No.1 Soybeans        a2601       4215   4218   4165   4178   150656   6308994.33
Corn                 c2601       2188   2188   2171   2182   500087   10901553.43
Iron Ore             i2601       769    791    767.5  788.5  351270   27449024.80
```

---

## Why Tokens Expire

The **VoGRv6Ir** token expires in ~30 minutes for security.

**Solutions:**
1. **Manual (Current)**: Get fresh token each time (takes 30 seconds)
2. **Script**: Run daily when you need data
3. **Cron job**: Schedule with fresh token generation (advanced)

---

## Files

| File | Purpose |
|------|---------|
| `dce_downloader.py` | Main downloader script |
| `download_dce_now.py` | Simple test script |
| `quick_test.py` | Quick token tester |
| `README_DOWNLOADER.md` | This guide |

---

## Troubleshooting

### "400 Bad Request"
→ Token expired. Get fresh one from browser (takes 30 seconds)

### "401 Unauthorized"
→ Cookies expired. Get fresh cURL command

### "Could not parse cURL"
→ Make sure to copy the ENTIRE cURL command including headers

### No data downloaded
→ Check the trade date - markets might be closed

---

## Advanced Usage

### Edit Default Config

Instead of using `--curl` every time, edit `dce_downloader.py`:

```python
DEFAULT_CONFIG = {
    "url": "http://www.dce.com.cn/dcereport/publicweb/dailystat/dayQuotes?VoGRv6Ir=YOUR_TOKEN",
    "headers": {
        "Cookie": "YOUR_COOKIES",
        # ...
    },
    # ...
}
```

Then just run:
```bash
python3 dce_downloader.py
```

### Automation Script

Create a shell script:
```bash
#!/bin/bash
# download_dce.sh

echo "Paste your cURL command:"
read curl_cmd

python3 dce_downloader.py --curl "$curl_cmd"
```

---

## What We Accomplished

✅ **Complete API understanding** - Exact endpoint, payload, response format
✅ **Working downloader** - Gets data in seconds
✅ **Auto-conversion** - JSON → TXT automatically
✅ **Proven with real data** - Tested with actual DCE response

**Only limitation:** Token expires (unavoidable with this level of security)

**Solution:** 30-second manual token refresh when needed (acceptable for daily use)

---

## Full Automation (Future)

To make this 100% automated:

1. Use `undetected-chromedriver` to maintain browser session
2. Auto-refresh tokens
3. Schedule with cron

This requires more setup but is doable. Let me know if you want this!

---

## Support

The token/cookies expire quickly by design (security feature).

**Current workflow (optimal):**
1. When you need data: Open browser (F12)
2. Copy cURL command (10 seconds)
3. Run script (5 seconds)
4. Get JSON + TXT files (instant)

**Total time: ~30 seconds for complete data download**

This is actually pretty efficient for a daily task!
