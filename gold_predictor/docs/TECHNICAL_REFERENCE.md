# Technical Reference Guide

## 🔧 API Integration & Error Handling

### Tanshu Historical Data API

**API Endpoint:**
```
https://api.tanshuapi.com/api/precious_metals_history/v1/kline_data
```

**Example Usage:**
```
https://api.tanshuapi.com/api/precious_metals_history/v1/kline_data?key=83b60dc2419a755761c2c76541943a5a&product=Au9999&type=1&limit=30
```

#### Parameters

**Required Parameters:**
- **key**: API authentication key
- **product**: Product code (see available products below)
- **type**: Data interval type (1=daily, 2=weekly, 3=monthly)
- **limit**: Number of records to return

#### Available Product Codes

| Code | Name (Chinese) | Name (English) | Historical Data Since |
|------|---------------|----------------|----------------------|
| XAU | 国际黄金 | International Gold | 2005-12-30 |
| XAG | 国际白银 | International Silver | 2005-12-27 |
| XPT | 国际铂金 | International Platinum | 2009-06-10 |
| XPD | 国际钯金 | International Palladium | 2005-11-24 |
| HKD | 香港黄金 | Hong Kong Gold | 2005-10-14 |
| TWAU | 台湾黄金 | Taiwan Gold | 2009-06-30 |
| Au9995 | 黄金9995 | Gold 9995 | 2004-06-04 |
| Au9999 | 黄金9999 | Gold 9999 | 2004-09-17 |
| Au100g | 100克金条 | 100g Gold Bar | 2006-12-25 |

## 🚨 Error Codes Reference

### API Error Codes

| Error Code | Chinese Description | English Description | Solution |
|------------|-------------------|-------------------|----------|
| **10001** | 错误的请求KEY | Invalid API Key | Check your API key is correct |
| **10002** | 该KEY无请求权限 | Key has no request permission | Contact API provider for permissions |
| **10003** | KEY过期 | API Key expired | Renew your API subscription |
| **10004** | 未知的请求源 | Unknown request source | Check API endpoint URL |
| **10005** | 被禁止的IP | Banned IP address | Contact support, IP may be blocked |
| **10006** | 被禁止的KEY | Banned API Key | API key is blacklisted, get new key |
| **10007** | 请求超过次数限制 | Request limit exceeded | Wait for quota reset or upgrade plan |
| **10008** | 接口维护 | API under maintenance | Wait for maintenance to complete |

### Error Display Features

The GUI includes a dedicated **"Error Status & Diagnostics"** section in the API Info tab that shows:

1. **Error Status**: ✅ No errors or ❌ Error detected
2. **Error Code**: The specific numeric code from the API
3. **Description**: Bilingual description (Chinese + English explanation)

### Error Handling Behavior

#### ✅ **When Everything Works:**
- Status shows: ✅ All systems operational
- Error Code: None
- Description: All systems operational

#### ❌ **When Errors Occur:**
- Status shows: ❌ API Error Detected (in red)
- Error Code: Shows specific code (e.g., 10007)
- Description: Shows bilingual explanation

## 📊 Historical API Integration Details

### Code Cleanup Completed

**Removed Redundant Code:**
1. ❌ **Removed `products_api_url`** - Was never properly used
2. ❌ **Removed `fetch_product_list()` method** - Unnecessary API call
3. ❌ **Removed duplicate `available_products` definition** - Consolidated into one
4. ❌ **Fixed duplicate exception handlers** - Cleaned up error handling

### Optimized Structure

#### ✅ **Single Historical API Endpoint:**
- **URL**: `https://api.tanshuapi.com/api/precious_metals_history/v1/kline_data`
- **Purpose**: Fetch historical OHLC data for precious metals
- **Parameters**: `product`, `type` (1=daily, 2=weekly, 3=monthly), `limit`

#### ✅ **Comprehensive Product List (No API Needed):**
```python
available_products = {
    'XAU': 'International Gold (since 2005-12-30)',
    'XAG': 'International Silver (since 2005-12-27)', 
    'XPT': 'International Platinum (since 2009-06-10)',
    'XPD': 'International Palladium (since 2005-11-24)',
    'HKD': 'Hong Kong Gold (since 2005-10-14)',
    'Au9995': 'Gold 9995 (since 2004-06-04)',
    'Au9999': 'Gold 9999 (since 2004-09-17)',
    'Au100g': '100g Gold Bar (since 2006-12-25)',
    # ... and more
}
```

### Implementation Features

**Smart API Usage:**
- ✅ **Shared Cache System**: Prevents duplicate calls
- ✅ **30-minute Cache Duration**: Balances freshness vs quota
- ✅ **Usage Tracking**: Monitor API calls per month (600 limit)
- ✅ **Error Recovery**: Graceful handling of API failures

**Data Processing:**
- ✅ **OHLC Data Parsing**: Open, High, Low, Close prices
- ✅ **Multiple Timeframes**: Daily, Weekly, Monthly data
- ✅ **Historical Range**: 20+ years of data available
- ✅ **JSON Response Handling**: Robust parsing and validation

**GUI Integration:**
- ✅ **Real-time Updates**: Historical charts update automatically
- ✅ **Error Display**: User-friendly error messages
- ✅ **Progress Feedback**: Loading indicators and status updates
- ✅ **Quota Management**: API usage awareness

## 🔌 Current Data Sources

### Primary Sources
1. **CNBC Web Scraping** - Live gold prices and market factors
2. **Tanshu API** - Historical data and fallback for live prices
3. **Financial Scraper** - DXY, US10Y, TIPS, VIX, GLD, USD/CNY rates

### Data Flow Architecture
```
CNBC Scraping → Live Prices → GUI Display
     ↓
Tanshu API → Historical Data → Chart Generation
     ↓  
Financial Scraper → Market Factors → Prediction Engine
```
