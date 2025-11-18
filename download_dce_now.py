#!/usr/bin/env python3
"""
Attempt to download DCE data using the token/cookies from user
"""
import json
from datetime import datetime
from curl_cffi import requests

# From the user's POST request
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

PAYLOAD = {
    "varietyId": "all",
    "tradeDate": "20251118",
    "tradeType": "1",
    "contractId": "",
    "lang": "en",
    "optionSeries": "",
    "statisticsType": 0
}

def download_now():
    """Try to download with current token/cookies"""
    print("=" * 80)
    print("Attempting DCE Data Download")
    print("=" * 80)
    print(f"\nURL: {URL[:80]}...")
    print(f"Payload: {json.dumps(PAYLOAD, indent=2)}")
    print(f"\nSending POST request...\n")

    try:
        response = requests.post(
            URL,
            headers=HEADERS,
            json=PAYLOAD,
            timeout=30,
            impersonate="chrome110"
        )

        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Content-Length: {len(response.content)} bytes")

        if response.status_code == 200:
            print("\n🎉 SUCCESS! Got the data!")

            # Parse JSON
            data = response.json()

            # Save JSON
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_file = f"/home/user/mia/downloads/dce_data_{timestamp}.json"

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"\n✅ JSON saved to: {json_file}")

            # Convert to TXT
            txt_file = f"/home/user/mia/downloads/dce_data_{timestamp}.txt"

            with open(txt_file, 'w', encoding='utf-8') as f:
                # Write metadata
                f.write(f"# DCE Daily Quotes - Downloaded {datetime.now()}\n")
                f.write(f"# Status: {data.get('success')}\n")
                f.write(f"# Message: {data.get('msg')}\n")
                f.write(f"# Total Records: {len(data.get('data', []))}\n")
                f.write("#" + "=" * 78 + "\n\n")

                # Write data
                if data.get('data'):
                    entries = data['data']
                    headers = list(entries[0].keys())

                    # Header row
                    f.write('\t'.join(headers) + '\n')

                    # Data rows
                    for entry in entries:
                        row = [str(entry.get(h, '')) for h in headers]
                        f.write('\t'.join(row) + '\n')

            print(f"✅ TXT saved to: {txt_file}")

            # Show stats
            print(f"\n📊 Data Summary:")
            print(f"   Total entries: {len(data.get('data', []))}")
            print(f"   Fields per entry: {len(data.get('data', [{}])[0]) if data.get('data') else 0}")

            # Preview
            print(f"\n📄 First 3 entries:")
            for i, entry in enumerate(data.get('data', [])[:3], 1):
                variety = entry.get('variety', 'N/A')
                contract = entry.get('contractId', 'N/A')
                close = entry.get('close', 'N/A')
                volume = entry.get('volumn', 'N/A')
                print(f"   {i}. {variety} ({contract}) - Close: {close}, Volume: {volume}")

            return True

        elif response.status_code == 400:
            print("\n❌ 400 Bad Request - Token/cookies have expired")
            print(f"Response: {response.text[:200]}")
            return False

        elif response.status_code == 401:
            print("\n❌ 401 Unauthorized - Authentication failed")
            return False

        else:
            print(f"\n❌ Failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import os
    os.makedirs('/home/user/mia/downloads', exist_ok=True)

    success = download_now()

    print("\n" + "=" * 80)
    if success:
        print("✅ DOWNLOAD COMPLETE!")
        print("=" * 80)
        print("\nThe script works! You can now use this anytime with fresh tokens.")
    else:
        print("⏱️  TOKEN EXPIRED (as expected)")
        print("=" * 80)
        print("""
The token/cookies from earlier have expired, but the script is ready!

To download data:
1. Open browser → DevTools → Network tab
2. Visit the DCE page and let it load
3. Copy the fresh POST request (Right-click → Copy as cURL)
4. Update the URL, HEADERS, and PAYLOAD in this script
5. Run: python3 download_dce_now.py

Or I can build a helper script that prompts you for fresh values!
        """)
