#!/usr/bin/env python3
"""
Enhanced Financial Data Scraper for Gold Price Prediction
Scrapes multiple financial instruments from CNBC for comprehensive market analysis
"""

import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime
import json

class CNBCFinancialScraper:
    def __init__(self):
        self.base_url = "https://www.cnbc.com/quotes/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Define instruments and their gold price impact
        self.instruments = {
            '.DXY': {
                'name': 'US Dollar Index',
                'symbol': 'DXY',
                'gold_impact': 'inverse',  # Higher DXY = Lower Gold
                'weight': 0.25,
                'description': 'Strong USD pressures gold prices'
            },
            'US10Y': {
                'name': '10-Year Treasury Yield',
                'symbol': 'US10Y',
                'gold_impact': 'inverse',  # Higher yields = Lower Gold
                'weight': 0.20,
                'description': 'Higher yields increase opportunity cost of gold'
            },
            'US10YTIP': {
                'name': '10-Year TIPS Yield',
                'symbol': 'TIPS',
                'gold_impact': 'inverse',  # Higher real rates = Lower Gold
                'weight': 0.22,
                'description': 'Higher real rates very bearish for gold'
            },
            'VIX': {
                'name': 'Volatility Index',
                'symbol': 'VIX',
                'gold_impact': 'positive',  # Higher fear = Higher Gold
                'weight': 0.18,
                'description': 'Market fear drives safe-haven demand'
            },
            'GLD': {
                'name': 'Gold ETF',
                'symbol': 'GLD',
                'gold_impact': 'positive',  # Higher GLD = Higher Gold demand
                'weight': 0.15,
                'description': 'ETF demand directly affects gold prices'
            }
        }
        
    def _extract_price_data(self, soup, symbol):
        """Extract price data from CNBC page using proven selectors"""
        data = {
            'current_price': None,
            'change': None,
            'change_percent': None,
            'day_high': None,
            'day_low': None,
            'prev_close': None
        }
        
        try:
            # Extract price using working selector from test
            price_element = soup.select_one('.QuoteStrip-lastPrice')
            if price_element:
                price_text = price_element.get_text(strip=True)
                # Handle percentage symbols for yields
                if '%' in price_text:
                    price_match = re.search(r'([\d,]+\.?\d*)%', price_text)
                    if price_match:
                        data['current_price'] = float(price_match.group(1))
                else:
                    # Extract regular numbers
                    price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                    if price_match:
                        data['current_price'] = float(price_match.group())
            
            # Extract change data using improved method
            quote_strip = soup.find('div', {'class': re.compile(r'QuoteStrip')})
            if quote_strip:
                change_spans = quote_strip.find_all('span')
                
                # Strategy 1: Look for combined change format "+0.123 (+0.45%)"
                for span in change_spans:
                    text = span.get_text(strip=True)
                    full_change_match = re.search(r'([+-]?\d+\.?\d*)\s*\(([+-]?\d+\.?\d*%)\)', text)
                    if full_change_match:
                        try:
                            change_val = float(full_change_match.group(1))
                            change_pct = full_change_match.group(2)
                            data['change'] = change_val
                            data['change_percent'] = change_pct
                            break
                        except:
                            continue
                
                # Strategy 2: Look for separate elements (change value and percentage)
                if data['change'] is None:
                    change_val = None
                    change_pct = None
                    
                    for span in change_spans:
                        text = span.get_text(strip=True)
                        
                        # Look for percentage format like "+1.23%" or "-0.45%"
                        if not change_pct:
                            pct_match = re.search(r'^([+-]?\d+\.?\d*%)$', text)
                            if pct_match and len(text) < 12:  # Keep it short to avoid false matches
                                potential_pct = pct_match.group(1)
                                # For yields, avoid using the absolute yield value as change percentage
                                pct_value = float(potential_pct.replace('%', '').replace('+', ''))
                                # Reasonable daily change should be small for yields
                                if symbol in ['US10Y', 'TIPS'] and abs(pct_value) > 1.0:
                                    continue  # Skip if too large (probably the yield itself, not change)
                                change_pct = potential_pct
                        
                        # Look for change value format like "+0.123" or "-1.45"
                        if not change_val:
                            val_match = re.search(r'^([+-]?\d+\.?\d*)$', text)
                            if val_match and len(text) < 10:
                                try:
                                    potential_val = float(val_match.group(1))
                                    # Sanity check: reasonable change values
                                    if abs(potential_val) < 1000:
                                        change_val = potential_val
                                except:
                                    continue
                    
                    # Assign if found
                    if change_pct:
                        data['change_percent'] = change_pct
                    if change_val:
                        data['change'] = change_val
            
            # Fallback: Search the entire page for change data
            if data['change_percent'] is None:
                page_text = soup.get_text()
                
                # Look for patterns in the page text
                change_patterns = [
                    rf'{symbol}.*?([+-]?\d+\.?\d*)\s*\(([+-]?\d+\.?\d*%)\)',
                    r'Change.*?([+-]?\d+\.?\d*)\s*\(([+-]?\d+\.?\d*%)\)',
                    r'([+-]?\d+\.?\d*)\s*\(([+-]?\d+\.?\d*%)\)',
                ]
                
                for pattern in change_patterns:
                    matches = re.findall(pattern, page_text)
                    for match in matches:
                        if len(match) == 2:
                            try:
                                change_val = float(match[0])
                                change_pct = match[1]
                                pct_value = float(change_pct.replace('%', '').replace('+', ''))
                                
                                # For yields, be more strict about change percentages
                                if symbol in ['US10Y', 'TIPS'] and abs(pct_value) > 2.0:
                                    continue  # Skip unreasonably large changes for yields
                                
                                if abs(change_val) < 1000:  # Sanity check
                                    data['change'] = change_val
                                    data['change_percent'] = change_pct
                                    break
                            except:
                                continue
                    if data['change'] is not None:
                        break
                
                # Special fallback for yields: look for basis points or small changes
                if data['change_percent'] is None and symbol in ['US10Y', 'TIPS']:
                    # Look for basis points notation or small percentage changes
                    bp_patterns = [
                        r'([+-]?\d+\.?\d*)\s*(?:basis points|bps)',
                        r'([+-]?0\.\d+%)',  # Small percentages like +0.25%
                        r'([+-]?\d{1,2}\.\d+%)'  # Reasonable percentages like +1.25%
                    ]
                    
                    for pattern in bp_patterns:
                        matches = re.findall(pattern, page_text, re.IGNORECASE)
                        if matches:
                            try:
                                if 'basis' in pattern or 'bps' in pattern:
                                    # Convert basis points to percentage
                                    bp_val = float(matches[0])
                                    pct_val = bp_val / 100
                                    data['change_percent'] = f"{pct_val:+.2f}%"
                                else:
                                    # Direct percentage
                                    pct_str = matches[0]
                                    pct_val = float(pct_str.replace('%', '').replace('+', ''))
                                    if abs(pct_val) <= 2.0:  # Reasonable daily change for yields
                                        data['change_percent'] = pct_str
                                break
                            except:
                                continue
            
            # Extract additional data (high/low/previous close)
            page_text = soup.get_text()
            high_low_patterns = [
                (r'Day Range.*?([\d,]+\.?\d*)\s*-\s*([\d,]+\.?\d*)', 'range'),
                (r'Previous Close.*?([\d,]+\.?\d*)', 'prev_close'),
                (r'52 Week Range.*?([\d,]+\.?\d*)\s*-\s*([\d,]+\.?\d*)', '52week_range')
            ]
            
            for pattern, data_type in high_low_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    try:
                        if data_type == 'range':
                            data['day_low'] = float(matches[0][0].replace(',', ''))
                            data['day_high'] = float(matches[0][1].replace(',', ''))
                        elif data_type == 'prev_close':
                            data['prev_close'] = float(matches[0].replace(',', ''))
                    except:
                        continue
            
        except Exception as e:
            print(f"Error extracting data for {symbol}: {e}")
        
        return data
    
    def get_instrument_data(self, instrument_key):
        """Get data for a specific financial instrument with retry logic"""
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}{instrument_key}"
                timeout = 15 if attempt == 0 else 20  # Longer timeout on retry
                response = requests.get(url, headers=self.headers, timeout=timeout)
                
                if response.status_code != 200:
                    if attempt < max_retries - 1:
                        print(f"Attempt {attempt + 1} failed for {instrument_key}, retrying...")
                        time.sleep(2)  # Wait before retry
                        continue
                    return None
                
                soup = BeautifulSoup(response.content, 'html.parser')
                instrument_info = self.instruments[instrument_key]
                
                # Extract price data
                price_data = self._extract_price_data(soup, instrument_info['symbol'])
                
                # Combine with instrument metadata
                result = {
                    'timestamp': datetime.now().isoformat(),
                    'symbol': instrument_info['symbol'],
                    'name': instrument_info['name'],
                    'source': 'CNBC',
                    'gold_impact': instrument_info['gold_impact'],
                    'weight': instrument_info['weight'],
                    'description': instrument_info['description'],
                    **price_data
                }
                
                return result
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed for {instrument_key}: {e}, retrying...")
                    time.sleep(2)  # Wait before retry
                    continue
                else:
                    print(f"Error fetching {instrument_key} after {max_retries} attempts: {e}")
                    return None
        
        return None
    
    def get_all_market_factors(self):
        """Get data for all financial instruments"""
        results = {}
        
        for instrument_key in self.instruments.keys():
            print(f"Fetching {self.instruments[instrument_key]['name']}...")
            data = self.get_instrument_data(instrument_key)
            if data:
                results[data['symbol']] = data
            time.sleep(1)  # Be respectful to the server
        
        return results
    
    def get_all_financial_data(self):
        """Get comprehensive financial data with market impact analysis"""
        print("🔄 Collecting comprehensive financial market data...")
        
        # Get raw data for all instruments
        raw_data = self.get_all_market_factors()
        
        if not raw_data:
            return None
        
        # Format data for compatibility
        financial_instruments = {}
        
        for symbol, data in raw_data.items():
            financial_instruments[symbol] = {
                'name': data.get('name', symbol),
                'price': data.get('current_price'),
                'change': data.get('change'),
                'change_percent': data.get('change_percent', '0%'),
                'weight': data.get('weight', 0),
                'gold_impact': data.get('gold_impact', 'neutral'),
                'timestamp': data.get('timestamp', datetime.now().isoformat())
            }
        
        # Calculate market impact
        market_impact = self.calculate_gold_impact_score(financial_instruments)
        
        return {
            'financial_instruments': financial_instruments,
            'market_impact': market_impact,
            'timestamp': datetime.now().isoformat(),
            'total_instruments': len(financial_instruments)
        }
    
    def calculate_gold_impact_score(self, market_data):
        """Calculate overall gold impact score based on all factors"""
        if not market_data:
            return None
        
        total_score = 0
        total_weight = 0
        signals = []
        
        for symbol, data in market_data.items():
            if data.get('change_percent'):
                try:
                    # Extract percentage change
                    change_pct_str = data['change_percent'].replace('%', '').replace('+', '')
                    change_pct = float(change_pct_str)
                    weight = data['weight']
                    impact = data['gold_impact']
                    
                    # Calculate impact (inverse factors get negative multiplier)
                    if impact == 'inverse':
                        factor_score = -change_pct * weight
                        direction = "bearish" if change_pct > 0 else "bullish"
                    else:  # positive impact
                        factor_score = change_pct * weight
                        direction = "bullish" if change_pct > 0 else "bearish"
                    
                    total_score += factor_score
                    total_weight += weight
                    
                    # Generate signal if significant
                    if abs(change_pct) > 0.5:  # Significant move threshold
                        signals.append(f"{data['name']}: {change_pct:+.2f}% - {direction} for gold")
                
                except Exception as e:
                    print(f"Error calculating impact for {symbol}: {e}")
        
        # Normalize score
        if total_weight > 0:
            normalized_score = total_score / total_weight
        else:
            normalized_score = 0
        
        return {
            'overall_score': normalized_score,
            'total_weight': total_weight,
            'signals': signals,
            'recommendation': 'BUY' if normalized_score > 0.3 else 'SELL' if normalized_score < -0.3 else 'HOLD',
            'confidence': min(abs(normalized_score) * 100, 95)  # Cap at 95%
        }

    def get_dxy_data(self):
        """
        Backward compatibility method for DXY data extraction
        Returns DXY data in the same format as the old CNBCDXYScraper
        """
        try:
            dxy_data = self.get_instrument_data('.DXY')
            if dxy_data:
                # Convert to the format expected by the legacy code
                return {
                    'timestamp': dxy_data.get('timestamp', ''),
                    'symbol': dxy_data.get('symbol', 'DXY'),
                    'name': dxy_data.get('name', 'US Dollar Index'),
                    'current_price': dxy_data.get('current_price', 0),
                    'change': dxy_data.get('change', 0),
                    'change_percent': dxy_data.get('change_percent', '0%'),
                    'day_high': dxy_data.get('day_high'),
                    'day_low': dxy_data.get('day_low'),
                    'prev_close': dxy_data.get('prev_close'),
                    'source': 'CNBC'
                }
            return None
        except Exception as e:
            print(f"Warning: DXY data extraction failed: {e}")
            return None

def test_enhanced_scraper():
    """Test the enhanced financial scraper"""
    print("🔧 Testing Enhanced Financial Data Scraper")
    print("=" * 50)
    
    scraper = CNBCFinancialScraper()
    
    # Test individual instruments
    test_instruments = ['.DXY', 'US10Y', 'VIX']
    
    for instrument in test_instruments:
        print(f"\n📊 Testing {scraper.instruments[instrument]['name']}...")
        data = scraper.get_instrument_data(instrument)
        if data:
            print(f"✅ Success: {data['current_price']} ({data['change_percent']})")
        else:
            print("❌ Failed to fetch data")
    
    # Test complete market analysis
    print(f"\n🎯 Testing Complete Market Analysis...")
    market_data = scraper.get_all_market_factors()
    
    if market_data:
        print(f"✅ Fetched data for {len(market_data)} instruments")
        
        impact_analysis = scraper.calculate_gold_impact_score(market_data)
        if impact_analysis:
            print(f"\n🤖 Gold Impact Analysis:")
            print(f"   Overall Score: {impact_analysis['overall_score']:+.3f}")
            print(f"   Recommendation: {impact_analysis['recommendation']}")
            print(f"   Confidence: {impact_analysis['confidence']:.1f}%")
            
            if impact_analysis['signals']:
                print(f"   Key Signals:")
                for signal in impact_analysis['signals']:
                    print(f"     • {signal}")
    else:
        print("❌ Failed to fetch market data")

if __name__ == "__main__":
    test_enhanced_scraper()
