#!/usr/bin/env python3
"""
Test the POST request with full headers and cookies
"""
import json
from datetime import datetime
from curl_cffi import requests

URL = "http://www.dce.com.cn/dcereport/publicweb/dailystat/dayQuotes?VoGRv6Ir=0ycNvzqlqWJCFPvDUKT_hynwtFw45UGRV2K_AaZ2MesjE1w.X91.L1R22j52BYQAFc4ueeu2vxccE76CHOQJM_Af4.bOHZDpotxQb9NK2Jt6YeJGXRnihNA"

HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.8',
    'Access-Control-Allow-Origin-Type': '*',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Cookie': 'hNUS9DnJtejwS=60K6aH.QiNbE3mJL.3cjvz4gUBr4fjm1WSe3G97.0OBqp4iPhscSKjPPTQm0uQ2ErsNwgsl39hTHwrDqegKXDwja; SESSION=Y2ZhY2M3YWUtYmMyMC00MGY2LWEzMDEtNGUyNzgyNzA3NDc3; hNUS9DnJtejwT=0hTpiNp5kWUz8PXhQEdtWSIuUFtg1i7b48H52L2aqJ0Z.z8LBvUXA_nHDvooPGND97EX7lNN4vJW21kZ3mQlOitZkbNXZ8d96szjKWJurNRpBnxbH4x5YZ49lbGyNVBAI08eCGoT7Q4RW.UG4AZPfD8rk9zCcIUcxswLdZAUMM6mz9psmfOevXLJITe_bQOnOg7Ta0dGKubUyBBWqKhrr4s2AxG3vf0Ih0WG_8TCk6a_8ZTk.hTpZGgsaj1HH6sABR3Z6t_plgthjXigY39WBWXOikp831thkLZjgpJDBuUhQ3UyVpSCuMB3BDaCOgg7jmBG7ZhdxDWB4P6R5oiMCd0KK5503CR5ECvr4xnPM.LmYZpnMhHJnRWTdwouGBJswOpleGG47RvloZhAyj9YpmGFnV96aeOB._7fpiUJExB0_EU6a4g_S4L2Mur1IoP7KeV8tooj_z39aOO88g2P6GWAc45RWs2u2XVIAeuCcOTW',
    'DNT': '1',
    'Host': 'www.dce.com.cn',
    'Origin': 'http://www.dce.com.cn',
    'Pragma': 'no-cache',
    'Referer': 'http://www.dce.com.cn/frontend/dcereport/',
    'Sec-GPC': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'clientId': 'web',
}

# The Content-Length was 123, so there should be POST data
# We need to know what JSON was sent - trying some common patterns

POSSIBLE_BODIES = [
    # Common date query patterns
    {"date": datetime.now().strftime("%Y-%m-%d")},
    {"tradingDay": datetime.now().strftime("%Y-%m-%d")},
    {"queryDate": datetime.now().strftime("%Y-%m-%d")},
    {"startDate": datetime.now().strftime("%Y-%m-%d"), "endDate": datetime.now().strftime("%Y-%m-%d")},

    # With variety/commodity
    {"variety": "all", "date": datetime.now().strftime("%Y-%m-%d")},
    {"commodityId": "", "tradingDay": datetime.now().strftime("%Y-%m-%d")},

    # Empty (maybe all data in URL)
    {},
]

def test_with_body(body, index):
    """Test POST request with a specific body"""
    print(f"\n[Test #{index + 1}] POST body: {json.dumps(body)}")

    try:
        response = requests.post(
            URL,
            headers=HEADERS,
            json=body,
            timeout=30,
            impersonate="chrome110"
        )

        print(f"  Status: {response.status_code}")
        print(f"  Content-Type: {response.headers.get('content-type')}")
        print(f"  Content-Length: {len(response.content)} bytes")

        if response.status_code == 200:
            print("  ✅ SUCCESS!")

            # Try to parse JSON
            try:
                data = response.json()

                # Save it
                filename = f"success_response_{index + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                filepath = f"/home/user/mia/downloads/{filename}"

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                print(f"  Saved to: {filepath}")

                # Show preview
                preview = json.dumps(data, indent=2, ensure_ascii=False)[:800]
                print(f"\n  Preview:\n{preview}...\n")

                return True

            except json.JSONDecodeError:
                print(f"  Response (not JSON): {response.text[:300]}")

        elif response.status_code == 400:
            print(f"  ❌ 400 Bad Request - wrong POST body format")
            print(f"  Response: {response.text[:200]}")
        elif response.status_code == 401:
            print(f"  ❌ 401 Unauthorized - cookies may have expired")
        else:
            print(f"  ❌ Failed: {response.status_code}")
            print(f"  Response: {response.text[:200]}")

    except Exception as e:
        print(f"  ❌ Error: {e}")

    return False

def main():
    print("=" * 80)
    print("Testing POST Request with Captured Headers")
    print("=" * 80)
    print(f"\nURL: {URL[:80]}...")
    print(f"Method: POST")
    print(f"Has Cookies: Yes (3 cookies)")
    print(f"\n⚠️  NOTE: Content-Length was 123 bytes in your capture.")
    print("We need the actual POST body (JSON data sent with the request).")
    print("\nTrying common POST body patterns...\n")

    import os
    os.makedirs('/home/user/mia/downloads', exist_ok=True)

    # Try different body patterns
    success = False
    for i, body in enumerate(POSSIBLE_BODIES):
        if test_with_body(body, i):
            success = True
            print("\n" + "=" * 80)
            print("✅ FOUND WORKING REQUEST!")
            print("=" * 80)
            print(f"\nWorking POST body: {json.dumps(body, indent=2)}")
            break

    if not success:
        print("\n" + "=" * 80)
        print("❌ None of the test bodies worked")
        print("=" * 80)
        print("""
We need the actual POST body that was sent with this request.

In Chrome DevTools:
1. Find this request in the Network tab
2. Click on it
3. Go to "Payload" or "Request" tab
4. Copy the JSON data shown there

It should look something like:
{
  "tradingDay": "2025-11-18",
  "variety": "a",
  ...
}

Once you have that, I can test with the correct POST body!

Alternatively, right-click the request → "Copy as cURL" and paste the full command.
        """)

if __name__ == "__main__":
    main()
