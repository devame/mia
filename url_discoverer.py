"""
Intelligent URL discovery for exchange holiday calendars

This module crawls exchange websites to find the correct holiday calendar URLs
by analyzing page content, headings, and link patterns.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Tuple, Optional, Set
import time
import re


class CalendarURLDiscoverer:
    """Discovers holiday calendar URLs by intelligent crawling and scoring"""

    def __init__(self, timeout=10, max_depth=2):
        """
        Initialize discoverer

        Args:
            timeout: Request timeout in seconds
            max_depth: Maximum crawl depth from base URL
        """
        self.timeout = timeout
        self.max_depth = max_depth
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # Keywords that indicate holiday calendar pages
        self.url_keywords = [
            'holiday', 'calendar', 'trading-calendar', 'schedule',
            'trading-hours', 'market-holiday', 'closure', 'trading-schedule'
        ]

        self.heading_keywords = [
            'holiday calendar', 'trading calendar', 'market holiday',
            'market closure', 'trading schedule', 'holiday schedule',
            'public holiday', 'bank holiday'
        ]

    def discover(self, base_url: str, exchange_name: str = "") -> Optional[str]:
        """
        Discover holiday calendar URL for an exchange

        Args:
            base_url: Base URL of exchange website
            exchange_name: Name of exchange (for logging)

        Returns:
            URL of holiday calendar page, or None if not found
        """
        print(f"\n{'='*80}")
        print(f"Discovering calendar URL for: {exchange_name}")
        print(f"Base URL: {base_url}")
        print('='*80)

        visited: Set[str] = set()
        candidates: List[Tuple[int, str, str]] = []

        # Step 1: Get all links from homepage
        links = self._extract_links(base_url)
        print(f"Found {len(links)} links on homepage")

        # Step 2: Score links by URL keywords
        for link in links:
            url_score = self._score_url(link)
            if url_score > 0:
                candidates.append((url_score, link, 'url'))

        # Step 3: Also try common paths directly
        common_paths = self._generate_common_paths(base_url)
        for path in common_paths:
            candidates.append((15, path, 'common'))

        print(f"Found {len(candidates)} candidate URLs to check")

        # Step 4: Visit top candidates and score content
        candidates.sort(reverse=True, key=lambda x: x[0])
        best_url = None
        best_score = 0

        for initial_score, url, source in candidates[:20]:  # Check top 20
            if url in visited:
                continue

            visited.add(url)
            content_score = self._score_page_content(url)
            total_score = initial_score + content_score

            print(f"  [{total_score:3d}] {url[:80]} (url:{initial_score}, content:{content_score})")

            if total_score > best_score:
                best_score = total_score
                best_url = url

            # If we found a very high confidence match, return early
            if total_score > 80:
                print(f"\n✓ High confidence match found (score: {total_score})")
                return best_url

            time.sleep(0.5)  # Be polite

        if best_score > 30:
            print(f"\n✓ Best match found (score: {best_score})")
            return best_url
        else:
            print(f"\n✗ No good match found (best score: {best_score})")
            return None

    def _extract_links(self, url: str) -> List[str]:
        """Extract all links from a page"""
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.content, 'html.parser')
            links = []

            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                full_url = urljoin(url, href)

                # Only include same-domain links
                if urlparse(full_url).netloc == urlparse(url).netloc:
                    links.append(full_url)

            return list(set(links))  # Deduplicate

        except Exception as e:
            print(f"Error extracting links from {url}: {e}")
            return []

    def _score_url(self, url: str) -> int:
        """Score a URL based on keywords and patterns"""
        score = 0
        url_lower = url.lower()

        # Check for keywords in URL
        for keyword in self.url_keywords:
            if keyword in url_lower:
                score += 10

        # Bonus for PDFs
        if url.endswith('.pdf'):
            score += 15

        # Bonus for English sections
        if any(x in url for x in ['/en/', '/english/', '/en_us/', '/en-gb/']):
            score += 5

        # Bonus for common patterns
        if any(x in url_lower for x in ['/trading/', '/market/', '/about/']):
            score += 3

        return score

    def _generate_common_paths(self, base_url: str) -> List[str]:
        """Generate common calendar URL patterns to try"""
        paths = []
        base = base_url.rstrip('/')

        # Common direct paths
        common = [
            '/holiday-calendar',
            '/trading-calendar',
            '/market-holidays',
            '/trading-hours',
            '/en/holiday-calendar',
            '/en/trading-calendar',
            '/english/calendar',
            '/trading/calendar',
            '/trading/holiday',
        ]

        for path in common:
            paths.append(base + path)

        return paths

    def _score_page_content(self, url: str) -> int:
        """Score page content for holiday calendar relevance"""
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)

            if response.status_code != 200:
                return 0

            # If PDF, score based on filename
            if url.endswith('.pdf') or 'application/pdf' in response.headers.get('Content-Type', ''):
                filename = url.split('/')[-1].lower()
                if any(kw in filename for kw in ['holiday', 'calendar', 'schedule']):
                    return 50
                return 10

            soup = BeautifulSoup(response.content, 'html.parser')
            score = 0

            # Check h1/h2/h3 tags (MOST IMPORTANT)
            for heading in soup.find_all(['h1', 'h2', 'h3']):
                text = heading.get_text().lower().strip()

                for keyword_phrase in self.heading_keywords:
                    if keyword_phrase in text:
                        score += 30
                        break

                # Partial matches
                if 'holiday' in text or 'calendar' in text:
                    score += 10

            # Check title tag
            if soup.title:
                title = soup.title.string.lower() if soup.title.string else ""
                if any(kw in title for kw in ['holiday calendar', 'trading calendar']):
                    score += 20
                elif 'holiday' in title or 'calendar' in title:
                    score += 10

            # Check for tables (calendars usually have tables)
            tables = soup.find_all('table')
            if tables:
                score += 15

                # Check if tables contain dates/years
                for table in tables[:3]:  # Check first 3 tables
                    table_text = table.get_text()

                    # Look for years
                    if any(year in table_text for year in ['2024', '2025', '2026']):
                        score += 15
                        break

            # Check page text for year markers
            page_text = soup.get_text()[:3000]  # First 3000 chars
            year_count = sum(1 for year in ['2024', '2025', '2026'] if year in page_text)
            if year_count >= 2:
                score += 10

            # Look for date patterns in text
            date_pattern = r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}'
            if re.search(date_pattern, page_text):
                score += 10

            return score

        except Exception as e:
            return 0


if __name__ == '__main__':
    # Test with LME
    discoverer = CalendarURLDiscoverer()

    test_cases = [
        ("https://www.lme.com", "London Metal Exchange"),
        ("https://www.euronext.com", "Euronext"),
    ]

    for base_url, name in test_cases:
        url = discoverer.discover(base_url, name)
        if url:
            print(f"\n✓✓✓ Found URL: {url}\n")
        else:
            print(f"\n✗✗✗ No URL found\n")
