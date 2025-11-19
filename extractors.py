"""
Exchange-specific holiday extractors

Each exchange has its own extractor function that knows how to parse
that specific exchange's holiday calendar format.
"""

from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import re
import pdfplumber
import io


class ExchangeExtractors:
    """Registry of exchange-specific extractor functions"""

    def __init__(self, scraper):
        """
        Initialize extractors with reference to scraper for utility methods

        Args:
            scraper: HolidayScraper instance for fetch_url, parse_date, etc.
        """
        self.scraper = scraper

        # Registry mapping ISO codes to extractor functions
        self.extractors = {
            'XSES': self.extract_sgx_mom,  # Singapore - MOM calendar
            'XEUR': self.extract_eurex,
            'XCME': self.extract_cme,
            'XHKG': self.extract_hkex,
            'BVMF': self.extract_b3,
            'XNDE': self.extract_nasdaq_commodities,
            'NDEX': self.extract_ice_endex,
            # Add more as we build them
        }

    def get_extractor(self, iso_code: str):
        """Get extractor function for an exchange"""
        return self.extractors.get(iso_code)

    def has_extractor(self, iso_code: str) -> bool:
        """Check if extractor exists for an exchange"""
        return iso_code in self.extractors

    # =========================================================================
    # SINGAPORE - SGX (uses MOM calendar)
    # =========================================================================

    def extract_sgx_mom(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from Singapore MOM (Ministry of Manpower) calendar
        SGX follows Singapore public holidays

        URL: http://www.mom.gov.sg/employment-practices/public-holidays

        Table structure:
        - Column 0: Date (e.g., "1 January 2025") - may have <br> for multi-day
        - Column 1: Day of week (e.g., "Wednesday") - may have <br>
        - Column 2: Image with alt text
        - Column 3: Holiday name + <span class="text-date-mobile"> + optional <em> notes

        Examples:
        - Simple: "New Year's Day" on "1 January 2024", "Monday"
        - Multi-day: "Chinese New Year" on "10 February 2024<br>11 February 2024", "Saturday<br>Sunday"
        """
        success, content, _, _ = self.scraper.fetch_url(url)
        if not success:
            return []

        soup = BeautifulSoup(content, 'html.parser')
        holidays = []

        # Find the holiday table (has class "table--holiday")
        table = soup.find('table', class_='table--holiday')
        if not table:
            return []

        rows = table.find('tbody').find_all('tr') if table.find('tbody') else []

        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 4:
                continue

            # Cell 0: Date(s) - get first text node before <br> or all text
            date_cell = cells[0]
            # Get text content, split by <br> if exists
            date_texts = []
            for content in date_cell.stripped_strings:
                date_texts.append(content)

            # Cell 1: Day of week
            day_texts = []
            for content in cells[1].stripped_strings:
                day_texts.append(content)

            # Cell 2: Image - get alt as fallback name
            img_alt = None
            img = cells[2].find('img')
            if img:
                img_alt = img.get('alt', '')

            # Cell 3: Holiday name (first direct text child, before <span>)
            name_cell = cells[3]
            holiday_name = None

            # Get the first text node (before any tags)
            for content in name_cell.children:
                if isinstance(content, str):
                    text = content.strip()
                    if text:
                        holiday_name = text
                        break
                elif content.name is None:  # NavigableString
                    text = str(content).strip()
                    if text:
                        holiday_name = text
                        break

            # Fallback to image alt if no name found
            if not holiday_name:
                holiday_name = img_alt

            if not holiday_name:
                continue

            # For multi-day holidays (like Chinese New Year), create entry for each date
            for i, date_text in enumerate(date_texts):
                parsed_date = self.scraper.parse_date(date_text)

                if parsed_date:
                    day_of_week = day_texts[i] if i < len(day_texts) else day_texts[0] if day_texts else ''

                    holidays.append({
                        'iso_code': iso_code,
                        'holiday_date': parsed_date,
                        'holiday_name': holiday_name,
                        'holiday_description': f"{holiday_name} ({day_of_week})" if day_of_week else holiday_name,
                        'products_trading': None,
                        'is_full_closure': True,
                        'early_close_time': None
                    })

        return holidays

    # =========================================================================
    # GERMANY - Eurex
    # =========================================================================

    def extract_eurex(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from Eurex trading calendar

        URL: https://www.eurex.com/ex-en/trade/trading-calendar

        Eurex typically has a structured calendar with dates and market info.
        Need to inspect actual page structure.
        """
        success, content, _, _ = self.scraper.fetch_url(url)
        if not success:
            return []

        soup = BeautifulSoup(content, 'html.parser')
        holidays = []

        # TODO: Inspect actual Eurex page structure and implement
        # Placeholder for now - need to examine the actual HTML
        print(f"[DEBUG] Eurex extractor needs implementation")
        print(f"[DEBUG] Page title: {soup.title.string if soup.title else 'No title'}")

        # Look for common patterns
        tables = soup.find_all('table')
        print(f"[DEBUG] Found {len(tables)} tables")

        return holidays

    # =========================================================================
    # USA - CME Group
    # =========================================================================

    def extract_cme(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from CME Group trading hours page

        URL: https://www.cmegroup.com/trading-hours.html

        Note: CME blocks basic scraper requests (403 Forbidden)
        May need enhanced headers or alternative URL
        """
        success, content, _, _ = self.scraper.fetch_url(url)
        if not success:
            return []

        soup = BeautifulSoup(content, 'html.parser')
        holidays = []

        # TODO: CME blocks scrapers - need to handle
        print(f"[DEBUG] CME extractor needs implementation (currently blocked)")

        return holidays

    # =========================================================================
    # HONG KONG - HKEX
    # =========================================================================

    def extract_hkex(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from HKEX derivatives calendar

        URL: https://www.hkex.com.hk/Services/Trading/Derivatives/Overview/Trading-Calendar-and-Holiday-Schedule?sc_lang=en

        HKEX has detailed calendar with market segments and trading hours.
        """
        success, content, _, _ = self.scraper.fetch_url(url)
        if not success:
            return []

        soup = BeautifulSoup(content, 'html.parser')
        holidays = []

        # TODO: Inspect actual HKEX page structure
        print(f"[DEBUG] HKEX extractor needs implementation")

        tables = soup.find_all('table')
        print(f"[DEBUG] Found {len(tables)} tables")

        return holidays

    # =========================================================================
    # BRAZIL - B3
    # =========================================================================

    def extract_b3(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from B3 (Brasil Bolsa Balcao) trading calendar

        URL: https://www.b3.com.br/en_us/solutions/platforms/puma-trading-system/for-members-and-traders/trading-calendar/holidays/

        Note: B3 returns 503 - may have bot protection
        """
        success, content, _, _ = self.scraper.fetch_url(url)
        if not success:
            return []

        soup = BeautifulSoup(content, 'html.parser')
        holidays = []

        # TODO: Handle B3 bot protection and implement parser
        print(f"[DEBUG] B3 extractor needs implementation (currently blocked)")

        return holidays

    # =========================================================================
    # NORWAY - Nasdaq Commodities (PDF)
    # =========================================================================

    def extract_nasdaq_commodities(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from Nasdaq Commodities PDF calendar

        URL: https://www.nasdaq.com/docs/2024/12/11/Holiday-Calendar-Commodities-Markets.pdf

        PDF structure:
        - Page 3: Norwegian Trading Calendar
        - Page 4: European Trading Calendar
        - Format: "Holiday Name    Date" (e.g., "New Year    January 1")
        - No years listed - need to infer current/next year
        """
        success, content_bytes, _, _ = self.scraper.fetch_url(url, binary=True)
        if not success:
            return []

        holidays = []
        current_year = datetime.now().year

        try:
            with pdfplumber.open(io.BytesIO(content_bytes)) as pdf:
                # Page 3 = Norwegian calendar (index 2)
                # Page 4 = European calendar (index 3)

                for page_num in [2, 3]:  # Pages 3 and 4
                    if page_num >= len(pdf.pages):
                        continue

                    text = pdf.pages[page_num].extract_text()
                    if not text:
                        continue

                    # Look for holiday patterns
                    # Format: "Holiday Name    Month Day"
                    lines = text.split('\n')

                    # Skip until we find "TRADING ALL WEEK-DAYS EXCEPT ON HOLIDAYS:"
                    in_holiday_section = False

                    for line in lines:
                        if 'TRADING ALL WEEK-DAYS EXCEPT ON HOLIDAYS' in line:
                            in_holiday_section = True
                            continue

                        if in_holiday_section and line.strip():
                            # Skip header lines and page numbers
                            if any(x in line for x in ['DATE:', 'General Communication', 'PAGE']):
                                continue

                            # Try to parse line for holiday
                            # Examples:
                            # "New Year January 1"
                            # "Labor Day May 1"
                            # "Christmas Day December 25"

                            # TODO: Implement smart date parsing with year inference
                            print(f"[DEBUG] Nasdaq line: {line}")

        except Exception as e:
            print(f"Error parsing Nasdaq Commodities PDF: {e}")

        return holidays

    # =========================================================================
    # NETHERLANDS - ICE Endex (PDF)
    # =========================================================================

    def extract_ice_endex(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from ICE Endex PDF trading schedule

        URL: https://www.ice.com/publicdocs/ICE_Endex_Trading_Schedule.pdf

        PDF format varies by year.
        """
        success, content_bytes, _, _ = self.scraper.fetch_url(url, binary=True)
        if not success:
            return []

        holidays = []

        try:
            with pdfplumber.open(io.BytesIO(content_bytes)) as pdf:
                # TODO: Inspect actual PDF structure
                print(f"[DEBUG] ICE Endex PDF has {len(pdf.pages)} pages")

                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        print(f"[DEBUG] Page {i+1} preview: {text[:200]}")

        except Exception as e:
            print(f"Error parsing ICE Endex PDF: {e}")

        return holidays


# =========================================================================
# Helper functions for common patterns
# =========================================================================

def parse_month_day_with_year_inference(month_day_text: str, reference_year: int = None) -> Optional[str]:
    """
    Parse "Month Day" format and infer year

    Args:
        month_day_text: Text like "January 1", "May 1", "December 25"
        reference_year: Year to use (default: current year)

    Returns:
        ISO date string (YYYY-MM-DD) or None

    Logic:
    - If month has passed this year, use next year
    - Otherwise use current year
    """
    if reference_year is None:
        reference_year = datetime.now().year

    # Try to parse with current year
    for year in [reference_year, reference_year + 1]:
        test_string = f"{month_day_text} {year}"

        for fmt in ['%B %d %Y', '%b %d %Y']:
            try:
                parsed = datetime.strptime(test_string, fmt)
                return parsed.strftime('%Y-%m-%d')
            except ValueError:
                continue

    return None
