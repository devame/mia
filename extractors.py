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
            'XJPX': self.extract_jpx,  # Japan Exchange Group
            'XOSE': self.extract_jpx,  # Osaka Exchange (same source as JPX)
            'IFUS': self.extract_ice_futures,  # ICE Futures US (PDF)
            'IFEU': self.extract_ice_futures,  # ICE Futures Europe (same PDF)
            'IFSG': self.extract_ice_futures_singapore,  # ICE Futures Singapore (PDF)
            'XEUR': self.extract_eurex,
            'XCME': self.extract_cme,
            'XHKG': self.extract_hkex,
            'BVMF': self.extract_b3,
            'XNDE': self.extract_nasdaq_commodities,
            'NDEX': self.extract_ice_endex,
            'XLME': self.extract_lme,  # London Metal Exchange
            'XMOD': self.extract_montreal,  # Montreal Exchange (TMX)
            'XASX': self.extract_asx,  # Australian Securities Exchange
            # Euronext exchanges (all 7 use same extractor)
            'XPAR': self.extract_euronext,  # Euronext Paris
            'XAMS': self.extract_euronext,  # Euronext Amsterdam
            'XBRU': self.extract_euronext,  # Euronext Brussels
            'XLIS': self.extract_euronext,  # Euronext Lisbon
            'XDUB': self.extract_euronext,  # Euronext Dublin
            'XMIL': self.extract_euronext,  # Euronext Milan
            'XOSL': self.extract_euronext,  # Euronext Oslo
            # India exchanges
            'XBOM': self.extract_bse_india,  # BSE India (Bombay Stock Exchange)
            # Korea Exchange
            'XKRX': self.extract_krx,  # Korea Exchange
            # New Zealand
            'XNZE': self.extract_nzx,  # New Zealand Exchange
            # Spain
            'XMCE': self.extract_bme_spanish,  # BME Spanish Exchanges
            # Russia
            'MISX': self.extract_moex,  # Moscow Exchange
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
    # JAPAN - JPX / Osaka Exchange
    # =========================================================================

    def extract_jpx(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from Japan Exchange Group (JPX) calendar
        Also used for Osaka Exchange (OSE) as they share the same calendar

        URL: https://www.jpx.co.jp/english/corporate/about-jpx/calendar/index.html
        OSE URL: https://www.jpx.co.jp/english/derivatives/rules/holidaytrading/index.html

        Structure:
        - <h2>2025</h2>
        - <table> with holidays (format: "Jan. 1 (Wed.)" | "New Year's Day")
        - <h2>2026</h2>
        - <table> with holidays

        Date format: "Mon. D (Day)" without year - need to infer from section header
        """
        success, content, _, _ = self.scraper.fetch_url(url)
        if not success:
            return []

        soup = BeautifulSoup(content, 'html.parser')
        holidays = []
        current_year = datetime.now().year

        # Find all h2 headings that contain years
        year_headings = soup.find_all('h2')

        for heading in year_headings:
            heading_text = heading.get_text(strip=True)

            # Check if heading is a year (e.g., "2025", "2026")
            if heading_text.isdigit() and len(heading_text) == 4:
                year = int(heading_text)

                # Find the next table after this heading
                table = heading.find_next('table')
                if not table:
                    continue

                rows = table.find_all('tr')

                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 2:
                        continue

                    date_text = cells[0].get_text(strip=True)  # "Jan. 1 (Wed.)"
                    holiday_name = cells[1].get_text(strip=True)  # "New Year's Day"

                    if not date_text or not holiday_name:
                        continue

                    # Parse date with inferred year
                    # Format: "Jan. 1 (Wed.)" -> extract "Jan. 1"
                    # Remove day of week in parentheses
                    date_part = date_text.split('(')[0].strip()

                    # Add year to make parseable
                    full_date_str = f"{date_part} {year}"

                    # Parse with various formats
                    parsed_date = None
                    for fmt in ['%b. %d %Y', '%B. %d %Y', '%b %d %Y', '%B %d %Y']:
                        try:
                            parsed = datetime.strptime(full_date_str, fmt)
                            parsed_date = parsed.strftime('%Y-%m-%d')
                            break
                        except ValueError:
                            continue

                    if parsed_date:
                        holidays.append({
                            'iso_code': iso_code,
                            'holiday_date': parsed_date,
                            'holiday_name': holiday_name,
                            'holiday_description': holiday_name,
                            'products_trading': None,
                            'is_full_closure': True,
                            'early_close_time': None
                        })

        return holidays

    # =========================================================================
    # USA/EUROPE - ICE Futures (PDF)
    # =========================================================================

    def extract_ice_futures(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from ICE Futures trading schedule PDF
        Used for both ICE Futures US (IFUS) and ICE Futures Europe (IFEU)

        URL: https://www.ice.com/publicdocs/Trading_Schedule.pdf

        PDF contains trading schedules for multiple ICE exchanges with holiday closures.
        Structure varies - need to parse tables and look for closure dates.
        """
        success, content_bytes, _, _ = self.scraper.fetch_url(url, binary=True)
        if not success:
            return []

        holidays = []
        current_year = datetime.now().year

        try:
            with pdfplumber.open(io.BytesIO(content_bytes)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue

                    lines = text.split('\n')

                    # Look for date patterns and "Closed" indicators
                    for line in lines:
                        # Look for dates followed by "Closed" or "Holiday"
                        if any(indicator in line for indicator in ['Closed', 'Holiday', 'CLOSED']):
                            # Try to extract date from line
                            # Common patterns: "January 1" "Jan 1" "1/1/2025"
                            words = line.split()

                            # Try to find date in this line
                            for i, word in enumerate(words):
                                if i < len(words) - 1:
                                    # Try "Month Day" pattern
                                    date_str = f"{word} {words[i+1]}"
                                    parsed_date = parse_month_day_with_year_inference(date_str, current_year)

                                    if parsed_date:
                                        # Extract holiday name from line
                                        holiday_name = line.strip()

                                        holidays.append({
                                            'iso_code': iso_code,
                                            'holiday_date': parsed_date,
                                            'holiday_name': holiday_name,
                                            'holiday_description': holiday_name,
                                            'products_trading': None,
                                            'is_full_closure': True,
                                            'early_close_time': None
                                        })
                                        break

        except Exception as e:
            print(f"Error parsing ICE Futures PDF: {e}")

        return holidays

    # =========================================================================
    # GERMANY - Eurex
    # =========================================================================

    def extract_eurex(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from Eurex trading calendar PDF

        Eurex provides annual PDF trading calendars at:
        https://www.eurex.com/resource/blob/{id}/data/tradingcalendar_{year}_en.pdf

        Since the HTML page uses JavaScript rendering, we fetch the PDF directly.
        The PDF contains a table with trading days marked as either:
        - Regular trading day
        - Closed (full closure)
        - Special notes (partial closure, early close)

        Strategy:
        1. Try to fetch PDF for current year and next year
        2. Extract all dates marked as "closed" or with special trading notes
        3. Parse into holiday format

        Returns:
            List of dictionaries with holiday information
        """
        holidays = []
        current_year = datetime.now().year

        # Try to fetch PDFs for current year and next year
        for year in [current_year, current_year + 1]:
            # Known PDF URL pattern from 2025
            # The blob ID might change, so we try the known pattern first
            pdf_urls = [
                f"https://www.eurex.com/resource/blob/4242284/1c8da6dc2702d508ee2a4740654ea77d/data/tradingcalendar_{year}_en.pdf",
                f"https://www.eurex.com/ex-en/resources/trading-calendar/{year}",
            ]

            pdf_content = None
            for pdf_url in pdf_urls:
                success, content_bytes, _, _ = self.scraper.fetch_url(pdf_url, binary=True)
                if success and content_bytes:
                    pdf_content = content_bytes
                    break

            if not pdf_content:
                continue

            # Parse PDF
            try:
                year_holidays = self._extract_eurex_from_pdf(pdf_content, iso_code, year)
                holidays.extend(year_holidays)
            except Exception as e:
                print(f"[Eurex] Error parsing PDF for {year}: {e}")
                continue

        return holidays

    def _extract_eurex_from_pdf(self, content_bytes: bytes, iso_code: str, year: int) -> List[Dict]:
        """
        Extract holidays from Eurex trading calendar PDF

        The PDF format (as of 2025) contains text split across lines like:
        Line 1: "Eurex is closed for trading and clearing (exercise, settlement and cash)"
        Line 2: "in all derivatives: 1 January, 18 April, 21April, 1 May, 25 December,"
        Line 3: "26 December"

        Args:
            content_bytes: PDF file content
            iso_code: Exchange ISO code
            year: Year of the calendar

        Returns:
            List of holiday dictionaries
        """
        holidays = []

        try:
            with pdfplumber.open(io.BytesIO(content_bytes)) as pdf:
                # Extract text from all pages
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"

                if not full_text:
                    return holidays

                # Look for holiday declaration sections
                lines = full_text.split('\n')

                # Process lines looking for "Eurex is closed" declarations
                for i, line in enumerate(lines):
                    line_lower = line.lower()

                    # Check if line contains holiday closure information
                    if 'eurex is closed' in line_lower:
                        # Determine closure type from this line
                        is_full_closure = 'clearing' in line_lower and ('exercise' in line_lower or 'settlement' in line_lower)

                        # Look for dates in this line and the next few lines
                        # The dates might be on the same line or continuation lines
                        context_lines = [line]
                        for j in range(1, 4):  # Check next 3 lines
                            if i + j < len(lines):
                                context_lines.append(lines[i + j])

                        # Combine context lines for date extraction
                        context_text = ' '.join(context_lines)

                        # Extract dates from context
                        month_names = ['january', 'february', 'march', 'april', 'may', 'june',
                                      'july', 'august', 'september', 'october', 'november', 'december']

                        # Find all "DD Month" patterns
                        for month_idx, month_name in enumerate(month_names, 1):
                            # Look for patterns like "1 January", "18 April", "21April" (no space)
                            patterns = [
                                rf'(\d{{1,2}})\s+{month_name}',  # With space
                                rf'(\d{{1,2}}){month_name}',     # Without space
                            ]

                            for pattern in patterns:
                                matches = re.finditer(pattern, context_text.lower())
                                for match in matches:
                                    try:
                                        day = int(match.group(1))
                                        parsed_date = datetime(year, month_idx, day)
                                        iso_date = parsed_date.strftime('%Y-%m-%d')

                                        # Extract holiday name
                                        holiday_name = self._extract_eurex_holiday_name(context_text, parsed_date)

                                        # Check if we already have this holiday
                                        if not any(h['holiday_date'] == iso_date for h in holidays):
                                            holidays.append({
                                                'iso_code': iso_code,
                                                'holiday_date': iso_date,
                                                'holiday_name': holiday_name,
                                                'holiday_description': 'Eurex closed for trading' + (' and clearing' if is_full_closure else ''),
                                                'products_trading': None,
                                                'is_full_closure': is_full_closure,
                                                'early_close_time': None
                                            })
                                    except (ValueError, IndexError) as e:
                                        continue

        except Exception as e:
            print(f"[Eurex] Error extracting from PDF: {e}")

        return holidays

    def _extract_eurex_holiday_name(self, text: str, date: datetime) -> str:
        """
        Extract holiday name from Eurex calendar text or infer from date

        Args:
            text: Text containing the holiday mention
            date: The holiday date

        Returns:
            Holiday name
        """
        text_lower = text.lower()

        # Check for explicit holiday names (English and German)
        holiday_keywords = {
            "New Year's Day": ['new year', 'neujahr'],
            "Good Friday": ['good friday', 'karfreitag'],
            "Easter Monday": ['easter monday', 'ostermontag'],
            "Labour Day": ['labour day', 'labor day', 'tag der arbeit', '1. mai'],
            "Christmas Eve": ['christmas eve', 'heiligabend'],
            "Christmas Day": ['christmas day', '1. weihnachtstag', 'weihnachten'],
            "Boxing Day": ['boxing day', '2. weihnachtstag'],
            "Whit Monday": ['whit monday', 'pfingstmontag'],
            "German Unity Day": ['german unity', 'tag der deutschen einheit'],
        }

        for holiday_name, keywords in holiday_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return holiday_name

        # Infer from date (common German holidays)
        if date.month == 1 and date.day == 1:
            return "New Year's Day"
        elif date.month == 5 and date.day == 1:
            return "Labour Day"
        elif date.month == 10 and date.day == 3:
            return "German Unity Day"
        elif date.month == 12 and date.day == 24:
            return "Christmas Eve"
        elif date.month == 12 and date.day == 25:
            return "Christmas Day"
        elif date.month == 12 and date.day == 26:
            return "Boxing Day"

        # Default to formatted date
        return date.strftime('%B %d')

    # =========================================================================
    # EUROPE - Euronext (All 7 exchanges)
    # =========================================================================

    def extract_euronext(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from Euronext trading hours & holidays page
        Used for all 7 Euronext exchanges

        URL: https://www.euronext.com/en/trading/trading-hours-holidays

        Exchanges:
        - XPAR: Paris
        - XAMS: Amsterdam
        - XBRU: Brussels
        - XLIS: Lisbon
        - XDUB: Dublin
        - XMIL: Milan
        - XOSL: Oslo

        Structure:
        - Multiple tables (one per year: 2024, 2025, 2026)
        - First column: Date and holiday name (e.g., "Friday 3 April 2026 (Good Friday)")
        - Subsequent columns: One per exchange (Amsterdam, Brussels, Dublin, Lisbon, Milan, Oslo, Paris)
        - Cell values: "Closed", "Full Trading Day", "Half Trading Day", "*No TAH", etc.

        Returns holidays for the specific exchange (iso_code)
        """
        success, content, _, _ = self.scraper.fetch_url(url)
        if not success:
            return []

        soup = BeautifulSoup(content, 'html.parser')
        holidays = []

        # Mapping of ISO codes to exchange names (as they appear in table headers)
        iso_to_exchange = {
            'XPAR': 'Paris',
            'XAMS': 'Amsterdam',
            'XBRU': 'Brussels',
            'XLIS': 'Lisbon',
            'XDUB': 'Dublin',
            'XMIL': 'Milan',
            'XOSL': 'Oslo'
        }

        if iso_code not in iso_to_exchange:
            return []

        target_exchange = iso_to_exchange[iso_code]

        # Find all tables on the page
        tables = soup.find_all('table')

        for table in tables:
            # Get table headers to find the column index for our exchange
            headers = table.find_all('th')
            if not headers:
                continue

            # Find which column contains our target exchange
            target_column_index = None
            for idx, header in enumerate(headers):
                header_text = header.get_text(strip=True)
                if target_exchange.lower() in header_text.lower():
                    target_column_index = idx
                    break

            # If this table doesn't have our exchange, skip it
            if target_column_index is None:
                continue

            # Process table rows
            tbody = table.find('tbody')
            if not tbody:
                # Try rows directly in table
                rows = table.find_all('tr')
            else:
                rows = tbody.find_all('tr')

            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) <= target_column_index:
                    continue

                # First column: date and holiday name
                date_cell = cells[0]
                date_text = date_cell.get_text(strip=True)

                if not date_text:
                    continue

                # Skip header rows
                if any(x in date_text.lower() for x in ['amsterdam', 'brussels', 'dublin', 'lisbon', 'milan', 'oslo', 'paris']):
                    continue

                # Parse date - format: "Friday 3 April 2026 (Good Friday)"
                # Extract holiday name from parentheses
                holiday_name = None
                if '(' in date_text and ')' in date_text:
                    start = date_text.index('(')
                    end = date_text.index(')')
                    holiday_name = date_text[start+1:end].strip()
                    # Get date part (before parentheses)
                    date_part = date_text[:start].strip()
                else:
                    date_part = date_text
                    holiday_name = date_text

                # Parse the date - format: "Friday 3 April 2026" or "3 April 2026"
                parsed_date = self._parse_euronext_date(date_part)

                if not parsed_date:
                    continue

                # Get status for target exchange
                status_cell = cells[target_column_index]
                status_text = status_cell.get_text(strip=True)

                # Clean up status text (remove footnote markers)
                status_clean = status_text.replace('*', '').replace('**', '').strip()

                # Determine if it's a closure
                is_closed = 'closed' in status_clean.lower()
                is_half_day = 'half' in status_clean.lower()

                # Only add if it's a closure or half day (not full trading days)
                if is_closed or is_half_day:
                    holidays.append({
                        'iso_code': iso_code,
                        'holiday_date': parsed_date,
                        'holiday_name': holiday_name or 'Market Closure',
                        'holiday_description': f"{holiday_name or 'Market Closure'} - {status_clean}",
                        'products_trading': None,
                        'is_full_closure': is_closed,
                        'early_close_time': None if is_closed else 'See exchange website'
                    })

        return holidays

    def _parse_euronext_date(self, date_text: str) -> Optional[str]:
        """
        Parse Euronext date format: "Friday 3 April 2026" or "3 April 2026"

        Args:
            date_text: Date string to parse

        Returns:
            ISO date string (YYYY-MM-DD) or None
        """
        date_text = date_text.strip()

        # Try various date formats
        formats = [
            '%A %d %B %Y',  # "Friday 3 April 2026"
            '%d %B %Y',      # "3 April 2026"
            '%A, %d %B %Y',  # "Friday, 3 April 2026"
            '%d %b %Y',      # "3 Apr 2026"
            '%A %d %b %Y',   # "Friday 3 Apr 2026"
        ]

        for fmt in formats:
            try:
                parsed = datetime.strptime(date_text, fmt)
                return parsed.strftime('%Y-%m-%d')
            except ValueError:
                continue

        return None

    # =========================================================================
    # USA - CME Group
    # =========================================================================

    def extract_cme(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from CME Group trading hours page

        URL: https://www.cmegroup.com/trading-hours.html

        Note: CME blocks basic scraper requests (403 Forbidden)
        Uses browser automation to bypass anti-bot protection
        """
        # Try browser automation first (CME blocks regular requests)
        print(f"[INFO] CME: Using browser automation to bypass anti-bot protection")
        success, content, status_code, error = self.scraper.fetch_url_with_browser(
            url,
            wait_for_selector='table, .table, [class*="holiday"], [class*="calendar"]',
            wait_time=10000
        )

        if not success:
            print(f"[ERROR] CME browser fetch failed: {error}")
            return []

        soup = BeautifulSoup(content, 'html.parser')
        holidays = []

        # CME typically has holiday information in tables or specific sections
        # Look for holiday-related tables
        tables = soup.find_all('table')

        for table in tables:
            # Check if table contains holiday information
            table_text = table.get_text().lower()
            if 'holiday' in table_text or 'closed' in table_text or 'closure' in table_text:
                rows = table.find_all('tr')

                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 2:
                        continue

                    # Try to find date and holiday name
                    for i, cell in enumerate(cells):
                        cell_text = cell.get_text(strip=True)
                        parsed_date = self.scraper.parse_date(cell_text)

                        if parsed_date:
                            # Found a date, look for holiday name in adjacent cells
                            holiday_name = None

                            for j in range(len(cells)):
                                if j != i:
                                    text = cells[j].get_text(strip=True)
                                    if text and not self.scraper.parse_date(text) and len(text) > 2:
                                        holiday_name = text
                                        break

                            if holiday_name and holiday_name.lower() not in ['date', 'day', 'holiday']:
                                holiday = {
                                    'iso_code': iso_code,
                                    'holiday_date': parsed_date,
                                    'holiday_name': holiday_name,
                                    'holiday_description': None,
                                    'products_trading': None,
                                    'is_full_closure': True,
                                    'early_close_time': None
                                }

                                # Check for early close indicators
                                row_text = row.get_text().lower()
                                if 'early close' in row_text or 'early closing' in row_text:
                                    holiday['is_full_closure'] = False
                                    time_match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm|ct|et)?', row_text, re.IGNORECASE)
                                    if time_match:
                                        holiday['early_close_time'] = time_match.group(0)

                                holidays.append(holiday)
                                break

        # Also look for divs or sections with holiday information
        holiday_sections = soup.find_all(['div', 'section'], class_=re.compile(r'holiday|calendar', re.IGNORECASE))

        for section in holiday_sections:
            # Extract dates and holiday names from the section
            text_content = section.get_text()
            lines = text_content.split('\n')

            for i, line in enumerate(lines):
                parsed_date = self.scraper.parse_date(line)
                if parsed_date:
                    # Look for holiday name in nearby lines
                    holiday_name = None
                    for j in range(max(0, i-2), min(len(lines), i+3)):
                        if j != i and lines[j].strip() and not self.scraper.parse_date(lines[j]):
                            holiday_name = lines[j].strip()
                            break

                    if holiday_name and len(holiday_name) > 2:
                        holiday = {
                            'iso_code': iso_code,
                            'holiday_date': parsed_date,
                            'holiday_name': holiday_name,
                            'holiday_description': None,
                            'products_trading': None,
                            'is_full_closure': True,
                            'early_close_time': None
                        }
                        holidays.append(holiday)

        print(f"[INFO] CME: Found {len(holidays)} holidays")
        return holidays

    # =========================================================================
    # HONG KONG - HKEX
    # =========================================================================

    def extract_hkex(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from HKEX derivatives calendar

        URL: https://www.hkex.com.hk/Services/Trading/Derivatives/Overview/Trading-Calendar-and-Holiday-Schedule?sc_lang=en

        HKEX has detailed calendar with market segments and trading hours.
        Uses browser automation for JavaScript-rendered content.
        """
        print(f"[INFO] HKEX: Using browser automation for JavaScript-rendered content")
        success, content, status_code, error = self.scraper.fetch_url_with_browser(
            url,
            wait_for_selector='table',
            wait_time=10000
        )

        if not success:
            print(f"[ERROR] HKEX browser fetch failed: {error}")
            return []

        soup = BeautifulSoup(content, 'html.parser')
        holidays = []

        # HKEX typically has holiday information in tables
        tables = soup.find_all('table')
        print(f"[INFO] HKEX: Found {len(tables)} tables")

        for table in tables:
            # Check if this table contains holiday information
            table_text = table.get_text().lower()
            if not any(keyword in table_text for keyword in ['holiday', 'public', 'closed', 'closure']):
                continue

            rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue

                # Try to extract date and holiday name
                date_found = None
                holiday_name = None

                for i, cell in enumerate(cells):
                    cell_text = cell.get_text(strip=True)
                    parsed_date = self.scraper.parse_date(cell_text)

                    if parsed_date and not date_found:
                        date_found = parsed_date

                        # Look for holiday name in subsequent cells
                        for j in range(i + 1, len(cells)):
                            text = cells[j].get_text(strip=True)
                            if text and len(text) > 2 and not self.scraper.parse_date(text):
                                # Skip common header/label text
                                if text.lower() not in ['date', 'day', 'holiday', 'weekday', 'remarks', 'note', 'notes']:
                                    holiday_name = text
                                    break

                        if holiday_name:
                            holiday = {
                                'iso_code': iso_code,
                                'holiday_date': date_found,
                                'holiday_name': holiday_name,
                                'holiday_description': None,
                                'products_trading': None,
                                'is_full_closure': True,
                                'early_close_time': None
                            }

                            # Check for partial closure or early close
                            row_text = row.get_text().lower()
                            if any(keyword in row_text for keyword in ['half day', 'half-day', 'early close', 'early closing', 'partial']):
                                holiday['is_full_closure'] = False
                                time_match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm|hkt)?', row_text, re.IGNORECASE)
                                if time_match:
                                    holiday['early_close_time'] = time_match.group(0)

                            # Check for products still trading
                            if 'trading' in row_text and any(prod in row_text for prod in ['product', 'market', 'segment']):
                                # Try to extract which products are trading
                                for cell in cells:
                                    text = cell.get_text(strip=True).lower()
                                    if 'trading' in text or 'open' in text:
                                        holiday['products_trading'] = cell.get_text(strip=True)
                                        break

                            holidays.append(holiday)
                            break

        print(f"[INFO] HKEX: Found {len(holidays)} holidays")
        return holidays

    # =========================================================================
    # BRAZIL - B3
    # =========================================================================

    def extract_b3(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from B3 (Brasil Bolsa Balcao) trading calendar

        URL: https://www.b3.com.br/en_us/solutions/platforms/puma-trading-system/for-members-and-traders/trading-calendar/holidays/

        Note: B3 returns 503 - uses browser automation to bypass bot protection
        """
        print(f"[INFO] B3: Using browser automation to bypass bot protection")
        success, content, status_code, error = self.scraper.fetch_url_with_browser(
            url,
            wait_for_selector='table, .table, [class*="calendar"], [class*="holiday"]',
            wait_time=10000
        )

        if not success:
            print(f"[ERROR] B3 browser fetch failed: {error}")
            return []

        soup = BeautifulSoup(content, 'html.parser')
        holidays = []

        # B3 typically has holiday information in tables
        tables = soup.find_all('table')
        print(f"[INFO] B3: Found {len(tables)} tables")

        for table in tables:
            # Check if table contains holiday information
            table_text = table.get_text().lower()
            if not any(keyword in table_text for keyword in ['holiday', 'feriado', 'closed', 'closure', 'data', 'date']):
                continue

            rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue

                # Try to extract date and holiday name
                date_found = None
                holiday_name = None

                for i, cell in enumerate(cells):
                    cell_text = cell.get_text(strip=True)
                    parsed_date = self.scraper.parse_date(cell_text)

                    if parsed_date and not date_found:
                        date_found = parsed_date

                        # Look for holiday name in other cells
                        for j in range(len(cells)):
                            if j != i:
                                text = cells[j].get_text(strip=True)
                                if text and len(text) > 2 and not self.scraper.parse_date(text):
                                    # Skip common headers
                                    if text.lower() not in ['date', 'data', 'day', 'dia', 'holiday', 'feriado', 'weekday']:
                                        holiday_name = text
                                        break

                        if holiday_name:
                            holiday = {
                                'iso_code': iso_code,
                                'holiday_date': date_found,
                                'holiday_name': holiday_name,
                                'holiday_description': None,
                                'products_trading': None,
                                'is_full_closure': True,
                                'early_close_time': None
                            }

                            # Check for early close or partial trading
                            row_text = row.get_text().lower()
                            if any(keyword in row_text for keyword in ['early close', 'early closing', 'fechamento antecipado', 'parcial']):
                                holiday['is_full_closure'] = False
                                time_match = re.search(r'(\d{1,2}):(\d{2})\s*(h|am|pm)?', row_text, re.IGNORECASE)
                                if time_match:
                                    holiday['early_close_time'] = time_match.group(0)

                            holidays.append(holiday)
                            break

        print(f"[INFO] B3: Found {len(holidays)} holidays")
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
    # UK - London Metal Exchange
    # =========================================================================

    def extract_lme(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from London Metal Exchange (LME) trading calendar

        URL: https://www.lme.com/-/media/Files/Trading/Trading-Calendar-2025-2035-digital-version.pdf

        IMPORTANT: The PDF is image-based (scanned pages) and requires OCR to extract text.
        This implementation uses UK bank holiday data since LME follows UK bank holidays.

        LME closure days follow UK bank holidays:
        - New Year's Day (or substitute if weekend)
        - Good Friday
        - Easter Monday
        - Early May Bank Holiday (first Monday in May)
        - Spring Bank Holiday (last Monday in May)
        - Summer Bank Holiday (last Monday in August)
        - Christmas Day (or substitute if weekend)
        - Boxing Day (or substitute if weekend)

        Coverage: 2025-2035

        Returns:
            List of dictionaries with holiday information

        Note:
            For automated PDF extraction, you would need:
            - pytesseract (pip install pytesseract)
            - tesseract-ocr system binary
            - pdf2image (pip install pdf2image)
            - poppler-utils system binary
        """
        success, content_bytes, _, _ = self.scraper.fetch_url(url, binary=True)
        if not success:
            # Fall back to UK bank holidays calculation
            return self._get_lme_uk_bank_holidays(iso_code)

        try:
            # Try to parse PDF
            holidays = self._extract_lme_from_pdf(content_bytes, iso_code, url)

            if holidays:
                return holidays
            else:
                # Fall back to UK bank holidays if PDF parsing fails
                return self._get_lme_uk_bank_holidays(iso_code)

        except Exception as e:
            print(f"[LME] Error parsing PDF: {e}, using UK bank holiday data")
            return self._get_lme_uk_bank_holidays(iso_code)

    def _extract_lme_from_pdf(self, content_bytes: bytes, iso_code: str, url: str) -> List[Dict]:
        """
        Attempt to extract holidays from LME PDF

        Args:
            content_bytes: PDF file content
            iso_code: Exchange ISO code
            url: Original URL

        Returns:
            List of holiday dictionaries, or empty list if extraction fails
        """
        holidays = []

        try:
            with pdfplumber.open(io.BytesIO(content_bytes)) as pdf:
                # Check if PDF has text content
                if len(pdf.pages) > 0:
                    first_page = pdf.pages[0]
                    char_count = len(first_page.chars) if first_page.chars else 0

                    if char_count == 0:
                        # Image-based PDF - requires OCR
                        print("[LME] PDF is image-based and requires OCR. Using UK bank holiday data.")
                        return []

                    # PDF has text but holidays are marked visually (colored cells)
                    # Fall back to calculated UK bank holidays
                    print("[LME] PDF text doesn't explicitly list holidays. Using UK bank holiday data.")
                    return []

        except Exception as e:
            print(f"[LME] PDF parsing error: {e}")
            return []

        return holidays

    def _get_lme_uk_bank_holidays(self, iso_code: str) -> List[Dict]:
        """
        Return LME holidays based on UK bank holidays

        LME follows UK bank holidays. This provides comprehensive coverage
        for years 2025-2035.

        Args:
            iso_code: Exchange ISO code

        Returns:
            List of holiday dictionaries
        """
        holidays = []

        # Generate holidays for years 2025-2035
        for year in range(2025, 2036):
            year_holidays = self._calculate_uk_bank_holidays_for_year(year, iso_code)
            holidays.extend(year_holidays)

        return holidays

    def _calculate_uk_bank_holidays_for_year(self, year: int, iso_code: str) -> List[Dict]:
        """
        Calculate UK bank holidays for a specific year

        Args:
            year: Year to calculate holidays for
            iso_code: Exchange ISO code

        Returns:
            List of holiday dictionaries for the year
        """
        from datetime import timedelta

        # Calculate Easter Sunday
        try:
            from dateutil.easter import easter
            easter_date = easter(year)
        except ImportError:
            # Fallback: use Meeus's algorithm
            easter_date = self._calculate_easter_meeus(year)

        holidays = []

        # New Year's Day (with substitute if on weekend)
        new_year = datetime(year, 1, 1)
        if new_year.weekday() == 5:  # Saturday
            new_year_obs = datetime(year, 1, 3)  # Monday substitute
            holidays.append({
                'iso_code': iso_code,
                'holiday_date': new_year_obs.strftime('%Y-%m-%d'),
                'holiday_name': "New Year's Day (substitute)",
                'holiday_description': "New Year's Day observed (Saturday → Monday)",
                'products_trading': None,
                'is_full_closure': True,
                'early_close_time': None
            })
        elif new_year.weekday() == 6:  # Sunday
            new_year_obs = datetime(year, 1, 2)  # Monday substitute
            holidays.append({
                'iso_code': iso_code,
                'holiday_date': new_year_obs.strftime('%Y-%m-%d'),
                'holiday_name': "New Year's Day (substitute)",
                'holiday_description': "New Year's Day observed (Sunday → Monday)",
                'products_trading': None,
                'is_full_closure': True,
                'early_close_time': None
            })
        else:
            holidays.append({
                'iso_code': iso_code,
                'holiday_date': new_year.strftime('%Y-%m-%d'),
                'holiday_name': "New Year's Day",
                'holiday_description': "New Year's Day",
                'products_trading': None,
                'is_full_closure': True,
                'early_close_time': None
            })

        # Good Friday (Friday before Easter)
        good_friday = easter_date - timedelta(days=2)
        holidays.append({
            'iso_code': iso_code,
            'holiday_date': good_friday.strftime('%Y-%m-%d'),
            'holiday_name': "Good Friday",
            'holiday_description': "Good Friday",
            'products_trading': None,
            'is_full_closure': True,
            'early_close_time': None
        })

        # Easter Monday (Monday after Easter)
        easter_monday = easter_date + timedelta(days=1)
        holidays.append({
            'iso_code': iso_code,
            'holiday_date': easter_monday.strftime('%Y-%m-%d'),
            'holiday_name': "Easter Monday",
            'holiday_description': "Easter Monday",
            'products_trading': None,
            'is_full_closure': True,
            'early_close_time': None
        })

        # Early May Bank Holiday (first Monday in May)
        may_first = datetime(year, 5, 1)
        days_until_monday = (7 - may_first.weekday()) % 7
        if may_first.weekday() != 0:  # If not Monday
            early_may_bh = may_first + timedelta(days=days_until_monday)
        else:
            early_may_bh = may_first

        holidays.append({
            'iso_code': iso_code,
            'holiday_date': early_may_bh.strftime('%Y-%m-%d'),
            'holiday_name': "Early May Bank Holiday",
            'holiday_description': "Early May Bank Holiday (first Monday in May)",
            'products_trading': None,
            'is_full_closure': True,
            'early_close_time': None
        })

        # Spring Bank Holiday (last Monday in May)
        may_end = datetime(year, 5, 31)
        days_back = (may_end.weekday() - 0) % 7  # Days back to Monday
        spring_bh = may_end - timedelta(days=days_back)

        holidays.append({
            'iso_code': iso_code,
            'holiday_date': spring_bh.strftime('%Y-%m-%d'),
            'holiday_name': "Spring Bank Holiday",
            'holiday_description': "Spring Bank Holiday (last Monday in May)",
            'products_trading': None,
            'is_full_closure': True,
            'early_close_time': None
        })

        # Summer Bank Holiday (last Monday in August)
        aug_end = datetime(year, 8, 31)
        days_back = (aug_end.weekday() - 0) % 7  # Days back to Monday
        summer_bh = aug_end - timedelta(days=days_back)

        holidays.append({
            'iso_code': iso_code,
            'holiday_date': summer_bh.strftime('%Y-%m-%d'),
            'holiday_name': "Summer Bank Holiday",
            'holiday_description': "Summer Bank Holiday (last Monday in August)",
            'products_trading': None,
            'is_full_closure': True,
            'early_close_time': None
        })

        # Christmas Day and Boxing Day (with substitutes if on weekend)
        christmas = datetime(year, 12, 25)
        boxing_day = datetime(year, 12, 26)

        if christmas.weekday() == 5:  # Saturday
            # Christmas substitute: Monday Dec 27
            # Boxing Day substitute: Tuesday Dec 28
            holidays.append({
                'iso_code': iso_code,
                'holiday_date': datetime(year, 12, 27).strftime('%Y-%m-%d'),
                'holiday_name': "Christmas Day (substitute)",
                'holiday_description': "Christmas Day observed (Saturday → Monday)",
                'products_trading': None,
                'is_full_closure': True,
                'early_close_time': None
            })
            holidays.append({
                'iso_code': iso_code,
                'holiday_date': datetime(year, 12, 28).strftime('%Y-%m-%d'),
                'holiday_name': "Boxing Day (substitute)",
                'holiday_description': "Boxing Day observed (Sunday → Tuesday)",
                'products_trading': None,
                'is_full_closure': True,
                'early_close_time': None
            })
        elif christmas.weekday() == 6:  # Sunday
            # Christmas substitute: Tuesday Dec 27
            # Boxing Day is Monday Dec 26 (no substitute)
            holidays.append({
                'iso_code': iso_code,
                'holiday_date': boxing_day.strftime('%Y-%m-%d'),
                'holiday_name': "Boxing Day",
                'holiday_description': "Boxing Day",
                'products_trading': None,
                'is_full_closure': True,
                'early_close_time': None
            })
            holidays.append({
                'iso_code': iso_code,
                'holiday_date': datetime(year, 12, 27).strftime('%Y-%m-%d'),
                'holiday_name': "Christmas Day (substitute)",
                'holiday_description': "Christmas Day observed (Sunday → Tuesday)",
                'products_trading': None,
                'is_full_closure': True,
                'early_close_time': None
            })
        else:
            # Normal weekdays
            holidays.append({
                'iso_code': iso_code,
                'holiday_date': christmas.strftime('%Y-%m-%d'),
                'holiday_name': "Christmas Day",
                'holiday_description': "Christmas Day",
                'products_trading': None,
                'is_full_closure': True,
                'early_close_time': None
            })
            holidays.append({
                'iso_code': iso_code,
                'holiday_date': boxing_day.strftime('%Y-%m-%d'),
                'holiday_name': "Boxing Day",
                'holiday_description': "Boxing Day",
                'products_trading': None,
                'is_full_closure': True,
                'early_close_time': None
            })

        return holidays

    def _calculate_easter_meeus(self, year: int):
        """
        Calculate Easter Sunday using Meeus's algorithm (for Gregorian calendar)

        This is a fallback if python-dateutil is not available.

        Args:
            year: Year to calculate Easter for

        Returns:
            datetime object for Easter Sunday
        """
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1

        return datetime(year, month, day)

    # =========================================================================
    # CANADA - Montreal Exchange (TMX)
    # =========================================================================

    def extract_montreal(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from Montreal Exchange trading hours and holidays page

        URL: https://www.m-x.ca/en/trading/data/trading-hours-and-holidays

        Structure:
        - First table contains holiday calendar for current/next year
        - Format: "Date + Holiday Name" | "Interest Rate Status" | "Other Derivatives Status"
        - Example: "January 1, 2025New Year's Day" | "Closed" | "Closed"

        Returns:
            List of holiday dictionaries
        """
        success, content, _, _ = self.scraper.fetch_url(url)
        if not success:
            return []

        soup = BeautifulSoup(content, 'html.parser')
        holidays = []

        # Find the first table (holiday calendar)
        tables = soup.find_all('table')
        if not tables:
            return []

        holiday_table = tables[0]
        rows = holiday_table.find_all('tr')

        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 3:
                continue

            # First cell contains date and holiday name together
            date_holiday_text = cells[0].get_text(strip=True)

            # Skip header rows and year markers
            if not date_holiday_text or date_holiday_text.isdigit() or len(date_holiday_text) < 10:
                continue

            # Interest rate status
            interest_rate_status = cells[1].get_text(strip=True)
            # Other derivatives status
            other_status = cells[2].get_text(strip=True)

            # Parse date and holiday name
            # Format: "January 1, 2025New Year's Day" or "February 14, 2025Day preceding Family Day"
            # Split on year (20XX)
            import re
            match = re.search(r'([A-Za-z]+\s+\d{1,2},\s+\d{4})(.+)', date_holiday_text)
            if not match:
                continue

            date_str = match.group(1)  # "January 1, 2025"
            holiday_name = match.group(2).strip()  # "New Year's Day"

            # Parse the date
            parsed_date = self.scraper.parse_date(date_str)
            if not parsed_date:
                continue

            # Determine if it's a full closure or early close
            is_full_closure = 'closed' in interest_rate_status.lower() and 'closed' in other_status.lower()
            early_close_time = None

            if 'closing at' in interest_rate_status.lower() or 'closing at' in other_status.lower():
                # Extract early close time
                time_match = re.search(r'(\d{1,2}:\d{2}\s*[ap]\.?m\.?)', interest_rate_status + ' ' + other_status, re.IGNORECASE)
                if time_match:
                    early_close_time = time_match.group(1)
                is_full_closure = False

            # Add holiday
            holidays.append({
                'iso_code': iso_code,
                'holiday_date': parsed_date,
                'holiday_name': holiday_name,
                'holiday_description': f"{holiday_name} - IR: {interest_rate_status}, Other: {other_status}",
                'products_trading': None,
                'is_full_closure': is_full_closure,
                'early_close_time': early_close_time
            })

        return holidays

    # =========================================================================
    # AUSTRALIA - ASX (Australian Securities Exchange)
    # =========================================================================

    def extract_asx(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from ASX 24 derivatives trading calendar

        URL: https://www.asx.com.au/markets/market-resources/asx-24-trading-calendar

        The page lists public holidays and trading days for ASX 24 derivatives market.
        """
        success, content, _, _ = self.scraper.fetch_url(url)
        if not success:
            return []

        soup = BeautifulSoup(content, 'html.parser')
        holidays = []
        current_year = datetime.now().year

        # Look for tables with holiday information
        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue

                # Look for date patterns in cells
                for i, cell in enumerate(cells):
                    cell_text = cell.get_text(strip=True)

                    # Try to parse as a date
                    parsed_date = self.scraper.parse_date(cell_text)
                    if parsed_date:
                        # Look for holiday name in adjacent cells or same cell
                        holiday_name = None

                        # Check next cell
                        if i + 1 < len(cells):
                            next_text = cells[i + 1].get_text(strip=True)
                            if next_text and not self.scraper.parse_date(next_text):
                                holiday_name = next_text

                        # Check if holiday name is in same cell after date
                        if not holiday_name:
                            # Remove date from cell text to get holiday name
                            remaining = cell_text.replace(parsed_date, '').strip()
                            if remaining:
                                holiday_name = remaining

                        if holiday_name and holiday_name.lower() not in ['date', 'day', 'trading', 'status']:
                            holidays.append({
                                'iso_code': iso_code,
                                'holiday_date': parsed_date,
                                'holiday_name': holiday_name,
                                'holiday_description': holiday_name,
                                'products_trading': None,
                                'is_full_closure': True,
                                'early_close_time': None
                            })
                            break

        return holidays

    # =========================================================================
    # SINGAPORE - ICE Futures Singapore (PDF)
    # =========================================================================

    def extract_ice_futures_singapore(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from ICE Futures Singapore PDF trading schedule

        URL: https://www.ice.com/publicdocs/futures/IFSG_Trading_Schedule.pdf

        Similar format to other ICE PDFs - lists holidays with closure status.
        """
        success, content_bytes, _, _ = self.scraper.fetch_url(url, binary=True)
        if not success:
            return []

        holidays = []
        current_year = datetime.now().year

        try:
            with pdfplumber.open(io.BytesIO(content_bytes)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue

                    lines = text.split('\n')

                    # Look for holiday patterns
                    # ICE PDFs typically format: "Date | Holiday Name | Status"
                    for line in lines:
                        # Look for lines with "Closed" or "Holiday"
                        if any(indicator in line for indicator in ['Closed', 'Holiday', 'CLOSED']):
                            # Try to extract date
                            # Common patterns in ICE PDFs: "Monday, 1 January 2025", "1 January 2025", "01/01/2025"

                            # Try various date patterns
                            import re
                            date_patterns = [
                                r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
                                r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})',
                                r'(\d{1,2}/\d{1,2}/\d{4})',
                            ]

                            for pattern in date_patterns:
                                matches = re.findall(pattern, line, re.IGNORECASE)
                                for date_str in matches:
                                    parsed_date = self.scraper.parse_date(date_str)
                                    if parsed_date:
                                        # Extract holiday name from line
                                        holiday_name = line.strip()

                                        # Clean up the name (remove date and status indicators)
                                        for remove in [date_str, 'Closed', 'CLOSED', 'Holiday', 'HOLIDAY']:
                                            holiday_name = holiday_name.replace(remove, '')
                                        holiday_name = holiday_name.strip(' -|')

                                        if holiday_name:
                                            holidays.append({
                                                'iso_code': iso_code,
                                                'holiday_date': parsed_date,
                                                'holiday_name': holiday_name,
                                                'holiday_description': holiday_name,
                                                'products_trading': None,
                                                'is_full_closure': True,
                                                'early_close_time': None
                                            })
                                        break

        except Exception as e:
            print(f"[ICE Futures Singapore] Error parsing PDF: {e}")

        return holidays

    # =========================================================================
    # INDIA - BSE (Bombay Stock Exchange)
    # =========================================================================

    def extract_bse_india(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from BSE India

        URL: https://www.bseindia.com/static/markets/marketinfo/listholi.aspx

        Structure: Multiple HTML tables for different segments (equity, currency, commodity)
        Table format:
        - Column 0: SI.NO (serial number)
        - Column 1: Holidays/Festival Name
        - Column 2: Date (format: "February 26,2025")
        - Column 3: Day
        - Columns 4-5 (optional): Morning session / Evening session (for partial closures)
        """
        success, content, _, _ = self.scraper.fetch_url(url)
        if not success:
            return []

        soup = BeautifulSoup(content, 'html.parser')
        holidays = []
        seen_dates = set()  # To avoid duplicates by date (database has UNIQUE constraint on iso_code+date)

        # Find all tables
        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue

            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 4:
                    continue

                # Skip header rows
                cell_text = cells[1].get_text().strip()
                if cell_text in ['Holidays', 'Festival Name', 'Holiday Name']:
                    continue

                # Try to parse as holiday data
                try:
                    serial = cells[0].get_text().strip()
                    if not serial or not serial[0].isdigit():
                        continue

                    holiday_name = cells[1].get_text().strip()
                    date_text = cells[2].get_text().strip()
                    day = cells[3].get_text().strip()

                    if not holiday_name or not date_text:
                        continue

                    # Normalize date text (handle inconsistent comma spacing)
                    # "February 26,2025" -> "February 26, 2025"
                    normalized_date = re.sub(r'(\d+),\s*(\d{4})', r'\1, \2', date_text)

                    # Parse the date
                    parsed_date = self.scraper.parse_date(normalized_date)
                    if not parsed_date:
                        continue

                    # Check for partial closures
                    is_full_closure = True
                    if len(cells) >= 6:
                        morning_status = cells[4].get_text().strip()
                        evening_status = cells[5].get_text().strip()
                        # If either session is open, it's not a full closure
                        if 'Open' in morning_status or 'Open' in evening_status:
                            is_full_closure = 'Closed' in morning_status and 'Closed' in evening_status

                    # Avoid duplicate dates (database has UNIQUE constraint on iso_code+date)
                    if parsed_date in seen_dates:
                        continue

                    seen_dates.add(parsed_date)

                    holidays.append({
                        'iso_code': iso_code,
                        'holiday_date': parsed_date,
                        'holiday_name': holiday_name,
                        'holiday_description': holiday_name,
                        'products_trading': None,
                        'is_full_closure': is_full_closure,
                        'early_close_time': None
                    })

                except Exception as e:
                    continue  # Skip malformed rows

        return holidays

    # =========================================================================
    # KOREA - KRX (Korea Exchange)
    # =========================================================================

    def extract_krx(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from Korea Exchange

        URL: https://global.krx.co.kr/contents/GLB/05/0501/0501110000/GLB0501110000.jsp

        Structure: HTML page with holiday calendar
        Uses browser automation for JavaScript-rendered content
        """
        print(f"[INFO] KRX: Using browser automation for JavaScript-rendered content")
        success, content, status_code, error = self.scraper.fetch_url_with_browser(
            url,
            wait_for_selector='table',
            wait_time=10000
        )

        if not success:
            print(f"[ERROR] KRX browser fetch failed: {error}")
            return []

        soup = BeautifulSoup(content, 'html.parser')
        holidays = []

        # Find tables
        tables = soup.find_all('table')
        print(f"[INFO] KRX: Found {len(tables)} tables")

        for table in tables:
            rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue

                # Try to extract date and holiday name from cells
                date_found = None
                holiday_name = None

                for i, cell in enumerate(cells):
                    cell_text = cell.get_text(strip=True)
                    parsed_date = self.scraper.parse_date(cell_text)

                    if parsed_date and not date_found:
                        date_found = parsed_date

                        # Look for holiday name in other cells
                        for j in range(len(cells)):
                            if j != i:
                                text = cells[j].get_text(strip=True)
                                if text and len(text) > 2 and not self.scraper.parse_date(text):
                                    # Skip common headers
                                    if text.lower() not in ['date', 'day', 'holiday', 'weekday', 'no.', 'remarks']:
                                        holiday_name = text
                                        break

                        if holiday_name:
                            holiday = {
                                'iso_code': iso_code,
                                'holiday_date': date_found,
                                'holiday_name': holiday_name,
                                'holiday_description': None,
                                'products_trading': None,
                                'is_full_closure': True,
                                'early_close_time': None
                            }
                            holidays.append(holiday)
                            break

        print(f"[INFO] KRX: Found {len(holidays)} holidays")
        return holidays

    # =========================================================================
    # NEW ZEALAND - NZX
    # =========================================================================

    def extract_nzx(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from New Zealand Exchange

        URL: https://www.nzx.com/announcements/443000

        Structure: HTML page with announcement
        Uses browser automation for JavaScript-rendered content
        """
        print(f"[INFO] NZX: Using browser automation for JavaScript-rendered content")
        success, content, status_code, error = self.scraper.fetch_url_with_browser(
            url,
            wait_for_selector='table, .announcement-content, [class*="calendar"]',
            wait_time=10000
        )

        if not success:
            print(f"[ERROR] NZX browser fetch failed: {error}")
            return []

        soup = BeautifulSoup(content, 'html.parser')
        holidays = []

        # Look for tables
        tables = soup.find_all('table')
        print(f"[INFO] NZX: Found {len(tables)} tables")

        for table in tables:
            rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue

                # Try to extract date and holiday name from cells
                date_found = None
                holiday_name = None

                for i, cell in enumerate(cells):
                    cell_text = cell.get_text(strip=True)
                    parsed_date = self.scraper.parse_date(cell_text)

                    if parsed_date and not date_found:
                        date_found = parsed_date

                        # Look for holiday name in other cells
                        for j in range(len(cells)):
                            if j != i:
                                text = cells[j].get_text(strip=True)
                                if text and len(text) > 2 and not self.scraper.parse_date(text):
                                    # Skip common headers
                                    if text.lower() not in ['date', 'day', 'holiday', 'weekday', 'remarks', 'status']:
                                        holiday_name = text
                                        break

                        if holiday_name:
                            holiday = {
                                'iso_code': iso_code,
                                'holiday_date': date_found,
                                'holiday_name': holiday_name,
                                'holiday_description': None,
                                'products_trading': None,
                                'is_full_closure': True,
                                'early_close_time': None
                            }
                            holidays.append(holiday)
                            break

        print(f"[INFO] NZX: Found {len(holidays)} holidays")
        return holidays

    # =========================================================================
    # SPAIN - BME (Bolsas y Mercados Españoles)
    # =========================================================================

    def extract_bme_spanish(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from BME Spanish Exchanges

        URL: https://www.bolsasymercados.es/bme-exchange/en/Trading

        Structure: HTML page with trading calendar
        Uses browser automation for JavaScript-rendered content
        """
        print(f"[INFO] BME Spanish: Using browser automation for JavaScript-rendered content")
        success, content, status_code, error = self.scraper.fetch_url_with_browser(
            url,
            wait_for_selector='table, [class*="calendar"], [class*="trading"]',
            wait_time=10000
        )

        if not success:
            print(f"[ERROR] BME Spanish browser fetch failed: {error}")
            return []

        soup = BeautifulSoup(content, 'html.parser')
        holidays = []

        # Look for tables
        tables = soup.find_all('table')
        print(f"[INFO] BME Spanish: Found {len(tables)} tables")

        for table in tables:
            # Check if table contains holiday/calendar information
            table_text = table.get_text().lower()
            if not any(keyword in table_text for keyword in ['holiday', 'festivo', 'closed', 'calendar', 'trading']):
                continue

            rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue

                # Try to extract date and holiday name
                date_found = None
                holiday_name = None

                for i, cell in enumerate(cells):
                    cell_text = cell.get_text(strip=True)
                    parsed_date = self.scraper.parse_date(cell_text)

                    if parsed_date and not date_found:
                        date_found = parsed_date

                        # Look for holiday name in other cells
                        for j in range(len(cells)):
                            if j != i:
                                text = cells[j].get_text(strip=True)
                                if text and len(text) > 2 and len(text) < 100 and not self.scraper.parse_date(text):
                                    # Skip common headers
                                    if text.lower() not in ['date', 'fecha', 'day', 'día', 'holiday', 'festivo']:
                                        holiday_name = text
                                        break

                        if holiday_name:
                            holiday = {
                                'iso_code': iso_code,
                                'holiday_date': date_found,
                                'holiday_name': holiday_name,
                                'holiday_description': None,
                                'products_trading': None,
                                'is_full_closure': True,
                                'early_close_time': None
                            }
                            holidays.append(holiday)
                            break

        print(f"[INFO] BME Spanish: Found {len(holidays)} holidays")
        return holidays

    # =========================================================================
    # RUSSIA - MOEX (Moscow Exchange)
    # =========================================================================

    def extract_moex(self, url: str, iso_code: str) -> List[Dict]:
        """
        Extract holidays from Moscow Exchange

        URL: https://www.moex.com/en/tradingcalendar

        Structure: HTML page with trading calendar
        Uses browser automation for JavaScript-rendered content
        """
        print(f"[INFO] Moscow Exchange: Using browser automation for JavaScript-rendered content")
        success, content, status_code, error = self.scraper.fetch_url_with_browser(
            url,
            wait_for_selector='table, [class*="calendar"], [class*="trading"]',
            wait_time=10000
        )

        if not success:
            print(f"[ERROR] Moscow Exchange browser fetch failed: {error}")
            return []

        soup = BeautifulSoup(content, 'html.parser')
        holidays = []

        # Look for tables
        tables = soup.find_all('table')
        print(f"[INFO] Moscow Exchange: Found {len(tables)} tables")

        for table in tables:
            # Check if table contains holiday/calendar information
            table_text = table.get_text().lower()
            if not any(keyword in table_text for keyword in ['holiday', 'выходной', 'closed', 'calendar', 'trading']):
                continue

            rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue

                # Try to extract date and holiday name
                date_found = None
                holiday_name = None

                for i, cell in enumerate(cells):
                    cell_text = cell.get_text(strip=True)
                    parsed_date = self.scraper.parse_date(cell_text)

                    if parsed_date and not date_found:
                        date_found = parsed_date

                        # Look for holiday name in other cells
                        for j in range(len(cells)):
                            if j != i:
                                text = cells[j].get_text(strip=True)
                                if text and len(text) > 2 and len(text) < 100 and not self.scraper.parse_date(text):
                                    # Skip common headers
                                    if text.lower() not in ['date', 'дата', 'day', 'день', 'holiday', 'выходной']:
                                        holiday_name = text
                                        break

                        if holiday_name:
                            holiday = {
                                'iso_code': iso_code,
                                'holiday_date': date_found,
                                'holiday_name': holiday_name,
                                'holiday_description': None,
                                'products_trading': None,
                                'is_full_closure': True,
                                'early_close_time': None
                            }
                            holidays.append(holiday)
                            break

        print(f"[INFO] Moscow Exchange: Found {len(holidays)} holidays")
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
