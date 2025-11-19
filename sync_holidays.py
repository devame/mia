#!/usr/bin/env python3
"""
Holiday Calendar Synchronization Script
Main orchestration script for syncing exchange holiday calendars
"""

import sys
import argparse
from datetime import datetime
from typing import Dict, List, Optional
import traceback

from scraper import HolidayScraper
from db_operations import DatabaseOperations
from email_notifier import EmailNotifier, load_email_config


class HolidayCalendarSync:
    """Main synchronization coordinator"""

    def __init__(self, db_path='exchange_holidays.db', email_config_path='email_config.json',
                 send_email=True, verbose=False):
        """
        Initialize synchronization coordinator

        Args:
            db_path: Path to SQLite database
            email_config_path: Path to email configuration file
            send_email: Whether to send email notifications
            verbose: Enable verbose output
        """
        self.db_ops = DatabaseOperations(db_path)
        self.scraper = HolidayScraper()
        self.send_email = send_email
        self.verbose = verbose

        # Load email configuration
        self.email_notifier = None
        if send_email:
            email_config = load_email_config(email_config_path)
            if email_config:
                self.email_notifier = EmailNotifier(
                    smtp_server=email_config['smtp_server'],
                    smtp_port=email_config['smtp_port'],
                    sender_email=email_config['sender_email'],
                    sender_password=email_config['sender_password'],
                    use_tls=email_config.get('use_tls', True)
                )
                self.recipient_emails = email_config.get('recipient_emails', [])
            else:
                print("Warning: Email configuration not found. Email notifications disabled.")
                self.send_email = False

    def log(self, message: str, level: str = 'INFO'):
        """
        Log message with timestamp

        Args:
            message: Message to log
            level: Log level (INFO, WARNING, ERROR)
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")

    def try_alternative_urls(self, exchange: Dict) -> Optional[str]:
        """
        Try to find alternative calendar URLs when primary URL fails

        Args:
            exchange: Exchange dictionary

        Returns:
            Alternative URL if found, None otherwise
        """
        self.log(f"Attempting to discover alternative URL for {exchange['exchange_name']}...", 'INFO')

        # Get current year
        current_year = datetime.now().year

        # Try year-based URL pattern if available
        if exchange['calendar_url_pattern'] and '{year}' in exchange['calendar_url_pattern']:
            for year in [current_year, current_year + 1]:
                url = exchange['calendar_url_pattern'].replace('{year}', str(year))
                self.log(f"  Trying pattern-based URL: {url}", 'INFO')

                success, _, status_code, _ = self.scraper.fetch_url(url)
                if success:
                    self.log(f"  ✓ Found working URL: {url}", 'INFO')
                    return url

        # Try to discover URLs from base URL
        potential_urls = self.scraper.discover_calendar_url(exchange['base_url'], current_year)

        if potential_urls:
            self.log(f"  Found {len(potential_urls)} potential URLs from base URL", 'INFO')

            for url in potential_urls:
                if self.verbose:
                    self.log(f"  Trying discovered URL: {url}", 'INFO')

                success, _, status_code, _ = self.scraper.fetch_url(url)
                if success:
                    self.log(f"  ✓ Found working URL: {url}", 'INFO')
                    return url

        self.log(f"  ✗ No alternative URL found for {exchange['exchange_name']}", 'WARNING')
        return None

    def sync_exchange(self, exchange: Dict) -> Dict:
        """
        Synchronize holiday data for a single exchange

        Args:
            exchange: Exchange dictionary

        Returns:
            Result dictionary with statistics and status
        """
        result = {
            'exchange_name': exchange['exchange_name'],
            'iso_code': exchange['iso_code'],
            'success': False,
            'url': exchange['calendar_url'],
            'url_accessible': False,
            'alternative_url': None,
            'added': 0,
            'updated': 0,
            'unchanged': 0,
            'error_message': None
        }

        try:
            self.log(f"Processing {exchange['exchange_name']} ({exchange['iso_code']})...", 'INFO')

            # Try to fetch from primary URL
            calendar_url = exchange['calendar_url']
            success, content, status_code, error_msg = self.scraper.fetch_url(calendar_url)

            # Log URL status
            self.db_ops.log_url_status(
                exchange['iso_code'],
                calendar_url,
                status_code,
                success,
                error_msg if not success else None
            )

            # If primary URL failed, try alternatives
            if not success:
                self.log(f"  Primary URL failed: {error_msg}", 'WARNING')
                alternative_url = self.try_alternative_urls(exchange)

                if alternative_url:
                    calendar_url = alternative_url
                    result['alternative_url'] = alternative_url
                    success, content, status_code, error_msg = self.scraper.fetch_url(calendar_url)

                    # Log alternative URL status
                    self.db_ops.log_url_status(
                        exchange['iso_code'],
                        calendar_url,
                        status_code,
                        success,
                        error_msg if not success else None,
                        alternative_url
                    )

                    # Update database with new URL
                    if success:
                        self.db_ops.update_exchange_calendar_url(exchange['iso_code'], alternative_url)
                        self.log(f"  Updated calendar URL in database", 'INFO')

            if not success:
                result['error_message'] = error_msg or "Failed to fetch URL"
                self.log(f"  ✗ Failed to fetch calendar data", 'ERROR')
                return result

            result['url_accessible'] = True

            # Extract holidays from the fetched content
            self.log(f"  Extracting holiday data...", 'INFO')
            holidays = self.scraper.extract_holidays(calendar_url, exchange['iso_code'])

            if not holidays:
                self.log(f"  ⚠ No holidays extracted from URL", 'WARNING')
                result['error_message'] = "No holidays found in response"
                # Still mark as success since URL was accessible
                result['success'] = True
                return result

            self.log(f"  Extracted {len(holidays)} holidays", 'INFO')

            # Compare and update database
            self.log(f"  Comparing with database...", 'INFO')
            stats = self.db_ops.compare_and_update_holidays(exchange['iso_code'], holidays)

            result['added'] = stats['added']
            result['updated'] = stats['updated']
            result['unchanged'] = stats['unchanged']
            result['success'] = True

            self.log(f"  ✓ Complete: {stats['added']} added, {stats['updated']} updated, "
                     f"{stats['unchanged']} unchanged", 'INFO')

        except Exception as e:
            result['error_message'] = str(e)
            self.log(f"  ✗ Error: {str(e)}", 'ERROR')
            if self.verbose:
                traceback.print_exc()

        return result

    def sync_all_exchanges(self, iso_codes: Optional[List[str]] = None) -> Dict:
        """
        Synchronize all exchanges or specific exchanges

        Args:
            iso_codes: List of ISO codes to sync (None for all)

        Returns:
            Overall sync results dictionary
        """
        self.log("=" * 80, 'INFO')
        self.log("STARTING HOLIDAY CALENDAR SYNCHRONIZATION", 'INFO')
        self.log("=" * 80, 'INFO')

        # Start sync run in database
        run_id = self.db_ops.start_sync_run()

        # Get exchanges to process
        all_exchanges = self.db_ops.get_all_exchanges()

        if iso_codes:
            exchanges = [e for e in all_exchanges if e['iso_code'] in iso_codes]
            self.log(f"Processing {len(exchanges)} selected exchange(s)", 'INFO')
        else:
            exchanges = all_exchanges
            self.log(f"Processing all {len(exchanges)} exchanges", 'INFO')

        # Initialize statistics
        stats = {
            'exchanges_processed': 0,
            'exchanges_succeeded': 0,
            'exchanges_failed': 0,
            'holidays_added': 0,
            'holidays_updated': 0,
            'holidays_unchanged': 0,
            'errors': []
        }

        exchange_results = []

        # Process each exchange
        for exchange in exchanges:
            result = self.sync_exchange(exchange)
            exchange_results.append(result)

            stats['exchanges_processed'] += 1

            if result['success']:
                stats['exchanges_succeeded'] += 1
                stats['holidays_added'] += result['added']
                stats['holidays_updated'] += result['updated']
                stats['holidays_unchanged'] += result['unchanged']
            else:
                stats['exchanges_failed'] += 1
                error_msg = f"{exchange['exchange_name']} ({exchange['iso_code']}): {result['error_message']}"
                stats['errors'].append(error_msg)

        # Determine overall status
        if stats['exchanges_failed'] == 0:
            status = 'completed'
        else:
            status = 'completed'  # Still completed even with failures

        # Update sync run in database
        self.db_ops.update_sync_run(run_id, stats, status)

        # Log summary
        self.log("=" * 80, 'INFO')
        self.log("SYNCHRONIZATION COMPLETE", 'INFO')
        self.log("=" * 80, 'INFO')
        self.log(f"Exchanges Processed: {stats['exchanges_processed']}", 'INFO')
        self.log(f"Exchanges Succeeded: {stats['exchanges_succeeded']}", 'INFO')
        self.log(f"Exchanges Failed: {stats['exchanges_failed']}", 'INFO')
        self.log(f"Holidays Added: {stats['holidays_added']}", 'INFO')
        self.log(f"Holidays Updated: {stats['holidays_updated']}", 'INFO')
        self.log(f"Holidays Unchanged: {stats['holidays_unchanged']}", 'INFO')

        # Send email notification
        if self.send_email and self.email_notifier and self.recipient_emails:
            self.log("Sending email notification...", 'INFO')
            sync_results = {
                'stats': stats,
                'exchange_results': exchange_results,
                'errors': stats['errors']
            }

            email_sent = self.email_notifier.send_sync_report(self.recipient_emails, sync_results)
            if email_sent:
                self.log("✓ Email notification sent successfully", 'INFO')
            else:
                self.log("✗ Failed to send email notification", 'ERROR')

        return {
            'stats': stats,
            'exchange_results': exchange_results,
            'run_id': run_id
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Synchronize exchange holiday calendars from web sources',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync all exchanges
  python sync_holidays.py

  # Sync specific exchanges
  python sync_holidays.py --exchanges XCME XEUR XSES

  # Sync without email notifications
  python sync_holidays.py --no-email

  # Verbose output
  python sync_holidays.py --verbose
        """
    )

    parser.add_argument(
        '--exchanges',
        nargs='+',
        help='ISO codes of exchanges to sync (default: all)'
    )

    parser.add_argument(
        '--db',
        default='exchange_holidays.db',
        help='Path to SQLite database (default: exchange_holidays.db)'
    )

    parser.add_argument(
        '--email-config',
        default='email_config.json',
        help='Path to email configuration file (default: email_config.json)'
    )

    parser.add_argument(
        '--no-email',
        action='store_true',
        help='Disable email notifications'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Create sync coordinator
    sync = HolidayCalendarSync(
        db_path=args.db,
        email_config_path=args.email_config,
        send_email=not args.no_email,
        verbose=args.verbose
    )

    # Run synchronization
    results = sync.sync_all_exchanges(iso_codes=args.exchanges)

    # Exit with appropriate code
    if results['stats']['exchanges_failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
