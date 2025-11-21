#!/usr/bin/env python3
"""
Holiday Calendar Scraper
Extracts holiday calendar data from exchange websites
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import json
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
import time


class HolidayScraper:
    """Base scraper class for extracting holiday data from exchange websites"""

    def __init__(self, timeout=30, retry_attempts=3, use_browser=False):
        """
        Initialize the scraper

        Args:
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
            use_browser: Enable browser automation for JavaScript-rendered pages
        """
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.use_browser = use_browser
        self.session = requests.Session()
        self._browser = None
        self._playwright = None

        # Initialize exchange-specific extractors
        # Import here to avoid circular dependency
        from extractors import ExchangeExtractors
        self.extractors = ExchangeExtractors(self)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_url(self, url: str, binary: bool = False) -> Tuple[bool, Optional[str], Optional[int], Optional[str]]:
        """
        Fetch content from URL with retry logic

        Args:
            url: URL to fetch
            binary: If True, return binary content (bytes), otherwise text (str)

        Returns:
            Tuple of (success, content, status_code, error_message)
        """
        for attempt in range(self.retry_attempts):
            try:
                response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                response.raise_for_status()
                content = response.content if binary else response.text
                return True, content, response.status_code, None
            except requests.exceptions.RequestException as e:
                error_msg = f"Attempt {attempt + 1}/{self.retry_attempts} failed: {str(e)}"
                if attempt < self.retry_attempts - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return False, None, getattr(e.response, 'status_code', None), error_msg
        return False, None, None, "Max retry attempts exceeded"

    def discover_calendar_url(self, base_url: str, current_year: int = None) -> List[str]:
        """
        Discover potential calendar URLs from base URL

        Args:
            base_url: Base URL of the exchange
            current_year: Year to search for (default: current year)

        Returns:
            List of potential calendar URLs
        """
        if current_year is None:
            current_year = datetime.now().year

        potential_urls = []

        # Try to fetch the base URL
        success, content, _, _ = self.fetch_url(base_url)
        if not success or not content:
            return potential_urls

        soup = BeautifulSoup(content, 'html.parser')

        # Keywords to search for in links
        keywords = ['holiday', 'calendar', 'trading hours', 'trading-hours',
                    'trading calendar', 'market hours', 'trading-calendar',
                    'holidays', 'calendars', str(current_year)]

        # Find all links
        links = soup.find_all('a', href=True)

        for link in links:
            href = link.get('href', '')
            text = link.get_text().lower()

            # Check if link text or href contains relevant keywords
            if any(keyword.lower() in text or keyword.lower() in href.lower()
                   for keyword in keywords):
                full_url = urljoin(base_url, href)
                if full_url not in potential_urls:
                    potential_urls.append(full_url)

        return potential_urls

    def _init_browser(self):
        """Initialize Playwright browser instance (lazy initialization)"""
        if self._playwright is None:
            try:
                from playwright.sync_api import sync_playwright
                self._playwright = sync_playwright().start()
                self._browser = self._playwright.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )
                print("[INFO] Browser automation initialized")
            except ImportError:
                print("[ERROR] Playwright not installed. Run: pip install playwright && playwright install chromium")
                raise
            except Exception as e:
                print(f"[ERROR] Failed to initialize browser: {e}")
                raise

    def _close_browser(self):
        """Close browser and cleanup resources"""
        if self._browser:
            try:
                self._browser.close()
            except Exception as e:
                print(f"[WARN] Error closing browser: {e}")
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception as e:
                print(f"[WARN] Error stopping playwright: {e}")
        self._browser = None
        self._playwright = None

    def fetch_url_with_browser(self, url: str, wait_for_selector: str = None,
                               wait_time: int = 5000, execute_js: str = None) -> Tuple[bool, Optional[str], Optional[int], Optional[str]]:
        """
        Fetch content from URL using browser automation (Playwright)

        Useful for:
        - JavaScript-rendered content
        - Anti-bot protection (403/503 errors)
        - Dynamic content loading

        Args:
            url: URL to fetch
            wait_for_selector: CSS selector to wait for before extracting content
            wait_time: Maximum time to wait in milliseconds (default: 5000)
            execute_js: Optional JavaScript to execute before extracting content

        Returns:
            Tuple of (success, content, status_code, error_message)
        """
        try:
            # Initialize browser if needed
            if self._browser is None:
                self._init_browser()

            # Create new page
            page = self._browser.new_page()

            try:
                # Navigate to URL
                response = page.goto(url, wait_until='networkidle', timeout=self.timeout * 1000)
                status_code = response.status if response else None

                # Wait for specific selector if provided
                if wait_for_selector:
                    try:
                        page.wait_for_selector(wait_for_selector, timeout=wait_time)
                    except Exception as e:
                        print(f"[WARN] Selector '{wait_for_selector}' not found: {e}")
                else:
                    # Default wait for page to be ready
                    page.wait_for_load_state('domcontentloaded')

                # Execute custom JavaScript if provided
                if execute_js:
                    try:
                        page.evaluate(execute_js)
                    except Exception as e:
                        print(f"[WARN] JavaScript execution failed: {e}")

                # Extract HTML content
                content = page.content()

                return True, content, status_code, None

            finally:
                page.close()

        except Exception as e:
            error_msg = f"Browser automation failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return False, None, None, error_msg

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup browser resources"""
        self._close_browser()

    def parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse various date formats and convert to ISO format (YYYY-MM-DD)

        Args:
            date_str: Date string in various formats

        Returns:
            ISO formatted date string or None if parsing fails
        """
        # Remove extra whitespace
        date_str = ' '.join(date_str.split())

        # Common date formats to try
        formats = [
            '%Y-%m-%d',  # ISO format
            '%d/%m/%Y',  # DD/MM/YYYY
            '%m/%d/%Y',  # MM/DD/YYYY
            '%d-%m-%Y',  # DD-MM-YYYY
            '%Y/%m/%d',  # YYYY/MM/DD
            '%B %d, %Y',  # January 1, 2025
            '%b %d, %Y',  # Jan 1, 2025
            '%d %B %Y',  # 1 January 2025
            '%d %b %Y',  # 1 Jan 2025
            '%A, %B %d, %Y',  # Monday, January 1, 2025
            '%A, %d %B %Y',  # Monday, 1 January 2025
        ]

        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue

        # Try to extract date with regex
        # Match patterns like "January 1, 2025", "1 January 2025", etc.
        date_pattern = r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})'
        match = re.search(date_pattern, date_str, re.IGNORECASE)
        if match:
            day, month, year = match.groups()
            try:
                date_obj = datetime.strptime(f"{day} {month} {year}", '%d %B %Y')
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                try:
                    date_obj = datetime.strptime(f"{day} {month} {year}", '%d %b %Y')
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    pass

        return None

    def extract_holidays_generic(self, url: str, iso_code: str) -> List[Dict]:
        """
        Generic holiday extraction from HTML tables

        Args:
            url: Calendar URL
            iso_code: Exchange ISO code

        Returns:
            List of holiday dictionaries
        """
        success, content, _, _ = self.fetch_url(url)
        if not success or not content:
            return []

        soup = BeautifulSoup(content, 'html.parser')
        holidays = []

        # Look for tables that might contain holiday information
        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue

                # Try to extract date and holiday name
                for i, cell in enumerate(cells):
                    cell_text = cell.get_text(strip=True)
                    parsed_date = self.parse_date(cell_text)

                    if parsed_date:
                        # Found a date, look for holiday name in adjacent cells
                        holiday_name = None
                        description = None
                        products_trading = None

                        # Check next cells for holiday name
                        for j in range(i + 1, min(i + 4, len(cells))):
                            text = cells[j].get_text(strip=True)
                            if text and not self.parse_date(text):
                                if not holiday_name:
                                    holiday_name = text
                                elif not description and text != holiday_name:
                                    description = text

                        if holiday_name:
                            holiday = {
                                'iso_code': iso_code,
                                'holiday_date': parsed_date,
                                'holiday_name': holiday_name,
                                'holiday_description': description,
                                'products_trading': products_trading,
                                'is_full_closure': True,
                                'early_close_time': None
                            }

                            # Check if it's an early close
                            row_text = row.get_text().lower()
                            if 'early close' in row_text or 'early closing' in row_text:
                                holiday['is_full_closure'] = False
                                # Try to extract time
                                time_match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)?', row_text, re.IGNORECASE)
                                if time_match:
                                    holiday['early_close_time'] = time_match.group(0)

                            # Check for products still trading
                            if 'trading' in row_text and 'products' in row_text:
                                products_text = re.search(r'products:?\s*([^.]+)', row_text, re.IGNORECASE)
                                if products_text:
                                    holiday['products_trading'] = products_text.group(1).strip()

                            holidays.append(holiday)
                        break

        return holidays

    def extract_holidays_from_pdf(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from PDF files (requires pdfplumber)

        Args:
            url: PDF URL
            iso_code: Exchange ISO code

        Returns:
            List of holiday dictionaries
        """
        try:
            import pdfplumber
            import io

            success, content_bytes, _, _ = self.fetch_url(url, binary=True)
            if not success:
                return []

            holidays = []

            with pdfplumber.open(io.BytesIO(content_bytes)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue

                    # Look for dates and holiday names in text
                    lines = text.split('\n')
                    for line in lines:
                        parsed_date = self.parse_date(line)
                        if parsed_date:
                            # Extract holiday name from the line
                            words = line.split()
                            holiday_name = ' '.join([w for w in words if not any(c.isdigit() for c in w)])

                            if holiday_name:
                                holidays.append({
                                    'iso_code': iso_code,
                                    'holiday_date': parsed_date,
                                    'holiday_name': holiday_name.strip(),
                                    'holiday_description': None,
                                    'products_trading': None,
                                    'is_full_closure': True,
                                    'early_close_time': None
                                })

            return holidays

        except ImportError:
            print("Warning: pdfplumber not installed. Cannot parse PDF files.")
            return []
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return []

    def extract_holidays(self, url: str, iso_code: str) -> List[Dict]:
        """
        Main method to extract holidays from a URL

        Args:
            url: Calendar URL
            iso_code: Exchange ISO code

        Returns:
            List of holiday dictionaries
        """
        # Check if there's a custom extractor for this exchange
        if self.extractors.has_extractor(iso_code):
            print(f"[INFO] Using custom extractor for {iso_code}")
            extractor_func = self.extractors.get_extractor(iso_code)
            return extractor_func(url, iso_code)

        # Fall back to generic extraction
        print(f"[WARN] No custom extractor for {iso_code}, using generic parser")

        # Determine file type
        if url.lower().endswith('.pdf'):
            return self.extract_holidays_from_pdf(url, iso_code)
        else:
            return self.extract_holidays_generic(url, iso_code)


if __name__ == '__main__':
    # Test the scraper
    scraper = HolidayScraper()

    # Test date parsing
    test_dates = [
        "January 1, 2025",
        "01/01/2025",
        "2025-01-01",
        "1 Jan 2025",
        "Monday, January 1, 2025"
    ]

    print("Testing date parsing:")
    for date_str in test_dates:
        parsed = scraper.parse_date(date_str)
        print(f"  {date_str:30s} -> {parsed}")
