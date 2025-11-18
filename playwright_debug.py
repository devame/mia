#!/usr/bin/env python3
"""
Debug script to understand the JWT requirement
"""
import json
import time
from playwright.sync_api import sync_playwright

TARGET_URL = "http://www.dce.com.cn/dceg/channel/list/471.html"
MAIN_URL = "http://www.dce.com.cn/"

def debug_dce():
    print("=" * 60)
    print("DCE Website Debug - Understanding JWT Requirement")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--single-process']
        )

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            locale='zh-CN',
        )

        page = context.new_page()

        # Enable console logging
        page.on('console', lambda msg: print(f"  [CONSOLE] {msg.type}: {msg.text}"))

        # Track network requests
        requests_log = []
        page.on('request', lambda request: requests_log.append({
            'url': request.url,
            'method': request.method,
            'headers': dict(request.headers)
        }))

        try:
            print("\n[Step 1] Visiting main page...")
            page.goto(MAIN_URL, wait_until='load', timeout=60000)
            time.sleep(3)

            # Get cookies after main page
            cookies = context.cookies()
            print(f"\n[Cookies after main page] ({len(cookies)} total):")
            for cookie in cookies:
                print(f"  {cookie['name']}: {cookie['value'][:50]}...")

            # Check localStorage and sessionStorage
            local_storage = page.evaluate("() => JSON.stringify(localStorage)")
            session_storage = page.evaluate("() => JSON.stringify(sessionStorage)")

            print(f"\n[LocalStorage]: {local_storage}")
            print(f"[SessionStorage]: {session_storage}")

            print("\n[Step 2] Navigating to target page...")
            page.goto(TARGET_URL, wait_until='load', timeout=60000)
            time.sleep(5)

            # Get cookies after target page
            cookies = context.cookies()
            print(f"\n[Cookies after target page] ({len(cookies)} total):")
            for cookie in cookies:
                print(f"  {cookie['name']}: {cookie['value'][:50]}...")

            # Check localStorage again
            local_storage = page.evaluate("() => JSON.stringify(localStorage)")
            session_storage = page.evaluate("() => JSON.stringify(sessionStorage)")

            print(f"\n[LocalStorage after]: {local_storage}")
            print(f"[SessionStorage after]: {session_storage}")

            # Get page content
            content = page.content()
            print(f"\n[Page Content]:")
            print(content[:500])

            # Check for any iframes
            frames = page.frames
            print(f"\n[Frames] Found {len(frames)} frames:")
            for i, frame in enumerate(frames):
                print(f"  Frame {i}: {frame.url}")

            # Save request log
            print(f"\n[Network Requests] Total: {len(requests_log)}")
            with open('/home/user/mia/requests_log.json', 'w') as f:
                json.dump(requests_log[-20:], f, indent=2)  # Last 20 requests
            print("  Last 20 requests saved to requests_log.json")

            # Take screenshot
            page.screenshot(path='/home/user/mia/debug_screenshot.png', full_page=True)
            print("\n  Screenshot saved to debug_screenshot.png")

        except Exception as e:
            print(f"\nError: {e}")

        finally:
            browser.close()

if __name__ == "__main__":
    debug_dce()
