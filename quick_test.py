#!/usr/bin/env python3
"""
Quick test tool - paste fresh request details and test immediately

INSTRUCTIONS:
1. In your browser, open DevTools and click the Text(.txt) button
2. Right-click the POST request → Copy as cURL
3. Paste the cURL command below in the CURL_COMMAND variable
4. Run this script immediately (within 1 minute)

Alternatively, manually fill in the sections below.
"""
import json
import re
from datetime import datetime
from curl_cffi import requests

# ============================================================================
# OPTION 1: Paste your cURL command here (easiest!)
# ============================================================================
CURL_COMMAND = """
# Paste your "Copy as cURL" command here
# Example:
# curl 'http://www.dce.com.cn/dcereport/publicweb/dailystat/dayQuotes?VoGRv6Ir=...' \
#   -H 'Cookie: ...' \
#   --data-raw '{"varietyId":"all",...}'
"""

# ============================================================================
# OPTION 2: Or manually fill these (if cURL doesn't work)
# ============================================================================
MANUAL_CONFIG = {
    "url": "http://www.dce.com.cn/dcereport/publicweb/dailystat/dayQuotes?VoGRv6Ir=PASTE_NEW_TOKEN_HERE",
    "headers": {
        "Cookie": "PASTE_FRESH_COOKIES_HERE",
        "Content-Type": "application/json",
        "Referer": "http://www.dce.com.cn/frontend/dcereport/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    },
    "payload": {
        "varietyId": "all",
        "tradeDate": "20251118",  # Update to today's date (YYYYMMDD)
        "tradeType": "1",
        "contractId": "",
        "lang": "en",
        "optionSeries": "",
        "statisticsType": 0
    }
}

def parse_curl_command(curl_cmd):
    """Parse a cURL command to extract URL, headers, and data"""
    if not curl_cmd.strip() or curl_cmd.strip().startswith('#'):
        return None

    # Extract URL
    url_match = re.search(r"curl\s+'([^']+)'", curl_cmd)
    if not url_match:
        url_match = re.search(r'curl\s+"([^"]+)"', curl_cmd)
    if not url_match:
        url_match = re.search(r'curl\s+(\S+)', curl_cmd)

    if not url_match:
        print("❌ Could not extract URL from cURL command")
        return None

    url = url_match.group(1)

    # Extract headers
    headers = {}
    header_pattern = re.compile(r"-H\s+'([^:]+):\s*([^']+)'")
    for match in header_pattern.finditer(curl_cmd):
        headers[match.group(1)] = match.group(2)

    # Also try double quotes
    header_pattern2 = re.compile(r'-H\s+"([^:]+):\s*([^"]+)"')
    for match in header_pattern2.finditer(curl_cmd):
        headers[match.group(1)] = match.group(2)

    # Extract POST data
    data = None
    data_match = re.search(r"--data-raw\s+'([^']+)'", curl_cmd)
    if not data_match:
        data_match = re.search(r'--data-raw\s+"([^"]+)"', curl_cmd)
    if not data_match:
        data_match = re.search(r"--data\s+'([^']+)'", curl_cmd)
    if not data_match:
        data_match = re.search(r'--data\s+"([^"]+)"', curl_cmd)

    if data_match:
        try:
            data = json.loads(data_match.group(1))
        except:
            data = data_match.group(1)

    return {"url": url, "headers": headers, "payload": data}

def test_request(config):
    """Test the request"""
    print("=" * 80)
    print("Testing DCE API Request")
    print("=" * 80)

    url = config['url']
    headers = config['headers']
    payload = config.get('payload', {})

    print(f"\nURL: {url[:100]}...")
    print(f"Payload: {json.dumps(payload, indent=2) if payload else 'None'}")
    print(f"Headers: {len(headers)} headers")
    print("\nSending request...\n")

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30,
            impersonate="chrome110"
        )

        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Size: {len(response.content)} bytes")

        if response.status_code == 200:
            print("\n🎉 SUCCESS!")

            # Save response
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Try JSON
            try:
                data = response.json()

                json_file = f"/home/user/mia/downloads/success_{timestamp}.json"
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                print(f"\n✅ Saved JSON to: {json_file}")

                # Also save as TXT
                txt_file = f"/home/user/mia/downloads/success_{timestamp}.txt"
                with open(txt_file, 'w', encoding='utf-8') as f:
                    if isinstance(data, dict) and 'data' in data:
                        items = data['data']
                        if items and isinstance(items[0], dict):
                            # Write header
                            headers_list = list(items[0].keys())
                            f.write('\t'.join(headers_list) + '\n')
                            # Write rows
                            for item in items:
                                row = [str(item.get(h, '')) for h in headers_list]
                                f.write('\t'.join(row) + '\n')

                print(f"✅ Saved TXT to: {txt_file}")

                # Preview
                preview = json.dumps(data, indent=2, ensure_ascii=False)[:1000]
                print(f"\nPreview:\n{preview}...")

                return True

            except:
                # Not JSON
                txt_file = f"/home/user/mia/downloads/success_{timestamp}.txt"
                with open(txt_file, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Saved to: {txt_file}")
                print(f"\nContent:\n{response.text[:500]}")

        else:
            print(f"\n❌ Failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")

            if response.status_code == 400:
                print("\n⏱️  Token/cookies likely expired")
                print("Get fresh data and try again within 30 seconds")

    except Exception as e:
        print(f"\n❌ Error: {e}")

def main():
    import os
    os.makedirs('/home/user/mia/downloads', exist_ok=True)

    print("=" * 80)
    print("DCE Quick Test Tool")
    print("=" * 80)

    # Try to parse cURL command first
    config = parse_curl_command(CURL_COMMAND)

    if config:
        print("\n✓ Using cURL command")
        test_request(config)
    else:
        print("\n✓ Using manual configuration")
        test_request(MANUAL_CONFIG)

    print("\n" + "=" * 80)
    print("Tips:")
    print("=" * 80)
    print("""
For best results:
1. Open browser → DevTools → Network tab
2. Click Text(.txt) button
3. Right-click the POST request → Copy as cURL
4. Paste in this script at CURL_COMMAND
5. Run immediately (within 30 seconds)

The VoGRv6Ir tokens expire very quickly!
    """)

if __name__ == "__main__":
    main()
