#!/usr/bin/env python3
"""
DCE Data Downloader - Semi-Automated Tool

This script downloads DCE commodity futures data.
You provide a fresh token/cookies, it downloads and converts to TXT automatically.

Usage:
    python3 dce_downloader.py --curl "PASTE_CURL_COMMAND_HERE"

Or edit the config section below with fresh values.
"""
import json
import re
import sys
import argparse
from datetime import datetime
from curl_cffi import requests

# ============================================================================
# CONFIGURATION - Update these with fresh values from your browser
# ============================================================================

DEFAULT_CONFIG = {
    "url": "http://www.dce.com.cn/dcereport/publicweb/dailystat/dayQuotes?VoGRv6Ir=PASTE_FRESH_TOKEN_HERE",
    "headers": {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Cookie": "PASTE_FRESH_COOKIES_HERE",
        "Referer": "http://www.dce.com.cn/frontend/dcereport/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "clientId": "web",
    },
    "payload": {
        "varietyId": "all",
        "tradeDate": datetime.now().strftime("%Y%m%d"),  # Today's date
        "tradeType": "1",
        "contractId": "",
        "lang": "en",
        "optionSeries": "",
        "statisticsType": 0
    }
}

def parse_curl(curl_command):
    """Parse a cURL command into config"""
    print("Parsing cURL command...")

    # Extract URL
    url_match = re.search(r"curl\s+'([^']+)'", curl_command) or \
                re.search(r'curl\s+"([^"]+)"', curl_command) or \
                re.search(r'curl\s+(\S+)', curl_command)

    if not url_match:
        print("❌ Could not extract URL from cURL")
        return None

    url = url_match.group(1)

    # Extract headers
    headers = {}
    for match in re.finditer(r"-H\s+'([^:]+):\s*([^']+)'", curl_command):
        headers[match.group(1)] = match.group(2)
    for match in re.finditer(r'-H\s+"([^:]+):\s*([^"]+)"', curl_command):
        headers[match.group(1)] = match.group(2)

    # Extract POST data
    data = None
    data_match = re.search(r"--data-raw\s+'([^']+)'", curl_command) or \
                 re.search(r'--data-raw\s+"([^"]+)"', curl_command) or \
                 re.search(r"--data\s+'([^']+)'", curl_command) or \
                 re.search(r'--data\s+"([^"]+)"', curl_command)

    if data_match:
        try:
            data = json.loads(data_match.group(1))
        except:
            data = data_match.group(1)

    return {"url": url, "headers": headers, "payload": data}

def download_data(config):
    """Download DCE data using the provided config"""
    print("=" * 80)
    print("DCE Data Downloader")
    print("=" * 80)

    url = config['url']
    headers = config['headers']
    payload = config.get('payload', {})

    # Check if token is placeholder
    if 'PASTE_FRESH_TOKEN_HERE' in url:
        print("\n❌ ERROR: You need to update the token in the URL!")
        print("\nPlease either:")
        print("1. Run with --curl flag and paste your cURL command")
        print("2. Edit dce_downloader.py and update DEFAULT_CONFIG")
        return False

    print(f"\n📡 Endpoint: /dailystat/dayQuotes")
    print(f"📅 Trade Date: {payload.get('tradeDate', 'N/A')}")
    print(f"🌐 Language: {payload.get('lang', 'N/A')}")
    print(f"📊 Variety: {payload.get('varietyId', 'N/A')}")

    print(f"\n⏳ Sending request...")

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30,
            impersonate="chrome110"
        )

        print(f"📥 Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ SUCCESS! Data received!")

            # Parse response
            data = response.json()

            # Generate filenames
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            trade_date = payload.get('tradeDate', 'unknown')

            json_file = f"/home/user/mia/downloads/dce_{trade_date}_{timestamp}.json"
            txt_file = f"/home/user/mia/downloads/dce_{trade_date}_{timestamp}.txt"

            # Save JSON
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"\n💾 JSON saved: {json_file}")

            # Convert to TXT
            convert_to_txt(data, txt_file, payload)

            print(f"💾 TXT saved: {txt_file}")

            # Show summary
            print(f"\n" + "=" * 80)
            print("📊 Data Summary")
            print("=" * 80)

            total = len(data.get('data', []))
            print(f"Total entries: {total}")

            if data.get('data'):
                # Count by variety
                varieties = {}
                for entry in data['data']:
                    v = entry.get('variety', 'Unknown')
                    varieties[v] = varieties.get(v, 0) + 1

                print(f"\nTop 10 commodities:")
                for i, (variety, count) in enumerate(sorted(varieties.items(), key=lambda x: -x[1])[:10], 1):
                    print(f"  {i}. {variety}: {count} contracts")

            print(f"\n✅ Download complete!")
            return True

        elif response.status_code == 400:
            print(f"\n❌ 400 Bad Request - Token/cookies expired")
            print(f"\n💡 Solution: Get fresh credentials from your browser:")
            print("   1. Open DCE page in browser")
            print("   2. DevTools (F12) → Network tab")
            print("   3. Let page load (captures POST request)")
            print("   4. Right-click request → Copy as cURL")
            print("   5. Run: python3 dce_downloader.py --curl 'PASTE_HERE'")
            return False

        elif response.status_code == 401:
            print(f"\n❌ 401 Unauthorized - Authentication failed")
            return False

        else:
            print(f"\n❌ Failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def convert_to_txt(data, output_file, payload):
    """Convert JSON to tab-separated TXT file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write metadata
        f.write(f"# DCE Daily Quotes\n")
        f.write(f"# Downloaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Trade Date: {payload.get('tradeDate', 'N/A')}\n")
        f.write(f"# Status: {data.get('success')}\n")
        f.write(f"# Message: {data.get('msg')}\n")
        f.write(f"# Total Records: {len(data.get('data', []))}\n")
        f.write("#" + "=" * 78 + "\n\n")

        # Write data table
        if data.get('data'):
            entries = data['data']
            headers = list(entries[0].keys())

            # Header row
            f.write('\t'.join(headers) + '\n')

            # Data rows
            for entry in entries:
                row = [str(entry.get(h, '')) for h in headers]
                f.write('\t'.join(row) + '\n')

def main():
    parser = argparse.ArgumentParser(
        description='Download DCE commodity futures data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using cURL command (recommended):
  python3 dce_downloader.py --curl "curl 'http://www.dce.com.cn/...' -H 'Cookie: ...' ..."

  # Using custom date:
  python3 dce_downloader.py --date 20251117

  # Using config file:
  Edit DEFAULT_CONFIG in this script, then:
  python3 dce_downloader.py
        """
    )

    parser.add_argument('--curl', help='Paste cURL command from browser DevTools')
    parser.add_argument('--date', help='Trade date in YYYYMMDD format (default: today)')
    parser.add_argument('--lang', choices=['en', 'zh'], default='en', help='Language (default: en)')

    args = parser.parse_args()

    import os
    os.makedirs('/home/user/mia/downloads', exist_ok=True)

    # Determine config source
    if args.curl:
        print("Using cURL command...")
        config = parse_curl(args.curl)
        if not config:
            print("❌ Failed to parse cURL command")
            return 1
    else:
        print("Using default configuration...")
        config = DEFAULT_CONFIG.copy()

    # Apply overrides
    if args.date:
        config['payload']['tradeDate'] = args.date

    if args.lang:
        config['payload']['lang'] = args.lang

    # Download
    success = download_data(config)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
