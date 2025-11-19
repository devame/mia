-- Exchange Holiday Calendar Database Schema
-- SQLite Database for tracking derivative exchange holidays worldwide

-- Table 1: Exchanges
-- Stores information about derivative exchanges
CREATE TABLE IF NOT EXISTS exchanges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exchange_name TEXT NOT NULL,
    iso_code TEXT UNIQUE NOT NULL,  -- MIC code (Market Identifier Code)
    country TEXT NOT NULL,
    base_url TEXT NOT NULL,
    calendar_url TEXT NOT NULL,
    calendar_url_pattern TEXT,  -- Pattern for year-based URLs, e.g., {base_url}/calendar/{year}
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: Holidays
-- Stores holiday dates and trading information for each exchange
CREATE TABLE IF NOT EXISTS holidays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    iso_code TEXT NOT NULL,
    holiday_date DATE NOT NULL,  -- ISO format: YYYY-MM-DD
    holiday_name TEXT NOT NULL,
    holiday_description TEXT,
    products_trading TEXT,  -- JSON array or comma-separated list of products still trading
    is_full_closure BOOLEAN DEFAULT 1,  -- 1 for full closure, 0 for partial
    early_close_time TEXT,  -- Time if early close (HH:MM format)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (iso_code) REFERENCES exchanges(iso_code) ON DELETE CASCADE,
    UNIQUE(iso_code, holiday_date)  -- One holiday per exchange per date
);

-- Table 3: Holiday Change History
-- Tracks all changes to holiday data for audit purposes
CREATE TABLE IF NOT EXISTS holiday_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    iso_code TEXT NOT NULL,
    holiday_date DATE NOT NULL,
    change_type TEXT NOT NULL,  -- 'INSERT', 'UPDATE', 'DELETE'
    field_changed TEXT,  -- Which field was changed
    old_value TEXT,
    new_value TEXT,
    change_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_source TEXT DEFAULT 'automated_scraper'  -- Source of the change
);

-- Table 4: URL Status Log
-- Tracks URL availability and changes
CREATE TABLE IF NOT EXISTS url_status_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    iso_code TEXT NOT NULL,
    url TEXT NOT NULL,
    status_code INTEGER,  -- HTTP status code
    is_accessible BOOLEAN,
    error_message TEXT,
    alternative_url_found TEXT,  -- New URL if discovered
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (iso_code) REFERENCES exchanges(iso_code) ON DELETE CASCADE
);

-- Table 5: Sync Log
-- Tracks synchronization runs
CREATE TABLE IF NOT EXISTS sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    run_completed_at TIMESTAMP,
    exchanges_processed INTEGER DEFAULT 0,
    exchanges_succeeded INTEGER DEFAULT 0,
    exchanges_failed INTEGER DEFAULT 0,
    holidays_added INTEGER DEFAULT 0,
    holidays_updated INTEGER DEFAULT 0,
    holidays_unchanged INTEGER DEFAULT 0,
    errors_encountered TEXT,  -- JSON array of errors
    status TEXT DEFAULT 'running'  -- 'running', 'completed', 'failed'
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_holidays_iso_code ON holidays(iso_code);
CREATE INDEX IF NOT EXISTS idx_holidays_date ON holidays(holiday_date);
CREATE INDEX IF NOT EXISTS idx_history_iso_code ON holiday_history(iso_code);
CREATE INDEX IF NOT EXISTS idx_history_date ON holiday_history(holiday_date);
CREATE INDEX IF NOT EXISTS idx_url_status_iso_code ON url_status_log(iso_code);

-- Triggers to automatically update the updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_exchanges_timestamp
AFTER UPDATE ON exchanges
BEGIN
    UPDATE exchanges SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_holidays_timestamp
AFTER UPDATE ON holidays
BEGIN
    UPDATE holidays SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger to automatically log changes to holidays table
CREATE TRIGGER IF NOT EXISTS log_holiday_insert
AFTER INSERT ON holidays
BEGIN
    INSERT INTO holiday_history (iso_code, holiday_date, change_type, new_value)
    VALUES (NEW.iso_code, NEW.holiday_date, 'INSERT',
            json_object('holiday_name', NEW.holiday_name,
                       'holiday_description', NEW.holiday_description,
                       'products_trading', NEW.products_trading));
END;

CREATE TRIGGER IF NOT EXISTS log_holiday_update
AFTER UPDATE ON holidays
BEGIN
    INSERT INTO holiday_history (iso_code, holiday_date, change_type, field_changed, old_value, new_value)
    SELECT NEW.iso_code, NEW.holiday_date, 'UPDATE',
           CASE
               WHEN OLD.holiday_name != NEW.holiday_name THEN 'holiday_name'
               WHEN OLD.holiday_description != NEW.holiday_description THEN 'holiday_description'
               WHEN OLD.products_trading != NEW.products_trading THEN 'products_trading'
               WHEN OLD.is_full_closure != NEW.is_full_closure THEN 'is_full_closure'
               WHEN OLD.early_close_time != NEW.early_close_time THEN 'early_close_time'
               ELSE 'multiple_fields'
           END,
           json_object('holiday_name', OLD.holiday_name,
                      'holiday_description', OLD.holiday_description,
                      'products_trading', OLD.products_trading,
                      'is_full_closure', OLD.is_full_closure,
                      'early_close_time', OLD.early_close_time),
           json_object('holiday_name', NEW.holiday_name,
                      'holiday_description', NEW.holiday_description,
                      'products_trading', NEW.products_trading,
                      'is_full_closure', NEW.is_full_closure,
                      'early_close_time', NEW.early_close_time)
    WHERE OLD.holiday_name != NEW.holiday_name
       OR OLD.holiday_description != NEW.holiday_description
       OR OLD.products_trading != NEW.products_trading
       OR OLD.is_full_closure != NEW.is_full_closure
       OR COALESCE(OLD.early_close_time, '') != COALESCE(NEW.early_close_time, '');
END;

CREATE TRIGGER IF NOT EXISTS log_holiday_delete
AFTER DELETE ON holidays
BEGIN
    INSERT INTO holiday_history (iso_code, holiday_date, change_type, old_value)
    VALUES (OLD.iso_code, OLD.holiday_date, 'DELETE',
            json_object('holiday_name', OLD.holiday_name,
                       'holiday_description', OLD.holiday_description,
                       'products_trading', OLD.products_trading));
END;
