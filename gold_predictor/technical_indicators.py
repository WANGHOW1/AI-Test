#!/usr/bin/env python3
"""
Technical Indicators Module for Gold Predictor GUI
Provides comprehensive technical analysis with weighted signals
"""

from gold_predictor import GoldPricePredictor

class TechnicalIndicatorsEngine:
    """
    Professional Technical Analysis Engine for GUI Integration
    """
    
    def __init__(self):
        self.predictor = GoldPricePredictor()
        
    def calculate_sma(self, prices, period):
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return []
        
        sma = []
        for i in range(period - 1, len(prices)):
            avg = sum(prices[i - period + 1:i + 1]) / period
            sma.append(round(avg, 2))
        
        return sma
    
    def calculate_cci(self, high_prices, low_prices, close_prices, period=20):
        """Calculate CCI (Commodity Channel Index)"""
        if len(high_prices) < period:
            return []
        
        # Calculate Typical Prices
        typical_prices = []
        for i in range(len(close_prices)):
            tp = (high_prices[i] + low_prices[i] + close_prices[i]) / 3
            typical_prices.append(tp)
        
        # Calculate SMA of Typical Prices
        sma_typical = self.calculate_sma(typical_prices, period)
        
        if not sma_typical:
            return []
        
        # Calculate CCI
        cci_values = []
        start_index = period - 1
        
        for i in range(len(sma_typical)):
            # Get period of typical prices for mean deviation
            period_start = start_index + i - period + 1
            period_end = start_index + i + 1
            period_prices = typical_prices[period_start:period_end]
            
            current_tp = typical_prices[start_index + i]
            current_sma = sma_typical[i]
            
            # Calculate mean deviation
            deviations = [abs(price - current_sma) for price in period_prices]
            mean_deviation = sum(deviations) / period
            
            if mean_deviation == 0:
                cci = 0
            else:
                cci = (current_tp - current_sma) / (0.015 * mean_deviation)
            
            cci_values.append(round(cci, 2))
        
        return cci_values
    
    def categorize_cci(self, cci_value):
        """Categorize CCI into trading signals"""
        if cci_value > 200:
            return "Strong Sell", "🔥"
        elif cci_value > 100:
            return "Sell", "📉"
        elif cci_value > -100:
            return "Neutral", "📊"
        elif cci_value > -200:
            return "Buy", "💎"
        else:
            return "Strong Buy", "🚨"
    
    def categorize_ma_trend(self, current_price, ma_value):
        """Categorize MA based on price position relative to MA"""
        price_diff_pct = ((current_price - ma_value) / ma_value) * 100
        
        if price_diff_pct > 5:
            return "Strong Buy", "🚀"
        elif price_diff_pct > 2:
            return "Buy", "📈"
        elif price_diff_pct > -2:
            return "Neutral", "📊"
        elif price_diff_pct > -5:
            return "Sell", "📉"
        else:
            return "Strong Sell", "🔥"
    
    def categorize_ma_crossover(self, ma_fast, ma_slow, fast_period, slow_period):
        """Categorize MA crossover signals"""
        spread_pct = ((ma_fast - ma_slow) / ma_slow) * 100
        
        # Different thresholds based on MA combination
        if fast_period <= 10:  # Short-term pairs (MA5-MA10, MA10-MA20)
            strong_threshold = 1.5
            weak_threshold = 0.5
        elif fast_period <= 20:  # Medium-term pairs (MA20-MA40, MA20-MA60)
            strong_threshold = 2.0
            weak_threshold = 0.8
        else:  # Long-term pairs (MA40-MA60)
            strong_threshold = 1.0
            weak_threshold = 0.3
        
        if spread_pct > strong_threshold:
            return "Strong Buy", "🚀"
        elif spread_pct > weak_threshold:
            return "Buy", "📈"
        elif spread_pct > -weak_threshold:
            return "Neutral", "📊"
        elif spread_pct > -strong_threshold:
            return "Sell", "📉"
        else:
            return "Strong Sell", "🔥"
    
    def calculate_weighted_sentiment(self, indicator_data):
        """
        Calculate weighted overall sentiment based on indicator importance
        """
        weights = {
            'CCI-20': 15,        # Momentum oscillator - key for timing
            'MA5': 2,            # Too volatile for major decisions
            'MA20': 8,           # Important trend line
            'MA40': 10,          # Major support/resistance
            'MA60': 10,          # Long-term trend
            'MA5-MA10': 8,       # Short-term momentum
            'MA10-MA20': 12,     # Medium-term trend
            'MA20-MA40': 20,     # PRIMARY trend indicator
            'MA20-MA60': 18,     # Long-term trend confirmation
            'MA40-MA60': 5       # Long-term stability
        }
        
        # Signal scores
        scores = {
            "Strong Buy": 2,
            "Buy": 1,
            "Neutral": 0,
            "Sell": -1,
            "Strong Sell": -2
        }
        
        weighted_score = 0
        total_weight = 0
        
        for indicator, indicator_tuple in indicator_data.items():
            if indicator in weights:
                weight = weights[indicator]
                # Extract category (first element) from tuple regardless of length
                category = indicator_tuple[0] if len(indicator_tuple) > 0 else "Neutral"
                score = scores.get(category, 0)
                weighted_score += score * weight
                total_weight += weight
        
        if total_weight == 0:
            return "Neutral", "📊", 0.0
        
        # Calculate weighted average
        avg_weighted_score = weighted_score / total_weight
        
        # Determine final category with weighted thresholds
        if avg_weighted_score >= 1.3:
            return "Strong Buy", "🚀", avg_weighted_score
        elif avg_weighted_score >= 0.4:
            return "Buy", "📈", avg_weighted_score
        elif avg_weighted_score >= -0.4:
            return "Neutral", "📊", avg_weighted_score
        elif avg_weighted_score >= -1.3:
            return "Sell", "📉", avg_weighted_score
        else:
            return "Strong Sell", "🔥", avg_weighted_score
    
    def get_comprehensive_analysis(self, days=80, historical_data=None):
        """
        Get comprehensive technical analysis for GUI display
        Returns structured data for table display
        
        Args:
            days (int): Number of days of data needed (used only if historical_data is None)
            historical_data (list): Pre-fetched historical data to avoid API calls
        """
        try:
            # Use provided historical data or fetch if not available
            if historical_data is not None:
                success = True
                data = historical_data
                message = "Using cached data"
                fetch_result = (success, data, message)
            else:
                # Fetch historical data only if not provided
                fetch_result = self.predictor.fetch_historical_data(
                    product='XAU',
                    data_type='1',
                    limit=days,
                    force=False  # Use cache when possible for GUI
                )
            
            # Handle different return formats
            if len(fetch_result) == 3:
                success, data, message = fetch_result
            elif len(fetch_result) == 2:
                success, message = fetch_result
                data = None
            else:
                return None, "Unexpected API response format"
            
            if not success:
                return None, f"Failed to fetch data: {message}"
            
            if not data or 'data' not in data or 'list' not in data['data']:
                return None, "Invalid data structure received"
            
            # Process data
            records = data['data']['list']
            if not records:
                return None, "No historical data available"
                
            dates = [record['day'] for record in records]
            high_prices = [float(record['maxprice']) for record in records]
            low_prices = [float(record['minprice']) for record in records]
            close_prices = [float(record['close']) for record in records]
            
            # Reverse to chronological order
            dates.reverse()
            high_prices.reverse()
            low_prices.reverse()
            close_prices.reverse()
            
            current_price = close_prices[-1]
            current_date = dates[-1]
            
            # Calculate all indicators
            indicator_data = {}
            
            # CCI Analysis
            cci_values = self.calculate_cci(high_prices, low_prices, close_prices, 20)
            if cci_values:
                current_cci = cci_values[-1]
                cci_category, cci_icon = self.categorize_cci(current_cci)
                indicator_data['CCI-20'] = (cci_category, cci_icon, current_cci)
            
            # Moving Averages Analysis
            ma_periods = [5, 20, 40, 60]
            ma_values = {}
            
            for period in ma_periods:
                ma = self.calculate_sma(close_prices, period)
                if ma:
                    current_ma = ma[-1]
                    ma_values[period] = current_ma
                    ma_category, ma_icon = self.categorize_ma_trend(current_price, current_ma)
                    price_diff = current_price - current_ma
                    indicator_data[f'MA{period}'] = (ma_category, ma_icon, current_ma, price_diff)
            
            # MA Crossover Analysis
            crossover_pairs = [
                (5, 10, "MA5-MA10"),
                (10, 20, "MA10-MA20"), 
                (20, 40, "MA20-MA40"),
                (20, 60, "MA20-MA60"),
                (40, 60, "MA40-MA60")
            ]
            
            for fast_period, slow_period, pair_name in crossover_pairs:
                # Calculate both MAs
                ma_fast = self.calculate_sma(close_prices, fast_period)
                ma_slow = self.calculate_sma(close_prices, slow_period)
                
                if ma_fast and ma_slow:
                    current_fast = ma_fast[-1]
                    current_slow = ma_slow[-1]
                    
                    cross_category, cross_icon = self.categorize_ma_crossover(
                        current_fast, current_slow, fast_period, slow_period
                    )
                    
                    spread = current_fast - current_slow
                    spread_pct = ((current_fast - current_slow) / current_slow) * 100
                    
                    indicator_data[pair_name] = (cross_category, cross_icon, spread, spread_pct)
            
            # Calculate weighted sentiment
            try:
                sentiment_result = self.calculate_weighted_sentiment(indicator_data)
                if len(sentiment_result) == 3:
                    weighted_sentiment, weighted_icon, weighted_score = sentiment_result
                else:
                    weighted_sentiment, weighted_icon, weighted_score = "Neutral", "📊", 0.0
                    print(f"❌ Unexpected sentiment result length: {len(sentiment_result)}")
            except Exception as e:
                weighted_sentiment, weighted_icon, weighted_score = "Error", "❌", 0.0
                print(f"❌ Error calculating weighted sentiment: {e}")
                import traceback
                traceback.print_exc()
            
            # Format for GUI table
            table_data = []
            
            # Main indicators
            if 'CCI-20' in indicator_data:
                try:
                    cci_data = indicator_data['CCI-20']
                    if len(cci_data) >= 3:
                        cat, icon, value = cci_data[:3]
                        table_data.append({
                            'indicator': 'CCI-20',
                            'value': f"{value:+.2f}",
                            'category': cat,
                            'icon': icon,
                            'type': 'momentum'
                        })
                except Exception as e:
                    print(f"❌ Error processing CCI data: {e}")
            
            # MA indicators
            for period in ma_periods:
                key = f'MA{period}'
                if key in indicator_data:
                    try:
                        ma_data = indicator_data[key]
                        if len(ma_data) >= 4:
                            cat, icon, ma_val, diff = ma_data[:4]
                            table_data.append({
                                'indicator': f'MA{period}',
                                'value': f"${ma_val:.2f}",
                                'category': cat,
                                'icon': icon,
                                'type': 'ma',
                                'extra': f"${diff:+.2f}"
                            })
                    except Exception as e:
                        print(f"❌ Error processing MA{period} data: {e}")
            
            # Crossover indicators
            for _, _, pair_name in crossover_pairs:
                if pair_name in indicator_data:
                    try:
                        cross_data = indicator_data[pair_name]
                        if len(cross_data) >= 4:
                            cat, icon, spread, spread_pct = cross_data[:4]
                            table_data.append({
                                'indicator': pair_name,
                                'value': f"${spread:+.2f}",
                                'category': cat,
                                'icon': icon,
                                'type': 'crossover',
                                'extra': f"{spread_pct:+.2f}%"
                            })
                    except Exception as e:
                        print(f"❌ Error processing {pair_name} data: {e}")
            
            # Overall sentiment
            overall_data = {
                'sentiment': weighted_sentiment,
                'icon': weighted_icon,
                'score': weighted_score,
                'current_price': current_price,
                'current_date': current_date
            }
            
            return table_data, overall_data
            
        except Exception as e:
            return None, f"Analysis error: {str(e)}"
