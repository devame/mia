#!/usr/bin/env python3
"""
Research script to access dce.com.cn and analyze the Text(.txt) button
"""
import json
from curl_cffi import requests
from bs4 import BeautifulSoup

TARGET_URL = "http://www.dce.com.cn/dceg/channel/list/471.html"

def attempt_curl_cffi():
    """Try accessing with curl_cffi which mimics browser TLS fingerprints"""
    print("=" * 60)
    print("Attempt 1: curl_cffi with Chrome impersonation")
    print("=" * 60)

    try:
        # Impersonate Chrome browser
        response = requests.get(
            TARGET_URL,
            impersonate="chrome110",
            timeout=30,
            allow_redirects=True
        )

        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.content)}")
        print(f"Content Type: {response.headers.get('content-type', 'N/A')}")
        print(f"Response Headers:\n{json.dumps(dict(response.headers), indent=2)}")

        if response.status_code == 200:
            # Parse HTML
            soup = BeautifulSoup(response.content, 'lxml')

            # Save full HTML for analysis
            with open('/home/user/mia/page_dump.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            print("\n✓ Page saved to page_dump.html")

            # Look for text/txt buttons
            print("\n" + "=" * 60)
            print("Searching for Text(.txt) related elements...")
            print("=" * 60)

            # Search for various patterns
            txt_buttons = soup.find_all(['button', 'a', 'div', 'span'],
                                       string=lambda text: text and 'txt' in text.lower())

            if txt_buttons:
                print(f"\nFound {len(txt_buttons)} elements containing 'txt':")
                for i, elem in enumerate(txt_buttons, 1):
                    print(f"\n{i}. Tag: {elem.name}")
                    print(f"   Text: {elem.get_text(strip=True)}")
                    print(f"   Attributes: {elem.attrs}")

                    # Check for onclick or href
                    if elem.get('onclick'):
                        print(f"   OnClick: {elem.get('onclick')}")
                    if elem.get('href'):
                        print(f"   Href: {elem.get('href')}")

            # Also search for download links
            print("\n" + "=" * 60)
            print("Searching for download-related elements...")
            print("=" * 60)

            download_links = soup.find_all(['a', 'button'],
                                          attrs={'href': True, 'onclick': True})

            for link in download_links[:10]:  # Show first 10
                if any(keyword in str(link).lower() for keyword in ['download', 'txt', 'text', 'export']):
                    print(f"\nElement: {link.name}")
                    print(f"Text: {link.get_text(strip=True)}")
                    print(f"Attributes: {link.attrs}")

            # Check for JavaScript files that might handle downloads
            print("\n" + "=" * 60)
            print("JavaScript files loaded:")
            print("=" * 60)

            scripts = soup.find_all('script', src=True)
            for script in scripts:
                print(f"  - {script.get('src')}")

            return True
        else:
            print(f"\n✗ Failed with status code: {response.status_code}")
            print(f"Response text (first 500 chars):\n{response.text[:500]}")
            return False

    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {e}")
        return False

def attempt_httpx():
    """Try with httpx and custom headers"""
    print("\n\n" + "=" * 60)
    print("Attempt 2: httpx with browser-like headers")
    print("=" * 60)

    import httpx

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'http://www.dce.com.cn/'
    }

    try:
        response = httpx.get(TARGET_URL, headers=headers, timeout=30, follow_redirects=True)
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.content)}")

        if response.status_code == 200:
            print("✓ Success with httpx!")
            return True
        else:
            print(f"✗ Failed with status code: {response.status_code}")
            return False

    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("DCE Website Research Tool")
    print("Analyzing: http://www.dce.com.cn/dceg/channel/list/471.html")
    print("\n")

    success = attempt_curl_cffi()

    if not success:
        attempt_httpx()

    print("\n" + "=" * 60)
    print("Research complete!")
    print("=" * 60)
