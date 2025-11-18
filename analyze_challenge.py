#!/usr/bin/env python3
"""
Analyze the anti-bot challenge from DCE website
"""
from curl_cffi import requests
from bs4 import BeautifulSoup
import re
import json

TARGET_URL = "http://www.dce.com.cn/dceg/channel/list/471.html"

def analyze_challenge():
    """Analyze the JavaScript challenge"""
    print("Fetching challenge page...")

    response = requests.get(
        TARGET_URL,
        impersonate="chrome110",
        timeout=30
    )

    print(f"Status: {response.status_code}\n")

    # Save the challenge HTML
    with open('/home/user/mia/challenge.html', 'w', encoding='utf-8') as f:
        f.write(response.text)

    print("Challenge HTML saved to challenge.html")
    print("\n" + "=" * 60)
    print("Analyzing challenge structure...")
    print("=" * 60)

    soup = BeautifulSoup(response.text, 'lxml')

    # Extract meta tag with challenge data
    meta_tag = soup.find('meta', id='9wq7NOeAWkjr')
    if meta_tag:
        print(f"\nChallenge Meta Tag:")
        print(f"  ID: {meta_tag.get('id')}")
        print(f"  Content: {meta_tag.get('content')[:100]}...")
        print(f"  Attribute 'r': {meta_tag.get('r')}")

    # Extract all scripts
    print("\n" + "=" * 60)
    print("JavaScript Code Analysis:")
    print("=" * 60)

    scripts = soup.find_all('script')
    for i, script in enumerate(scripts, 1):
        if script.string:
            code = script.string.strip()
            if code:
                print(f"\nScript {i}:")
                print(f"  Type: {script.get('type', 'text/javascript')}")
                print(f"  Attribute 'r': {script.get('r')}")
                print(f"  Length: {len(code)} chars")

                # Look for key variables
                if '$_ts' in code:
                    print("  ✓ Contains $_ts (challenge system)")
                if 'cookie' in code.lower():
                    print("  ✓ Contains cookie operations")
                if 'reload' in code.lower() or 'location' in code.lower():
                    print("  ✓ Contains redirect/reload logic")

                # Print first 300 chars
                print(f"  Preview:\n{code[:300]}")

    # Extract cookies
    print("\n" + "=" * 60)
    print("Cookies Set:")
    print("=" * 60)
    print(json.dumps(dict(response.cookies), indent=2))

    # Check if there's a noscript fallback
    noscript = soup.find('noscript')
    if noscript:
        print("\n" + "=" * 60)
        print("NoScript Fallback:")
        print("=" * 60)
        print(noscript.get_text(strip=True))

    print("\n" + "=" * 60)
    print("Recommendations:")
    print("=" * 60)
    print("""
This site uses JavaScript-based anti-bot protection that:
1. Sets challenge cookies
2. Executes JavaScript to verify the client
3. Redirects to the actual page after verification

HTTP-only approaches will NOT work here.

RECOMMENDED SOLUTION: Use Playwright/Puppeteer
- They can execute JavaScript and handle the challenge automatically
- Stealth plugins can help avoid detection
- Can properly wait for the page to load after challenge
    """)

if __name__ == "__main__":
    analyze_challenge()
