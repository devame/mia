#!/usr/bin/env python3
"""
Test the discovered DCE API endpoints
"""
import json
from datetime import datetime
from curl_cffi import requests

# Endpoints provided by user
ENDPOINTS = [
    "http://www.dce.com.cn/dcereport/publicweb/variety?VoGRv6Ir=0GtOdnqlqWJCFPvDUKT_hynwtFw45UGRV2K_AaZ2MesjE1w.X91.L1R22j52BYQAFc4ueeu2vxcqpLfigT.b9sEMWwosfACvijsYQniQyyE1sSqtQ4Uxtqa",
    "http://www.dce.com.cn/dcereport/publicweb/dailystat/dayQuotes?VoGRv6Ir=0v8mYPGlqWJCFPvDUKT_hynwtFw45UGRV2K_AaZ2MesjE1w.X91.L1R22j52BYQAFc4ueeu2vxcroyWEls8uJJmBqzeN2ZB8FIPpJwaAGgF_Tee.3CZbIqG",
    "http://www.dce.com.cn/dcereport/publicweb/variety?VoGRv6Ir=0rn.VkGlqWJCFPvDUKT_hynwtFw45UGRV2K_AaZ2MesjE1w.X91.L1R22j52BYQAFc4ueeu2vxcrEfgg4O0PLd8W4W_.8qyOUQ7YuBL9TeitIVztNrLjMjG",
    "http://www.dce.com.cn/dcereport/publicweb/dailystat/dayQuotes?VoGRv6Ir=0ycNvzqlqWJCFPvDUKT_hynwtFw45UGRV2K_AaZ2MesjE1w.X91.L1R22j52BYQAFc4ueeu2vxccE76CHOQJM_Af4.bOHZDpotxQb9NK2Jt6YeJGXRnihNA",
]

def analyze_url(url):
    """Analyze the URL structure"""
    from urllib.parse import urlparse, parse_qs

    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    print(f"\nPath: {parsed.path}")
    print(f"VoGRv6Ir token: {params.get('VoGRv6Ir', [''])[0][:50]}...")

    return parsed.path, params.get('VoGRv6Ir', [''])[0]

def test_endpoint(url, index):
    """Test a single endpoint"""
    print("\n" + "=" * 80)
    print(f"Testing Endpoint #{index + 1}")
    print("=" * 80)

    # Analyze URL structure
    path, token = analyze_url(url)

    # Test with minimal headers
    print("\n[Attempt 1] Simple GET request...")
    try:
        response = requests.get(
            url,
            timeout=30,
            impersonate="chrome110"
        )

        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"Content-Length: {len(response.content)} bytes")

        if response.status_code == 200:
            print("✅ SUCCESS!")

            # Try to parse as JSON
            content_type = response.headers.get('content-type', '')

            if 'json' in content_type.lower():
                try:
                    data = response.json()
                    print("\n📊 JSON Response received!")

                    # Save JSON
                    filename = f"api_response_{index + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    filepath = f"/home/user/mia/downloads/{filename}"

                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

                    print(f"Saved to: {filepath}")

                    # Show structure
                    print(f"\nData structure:")
                    if isinstance(data, dict):
                        print(f"  Keys: {list(data.keys())}")
                        for key, value in list(data.items())[:3]:
                            print(f"    {key}: {type(value).__name__}")
                            if isinstance(value, list) and len(value) > 0:
                                print(f"      (List with {len(value)} items)")
                                if len(value) > 0:
                                    print(f"      First item: {value[0]}")

                    # Preview
                    preview = json.dumps(data, indent=2, ensure_ascii=False)[:1000]
                    print(f"\nPreview (first 1000 chars):")
                    print(preview)

                    return {'success': True, 'type': 'json', 'data': data, 'url': url}

                except json.JSONDecodeError:
                    print("⚠️  Response claims to be JSON but couldn't parse")
                    print(f"Content preview: {response.text[:500]}")

            else:
                # Might be HTML, text, or other format
                print(f"\n📄 Non-JSON Response received")

                # Save as text
                filename = f"api_response_{index + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                filepath = f"/home/user/mia/downloads/{filename}"

                with open(filepath, 'wb') as f:
                    f.write(response.content)

                print(f"Saved to: {filepath}")

                # Preview
                try:
                    preview = response.text[:1000]
                    print(f"\nPreview (first 1000 chars):")
                    print(preview)
                except:
                    print("\n(Binary content)")

                return {'success': True, 'type': 'other', 'content': response.text[:500], 'url': url}

        else:
            print(f"❌ Failed with status code: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return {'success': False, 'status': response.status_code, 'url': url}

    except Exception as e:
        print(f"❌ Error: {e}")
        return {'success': False, 'error': str(e), 'url': url}

def analyze_vogr_parameter():
    """Analyze the VoGRv6Ir parameter patterns"""
    print("\n" + "=" * 80)
    print("Analyzing VoGRv6Ir Parameter Patterns")
    print("=" * 80)

    from urllib.parse import parse_qs, urlparse

    tokens = []
    for url in ENDPOINTS:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        token = params.get('VoGRv6Ir', [''])[0]
        tokens.append(token)

    print(f"\nFound {len(tokens)} tokens:")
    for i, token in enumerate(tokens, 1):
        print(f"\n  Token {i}:")
        print(f"    Length: {len(token)} chars")
        print(f"    Start: {token[:30]}...")
        print(f"    End: ...{token[-30:]}")

        # Check for common patterns
        common_start = token[:30]
        print(f"    Starts with 0: {'Yes' if token.startswith('0') else 'No'}")

    # Check if tokens share common prefix
    if len(set(t[:20] for t in tokens)) < len(tokens):
        print("\n⚠️  Note: Tokens share common prefixes - might be session/time-based")
    else:
        print("\n✓ Tokens appear unique - might be request-specific")

def main():
    print("=" * 80)
    print("DCE API Endpoint Testing - User-Provided URLs")
    print("=" * 80)
    print(f"\nTesting {len(ENDPOINTS)} endpoints...")

    import os
    os.makedirs('/home/user/mia/downloads', exist_ok=True)

    results = []

    # Test each endpoint
    for i, url in enumerate(ENDPOINTS):
        result = test_endpoint(url, i)
        results.append(result)

    # Analyze VoGRv6Ir parameter
    analyze_vogr_parameter()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    successful = [r for r in results if r.get('success')]
    json_responses = [r for r in results if r.get('type') == 'json']

    print(f"\nTotal endpoints tested: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"JSON responses: {len(json_responses)}")

    if json_responses:
        print("\n✅ SUCCESS! Found working JSON API endpoints:")
        for r in json_responses:
            print(f"\n  URL: {r['url'][:80]}...")
            if 'data' in r:
                data = r['data']
                if isinstance(data, dict):
                    print(f"  Keys: {list(data.keys())}")

    if successful:
        print("\n" + "=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print("""
✅ Found working endpoints!

Next steps:
1. Review the saved JSON/text files in downloads/
2. Identify which endpoint has the data you need
3. Understand the VoGRv6Ir parameter:
   - Is it time-based? (expires)
   - Is it session-based? (needs cookies)
   - Is it request-specific? (needs to be generated)
4. Find how to generate new VoGRv6Ir tokens
5. Look for a TXT export endpoint (or we can convert JSON ourselves)

Check the downloaded files to see the data structure.
        """)
    else:
        print("\n❌ All endpoints failed")
        print("\nPossible reasons:")
        print("- VoGRv6Ir tokens expired")
        print("- Need additional headers (Cookie, Referer)")
        print("- IP restriction")
        print("\nTry capturing fresh URLs from your browser")

if __name__ == "__main__":
    main()
