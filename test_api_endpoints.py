#!/usr/bin/env python3
"""
Test captured API endpoints for JSON → TXT workflow

This script tests the two-step process:
1. Call JSON API to get data
2. Call TXT conversion endpoint (or convert ourselves)
"""

import json
import os
from datetime import datetime
from curl_cffi import requests

CONFIG_FILE = '/home/user/mia/captured_api_endpoints.json'
DOWNLOAD_DIR = '/home/user/mia/downloads'

def load_config():
    """Load captured API endpoint configuration"""
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ Config file not found: {CONFIG_FILE}")
        print("\nPlease create the file with this format:")
        print(json.dumps({
            "json_api": {
                "url": "http://www.dce.com.cn/dceg/api/data/list",
                "method": "GET",
                "headers": {
                    "Cookie": "JSESSIONID=...",
                    "Referer": "http://www.dce.com.cn/dceg/channel/list/471.html"
                },
                "params": {
                    "date": "2025-11-18"
                }
            },
            "txt_conversion": {
                "url": "http://www.dce.com.cn/dceg/api/export/txt",
                "method": "POST",
                "headers": {
                    "Cookie": "JSESSIONID=...",
                    "Content-Type": "application/json"
                },
                "note": "Body will be the JSON data from json_api"
            }
        }, indent=2))
        return None

    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def call_json_api(config):
    """Step 1: Call the JSON API to get data"""
    print("\n" + "=" * 70)
    print("STEP 1: Getting JSON Data")
    print("=" * 70)

    api_config = config.get('json_api')
    if not api_config:
        print("❌ No json_api configuration found")
        return None

    url = api_config['url']
    method = api_config.get('method', 'GET').upper()
    headers = api_config.get('headers', {})
    params = api_config.get('params', {})
    body = api_config.get('body', {})

    print(f"URL: {url}")
    print(f"Method: {method}")
    print(f"Parameters: {params}")

    try:
        if method == 'POST':
            response = requests.post(
                url,
                headers=headers,
                params=params,
                json=body,
                timeout=30,
                impersonate="chrome110"
            )
        else:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=30,
                impersonate="chrome110"
            )

        print(f"\nStatus Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")

        if response.status_code == 200:
            # Try to parse JSON
            try:
                json_data = response.json()
                print(f"✓ Successfully retrieved JSON data")
                print(f"Response size: {len(response.content)} bytes")

                # Save JSON for inspection
                json_file = os.path.join(DOWNLOAD_DIR, f'api_response_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)

                print(f"Saved to: {json_file}")

                # Show preview
                preview = json.dumps(json_data, indent=2, ensure_ascii=False)[:500]
                print(f"\nPreview:\n{preview}...")

                return json_data

            except json.JSONDecodeError:
                print("⚠️  Response is not JSON")
                print(f"Content preview: {response.text[:200]}")
                return response.text

        else:
            print(f"❌ Failed with status code: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None

    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def convert_to_txt_via_api(json_data, config):
    """Step 2: Call the TXT conversion endpoint"""
    print("\n" + "=" * 70)
    print("STEP 2: Converting JSON to TXT via API")
    print("=" * 70)

    conversion_config = config.get('txt_conversion')
    if not conversion_config:
        print("⚠️  No txt_conversion endpoint configured")
        print("Will convert JSON to TXT locally instead")
        return convert_to_txt_locally(json_data)

    url = conversion_config['url']
    method = conversion_config.get('method', 'POST').upper()
    headers = conversion_config.get('headers', {})

    print(f"URL: {url}")
    print(f"Method: {method}")

    try:
        if method == 'POST':
            response = requests.post(
                url,
                headers=headers,
                json=json_data,
                timeout=30,
                impersonate="chrome110"
            )
        else:
            # For GET, might need to encode JSON in URL params
            response = requests.get(
                url,
                headers=headers,
                params={'data': json.dumps(json_data)},
                timeout=30,
                impersonate="chrome110"
            )

        print(f"\nStatus Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")

        if response.status_code == 200:
            # Save the TXT file
            txt_file = os.path.join(DOWNLOAD_DIR, f'converted_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
            with open(txt_file, 'wb') as f:
                f.write(response.content)

            print(f"✓ Successfully converted and downloaded")
            print(f"Saved to: {txt_file}")
            print(f"File size: {os.path.getsize(txt_file)} bytes")

            # Show preview
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    preview = f.read(500)
                print(f"\nPreview:\n{preview}")
            except:
                print("\n(Binary file or encoding issue)")

            return txt_file

        else:
            print(f"❌ Failed with status code: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nFalling back to local conversion...")
        return convert_to_txt_locally(json_data)

def convert_to_txt_locally(json_data):
    """Fallback: Convert JSON to TXT locally using Python"""
    print("\n" + "=" * 70)
    print("STEP 2: Converting JSON to TXT Locally (Python)")
    print("=" * 70)

    if not json_data:
        print("❌ No JSON data to convert")
        return None

    try:
        txt_file = os.path.join(DOWNLOAD_DIR, f'converted_local_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')

        with open(txt_file, 'w', encoding='utf-8') as f:
            # Generic conversion - adapt based on your data structure
            if isinstance(json_data, dict):
                # If it's an object with a data array
                if 'data' in json_data and isinstance(json_data['data'], list):
                    for item in json_data['data']:
                        # Convert each item to tab-separated values
                        if isinstance(item, dict):
                            line = '\t'.join(str(v) for v in item.values())
                            f.write(line + '\n')
                        else:
                            f.write(str(item) + '\n')
                else:
                    # Just dump the JSON in readable format
                    json.dump(json_data, f, indent=2, ensure_ascii=False)

            elif isinstance(json_data, list):
                # If it's directly a list
                for item in json_data:
                    if isinstance(item, dict):
                        line = '\t'.join(str(v) for v in item.values())
                        f.write(line + '\n')
                    else:
                        f.write(str(item) + '\n')
            else:
                # Just write as string
                f.write(str(json_data))

        print(f"✓ Successfully converted locally")
        print(f"Saved to: {txt_file}")
        print(f"File size: {os.path.getsize(txt_file)} bytes")

        # Show preview
        with open(txt_file, 'r', encoding='utf-8') as f:
            preview = f.read(500)
        print(f"\nPreview:\n{preview}")

        print("\n⚠️  Note: This is a generic conversion.")
        print("You may need to customize the format based on your needs.")

        return txt_file

    except Exception as e:
        print(f"❌ Error during local conversion: {e}")
        return None

def main():
    print("=" * 70)
    print("DCE API Endpoint Tester - JSON → TXT Workflow")
    print("=" * 70)

    # Create download directory
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Load config
    config = load_config()
    if not config:
        print("\n" + "=" * 70)
        print("Quick Start:")
        print("=" * 70)
        print("1. Follow MANUAL_API_CAPTURE_GUIDE.md to capture the API endpoints")
        print("2. Create captured_api_endpoints.json with the configuration")
        print("3. Run this script again")
        return

    # Step 1: Get JSON data
    json_data = call_json_api(config)

    if not json_data:
        print("\n" + "=" * 70)
        print("❌ FAILED: Could not retrieve JSON data")
        print("=" * 70)
        print("\nCheck:")
        print("- Is the URL correct?")
        print("- Are headers/cookies still valid?")
        print("- Try capturing fresh credentials")
        return

    # Step 2: Convert to TXT
    txt_file = convert_to_txt_via_api(json_data, config)

    if txt_file:
        print("\n" + "=" * 70)
        print("✅ SUCCESS! Full workflow completed")
        print("=" * 70)
        print(f"\nTXT file: {txt_file}")
        print("\nYou can now automate this workflow:")
        print("1. Call JSON API to get data")
        print("2. Convert to TXT (via API or locally)")
        print("3. Save to your desired location")
    else:
        print("\n" + "=" * 70)
        print("⚠️  PARTIAL SUCCESS")
        print("=" * 70)
        print("\nWe got the JSON data but couldn't convert to TXT")
        print("Check the saved JSON file and convert manually")

if __name__ == "__main__":
    main()
