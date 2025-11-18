#!/usr/bin/env python3
"""
Test the complete POST request with actual payload
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

# The actual payload from user
PAYLOAD = {
    "varietyId": "all",
    "tradeDate": "20251118",
    "tradeType": "1",
    "contractId": "",
    "lang": "en",
    "optionSeries": "",
    "statisticsType": 0
}

def test_complete_request():
    """Test with complete request including payload"""
    print("=" * 80)
    print("Testing COMPLETE Request with Actual Payload")
    print("=" * 80)
    print(f"\nURL: {URL[:80]}...")
    print(f"Method: POST")
    print(f"Payload: {json.dumps(PAYLOAD, indent=2)}")
    print("\nSending request...")

    try:
        response = requests.post(
            URL,
            headers=HEADERS,
            json=PAYLOAD,
            timeout=30,
            impersonate="chrome110"
        )

        print(f"\n✓ Response received!")
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Content-Length: {len(response.content)} bytes")

        if response.status_code == 200:
            print("\n🎉 SUCCESS! Got data from the API!")

            # Try to parse as JSON
            try:
                data = response.json()

                # Save the response
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                json_file = f"/home/user/mia/downloads/dce_data_{timestamp}.json"

                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                print(f"\n✅ JSON saved to: {json_file}")

                # Analyze the structure
                print("\n" + "=" * 80)
                print("Data Structure Analysis")
                print("=" * 80)

                if isinstance(data, dict):
                    print(f"\nTop-level keys: {list(data.keys())}")

                    for key, value in data.items():
                        print(f"\n  {key}:")
                        print(f"    Type: {type(value).__name__}")

                        if isinstance(value, list):
                            print(f"    Length: {len(value)} items")
                            if len(value) > 0:
                                print(f"    First item: {value[0]}")
                        elif isinstance(value, dict):
                            print(f"    Keys: {list(value.keys())[:5]}")
                        else:
                            print(f"    Value: {value}")

                # Show preview
                preview = json.dumps(data, indent=2, ensure_ascii=False)
                if len(preview) > 1500:
                    preview = preview[:1500] + "\n... (truncated)"

                print("\n" + "=" * 80)
                print("Response Preview")
                print("=" * 80)
                print(preview)

                # Try to convert to TXT
                print("\n" + "=" * 80)
                print("Converting to TXT Format")
                print("=" * 80)

                txt_file = f"/home/user/mia/downloads/dce_data_{timestamp}.txt"
                convert_to_txt(data, txt_file)

                print(f"\n✅ TXT file saved to: {txt_file}")

                # Show TXT preview
                with open(txt_file, 'r', encoding='utf-8') as f:
                    txt_preview = f.read(1000)
                print("\nTXT Preview (first 1000 chars):")
                print(txt_preview)

                return True

            except json.JSONDecodeError:
                print("\n⚠️  Response is not JSON")
                print(f"Content: {response.text[:500]}")

                # Save as text
                txt_file = f"/home/user/mia/downloads/dce_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(txt_file, 'wb') as f:
                    f.write(response.content)
                print(f"Saved to: {txt_file}")

        elif response.status_code == 400:
            print("\n❌ 400 Bad Request")
            print(f"Response: {response.text}")
            print("\nThe payload might be incorrect or VoGRv6Ir token expired")
        elif response.status_code == 401:
            print("\n❌ 401 Unauthorized")
            print("Cookies have expired - need fresh cookies from browser")
        else:
            print(f"\n❌ Failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

def convert_to_txt(data, output_file):
    """Convert JSON data to TXT format"""
    with open(output_file, 'w', encoding='utf-8') as f:
        # Handle different data structures
        if isinstance(data, dict):
            # Check for common patterns
            if 'data' in data and isinstance(data['data'], list):
                # Tabular data
                items = data['data']

                if len(items) > 0 and isinstance(items[0], dict):
                    # Write header
                    headers = list(items[0].keys())
                    f.write('\t'.join(headers) + '\n')

                    # Write rows
                    for item in items:
                        row = [str(item.get(h, '')) for h in headers]
                        f.write('\t'.join(row) + '\n')
                else:
                    # Just write each item on a line
                    for item in items:
                        f.write(str(item) + '\n')
            else:
                # Just format as JSON
                json.dump(data, f, indent=2, ensure_ascii=False)

        elif isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                # Tabular data
                headers = list(data[0].keys())
                f.write('\t'.join(headers) + '\n')

                for item in data:
                    row = [str(item.get(h, '')) for h in headers]
                    f.write('\t'.join(row) + '\n')
            else:
                for item in data:
                    f.write(str(item) + '\n')
        else:
            f.write(str(data))

    print(f"  ✓ Converted to TXT format")

if __name__ == "__main__":
    import os
    os.makedirs('/home/user/mia/downloads', exist_ok=True)

    success = test_complete_request()

    if success:
        print("\n" + "=" * 80)
        print("🎉 BREAKTHROUGH! We can now automate this!")
        print("=" * 80)
        print("""
Next steps:
1. Review the JSON and TXT files to see if this is the data you need
2. Figure out how to generate the VoGRv6Ir token (or if we can reuse it)
3. Understand the tradeDate format (YYYYMMDD)
4. Create an automation script

Key parameters you can change:
- tradeDate: "20251118" (YYYYMMDD format)
- varietyId: "all" (or specific variety)
- lang: "en" (or "zh" for Chinese)
        """)
    else:
        print("\n" + "=" * 80)
        print("Troubleshooting")
        print("=" * 80)
        print("""
If it failed:
1. VoGRv6Ir token might have expired - get a fresh one
2. Cookies might have expired - copy fresh cookies
3. The payload might need adjustment

To get fresh data:
- Open the page in your browser
- Click the Text(.txt) button again
- Copy the new request details (headers, payload, VoGRv6Ir)
        """)
