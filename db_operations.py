#!/usr/bin/env python3
"""
Database Operations Module
Handles holiday data comparison, updates, and history tracking
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import json


class DatabaseOperations:
    """Manages database operations for holiday calendar data"""

    def __init__(self, db_path='exchange_holidays.db'):
        """
        Initialize database operations

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def get_all_exchanges(self) -> List[Dict]:
        """
        Get all active exchanges from database

        Returns:
            List of exchange dictionaries
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, exchange_name, iso_code, country, base_url, calendar_url, calendar_url_pattern
            FROM exchanges
            WHERE active = 1
            ORDER BY exchange_name
        """)

        columns = ['id', 'exchange_name', 'iso_code', 'country', 'base_url',
                   'calendar_url', 'calendar_url_pattern']
        exchanges = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return exchanges

    def get_existing_holidays(self, iso_code: str) -> Dict[str, Dict]:
        """
        Get existing holidays for an exchange

        Args:
            iso_code: Exchange ISO code

        Returns:
            Dictionary mapping holiday_date to holiday data
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT holiday_date, holiday_name, holiday_description,
                   products_trading, is_full_closure, early_close_time
            FROM holidays
            WHERE iso_code = ?
        """, (iso_code,))

        holidays = {}
        for row in cursor.fetchall():
            date = row[0]
            holidays[date] = {
                'holiday_name': row[1],
                'holiday_description': row[2],
                'products_trading': row[3],
                'is_full_closure': bool(row[4]),
                'early_close_time': row[5]
            }

        conn.close()
        return holidays

    def compare_and_update_holidays(self, iso_code: str, new_holidays: List[Dict]) -> Dict[str, int]:
        """
        Compare scraped holidays with database and update as needed

        Args:
            iso_code: Exchange ISO code
            new_holidays: List of holiday dictionaries from scraper

        Returns:
            Dictionary with counts: {'added': n, 'updated': n, 'unchanged': n}
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        stats = {'added': 0, 'updated': 0, 'unchanged': 0}

        # Get existing holidays
        existing_holidays = self.get_existing_holidays(iso_code)

        for holiday in new_holidays:
            date = holiday['holiday_date']

            if date not in existing_holidays:
                # New holiday - insert
                self._insert_holiday(cursor, holiday)
                stats['added'] += 1
            else:
                # Existing holiday - check if update needed
                existing = existing_holidays[date]
                if self._holidays_differ(existing, holiday):
                    self._update_holiday(cursor, holiday)
                    stats['updated'] += 1
                else:
                    stats['unchanged'] += 1

        conn.commit()
        conn.close()

        return stats

    def _holidays_differ(self, existing: Dict, new: Dict) -> bool:
        """
        Check if two holiday records differ

        Args:
            existing: Existing holiday data
            new: New holiday data

        Returns:
            True if holidays differ, False otherwise
        """
        # Compare relevant fields
        fields_to_compare = ['holiday_name', 'holiday_description',
                             'products_trading', 'is_full_closure', 'early_close_time']

        for field in fields_to_compare:
            existing_value = existing.get(field)
            new_value = new.get(field)

            # Normalize None and empty string
            if existing_value == '' or existing_value is None:
                existing_value = None
            if new_value == '' or new_value is None:
                new_value = None

            if existing_value != new_value:
                return True

        return False

    def _insert_holiday(self, cursor, holiday: Dict):
        """
        Insert a new holiday record

        Args:
            cursor: Database cursor
            holiday: Holiday dictionary
        """
        cursor.execute("""
            INSERT INTO holidays
            (iso_code, holiday_date, holiday_name, holiday_description,
             products_trading, is_full_closure, early_close_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            holiday['iso_code'],
            holiday['holiday_date'],
            holiday['holiday_name'],
            holiday.get('holiday_description'),
            holiday.get('products_trading'),
            holiday.get('is_full_closure', True),
            holiday.get('early_close_time')
        ))

    def _update_holiday(self, cursor, holiday: Dict):
        """
        Update an existing holiday record

        Args:
            cursor: Database cursor
            holiday: Holiday dictionary
        """
        cursor.execute("""
            UPDATE holidays
            SET holiday_name = ?,
                holiday_description = ?,
                products_trading = ?,
                is_full_closure = ?,
                early_close_time = ?
            WHERE iso_code = ? AND holiday_date = ?
        """, (
            holiday['holiday_name'],
            holiday.get('holiday_description'),
            holiday.get('products_trading'),
            holiday.get('is_full_closure', True),
            holiday.get('early_close_time'),
            holiday['iso_code'],
            holiday['holiday_date']
        ))

    def log_url_status(self, iso_code: str, url: str, status_code: Optional[int],
                       is_accessible: bool, error_message: Optional[str] = None,
                       alternative_url: Optional[str] = None):
        """
        Log URL access status

        Args:
            iso_code: Exchange ISO code
            url: Attempted URL
            status_code: HTTP status code
            is_accessible: Whether URL was accessible
            error_message: Error message if failed
            alternative_url: Alternative URL if discovered
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO url_status_log
            (iso_code, url, status_code, is_accessible, error_message, alternative_url_found)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (iso_code, url, status_code, is_accessible, error_message, alternative_url))

        conn.commit()
        conn.close()

    def update_exchange_calendar_url(self, iso_code: str, new_url: str):
        """
        Update the calendar URL for an exchange

        Args:
            iso_code: Exchange ISO code
            new_url: New calendar URL
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE exchanges
            SET calendar_url = ?
            WHERE iso_code = ?
        """, (new_url, iso_code))

        conn.commit()
        conn.close()

    def start_sync_run(self) -> int:
        """
        Start a new synchronization run

        Returns:
            Sync run ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sync_log (status)
            VALUES ('running')
        """)

        run_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return run_id

    def update_sync_run(self, run_id: int, stats: Dict, status: str = 'completed'):
        """
        Update synchronization run statistics

        Args:
            run_id: Sync run ID
            stats: Statistics dictionary
            status: Run status ('completed' or 'failed')
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE sync_log
            SET run_completed_at = CURRENT_TIMESTAMP,
                exchanges_processed = ?,
                exchanges_succeeded = ?,
                exchanges_failed = ?,
                holidays_added = ?,
                holidays_updated = ?,
                holidays_unchanged = ?,
                errors_encountered = ?,
                status = ?
            WHERE id = ?
        """, (
            stats.get('exchanges_processed', 0),
            stats.get('exchanges_succeeded', 0),
            stats.get('exchanges_failed', 0),
            stats.get('holidays_added', 0),
            stats.get('holidays_updated', 0),
            stats.get('holidays_unchanged', 0),
            json.dumps(stats.get('errors', [])),
            status,
            run_id
        ))

        conn.commit()
        conn.close()

    def get_holidays_by_date_range(self, iso_code: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Get holidays for an exchange within a date range

        Args:
            iso_code: Exchange ISO code
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of holiday dictionaries
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT holiday_date, holiday_name, holiday_description,
                   products_trading, is_full_closure, early_close_time
            FROM holidays
            WHERE iso_code = ? AND holiday_date BETWEEN ? AND ?
            ORDER BY holiday_date
        """, (iso_code, start_date, end_date))

        columns = ['holiday_date', 'holiday_name', 'holiday_description',
                   'products_trading', 'is_full_closure', 'early_close_time']
        holidays = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return holidays

    def get_change_history(self, iso_code: str, limit: int = 100) -> List[Dict]:
        """
        Get change history for an exchange

        Args:
            iso_code: Exchange ISO code
            limit: Maximum number of records to return

        Returns:
            List of change history dictionaries
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT holiday_date, change_type, field_changed,
                   old_value, new_value, change_timestamp, change_source
            FROM holiday_history
            WHERE iso_code = ?
            ORDER BY change_timestamp DESC
            LIMIT ?
        """, (iso_code, limit))

        columns = ['holiday_date', 'change_type', 'field_changed',
                   'old_value', 'new_value', 'change_timestamp', 'change_source']
        history = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return history

    def export_holidays_to_csv(self, iso_code: str, output_file: str):
        """
        Export holidays to CSV file

        Args:
            iso_code: Exchange ISO code
            output_file: Output CSV file path
        """
        import csv

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT iso_code, holiday_date, holiday_name, holiday_description,
                   products_trading, is_full_closure, early_close_time
            FROM holidays
            WHERE iso_code = ?
            ORDER BY holiday_date
        """, (iso_code,))

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ISO Code', 'Holiday Date', 'Holiday Name', 'Description',
                             'Products Trading', 'Full Closure', 'Early Close Time'])
            writer.writerows(cursor.fetchall())

        conn.close()


if __name__ == '__main__':
    # Test database operations
    db_ops = DatabaseOperations()

    # Get all exchanges
    exchanges = db_ops.get_all_exchanges()
    print(f"Found {len(exchanges)} exchanges in database")

    for exchange in exchanges[:3]:  # Show first 3
        print(f"  - {exchange['exchange_name']} ({exchange['iso_code']})")
