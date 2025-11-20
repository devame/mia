# Manual URL Updates for Exchange Holiday Calendars

## Verified Correct URLs

### Europe

**Euronext (ALL 7 exchanges)**
ISO Codes: XPAR, XAMS, XBRU, XLIS, XDUB, XMIL, XOSL
- **New URL**: `https://www.euronext.com/en/trading/trading-hours-holidays`
- **Status**: ✅ VERIFIED - Discoverer found (score: 218)
- **Content**: h1 "Euronext Trading Hours & Holidays", tables for 2024-2026, all 7 exchanges
- **Old URL**: `https://www.euronext.com/en/trade/trading-calendar` (404)

**London Metal Exchange (LME)**
ISO Code: XLME
- **New URL**: `https://www.lme.com/-/media/Files/Trading/Trading-Calendar-2025-2035-digital-version.pdf`
- **Status**: ✅ VERIFIED - User provided, tested working (9MB PDF)
- **Content**: PDF with trading calendar 2025-2035
- **Old URL**: `https://www.lme.com/en/Trading/Trading-information/Trading-calendar` (403)

### Asia-Pacific

**Australian Securities Exchange (ASX)**
ISO Code: XASX
- **New URL**: `https://www.asx.com.au/markets/market-resources/trading-hours-calendar`
- **Status**: ✅ VERIFIED - Discoverer found (score: 50)
- **Old URL**: Same (already correct in CSV)

**Singapore Exchange (SGX)**
ISO Code: XSES
- **URL**: `http://www.mom.gov.sg/employment-practices/public-holidays`
- **Status**: ✅ VERIFIED - Extractor built and tested (11 holidays)
- **Note**: Already updated in CSV

**Japan Exchange Group (JPX)**
ISO Code: XJPX
- **URL**: `https://www.jpx.co.jp/english/corporate/about-jpx/calendar/index.html`
- **Status**: ✅ VERIFIED - Extractor built and tested (41 holidays)
- **Note**: Already correct in CSV

**Osaka Exchange (OSE)**
ISO Code: XOSE
- **URL**: `https://www.jpx.co.jp/english/derivatives/rules/holidaytrading/index.html`
- **Status**: ✅ VERIFIED - Uses JPX extractor
- **Note**: Already correct in CSV

## URLs Needing Manual Research

### North America

**CME Group**
ISO Code: XCME
- **Current URL**: `https://www.cmegroup.com/trading-hours.html` (403 Forbidden)
- **Status**: ❌ NEEDS RESEARCH
- **Notes**: JavaScript-heavy site, discoverer can't scrape homepage

**Cboe Global Markets**
ISO Code: XCBO
- **Current URL**: `https://www.cboe.com/us/futures/market_statistics/holiday_calendar/`
- **Status**: ❓ NEEDS VERIFICATION

**Montreal Exchange (TMX)**
ISO Code: XMOD
- **Current URL**: `https://www.m-x.ca/en/trading/calendar`
- **Status**: ❓ NEEDS VERIFICATION

**ICE Futures U.S.**
ISO Code: IFUS
- **Current URL**: `https://www.ice.com/publicdocs/Trading_Schedule.pdf`
- **Status**: ✅ VERIFIED - PDF extractor built
- **Note**: Same PDF as IFEU

### Latin America

**B3 (Brasil Bolsa Balcao)**
ISO Code: BVMF
- **Current URL**: `https://www.b3.com.br/en_us/solutions/platforms/puma-trading-system/for-members-and-traders/trading-calendar/holidays/`
- **Status**: ❌ SSL CONNECTION ERROR
- **Notes**: Need to find alternative URL or fix SSL issue

**MexDer (Mexican Derivatives Exchange)**
ISO Code: MEXD
- **Current URL**: `https://www.bmv.com.mx/en/Grupo_BMV`
- **Status**: ❓ NEEDS VERIFICATION - Likely wrong (too generic)

### Asia-Pacific - India

**NSE India**
ISO Code: XNSE
- **Current URL**: `https://www.nseindia.com/holidays-for-the-calendar-year-2025`
- **Status**: ❓ NEEDS VERIFICATION - JavaScript site, discoverer failed

**BSE India**
ISO Code: XBOM
- **Current URL**: `https://www.bseindia.com/static/markets/marketinfo/listholi.aspx`
- **Status**: ❓ NEEDS VERIFICATION

**MCX India**
ISO Code: MCXI
- **Current URL**: `https://www.mcxindia.com/market-operations/trading-survelliance/trading-holidays`
- **Status**: ❓ NEEDS VERIFICATION

### Africa

**Johannesburg Stock Exchange (JSE)**
ISO Code: XJSE
- **Current URL**: `https://clientportal.jse.co.za/reports/trading-calendars`
- **Status**: ❌ NEEDS RESEARCH - Discoverer found no links

## Research Strategy

For each exchange needing research:

1. **Google site search**: `site:exchange.com holiday calendar 2025`
2. **Check investor relations** or **trading** sections
3. **Look for PDFs** in `/media/`, `/publicdocs/`, `/static/` paths
4. **Check sitemap.xml** if available
5. **Search for "trading hours" pages** (often include holidays)
6. **Check year-based patterns** like `/calendar-2025` or `/2025/holidays`

## Next Steps

1. Manually research and verify URLs for high-priority exchanges (CME, B3, NSE, JSE)
2. Update exchanges_data.csv with all verified URLs
3. Run discoverer on remaining exchanges
4. Build extractors once all URLs are verified
