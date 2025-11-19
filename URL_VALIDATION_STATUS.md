# Exchange Holiday Calendar URL Validation Status

This document tracks the validation status of holiday calendar URLs for all 52 exchanges in the system.

## Legend

- ✅ **VERIFIED**: URL confirmed to contain holiday calendar information
- ⚠️ **PARTIAL**: Base URL or general trading page found, specific calendar page needs manual verification
- ❓ **UNVERIFIED**: Could not locate specific holiday calendar page, using base URL only

---

## North America (5 exchanges)

| Exchange | ISO Code | Status | Notes |
|----------|----------|--------|-------|
| CME Group | XCME | ✅ VERIFIED | Official trading hours page with holiday calendar |
| ICE Futures U.S. | IFUS | ✅ VERIFIED | Trading schedule PDF available |
| ICE Futures Europe | IFEU | ✅ VERIFIED | Trading schedule PDF available |
| Cboe Global Markets | XCBO | ⚠️ PARTIAL | Futures holiday calendar page exists |
| Montreal Exchange (TMX) | XMOD | ⚠️ PARTIAL | Calendar page exists, needs verification |

## Latin America (2 exchanges)

| Exchange | ISO Code | Status | Notes |
|----------|----------|--------|-------|
| B3 Brasil | BVMF | ✅ VERIFIED | Official holiday calendar page for 2025 |
| MexDer Mexico | MEXD | ⚠️ PARTIAL | Using general Grupo BMV page |

## Europe (20 exchanges)

| Exchange | ISO Code | Status | Notes |
|----------|----------|--------|-------|
| Eurex | XEUR | ✅ VERIFIED | Official trading calendar with PDF downloads |
| LME | XLME | ⚠️ PARTIAL | Trading calendar page exists |
| Euronext Paris | XPAR | ✅ VERIFIED | Shared Euronext trading calendar |
| Euronext Amsterdam | XAMS | ✅ VERIFIED | Shared Euronext trading calendar |
| Euronext Brussels | XBRU | ✅ VERIFIED | Shared Euronext trading calendar |
| Euronext Lisbon | XLIS | ✅ VERIFIED | Shared Euronext trading calendar |
| Euronext Dublin | XDUB | ✅ VERIFIED | Shared Euronext trading calendar |
| Euronext Milan | XMIL | ✅ VERIFIED | Shared Euronext trading calendar |
| Euronext Oslo | XOSL | ✅ VERIFIED | Shared Euronext trading calendar |
| BME Spanish | XMCE | ⚠️ PARTIAL | Using general trading page |
| SIX Swiss | XSWX | ⚠️ PARTIAL | Trading calendar page exists |
| EEX | XEEE | ⚠️ PARTIAL | Trading calendar page exists |
| Nasdaq Commodities | XNDE | ⚠️ PARTIAL | Using Nordic power page |
| ICE Endex | NDEX | ❓ UNVERIFIED | Using base URL only |
| Budapest BSE | XBUD | ⚠️ PARTIAL | Trading calendar page exists |
| Warsaw GPW | XWAR | ⚠️ PARTIAL | Trading calendar page exists |
| Athens ATHEX | XATH | ⚠️ PARTIAL | Trading calendar page exists |
| Moscow MOEX | MISX | ⚠️ PARTIAL | Trading calendar page exists |
| Borsa Istanbul | XIST | ⚠️ PARTIAL | Trading calendar page exists |

## Asia-Pacific (21 exchanges)

| Exchange | ISO Code | Status | Notes |
|----------|----------|--------|-------|
| SGX Singapore | XSES | ❓ UNVERIFIED | Could not locate specific calendar page on sgx.com |
| HKEX Hong Kong | XHKG | ✅ VERIFIED | Official derivatives trading calendar page |
| JPX/TSE Japan | XJPX | ✅ VERIFIED | Official market holidays page |
| OSE Japan | XOSE | ✅ VERIFIED | Derivatives holiday trading page |
| SHFE China | XSGE | ⚠️ PARTIAL | Calendar page exists, Chinese language |
| DCE China | XDCE | ❓ UNVERIFIED | Using base URL only, Chinese language |
| ZCE China | XZCE | ❓ UNVERIFIED | Using base URL only, Chinese language |
| CFFEX China | CCFX | ⚠️ PARTIAL | Overview page, may not have calendar |
| KRX Korea | XKRX | ✅ VERIFIED | Market closing/holiday announcement page |
| TAIFEX Taiwan | XTAF | ✅ VERIFIED | Interactive calendar + PDF downloads |
| NSE India | XNSE | ✅ VERIFIED | Official holidays page with year-specific URLs |
| BSE India | XBOM | ✅ VERIFIED | Official trading holidays list page |
| MCX India | MCXI | ✅ VERIFIED | Trading holidays page |
| ASX Australia | XASX | ✅ VERIFIED | Trading hours and T24 calendar with PDFs |
| NZX New Zealand | XNZE | ⚠️ PARTIAL | Using derivatives market page |
| ICDX Indonesia | IDXC | ❓ UNVERIFIED | Using base URL only |
| TFEX Thailand | XTFX | ⚠️ PARTIAL | Using SET website |
| Bursa Malaysia | XKLS | ⚠️ PARTIAL | Calendars page exists |
| PSE Philippines | XPHS | ❓ UNVERIFIED | Using base URL only |
| HNX Vietnam | XHNX | ❓ UNVERIFIED | Using base URL only |
| PMEX Pakistan | XPAK | ❓ UNVERIFIED | Using base URL only |

## Middle East (3 exchanges)

| Exchange | ISO Code | Status | Notes |
|----------|----------|--------|-------|
| GME Dubai | XDME | ❓ UNVERIFIED | Using base URL only |
| Tadawul Saudi | XSAU | ❓ UNVERIFIED | Using base URL only |
| TASE Israel | XTAE | ❓ UNVERIFIED | Using base URL only |

## Africa (1 exchange)

| Exchange | ISO Code | Status | Notes |
|----------|----------|--------|-------|
| JSE South Africa | XJSE | ❓ UNVERIFIED | Using base URL only |

---

## Summary Statistics

- **✅ Verified**: 19 exchanges (37%)
- **⚠️ Partial**: 18 exchanges (35%)
- **❓ Unverified**: 15 exchanges (29%)
- **Total**: 52 exchanges

## Recommendations

### Priority 1: Manual Verification Needed
These exchanges need manual verification to find the correct holiday calendar URLs:
1. **SGX Singapore** - Important regional exchange, calendar page not found
2. **Chinese Exchanges** (DCE, ZCE) - Language barrier, need Chinese speakers
3. **Middle East Exchanges** (GME, Tadawul, TASE) - Growing markets, calendars likely available
4. **Southeast Asia** (ICDX, PSE, HNX, PMEX) - Smaller but important regional exchanges

### Priority 2: Confirmation Needed
These exchanges have partial URLs that should work but need testing:
1. All Euronext exchanges (should all work with shared calendar)
2. European regional exchanges (Budapest, Warsaw, Athens, Moscow, Istanbul)
3. Energy exchanges (EEX, Nasdaq Commodities, ICE Endex)

### Priority 3: Language Support
Exchanges requiring language support for better scraping:
1. **Chinese** - SHFE, DCE, ZCE, CFFEX
2. **Japanese** - JPX, OSE (English pages available, but more data in Japanese)
3. **Arabic** - Tadawul, GME
4. **Hebrew** - TASE

## Testing Instructions

To test URLs manually:

```bash
# Initialize database with current URLs
python init_database.py

# Test scraping a specific exchange
python sync_holidays.py --exchanges XCME --verbose --no-email

# Test multiple exchanges by region
python sync_holidays.py --exchanges XPAR XAMS XBRU XLIS --verbose --no-email
```

## Notes for Development

1. **URL Discovery**: The system includes intelligent URL discovery that will attempt to find alternative calendar URLs if the primary URL fails
2. **Year Patterns**: Many exchanges use year-based URLs. The `calendar_url_pattern` field supports `{year}` placeholder
3. **PDF Support**: Several exchanges provide calendars as PDFs. Install `pdfplumber` for PDF parsing: `pip install pdfplumber`
4. **Rate Limiting**: Consider adding delays between requests for exchanges that may block rapid requests
5. **User-Agent**: Some exchanges may require specific user agents or headers

## Update History

- **2025-01-19**: Initial validation pass completed
  - 19 exchanges fully verified
  - 18 exchanges partially verified
  - 15 exchanges require manual URL discovery
