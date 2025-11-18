#!/usr/bin/env python3
"""
Test with playwright-stealth to evade detection
"""
import time
from playwright.sync_api import sync_playwright
try:
    from playwright_stealth import stealth_sync
    has_stealth = True
except ImportError:
    has_stealth = False
    print("Warning: playwright-stealth not installed")

TARGET_URL = "http://www.dce.com.cn/dceg/channel/list/471.html"

def test_with_firefox():
    print("=" * 60)
    print("Test 1: Firefox Browser (different fingerprint)")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.firefox.launch(
            headless=True,
            args=['--no-sandbox']
        )

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            locale='zh-CN',
        )

        page = context.new_page()

        try:
            print("\nNavigating to target page...")
            page.goto(TARGET_URL, wait_until='load', timeout=60000)
            time.sleep(5)

            content = page.content()[:200]
            cookies = context.cookies()

            print(f"Cookies: {len(cookies)}")
            print(f"Content preview: {content}")

            if "Jwt is missing" in page.content():
                print("❌ Still blocked with Firefox")
            else:
                print("✓ Success with Firefox!")
                page.screenshot(path='/home/user/mia/firefox_success.png')

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

def test_with_stealth():
    if not has_stealth:
        print("\n⚠ Skipping stealth test - package not available")
        return

    print("\n" + "=" * 60)
    print("Test 2: Chromium with playwright-stealth")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--single-process',
            ]
        )

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        )

        page = context.new_page()

        # Apply stealth
        stealth_sync(page)

        try:
            print("\nNavigating to target page with stealth...")
            page.goto(TARGET_URL, wait_until='load', timeout=60000)
            time.sleep(5)

            content = page.content()[:200]
            cookies = context.cookies()

            print(f"Cookies: {len(cookies)}")
            print(f"Content preview: {content}")

            if "Jwt is missing" in page.content():
                print("❌ Still blocked even with stealth")
            else:
                print("✓ Success with stealth!")
                page.screenshot(path='/home/user/mia/stealth_success.png')

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_with_firefox()
    test_with_stealth()

    print("\n" + "=" * 60)
    print("Conclusion")
    print("=" * 60)
    print("""
The DCE website has very sophisticated anti-bot protection that:
1. Detects browser automation (Playwright/Selenium)
2. Returns "Jwt is missing" as a blocking message
3. May require:
   - Real browser with manual interaction
   - Undetectable browser automation (very difficult)
   - API access (if available)
   - Different approach entirely

Next steps to consider:
- Try undetected-chromedriver (more stealthy)
- Use real browser profile
- Investigate if there's a mobile app with an API
- Contact the site for official API access
- Use browser extension automation
    """)
