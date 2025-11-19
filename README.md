# Exchange Holiday Calendar Management System

A comprehensive Python system for tracking and synchronizing holiday calendars from derivative exchanges worldwide. The system automatically fetches holiday data from exchange websites, compares it with stored data, tracks changes, and sends email notifications.

## Features

- **Global Exchange Coverage**: Tracks 50+ derivative exchanges worldwide across North America, Latin America, Europe, Asia-Pacific, Middle East, and Africa
- **Automated Scraping**: Extracts holiday data from various formats (HTML, PDF, tables)
- **Intelligent URL Discovery**: Automatically finds alternative calendar URLs when primary URLs fail
- **Change Tracking**: Maintains complete audit trail of all changes to holiday data
- **Database Management**: SQLite database with automatic history logging via triggers
- **Email Notifications**: Sends detailed HTML email reports with sync results and errors
- **Flexible Synchronization**: Sync all exchanges or select specific ones
- **Date Format Normalization**: Converts various date formats to ISO 8601 (YYYY-MM-DD)
- **Product Tracking**: Records which products are still trading on partial holidays

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     sync_holidays.py                        │
│              (Main Orchestration Script)                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
  ┌──────────┐ ┌─────────┐ ┌──────────────┐
  │ scraper  │ │   db    │ │    email     │
  │   .py    │ │operations│ │  notifier.py │
  └──────────┘ │   .py   │ └──────────────┘
               └─────────┘
                    │
                    ▼
          ┌──────────────────┐
          │  SQLite Database │
          │ (exchange_       │
          │  holidays.db)    │
          └──────────────────┘
```

## Database Schema

### Table 1: Exchanges
Stores information about derivative exchanges.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| exchange_name | TEXT | Full name of exchange |
| iso_code | TEXT | MIC code (Market Identifier Code) |
| country | TEXT | Country location |
| base_url | TEXT | Exchange base URL |
| calendar_url | TEXT | Holiday calendar URL |
| calendar_url_pattern | TEXT | Pattern for year-based URLs |
| active | BOOLEAN | Whether exchange is active |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### Table 2: Holidays
Stores holiday dates and trading information for each exchange.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| iso_code | TEXT | Exchange ISO code (foreign key) |
| holiday_date | DATE | Holiday date (ISO format: YYYY-MM-DD) |
| holiday_name | TEXT | Name of holiday |
| holiday_description | TEXT | Additional description |
| products_trading | TEXT | Products still trading (if partial closure) |
| is_full_closure | BOOLEAN | Full closure vs. partial |
| early_close_time | TEXT | Early close time if applicable |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### Table 3: Holiday History
Tracks all changes to holiday data for audit purposes.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| iso_code | TEXT | Exchange ISO code |
| holiday_date | DATE | Holiday date |
| change_type | TEXT | INSERT, UPDATE, or DELETE |
| field_changed | TEXT | Which field was changed |
| old_value | TEXT | Previous value (JSON) |
| new_value | TEXT | New value (JSON) |
| change_timestamp | TIMESTAMP | When change occurred |
| change_source | TEXT | Source of change |

### Table 4: URL Status Log
Tracks URL availability and changes.

### Table 5: Sync Log
Tracks synchronization runs.

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone or download the repository**

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**
   ```bash
   python init_database.py
   ```

   This will:
   - Create the SQLite database with schema
   - Load initial exchange data from `exchanges_data.csv`
   - Display list of registered exchanges

4. **Configure email notifications**
   ```bash
   cp email_config.example.json email_config.json
   ```

   Edit `email_config.json` with your SMTP settings:
   ```json
   {
       "smtp_server": "smtp.gmail.com",
       "smtp_port": 587,
       "sender_email": "your-email@gmail.com",
       "sender_password": "your-app-password",
       "recipient_emails": [
           "recipient1@example.com",
           "recipient2@example.com"
       ],
       "use_tls": true
   }
   ```

   **For Gmail users:**
   - Use an App Password instead of your regular password
   - Enable 2-factor authentication
   - Generate App Password at: https://myaccount.google.com/apppasswords

## Usage

### Basic Synchronization

Sync all exchanges:
```bash
python sync_holidays.py
```

### Sync Specific Exchanges

```bash
python sync_holidays.py --exchanges XCME XEUR XSES
```

### Disable Email Notifications

```bash
python sync_holidays.py --no-email
```

### Verbose Output

```bash
python sync_holidays.py --verbose
```

### Custom Database Path

```bash
python sync_holidays.py --db /path/to/database.db
```

### Combined Options

```bash
python sync_holidays.py --exchanges XCME IFUS --verbose --no-email
```

## Supported Exchanges

The system currently includes 50+ derivative exchanges worldwide:

### North America (5 exchanges)
| Exchange Name | ISO Code | Country |
|--------------|----------|---------|
| CME Group (Chicago Mercantile Exchange) | XCME | United States |
| ICE Futures U.S. | IFUS | United States |
| Cboe Global Markets | XCBO | United States |
| Nasdaq Futures (NFX) | IFNY | United States |
| Montreal Exchange (TMX) | XMOD | Canada |

### Latin America (2 exchanges)
| Exchange Name | ISO Code | Country |
|--------------|----------|---------|
| B3 (Brasil Bolsa Balcao) | BVMF | Brazil |
| MexDer (Mexican Derivatives Exchange) | MEXD | Mexico |

### Europe (18 exchanges)
| Exchange Name | ISO Code | Country |
|--------------|----------|---------|
| Eurex (Eurex Deutschland) | XEUR | Germany |
| ICE Futures Europe | IFEU | United Kingdom |
| London Metal Exchange (LME) | XLME | United Kingdom |
| Euronext Paris | XPAR | France |
| Euronext Amsterdam | XAMS | Netherlands |
| Euronext Brussels | XBRU | Belgium |
| Euronext Lisbon | XLIS | Portugal |
| Euronext Dublin | XDUB | Ireland |
| Euronext Milan (Borsa Italiana) | XMIL | Italy |
| Euronext Oslo | XOSL | Norway |
| BME Spanish Exchanges | XMCE | Spain |
| SIX Swiss Exchange | XSWX | Switzerland |
| European Energy Exchange (EEX) | XEEE | Germany |
| Nasdaq Commodities (formerly Nasdaq Oslo) | XNDE | Norway |
| ICE Endex | NDEX | Netherlands |
| Budapest Stock Exchange (BSE) | XBUD | Hungary |
| Warsaw Stock Exchange (GPW) | XWAR | Poland |
| Athens Exchange (ATHEX) Derivatives | XATH | Greece |
| Moscow Exchange (MOEX) | MISX | Russia |
| Borsa Istanbul VIOP | XIST | Turkey |

### Asia-Pacific (17 exchanges)
| Exchange Name | ISO Code | Country |
|--------------|----------|---------|
| Singapore Exchange (SGX) | XSES | Singapore |
| Hong Kong Exchanges and Clearing (HKEX) | XHKG | Hong Kong |
| Japan Exchange Group (JPX/TSE) | XJPX | Japan |
| Osaka Exchange (OSE) | XOSE | Japan |
| Shanghai Futures Exchange (SHFE) | XSGE | China |
| Dalian Commodity Exchange (DCE) | XDCE | China |
| Zhengzhou Commodity Exchange (ZCE) | XZCE | China |
| China Financial Futures Exchange (CFFEX) | CCFX | China |
| Korea Exchange (KRX) | XKRX | South Korea |
| Taiwan Futures Exchange (TAIFEX) | XTAF | Taiwan |
| National Stock Exchange of India (NSE) | XNSE | India |
| BSE India (Bombay Stock Exchange) | XBOM | India |
| Multi Commodity Exchange of India (MCX) | MCXI | India |
| Australian Securities Exchange (ASX) | XASX | Australia |
| New Zealand Exchange (NZX) | XNZE | New Zealand |
| Indonesia Commodity & Derivatives Exchange (ICDX) | IDXC | Indonesia |
| Thailand Futures Exchange (TFEX) | XTFX | Thailand |
| Bursa Malaysia Derivatives | XKLS | Malaysia |
| Philippine Stock Exchange (PSE) | XPHS | Philippines |
| Hanoi Stock Exchange (HNX) - Vietnam Derivatives | XHNX | Vietnam |
| Pakistan Mercantile Exchange (PMEX) | XPAK | Pakistan |

### Middle East (3 exchanges)
| Exchange Name | ISO Code | Country |
|--------------|----------|---------|
| Gulf Mercantile Exchange (GME) / Dubai Mercantile Exchange | XDME | United Arab Emirates |
| Saudi Exchange (Tadawul) | XSAU | Saudi Arabia |
| Tel Aviv Stock Exchange (TASE) | XTAE | Israel |

### Africa (1 exchange)
| Exchange Name | ISO Code | Country |
|--------------|----------|---------|
| Johannesburg Stock Exchange (JSE) | XJSE | South Africa |

**Total: 50+ derivative and futures exchanges globally**

## How It Works

### 1. URL Fetching

The system attempts to fetch holiday calendar data from the configured URL for each exchange, with automatic fallback to alternative URLs if needed.

### 2. Data Extraction

The scraper can extract holiday data from:
- **HTML Tables**: Parses table structures looking for dates and holiday names
- **PDF Files**: Extracts text from PDFs (requires `pdfplumber`)
- **Various Date Formats**: Automatically converts to ISO format

### 3. Database Comparison

For each extracted holiday:

1. **Check if holiday exists** in database for that exchange and date
2. **If new**: Insert into database (triggers log INSERT in history table)
3. **If exists**: Compare all fields
   - If different: Update database (triggers log UPDATE in history table)
   - If same: Mark as unchanged

### 4. Change History

All changes are automatically logged via SQLite triggers.

### 5. Email Notification

After sync completes, an HTML email is sent with statistics, results, and any errors.

## Scheduling Automated Runs

### Linux/Mac (cron)

Edit crontab:
```bash
crontab -e
```

Add a daily run at 2 AM:
```
0 2 * * * cd /path/to/mia && /usr/bin/python3 sync_holidays.py >> /var/log/holiday_sync.log 2>&1
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., Daily at 2:00 AM)
4. Action: Start a Program
   - Program: `python`
   - Arguments: `sync_holidays.py`
   - Start in: `C:\path\to\mia`

## Querying the Database

### Using Python

```python
from db_operations import DatabaseOperations

db = DatabaseOperations('exchange_holidays.db')

# Get all exchanges
exchanges = db.get_all_exchanges()

# Get holidays for a specific exchange
holidays = db.get_existing_holidays('XCME')

# Get holidays in date range
holidays = db.get_holidays_by_date_range('XCME', '2025-01-01', '2025-12-31')

# Get change history
history = db.get_change_history('XCME', limit=50)

# Export to CSV
db.export_holidays_to_csv('XCME', 'cme_holidays.csv')
```

### Using SQLite CLI

```bash
sqlite3 exchange_holidays.db

# List all exchanges
SELECT * FROM exchanges;

# Get holidays for CME
SELECT * FROM holidays WHERE iso_code = 'XCME' ORDER BY holiday_date;

# Get recent changes
SELECT * FROM holiday_history ORDER BY change_timestamp DESC LIMIT 20;
```

## Adding New Exchanges

1. **Add to `exchanges_data.csv`**:
   ```csv
   "Exchange Name",ISO_CODE,Country,https://base-url.com,https://calendar-url.com,pattern
   ```

2. **Reload database**:
   ```bash
   python init_database.py
   ```

## Troubleshooting

### Issue: No holidays extracted
- Check URL manually in browser
- Update scraper logic for specific exchange
- Implement exchange-specific scraper class

### Issue: Email not sending
- Use App Password for Gmail
- Check SMTP server and port
- Enable "Less secure app access" or use OAuth2

### Issue: URL discovery not finding calendar
- Manually update `calendar_url` in database
- Add keywords to `discover_calendar_url()` method
- Create exchange-specific URL discovery logic

## File Structure

```
mia/
├── schema.sql                    # Database schema with triggers
├── exchanges_data.csv            # Initial exchange data
├── init_database.py              # Database initialization script
├── scraper.py                    # Holiday data scraper
├── db_operations.py              # Database operations
├── email_notifier.py             # Email notification system
├── sync_holidays.py              # Main orchestration script
├── requirements.txt              # Python dependencies
├── email_config.json             # Email configuration (create from example)
├── email_config.example.json     # Example email configuration
├── exchange_holidays.db          # SQLite database (created on init)
└── README.md                     # This file
```

## Security Considerations

1. **Email Credentials**: Store securely, use environment variables
2. **Database Access**: Restrict file permissions
   ```bash
   chmod 600 exchange_holidays.db
   chmod 600 email_config.json
   ```

3. **HTTPS Only**: System uses HTTPS for all exchange URLs
4. **SQL Injection**: All queries use parameterized statements

## Version History

- **v1.1.0** (2025-01-19): Expanded coverage
  - 50+ exchanges supported worldwide
  - Added comprehensive regional coverage (North America, Latin America, Europe, Asia-Pacific, Middle East, Africa)
  - Includes all Chinese commodity exchanges (SHFE, DCE, ZCE, CFFEX)
  - Added all Euronext exchanges (Paris, Amsterdam, Brussels, Lisbon, Dublin, Milan, Oslo)
  - Added energy exchanges (EEX, Nasdaq Commodities, ICE Endex)
  - Added emerging market exchanges (PMEX Pakistan, TFEX Thailand, PSE Philippines, HNX Vietnam, ICDX Indonesia)

- **v1.0.0** (2025-01-19): Initial release
  - 14 exchanges supported
  - Automated scraping and URL discovery
  - Change history tracking
  - Email notifications
