#!/usr/bin/env python3
"""
Test script for captured download URLs from DCE website

Usage:
1. Manually capture the download URL using a real browser (see MANUAL_URL_CAPTURE_GUIDE.md)
2. Save the information to captured_request.json
3. Run this script: python3 test_captured_url.py
"""

import json
import os
from datetime import datetime
from curl_cffi import requests

# Configuration file
CONFIG_FILE = '/home/user/mia/captured_request.json'
DOWNLOAD_DIR = '/home/user/mia/downloads'

def load_config():
    """Load captured request configuration"""
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ Config file not found: {CONFIG_FILE}")
        print("\nPlease create the file with this format:")
        print(json.dumps({
            "url": "http://www.dce.com.cn/dceg/api/download/...",
            "method": "GET",
            "headers": {
                "Cookie": "JSESSIONID=...; _jwt_token=...",
                "Referer": "http://www.dce.com.cn/dceg/channel/list/471.html",
                "User-Agent": "Mozilla/5.0 ...",
                "X-Requested-With": "XMLHttpRequest"
            },
            "data": {}
        }, indent=2))
        return None

    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def test_url_simple(url):
    """Test 1: Simple GET request (no auth)"""
    print("\n" + "=" * 60)
    print("Test 1: Simple GET (no authentication)")
    print("=" * 60)

    try:
        response = requests.get(url, timeout=30, impersonate="chrome110")

        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"Content-Length: {len(response.content)} bytes")

        if response.status_code == 200:
            # Try to save
            filename = f"download_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = os.path.join(DOWNLOAD_DIR, filename)

            with open(filepath, 'wb') as f:
                f.write(response.content)

            print(f"✅ SUCCESS! Downloaded to: {filepath}")
            print(f"Preview (first 200 chars):\n{response.text[:200]}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_url_with_headers(config):
    """Test 2: Request with captured headers"""
    print("\n" + "=" * 60)
    print("Test 2: With Captured Headers")
    print("=" * 60)

    url = config['url']
    headers = config.get('headers', {})
    method = config.get('method', 'GET').upper()
    data = config.get('data', {})

    print(f"URL: {url}")
    print(f"Method: {method}")
    print(f"Headers: {len(headers)} headers")

    try:
        if method == 'POST':
            response = requests.post(
                url,
                headers=headers,
                data=data,
                timeout=30,
                impersonate="chrome110"
            )
        else:
            response = requests.get(
                url,
                headers=headers,
                timeout=30,
                impersonate="chrome110"
            )

        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"Content-Length: {len(response.content)} bytes")

        if response.status_code == 200:
            # Save the file
            filename = f"download_authenticated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = os.path.join(DOWNLOAD_DIR, filename)

            with open(filepath, 'wb') as f:
                f.write(response.content)

            print(f"✅ SUCCESS! Downloaded to: {filepath}")
            print(f"File size: {os.path.getsize(filepath)} bytes")

            # Show preview
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    preview = f.read(500)
                print(f"\nPreview (first 500 chars):\n{preview}")
            except:
                print("\n(Binary file - cannot preview as text)")

            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_url_from_curl(curl_command):
    """Test 3: Parse and execute a cURL command"""
    print("\n" + "=" * 60)
    print("Test 3: From cURL Command")
    print("=" * 60)

    # This is a simplified parser - for complex cases, use a library
    print("⚠️  Note: For best results, use the JSON config format")
    print("Trying basic cURL parsing...")

    # Extract URL (first quoted string after 'curl')
    import re
    url_match = re.search(r"curl\s+'([^']+)'", curl_command)
    if not url_match:
        url_match = re.search(r'curl\s+"([^"]+)"', curl_command)
    if not url_match:
        url_match = re.search(r'curl\s+(\S+)', curl_command)

    if not url_match:
        print("❌ Could not parse URL from cURL command")
        return False

    url = url_match.group(1)
    print(f"Extracted URL: {url}")

    # Extract headers
    header_pattern = re.compile(r"-H\s+'([^:]+):\s*([^']+)'")
    headers = {}
    for match in header_pattern.finditer(curl_command):
        headers[match.group(1)] = match.group(2)

    print(f"Extracted {len(headers)} headers")

    return test_url_with_headers({
        'url': url,
        'method': 'GET',
        'headers': headers
    })

def main():
    print("=" * 60)
    print("DCE Download URL Tester")
    print("=" * 60)

    # Create download directory
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Load config
    config = load_config()

    if not config:
        print("\n" + "=" * 60)
        print("Quick Start:")
        print("=" * 60)
        print("1. Follow MANUAL_URL_CAPTURE_GUIDE.md to capture the download URL")
        print("2. Create captured_request.json with the URL and headers")
        print("3. Run this script again")
        print("\nAlternatively, edit this script and add the URL directly in test_url_simple()")
        return

    # Run tests
    url = config.get('url')

    if not url:
        print("❌ No URL found in config")
        return

    # Test 1: Simple (rarely works with protected sites)
    success1 = test_url_simple(url)

    if not success1:
        # Test 2: With headers (most likely to work)
        success2 = test_url_with_headers(config)

        if success2:
            print("\n" + "=" * 60)
            print("✅ SUCCESS! The URL works with authentication headers")
            print("=" * 60)
            print("\nNext steps:")
            print("1. You can now automate downloads using this URL pattern")
            print("2. Monitor if tokens expire (retest after a few hours)")
            print("3. Check if URL pattern changes daily (date in URL?)")
        else:
            print("\n" + "=" * 60)
            print("❌ All tests failed")
            print("=" * 60)
            print("\nPossible reasons:")
            print("1. Token/session expired (capture and test quickly)")
            print("2. IP restriction (must request from same IP)")
            print("3. Additional security checks (user-agent, referer)")
            print("4. URL is one-time use only")
            print("\nTry:")
            print("- Capture and test immediately (within 1 minute)")
            print("- Ensure all headers are copied (especially Cookie)")
            print("- Check if URL contains a timestamp or session ID")
    else:
        print("\n" + "=" * 60)
        print("✅ SUCCESS! URL is publicly accessible")
        print("=" * 60)

if __name__ == "__main__":
    main()
