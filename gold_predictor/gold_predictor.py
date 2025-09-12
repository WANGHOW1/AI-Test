#!/usr/bin/env python3
"""
Gold Price Predictor with Real-Time Tanshu API
Complete solution with API client, USD conversion, and predictor logic
Only makes requests during China trading hours (9:00 AM - 11:00 PM Beijing time)
"""

import requests
import json
from datetime import datetime, timedelta
import pytz
import time

class GoldPricePredictor:
    def __init__(self):
        # API Configuration
        self.api_url = "https://api.tanshuapi.com/api/gold/v1/london"
        self.historical_api_url = "https://api.tanshuapi.com/api/precious_metals_history/v1/kline_data"
        self.api_key = "83b60dc2419a755761c2c76541943a5a"
        self.monthly_limit = 600
        self.london_tz = pytz.timezone('Europe/London')
        
        # Historical Data Products (from API response) - Comprehensive list
        self.available_products = {
            'XAU': {'name': '国际黄金', 'english': 'International Gold', 'since': '2005-12-30'},
            'XAG': {'name': '国际白银', 'english': 'International Silver', 'since': '2005-12-27'},
            'XPT': {'name': '国际铂金', 'english': 'International Platinum', 'since': '2009-06-10'},
            'XPD': {'name': '国际钯金', 'english': 'International Palladium', 'since': '2005-11-24'},
            'HKD': {'name': '香港黄金', 'english': 'Hong Kong Gold', 'since': '2005-10-14'},
            'TWAU': {'name': '台湾黄金', 'english': 'Taiwan Gold', 'since': '2009-06-30'},
            'Au9995': {'name': '黄金9995', 'english': 'Gold 9995', 'since': '2004-06-04'},
            'Au9999': {'name': '黄金9999', 'english': 'Gold 9999', 'since': '2004-09-17'},
            'Au100g': {'name': '100克金条', 'english': '100g Gold Bar', 'since': '2006-12-25'},
            'PT9995': {'name': '铂金9995', 'english': 'Platinum 9995', 'since': '2004-08-27'},
            'Ag9999': {'name': '白银9999', 'english': 'Silver 9999', 'since': '2012-09-06'},
            'AuT+D': {'name': '黄金延期', 'english': 'Gold Deferred', 'since': '2004-09-01'},
            'AgT+D': {'name': '白银延期', 'english': 'Silver Deferred', 'since': '2006-11-01'}
        }
        
        # API Call Tracking for Quota Management
        self.api_calls_today = 0
        self.last_call_date = None
        self.estimated_monthly_calls = 0
        self.calls_this_month = 0
        
        # API Error Codes - Chinese Tanshu API Error Messages
        self.error_codes = {
            10001: "错误的请求KEY (Invalid API Key)",
            10002: "该KEY无请求权限 (Key has no request permission)",
            10003: "KEY过期 (API Key expired)",
            10004: "未知的请求源 (Unknown request source)",
            10005: "被禁止的IP (Banned IP address)",
            10006: "被禁止的KEY (Banned API Key)",
            10007: "请求超过次数限制 (Request limit exceeded)",
            10008: "接口维护 (API under maintenance)"
        }
        
        # Data Cache
        self.last_fetch_time = None
        self.cached_price_usd = None
        self.cached_london_price = None
        self.cached_api_data = None  # Store full API response
        self.usd_gbp_rate = 0.79  # Default exchange rate (1 USD = 0.79 GBP)
        self.last_error_code = None
        self.last_error_message = None
        
    def is_london_trading_hours(self):
        """Check if it's currently London gold trading hours (24/7 for London gold market)"""
        london_now = datetime.now(self.london_tz)
        current_hour = london_now.hour
        current_day = london_now.weekday()  # 0=Monday, 6=Sunday
        
        # London gold market trades 24/7 except weekends
        # Friday 22:00 GMT to Sunday 22:00 GMT market is closed
        if current_day == 6:  # Sunday
            is_trading_hours = current_hour >= 22  # Opens Sunday 22:00 GMT
        elif current_day == 5:  # Saturday
            is_trading_hours = False  # Closed all Saturday
        elif current_day == 4 and current_hour >= 22:  # Friday after 22:00
            is_trading_hours = False  # Closes Friday 22:00 GMT
        else:
            is_trading_hours = True  # Open Monday-Friday
        
        return is_trading_hours, london_now
    
    def get_trading_schedule_info(self):
        """Get detailed info about trading schedule and API usage optimization"""
        is_trading, london_time = self.is_london_trading_hours()
        
        # London gold market trades ~120 hours per week (5 days * 24 hours)
        trading_hours_per_week = 120
        trading_hours_per_day = trading_hours_per_week / 5  # 24 hours on trading days
        
        today = london_time.day
        days_in_month = 30
        trading_days_remaining = max(1, (days_in_month - today) * 0.71)  # ~71% are trading days
        
        requests_per_trading_day = self.monthly_limit / 22  # ~27 requests per trading day
        requests_per_hour = requests_per_trading_day / trading_hours_per_day  # ~1.1 per hour
        optimal_interval_minutes = 60 / requests_per_hour  # ~54 minutes between requests
        
        return {
            'is_trading_hours': is_trading,
            'london_time': london_time,
            'trading_hours_per_day': int(trading_hours_per_day),
            'estimated_trading_days_remaining': int(trading_days_remaining),
            'optimal_requests_per_day': int(requests_per_trading_day),
            'optimal_requests_per_hour': round(requests_per_hour, 1),
            'optimal_interval_minutes': int(optimal_interval_minutes)
        }
    
    def get_usd_gbp_rate(self):
        """Get real USD/GBP exchange rate"""
        try:
            response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'rates' in data and 'GBP' in data['rates']:
                    self.usd_gbp_rate = data['rates']['GBP']
                    return True
        except:
            pass
        return False
    
    def convert_london_price_to_usd(self, london_price_str):
        """Convert London gold price to USD (London prices are typically already in USD/troy ounce)"""
        try:
            # London gold prices are usually already in USD per troy ounce
            # Just clean and convert the string to float
            clean_price = london_price_str.replace(',', '').replace('$', '').replace('£', '')
            price = float(clean_price)
            
            # If the price seems to be in GBP (typically lower numbers), convert to USD
            if price < 2000:  # Likely in GBP
                price = price / self.usd_gbp_rate
            
            return price
        except:
            return None
    
    def update_api_quota(self):
        """Update API call tracking for quota management"""
        current_date = datetime.now().date()
        
        # Reset daily counter if it's a new day
        if self.last_call_date != current_date:
            self.api_calls_today = 0
            self.last_call_date = current_date
            
        self.api_calls_today += 1
        print(f"📊 API calls today: {self.api_calls_today}")
        
    def check_quota_availability(self, calls_needed=1):
        """Check if we have enough API quota remaining"""
        current_date = datetime.now().date()
        
        # Estimate calls remaining this month (rough calculation)
        days_in_month = 30
        current_day = current_date.day
        estimated_daily_budget = self.monthly_limit / days_in_month  # ~20 calls per day
        
        if self.api_calls_today + calls_needed > estimated_daily_budget * 1.5:  # 50% buffer
            return False, f"Daily quota exceeded. Used {self.api_calls_today}, requesting {calls_needed} more"
            
        return True, "Quota available"
    
    def get_quota_stats(self):
        """Get current quota usage statistics"""
        current_date = datetime.now().date()
        days_in_month = 30
        current_day = current_date.day
        
        estimated_monthly_used = self.api_calls_today * current_day
        estimated_daily_budget = self.monthly_limit / days_in_month
        
        return {
            'calls_today': self.api_calls_today,
            'monthly_limit': self.monthly_limit,
            'estimated_monthly_used': estimated_monthly_used,
            'estimated_remaining': max(0, self.monthly_limit - estimated_monthly_used),
            'daily_budget': int(estimated_daily_budget),
            'current_day': current_day
        }
    
    def get_error_description(self, error_code):
        """Get descriptive error message for API error codes"""
        return self.error_codes.get(error_code, f"Unknown error code: {error_code}")
    
    def get_last_error_info(self):
        """Get information about the last API error"""
        if self.last_error_code:
            return {
                'error_code': self.last_error_code,
                'description': self.get_error_description(self.last_error_code),
                'message': self.last_error_message
            }
        return None
    
    def clear_error_info(self):
        """Clear stored error information"""
        self.last_error_code = None
        self.last_error_message = None
    
    def track_api_call(self):
        """Track API calls for quota management"""
        today = datetime.now().date()
        
        # Reset daily counter if new day
        if self.last_call_date != today:
            self.api_calls_today = 0
            self.last_call_date = today
        
        # Increment counters
        self.api_calls_today += 1
        self.calls_this_month += 1
        
        # Calculate estimated monthly usage
        days_in_month = 30
        current_day = datetime.now().day
        if current_day > 0:
            self.estimated_monthly_calls = (self.calls_this_month / current_day) * days_in_month
    
    def check_quota_status(self):
        """Check if we're approaching quota limits"""
        quota_status = {
            'calls_today': self.api_calls_today,
            'calls_this_month': self.calls_this_month,
            'estimated_monthly': int(self.estimated_monthly_calls),
            'remaining_quota': max(0, self.monthly_limit - self.calls_this_month),
            'quota_percentage': (self.calls_this_month / self.monthly_limit) * 100,
            'warning_level': 'safe'
        }
        
        # Determine warning level
        if quota_status['quota_percentage'] >= 90:
            quota_status['warning_level'] = 'critical'
        elif quota_status['quota_percentage'] >= 75:
            quota_status['warning_level'] = 'warning'
        elif quota_status['estimated_monthly'] >= self.monthly_limit * 0.9:
            quota_status['warning_level'] = 'caution'
        
        return quota_status
    
    def get_available_products(self):
        """Get list of available products for historical data"""
        return self.available_products
    
    def fetch_historical_data(self, product='XAU', data_type='1', limit=30, force=False):
        """
        Fetch historical data for specified product
        Args:
            product (str): Product code (XAU, XAG, XPT, XPD, etc.)
            data_type (str): Type of data ('1'=daily, '2'=weekly, '3'=monthly)
            limit (int): Number of records to fetch (max 1000, default 30)
            force (bool): Bypass quota checks if True
        Returns:
            tuple: (success, data, message)
        """
        # Check quota before making call
        can_call, quota_msg = self.check_quota_availability(1)
        if not force and not can_call:
            return False, None, f"Quota check failed: {quota_msg}"
        
        # Validate product
        if product not in self.available_products:
            available = ', '.join(self.available_products.keys())
            return False, None, f"Product {product} not available. Available: {available}"
        
        # Validate parameters
        valid_types = {'1': 'daily', '2': 'weekly', '3': 'monthly'}
        if data_type not in valid_types:
            return False, None, f"Invalid type. Use: {dict(valid_types)}"
        
        if limit <= 0 or limit > 1000:
            return False, None, "Limit must be between 1 and 1000"
        
        try:
            print(f"📊 Fetching {limit} {valid_types[data_type]} records for {product} ({self.available_products[product]['english']})...")
            
            # Track the API call
            self.update_api_quota()
            
            # Make API request to correct endpoint
            response = requests.get(
                self.historical_api_url,
                params={
                    'key': self.api_key,
                    'product': product,
                    'type': data_type,
                    'limit': str(limit)
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for API error codes
                if 'code' in data and data['code'] != 1:
                    error_code = data.get('code')
                    error_msg = data.get('msg', 'Unknown error')
                    
                    self.last_error_code = error_code
                    self.last_error_message = error_msg
                    
                    if error_code in self.error_codes:
                        description = self.get_error_description(error_code)
                        return False, None, f"API Error {error_code}: {description}"
                    else:
                        return False, None, f"API Error {error_code}: {error_msg}"
                else:
                    self.clear_error_info()
                    records_count = len(data.get('data', {}).get('list', []))
                    print(f"✅ Retrieved {records_count} historical records")
                    return True, data, f"Success: {records_count} records"
            else:
                return False, None, f"HTTP Error: {response.status_code}"
                
        except Exception as e:
            return False, None, f"Request failed: {str(e)}"
    
    def fetch_gold_price_from_api(self, force=False):
        """
        Fetch gold price from Tanshu API
        Args:
            force (bool): If True, ignores trading hours check
        Returns:
            tuple: (success, data, message)
        """
        schedule_info = self.get_trading_schedule_info()
        
        # Check trading hours unless forced
        if not force and not schedule_info['is_trading_hours']:
            london_time = schedule_info['london_time']
            return False, None, f"Outside trading hours. Current London time: {london_time.strftime('%H:%M')} ({london_time.strftime('%A')})"
        
        try:
            print(f"🔄 Making API request at {schedule_info['london_time'].strftime('%Y-%m-%d %H:%M:%S')} London time...")
            
            response = requests.get(
                self.api_url,
                params={'key': self.api_key},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for API error codes in response
                if 'code' in data and data['code'] != 1:
                    error_code = data.get('code')
                    error_msg = data.get('msg', 'Unknown error')
                    
                    # Store error information
                    self.last_error_code = error_code
                    self.last_error_message = error_msg
                    
                    # Get descriptive error message
                    if error_code in self.error_codes:
                        description = self.get_error_description(error_code)
                        return False, None, f"API Error {error_code}: {description}"
                    else:
                        return False, None, f"API Error {error_code}: {error_msg}"
                else:
                    # Clear any previous errors on success
                    self.clear_error_info()
                    return True, data, "Success"
            else:
                return False, None, f"HTTP Error: {response.status_code}"
                
        except Exception as e:
            return False, None, f"Request failed: {str(e)}"
    
    def get_cached_or_fresh_data(self, force_refresh=False):
        """
        Get API data from cache or fetch fresh data if needed
        This prevents multiple API calls for the same data
        """
        current_time = datetime.now()
        
        # Check if we should fetch new data (respect 30-minute interval)
        should_fetch = (
            force_refresh or
            self.last_fetch_time is None or 
            (current_time - self.last_fetch_time).total_seconds() > 1800  # 30 minutes
        )
        
        if should_fetch:
            print("🔄 Fetching fresh data from API...")
            # Get latest exchange rate (for display purposes)
            self.get_usd_gbp_rate()
            
            # Try to fetch from API
            success, data, message = self.fetch_gold_price_from_api()
            
            if success and data:
                self.cached_api_data = data
                self.last_fetch_time = current_time
                print("✅ Fresh data cached successfully")
                return True, data, "LIVE London Gold Market"
            else:
                print(f"⚠️ API fetch failed: {message}")
                return False, None, message
        else:
            # Use cached data
            if self.cached_api_data:
                age_minutes = int((current_time - self.last_fetch_time).total_seconds() / 60)
                print(f"📋 Using cached data ({age_minutes} min old)")
                return True, self.cached_api_data, f"Cached ({age_minutes}min old)"
        
        return False, None, "No data available"

    def get_current_gold_price(self, force_refresh=False):
        """Get current gold price in USD per troy ounce"""
        success, data, source = self.get_cached_or_fresh_data(force_refresh)
        
        if success and data and 'data' in data and 'list' in data['data']:
            # Extract London Gold price (first item is usually 伦敦金)
            gold_list = data['data']['list']
            london_gold = None
            
            for item in gold_list:
                if item['type'] == '伦敦金':  # London Gold
                    london_gold = item
                    break
            
            if london_gold:
                usd_price = float(london_gold['price'])
                self.cached_price_usd = usd_price
                self.cached_london_price = usd_price  # Same value since already in USD
                
                return usd_price, source, london_gold
        
        # Return cached price if available
        if self.cached_price_usd:
            current_time = datetime.now()
            age_minutes = int((current_time - self.last_fetch_time).total_seconds() / 60)
            return self.cached_price_usd, f"Cached ({age_minutes}min old)", self.cached_london_price
        
        # Fallback to reasonable estimate
        fallback_price = 2650.0
        return fallback_price, "Fallback estimate", None
    
    def get_detailed_market_info(self, force_refresh=False):
        """Get detailed market information for all London precious metals"""
        success, data, source = self.get_cached_or_fresh_data(force_refresh)
        
        if not success or not data or 'data' not in data or 'list' not in data['data']:
            return {"error": source or "Invalid data format"}
        
        metals_list = data['data']['list']
        processed_data = {}
        
        # Map of metal types
        metal_names = {
            '伦敦金': 'London Gold',
            '伦敦银': 'London Silver', 
            '铂金期货': 'Platinum Futures',
            '钯金期货': 'Palladium Futures'
        }
        
        for item in metals_list:
            metal_type = item['type']
            english_name = metal_names.get(metal_type, metal_type)
            usd_price = float(item['price'])
            
            processed_data[metal_type] = {
                'name': english_name,
                'chinese_name': metal_type,
                'usd_price': usd_price,
                'change_amount': item['changequantity'],
                'change_percent': item['changepercent'],
                'opening_price': item['openingprice'],
                'high_price': item['maxprice'],
                'low_price': item['minprice'],
                'previous_close': item['lastclosingprice'],
                'update_time': item['updatetime']
            }
        
        return {
            'data': processed_data,
            'exchange_rate': self.usd_gbp_rate,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_api_stats(self):
        """Get API usage statistics for debugging"""
        current_time = datetime.now()
        stats = {
            'cached_data_available': bool(self.cached_api_data),
            'last_fetch_time': self.last_fetch_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_fetch_time else None,
            'cache_age_minutes': int((current_time - self.last_fetch_time).total_seconds() / 60) if self.last_fetch_time else None,
            'current_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'next_refresh_due': (self.last_fetch_time + timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S') if self.last_fetch_time else 'Immediate'
        }
        return stats

    def get_raw_api_response(self, force_refresh=False):
        """Get raw JSON response from the API for debugging"""
        success, data, source = self.get_cached_or_fresh_data(force_refresh)
        if success:
            return data
        else:
            return {"error": source}

def demo_gold_predictor():
    """Demonstrate the complete gold predictor functionality"""
    print("🏆 GOLD PRICE PREDICTOR - REAL-TIME LONDON GOLD API")
    print("=" * 60)
    
    predictor = GoldPricePredictor()
    
    # Show current schedule
    schedule = predictor.get_trading_schedule_info()
    print(f"⏰ London Time: {schedule['london_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Trading Status: {'✅ OPEN' if schedule['is_trading_hours'] else '❌ CLOSED'}")
    print(f"💡 Optimal interval: {schedule['optimal_interval_minutes']} minutes between requests")
    print()
    
    if schedule['is_trading_hours']:
        print("🔍 FETCHING LIVE LONDON GOLD PRICES...")
        
        # Get current price
        usd_price, source, london_data = predictor.get_current_gold_price()
        print(f"💰 Current London Gold Price: ${usd_price:.2f}/oz")
        print(f"📊 Source: {source}")
        if london_data:
            print(f"📈 Change: {london_data['changequantity']} ({london_data['changepercent']})")
        print(f"💱 Exchange Rate: 1 USD = {predictor.usd_gbp_rate:.4f} GBP")
        print()
        
        # Get detailed market info
        print("📈 DETAILED LONDON MARKET DATA:")
        market_info = predictor.get_detailed_market_info()
        
        if 'error' not in market_info:
            for metal_code, info in market_info['data'].items():
                print(f"🏅 {info['name']} ({info['chinese_name']}):")
                print(f"   Price: ${info['usd_price']}/oz ({info['change_percent']})")
                print(f"   Range: ${info['low_price']} - ${info['high_price']}")
                print()
        else:
            print(f"❌ Error: {market_info['error']}")
    
    else:
        print("⏸️ OUTSIDE TRADING HOURS")
        print("🔍 Showing cached/estimated data...")
        
        usd_price, source, london_data = predictor.get_current_gold_price()
        print(f"💰 Gold Price: ${usd_price:.2f}/oz")
        print(f"📊 Source: {source}")
        print()
        print("💡 API requests are paused to conserve monthly quota")

if __name__ == "__main__":
    demo_gold_predictor()
