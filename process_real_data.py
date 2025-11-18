#!/usr/bin/env python3
"""
Process the actual JSON response we got from the user
"""
import json
from datetime import datetime

# The actual JSON response from DCE API
RAW_JSON = '''{"success":true,"code":200,"msg":"操作成功","requestId":"0b87927e-d4c2-4db5-855b-0f598abf095e","data":[{"variety":"No.1 Soybeans","contractId":"a2601","open":"4215","high":"4218","low":"4165","close":"4178","lastClear":"4182","clearPrice":"4187","diff":"-4","diff1":"5","delta":null,"volumn":150656,"openInterest":278781,"diffI":-8699,"turnover":"6308994.33","matchQtySum":0,"diffT":null,"volumnRate":null,"openInterestRate":null,"periodOverPeriodChg":null,"diffV":null,"impliedVolatility":null,"seriesId":null},{"variety":"No.1 Soybeans","contractId":"a2603","open":"4211","high":"4219","low":"4170","close":"4182","lastClear":"4186","clearPrice":"4191","diff":"-4","diff1":"5","delta":null,"volumn":12678,"openInterest":53345,"diffI":466,"turnover":"531448.69","matchQtySum":0,"diffT":null,"volumnRate":null,"openInterestRate":null,"periodOverPeriodChg":null,"diffV":null,"impliedVolatility":null,"seriesId":null}]}'''

def analyze_json():
    """Analyze the JSON structure"""
    print("=" * 80)
    print("Analyzing DCE JSON Response")
    print("=" * 80)

    data = json.loads(RAW_JSON)

    print(f"\n✅ Status: {data['success']}")
    print(f"✅ Code: {data['code']}")
    print(f"✅ Message: {data['msg']}")
    print(f"✅ Request ID: {data['requestId']}")
    print(f"✅ Data entries: {len(data['data'])}")

    # Show first entry structure
    if data['data']:
        print("\n" + "=" * 80)
        print("Sample Data Entry (First Record)")
        print("=" * 80)
        first_entry = data['data'][0]
        for key, value in first_entry.items():
            print(f"  {key}: {value}")

    # Save JSON
    json_file = f"/home/user/mia/downloads/dce_real_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Full JSON saved to: {json_file}")

    # Convert to TXT
    convert_to_txt(data, json_file.replace('.json', '.txt'))

def convert_to_txt(data, output_file):
    """Convert JSON to TXT format"""
    print("\n" + "=" * 80)
    print("Converting to TXT Format")
    print("=" * 80)

    with open(output_file, 'w', encoding='utf-8') as f:
        # Write metadata
        f.write(f"# DCE Daily Quotes\n")
        f.write(f"# Status: {data['success']}\n")
        f.write(f"# Request ID: {data['requestId']}\n")
        f.write(f"# Total Records: {len(data['data'])}\n")
        f.write("#" + "=" * 78 + "\n\n")

        # Get all keys from first entry
        if data['data']:
            headers = list(data['data'][0].keys())

            # Write header row
            f.write('\t'.join(headers) + '\n')

            # Write data rows
            for entry in data['data']:
                row = [str(entry.get(h, '')) for h in headers]
                f.write('\t'.join(row) + '\n')

    print(f"✅ TXT file saved to: {output_file}")

    # Show preview
    with open(output_file, 'r', encoding='utf-8') as f:
        preview = f.read(1500)
    print(f"\nTXT Preview (first 1500 chars):\n")
    print(preview)
    print("...\n")

if __name__ == "__main__":
    analyze_json()

    print("\n" + "=" * 80)
    print("🎉 SUCCESS! We now have real data from the DCE API!")
    print("=" * 80)
    print("""
This JSON contains:
- Commodity futures trading data
- Fields: variety, contractId, open, high, low, close, volume, etc.
- Multiple contracts for different commodities

Next steps:
1. Build automation script to call this API daily
2. Figure out how to generate/refresh the VoGRv6Ir token
3. Schedule automated downloads
    """)
