#!/usr/bin/env python3
"""
Intercept and analyze JSON API calls from DCE website

Since the page loads data via JSON, then sends it to a server-side script
for .txt conversion, we need to find:
1. The JSON data API endpoint
2. The server-side .txt conversion endpoint

This script monitors ALL network requests to identify them.
"""

import json
import time
from playwright.sync_api import sync_playwright
from datetime import datetime

TARGET_URL = "http://www.dce.com.cn/dceg/channel/list/471.html"
OUTPUT_DIR = "/home/user/mia/api_analysis"

class NetworkMonitor:
    def __init__(self):
        self.requests = []
        self.responses = []
        self.json_apis = []
        self.download_endpoints = []

    def on_request(self, request):
        """Capture all outgoing requests"""
        req_data = {
            'timestamp': datetime.now().isoformat(),
            'url': request.url,
            'method': request.method,
            'resource_type': request.resource_type,
            'headers': dict(request.headers),
        }

        # Check for POST data
        if request.method == 'POST':
            try:
                req_data['post_data'] = request.post_data
            except:
                pass

        self.requests.append(req_data)

        # Flag potential JSON APIs
        if request.resource_type in ['xhr', 'fetch']:
            print(f"  [XHR/Fetch] {request.method} {request.url}")

    def on_response(self, response):
        """Capture all responses"""
        resp_data = {
            'timestamp': datetime.now().isoformat(),
            'url': response.url,
            'status': response.status,
            'headers': dict(response.headers),
            'request_method': response.request.method,
            'resource_type': response.request.resource_type,
        }

        # Try to get response body for JSON responses
        content_type = response.headers.get('content-type', '')

        if 'json' in content_type.lower():
            try:
                body = response.text()
                resp_data['body'] = body
                resp_data['body_json'] = json.loads(body)
                resp_data['is_json'] = True

                print(f"  [JSON Response] {response.url}")
                print(f"    Status: {response.status}")
                print(f"    Size: {len(body)} bytes")

                self.json_apis.append(resp_data)
            except Exception as e:
                resp_data['body_error'] = str(e)

        # Check for download responses
        content_disposition = response.headers.get('content-disposition', '')
        if 'attachment' in content_disposition or '.txt' in response.url:
            print(f"  [Download] {response.url}")
            print(f"    Content-Disposition: {content_disposition}")

            try:
                body = response.body()
                resp_data['body_size'] = len(body)
                resp_data['is_download'] = True

                # Save the actual file
                filename = f"downloaded_file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                filepath = f"{OUTPUT_DIR}/{filename}"
                with open(filepath, 'wb') as f:
                    f.write(body)
                resp_data['saved_to'] = filepath
                print(f"    Saved to: {filepath}")

                self.download_endpoints.append(resp_data)
            except Exception as e:
                resp_data['body_error'] = str(e)

        self.responses.append(resp_data)

def analyze_network_traffic():
    """Monitor network traffic and find API endpoints"""
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 70)
    print("DCE API Interception - Finding JSON and Download Endpoints")
    print("=" * 70)

    monitor = NetworkMonitor()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--single-process']
        )

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN',
        )

        page = context.new_page()

        # Attach network listeners
        page.on('request', monitor.on_request)
        page.on('response', monitor.on_response)

        # Enable console logging
        page.on('console', lambda msg: print(f"  [Console] {msg.text}"))

        try:
            print("\n[Step 1] Loading main page...")
            page.goto("http://www.dce.com.cn/", wait_until='load', timeout=60000)
            time.sleep(3)

            print("\n[Step 2] Loading target page...")
            print(f"URL: {TARGET_URL}")
            page.goto(TARGET_URL, wait_until='load', timeout=60000)
            time.sleep(5)

            print("\n[Step 3] Waiting for dynamic content and API calls...")
            time.sleep(5)

            # Try to find and click the Text(.txt) button
            print("\n[Step 4] Looking for Text(.txt) button...")

            # Get page content to analyze
            content = page.content()

            if "Jwt is missing" in content:
                print("  ⚠️  Still blocked - 'Jwt is missing' error")
                print("  However, we may have captured some API endpoints before blocking")
            else:
                print("  ✓ Page loaded successfully")

                # Try to find button
                selectors = [
                    "text=/.*txt.*/i",
                    "text=/.*文本.*/i",
                    "button:has-text('txt')",
                    "a:has-text('txt')",
                    "[title*='txt' i]",
                ]

                button_found = False
                for selector in selectors:
                    try:
                        element = page.locator(selector).first
                        if element.count() > 0:
                            print(f"  ✓ Found button with selector: {selector}")
                            print("  Clicking button and monitoring network...")

                            # Click and wait for network activity
                            element.click()
                            time.sleep(5)

                            button_found = True
                            break
                    except:
                        continue

                if not button_found:
                    print("  ⚠️  Could not find button, but monitoring network anyway")

            print("\n[Step 5] Network capture complete")

        except Exception as e:
            print(f"\n⚠️  Error during page load: {e}")
            print("Analyzing captured requests anyway...")

        finally:
            browser.close()

    # Analyze captured data
    print("\n" + "=" * 70)
    print("ANALYSIS RESULTS")
    print("=" * 70)

    print(f"\n[Total Requests Captured]: {len(monitor.requests)}")
    print(f"[Total Responses Captured]: {len(monitor.responses)}")
    print(f"[JSON API Calls]: {len(monitor.json_apis)}")
    print(f"[Download Endpoints]: {len(monitor.download_endpoints)}")

    # Detailed JSON API analysis
    if monitor.json_apis:
        print("\n" + "=" * 70)
        print("JSON API ENDPOINTS FOUND")
        print("=" * 70)

        for i, api in enumerate(monitor.json_apis, 1):
            print(f"\n[API #{i}]")
            print(f"  URL: {api['url']}")
            print(f"  Method: {api['request_method']}")
            print(f"  Status: {api['status']}")

            if 'body_json' in api:
                print(f"  Response Preview:")
                preview = json.dumps(api['body_json'], indent=2, ensure_ascii=False)[:500]
                print(f"    {preview}...")

            # Save full response
            filename = f"json_api_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = f"{OUTPUT_DIR}/{filename}"

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(api, f, indent=2, ensure_ascii=False)

            print(f"  Saved to: {filepath}")

    # Detailed download analysis
    if monitor.download_endpoints:
        print("\n" + "=" * 70)
        print("DOWNLOAD ENDPOINTS FOUND")
        print("=" * 70)

        for i, dl in enumerate(monitor.download_endpoints, 1):
            print(f"\n[Download #{i}]")
            print(f"  URL: {dl['url']}")
            print(f"  Method: {dl['request_method']}")
            print(f"  Size: {dl.get('body_size', 'N/A')} bytes")
            print(f"  Saved to: {dl.get('saved_to', 'N/A')}")

    # Save all requests for detailed analysis
    all_requests_file = f"{OUTPUT_DIR}/all_requests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(all_requests_file, 'w', encoding='utf-8') as f:
        json.dump({
            'requests': monitor.requests,
            'responses': [r for r in monitor.responses if 'body_json' not in r],  # Exclude large bodies
            'json_apis': monitor.json_apis,
            'download_endpoints': monitor.download_endpoints,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[Complete Network Log]: {all_requests_file}")

    # Recommendations
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)

    if monitor.json_apis:
        print("""
✓ Found JSON API endpoints!

Next steps:
1. Review the JSON API responses in api_analysis/
2. Identify which API returns the data you need
3. Find the parameters (date, product, etc.)
4. Call the JSON API directly with Python requests
5. Convert the JSON to .txt yourself (or find the conversion endpoint)

Check the saved JSON files to see the data structure.
        """)
    elif monitor.download_endpoints:
        print("""
✓ Found download endpoints!

The .txt file was downloaded. Check:
- The download URL pattern
- Required headers/cookies
- Whether it needs the JSON data as input

You may be able to call this endpoint directly.
        """)
    else:
        print("""
⚠️  No JSON APIs or downloads captured.

This could mean:
1. Page is blocked (check for "Jwt is missing")
2. Data loads after page load (try manual browser inspection)
3. Button click triggers the API (couldn't find button)

Recommended:
- Check api_analysis/all_requests_*.json for all network activity
- Try manual inspection in real browser with DevTools
        """)

    print(f"\nAll files saved to: {OUTPUT_DIR}/")

if __name__ == "__main__":
    analyze_network_traffic()
