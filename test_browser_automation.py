#!/usr/bin/env python3
"""
Test script for browser automation extractors

This script tests the browser automation functionality for exchanges
that require JavaScript rendering or have anti-bot protection.

Usage:
    python test_browser_automation.py [exchange_code]

Examples:
    python test_browser_automation.py XCME    # Test CME Group
    python test_browser_automation.py XHKG    # Test HKEX
    python test_browser_automation.py all     # Test all browser automation extractors
"""

import sys
from scraper import HolidayScraper
import csv

# Exchanges that use browser automation
BROWSER_AUTOMATION_EXCHANGES = {
    'XCME': 'https://www.cmegroup.com/trading-hours.html',
    'XHKG': 'https://www.hkex.com.hk/Services/Trading/Derivatives/Overview/Trading-Calendar-and-Holiday-Schedule?sc_lang=en',
    'XKRX': 'https://global.krx.co.kr/contents/GLB/05/0501/0501110000/GLB0501110000.jsp',
    'BVMF': 'https://www.b3.com.br/en_us/solutions/platforms/puma-trading-system/for-members-and-traders/trading-calendar/holidays/',
    'XNZE': 'https://www.nzx.com/announcements/443000',
    'XMCE': 'https://www.bolsasymercados.es/bme-exchange/en/Trading',
    'MISX': 'https://www.moex.com/en/tradingcalendar'
}


def test_extractor(iso_code: str, url: str):
    """
    Test a single extractor with browser automation

    Args:
        iso_code: Exchange ISO code
        url: Exchange calendar URL
    """
    print(f"\n{'='*80}")
    print(f"Testing {iso_code}")
    print(f"URL: {url}")
    print(f"{'='*80}\n")

    # Create scraper with browser automation enabled
    with HolidayScraper(use_browser=True) as scraper:
        # Extract holidays
        holidays = scraper.extract_holidays(url, iso_code)

        # Display results
        print(f"\n{'='*80}")
        print(f"Results for {iso_code}")
        print(f"{'='*80}")
        print(f"Total holidays found: {len(holidays)}\n")

        if holidays:
            # Display first 5 holidays as sample
            print("Sample holidays (first 5):")
            for i, holiday in enumerate(holidays[:5], 1):
                print(f"\n{i}. {holiday['holiday_name']}")
                print(f"   Date: {holiday['holiday_date']}")
                print(f"   Full closure: {holiday['is_full_closure']}")
                if holiday['early_close_time']:
                    print(f"   Early close: {holiday['early_close_time']}")
                if holiday['products_trading']:
                    print(f"   Products trading: {holiday['products_trading']}")

            if len(holidays) > 5:
                print(f"\n... and {len(holidays) - 5} more holidays")
        else:
            print("⚠️  No holidays found. This might indicate:")
            print("   - Page structure has changed")
            print("   - Browser automation needs adjustment")
            print("   - URL is incorrect or page is unavailable")

        return len(holidays) > 0


def test_all():
    """Test all browser automation extractors"""
    print("\n" + "="*80)
    print("BROWSER AUTOMATION TEST SUITE")
    print("="*80)
    print(f"\nTesting {len(BROWSER_AUTOMATION_EXCHANGES)} exchanges with browser automation\n")

    results = {}

    for iso_code, url in BROWSER_AUTOMATION_EXCHANGES.items():
        try:
            success = test_extractor(iso_code, url)
            results[iso_code] = 'SUCCESS' if success else 'NO DATA'
        except Exception as e:
            print(f"\n❌ ERROR testing {iso_code}: {e}")
            results[iso_code] = f'ERROR: {str(e)[:50]}'

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"\n{'Exchange':<15} {'Status':<20}")
    print("-" * 40)

    for iso_code, status in results.items():
        emoji = '✅' if status == 'SUCCESS' else '⚠️' if status == 'NO DATA' else '❌'
        print(f"{emoji} {iso_code:<15} {status:<20}")

    # Statistics
    successful = sum(1 for s in results.values() if s == 'SUCCESS')
    no_data = sum(1 for s in results.values() if s == 'NO DATA')
    errors = len(results) - successful - no_data

    print(f"\n{'='*40}")
    print(f"Total: {len(results)} | Success: {successful} | No Data: {no_data} | Errors: {errors}")
    print(f"Success Rate: {successful/len(results)*100:.1f}%")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nAvailable exchanges:")
        for code in BROWSER_AUTOMATION_EXCHANGES.keys():
            print(f"  - {code}")
        print("\nOr use 'all' to test all exchanges")
        sys.exit(1)

    exchange = sys.argv[1].upper()

    if exchange == 'ALL':
        test_all()
    elif exchange in BROWSER_AUTOMATION_EXCHANGES:
        url = BROWSER_AUTOMATION_EXCHANGES[exchange]
        success = test_extractor(exchange, url)
        sys.exit(0 if success else 1)
    else:
        print(f"❌ Unknown exchange: {exchange}")
        print("\nAvailable exchanges:")
        for code in BROWSER_AUTOMATION_EXCHANGES.keys():
            print(f"  - {code}")
        sys.exit(1)


if __name__ == '__main__':
    main()
