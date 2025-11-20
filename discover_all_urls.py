"""
Run URL discoverer on all exchanges and update CSV with findings
"""

import sqlite3
import csv
from url_discoverer import CalendarURLDiscoverer
import time


def discover_all_exchange_urls():
    """Discover calendar URLs for all exchanges"""

    # Get all exchanges from database
    conn = sqlite3.connect('exchange_holidays.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT iso_code, exchange_name, base_url, calendar_url
        FROM exchanges
        ORDER BY country, exchange_name
    """)

    exchanges = cursor.fetchall()
    conn.close()

    discoverer = CalendarURLDiscoverer(timeout=15, max_depth=2)

    results = []
    success_count = 0
    fail_count = 0

    print(f"\nDiscovering URLs for {len(exchanges)} exchanges...")
    print("="*80)

    for iso_code, name, base_url, current_url in exchanges:
        print(f"\n[{iso_code}] {name}")
        print(f"  Current URL: {current_url}")
        print(f"  Base URL: {base_url}")

        # Discover new URL
        discovered_url = discoverer.discover(base_url, name)

        if discovered_url:
            success_count += 1
            status = "✓ FOUND"
            results.append({
                'iso_code': iso_code,
                'name': name,
                'base_url': base_url,
                'old_url': current_url,
                'new_url': discovered_url,
                'status': 'found'
            })
        else:
            fail_count += 1
            status = "✗ NOT FOUND"
            results.append({
                'iso_code': iso_code,
                'name': name,
                'base_url': base_url,
                'old_url': current_url,
                'new_url': current_url,  # Keep old URL
                'status': 'not_found'
            })

        print(f"  Result: {status}")

        # Be polite - don't hammer servers
        time.sleep(2)

    # Print summary
    print("\n" + "="*80)
    print("DISCOVERY SUMMARY")
    print("="*80)
    print(f"Total exchanges: {len(exchanges)}")
    print(f"URLs found: {success_count}")
    print(f"URLs not found: {fail_count}")
    print(f"Success rate: {success_count/len(exchanges)*100:.1f}%")

    # Show changes
    print("\n" + "="*80)
    print("URL CHANGES")
    print("="*80)

    for result in results:
        if result['status'] == 'found' and result['old_url'] != result['new_url']:
            print(f"\n{result['iso_code']} - {result['name']}")
            print(f"  Old: {result['old_url']}")
            print(f"  New: {result['new_url']}")

    # Save results to CSV
    output_file = 'discovered_urls.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['iso_code', 'name', 'base_url', 'old_url', 'new_url', 'status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✓ Results saved to {output_file}")

    return results


if __name__ == '__main__':
    discover_all_exchange_urls()
