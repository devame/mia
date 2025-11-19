#!/usr/bin/env python3
"""
Database Initialization Script
Creates the SQLite database and loads initial exchange data
"""

import sqlite3
import csv
import os
from datetime import datetime


def init_database(db_path='exchange_holidays.db', schema_path='schema.sql', data_path='exchanges_data.csv'):
    """
    Initialize the database with schema and initial data

    Args:
        db_path: Path to SQLite database file
        schema_path: Path to SQL schema file
        data_path: Path to CSV file with exchange data
    """
    print(f"Initializing database: {db_path}")

    # Create database connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Load and execute schema
        print(f"Loading schema from: {schema_path}")
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        cursor.executescript(schema_sql)
        print("✓ Schema created successfully")

        # Load exchange data from CSV
        print(f"Loading exchange data from: {data_path}")
        with open(data_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            exchanges = list(reader)

        # Insert exchange data
        insert_count = 0
        for exchange in exchanges:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO exchanges
                    (exchange_name, iso_code, country, base_url, calendar_url, calendar_url_pattern)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    exchange['exchange_name'],
                    exchange['iso_code'],
                    exchange['country'],
                    exchange['base_url'],
                    exchange['calendar_url'],
                    exchange['calendar_url_pattern']
                ))
                if cursor.rowcount > 0:
                    insert_count += 1
                    print(f"  ✓ Inserted: {exchange['exchange_name']} ({exchange['iso_code']})")
            except sqlite3.IntegrityError as e:
                print(f"  ⚠ Skipped (already exists): {exchange['exchange_name']} ({exchange['iso_code']})")

        conn.commit()
        print(f"\n✓ Successfully loaded {insert_count} exchanges into database")

        # Display summary
        cursor.execute("SELECT COUNT(*) FROM exchanges")
        total_exchanges = cursor.fetchone()[0]
        print(f"\nDatabase Summary:")
        print(f"  Total exchanges: {total_exchanges}")
        print(f"  Database location: {os.path.abspath(db_path)}")

    except Exception as e:
        print(f"✗ Error during initialization: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def list_exchanges(db_path='exchange_holidays.db'):
    """List all exchanges in the database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT exchange_name, iso_code, country, calendar_url
        FROM exchanges
        WHERE active = 1
        ORDER BY exchange_name
    """)

    exchanges = cursor.fetchall()
    conn.close()

    print("\n" + "="*80)
    print("REGISTERED DERIVATIVE EXCHANGES")
    print("="*80)

    for name, iso, country, url in exchanges:
        print(f"\n{name}")
        print(f"  ISO Code: {iso}")
        print(f"  Country: {country}")
        print(f"  Calendar URL: {url}")

    print("\n" + "="*80)


if __name__ == '__main__':
    import sys

    # Check if database already exists
    db_file = 'exchange_holidays.db'

    if os.path.exists(db_file):
        response = input(f"Database '{db_file}' already exists. Recreate? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Initialization cancelled.")
            sys.exit(0)
        os.remove(db_file)
        print(f"Removed existing database: {db_file}\n")

    # Initialize database
    init_database()

    # List all exchanges
    list_exchanges()
