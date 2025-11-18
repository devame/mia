#!/usr/bin/env python3
"""
Playwright script to access DCE website and click Text(.txt) button
"""
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

TARGET_URL = "http://www.dce.com.cn/dceg/channel/list/471.html"

def access_dce_website():
    print("=" * 60)
    print("DCE Website Automation with Playwright")
    print("=" * 60)

    with sync_playwright() as p:
        # Launch browser in headless mode with additional stability args
        print("\n[1/7] Launching Chromium browser (headless)...")
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-extensions',
                '--disable-web-security',  # Sometimes needed for CORS
                '--single-process',  # Use single process to avoid crashes
            ]
        )

        # Create context with realistic settings
        print("[2/7] Creating browser context...")
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
        )

        # Add extra headers
        context.set_extra_http_headers({
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })

        page = context.new_page()

        # Hide webdriver property
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        try:
            # First, visit the main site to establish session and get JWT
            print("[3/7] Visiting main site to establish session...")
            main_url = "http://www.dce.com.cn/"
            page.goto(main_url, wait_until='load', timeout=60000)
            print("      ✓ Main page loaded!")
            time.sleep(3)

            # Now navigate to the target page
            print(f"[4/7] Navigating to target page: {TARGET_URL}...")
            print("      (This may take a moment as anti-bot challenge is solved...)")

            # Navigate with load event (more stable than networkidle)
            page.goto(TARGET_URL, wait_until='load', timeout=60000)

            print("      ✓ Target page loaded!")
            print("      Waiting for JavaScript and dynamic content to load...")

            # Wait for the page to stabilize
            time.sleep(5)

            print("      ✓ Page should be ready!")

            # Get page title
            title = page.title()
            print(f"\n[5/7] Page Title: {title}")

            # Take screenshot for inspection
            screenshot_path = '/home/user/mia/screenshot_after_load.png'
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"[6/7] Screenshot saved to: {screenshot_path}")

            # Get page URL (might have redirected)
            current_url = page.url
            print(f"      Current URL: {current_url}")

            # Look for Text(.txt) button
            print("\n[7/8] Searching for Text(.txt) button...")

            # Try multiple selectors
            selectors_to_try = [
                "text=/.*txt.*/i",  # Case-insensitive text containing 'txt'
                "text=/.*文本.*/i",  # Chinese for 'text'
                "text=/.*Text.*/i",  # Case-sensitive Text
                "button:has-text('txt')",
                "a:has-text('txt')",
                "[title*='txt' i]",
                "[alt*='txt' i]",
            ]

            found_button = None
            for selector in selectors_to_try:
                try:
                    element = page.locator(selector).first
                    if element.count() > 0:
                        text = element.text_content()
                        print(f"      ✓ Found element with selector: {selector}")
                        print(f"        Text: {text}")
                        found_button = element
                        break
                except Exception as e:
                    continue

            if not found_button:
                # Fallback: get all clickable elements and print them
                print("\n      No Text(.txt) button found with common selectors.")
                print("      Analyzing page for all clickable elements...")

                # Get all buttons and links
                buttons = page.locator('button, a, [role="button"]').all()
                print(f"\n      Found {len(buttons)} clickable elements:")

                for i, btn in enumerate(buttons[:20], 1):  # Show first 20
                    try:
                        text = btn.text_content()[:50] if btn.text_content() else ""
                        attrs = btn.evaluate("el => Array.from(el.attributes).map(a => `${a.name}=${a.value}`).join(' ')")
                        print(f"\n      {i}. Text: {text}")
                        print(f"         Attributes: {attrs[:100]}...")
                    except:
                        pass

                # Save HTML for analysis
                html_content = page.content()
                with open('/home/user/mia/page_source.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"\n      Full page HTML saved to: /home/user/mia/page_source.html")

                print("\n[8/8] Could not find Text(.txt) button automatically.")
                print("      Please review screenshot and HTML to identify the button.")

            else:
                print(f"\n[8/8] Attempting to click button...")

                # Try to click
                try:
                    # Scroll into view
                    found_button.scroll_into_view_if_needed()

                    # Wait for download
                    with page.expect_download(timeout=30000) as download_info:
                        found_button.click()
                        download = download_info.value

                        # Save the download
                        save_path = f'/home/user/mia/downloads/{download.suggested_filename}'
                        download.save_as(save_path)
                        print(f"      ✓ File downloaded: {save_path}")
                        print(f"      File size: {download.path().stat().st_size} bytes")

                except PlaywrightTimeout:
                    print("      ! Click succeeded but no download detected within 30s")
                    print("      Button might open a new page or require additional steps")

                    # Take another screenshot
                    page.screenshot(path='/home/user/mia/screenshot_after_click.png', full_page=True)
                    print("      Screenshot after click saved to: screenshot_after_click.png")

                except Exception as e:
                    print(f"      ✗ Error clicking: {e}")

            # Wait a moment before closing
            print("\n" + "=" * 60)
            print("Execution complete. Closing browser...")
            print("=" * 60)
            time.sleep(2)

        except Exception as e:
            print(f"\n✗ Error: {type(e).__name__}: {e}")

            # Take screenshot of error state
            try:
                page.screenshot(path='/home/user/mia/screenshot_error.png', full_page=True)
                print(f"Error screenshot saved to: screenshot_error.png")
            except:
                pass

        finally:
            browser.close()
            print("\nBrowser closed.")

if __name__ == "__main__":
    # Create downloads directory
    import os
    os.makedirs('/home/user/mia/downloads', exist_ok=True)

    access_dce_website()
