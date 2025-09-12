# 🏆 Gold Price Predictor - Real-Time AI System

A sophisticated real-time gold price monitoring and prediction system using the Tanshu API with advanced GUI interface and intelligent quota management.

## ✨ Features

### 🔴 **Real-Time Monitoring**
- **Live London Gold Market** data via Tanshu API
- **Multi-Metal Tracking** (Gold, Silver, Platinum, Palladium)
- **Smart API Caching** (30-minute intervals, 600 calls/month optimized)
- **Trading Hours Awareness** (24/7 London market schedule)

### 📊 **Professional GUI Interface**
- **Dark Theme** with high contrast visibility
- **Real-Time Updates** every 30 seconds
- **Color-Coded Changes** (green/red indicators)
- **Multi-Tab Layout** (Market Data, API Info, Raw Data)
- **Error Status Display** with bilingual descriptions

### 🔧 **Advanced API Management**
- **Quota Tracking** (600 requests/month shared)
- **Error Code Handling** (8 Tanshu API error codes)
- **Smart Caching** prevents duplicate API calls
- **Historical Data Access** (20+ years of precious metals data)

### 📈 **Historical Data Integration**
- **13+ Precious Metals** with comprehensive coverage
- **Multiple Timeframes** (Daily, Weekly, Monthly)
- **OHLC Data** with volume and technical indicators
- **Optimized Usage** for AI model training

## 🚀 Quick Start

### Prerequisites
```bash
pip install PyQt5 requests pytz
```

### Running the Application
```bash
cd gold_predictor
python gold_gui.py
```

## 📁 Project Structure

```
gold_predictor/
├── gold_predictor.py          # Core prediction logic & API client
├── gold_gui.py               # PyQt5 GUI application
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── .env.example              # Environment variables template
├── docs/                     # Additional documentation
│   ├── enhanced_apis.md      # API enhancement plans
│   └── gold_price_factors.md # Market factors analysis
├── logs/                     # Application logs
└── *.md                      # Feature documentation
```

## 🔑 Configuration

1. **API Key Setup**: Update the API key in `gold_predictor.py`:
   ```python
   self.api_key = "your_tanshu_api_key_here"
   ```

2. **Environment Variables** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## 📊 API Usage & Quota Management

### Current Usage Strategy
- **Real-Time Data**: ~27 calls/month (52-minute optimal intervals)
- **Historical Data**: ~573 calls available for AI training
- **Smart Caching**: Prevents duplicate API calls
- **Quota Monitoring**: Built-in usage tracking and warnings

### Supported Data Sources
- **Real-Time**: London Gold Market (伦敦金/银/铂金/钯金)
- **Historical**: 13+ precious metals since 2004-2005
- **Coverage**: Daily/Weekly/Monthly OHLC data
- **Volume**: Up to 1000 records per API call

## 🎯 AI Prediction Roadmap

### Phase 1: Data Foundation ✅
- [x] Real-time API integration
- [x] Historical data access
- [x] Quota management
- [x] Professional GUI

### Phase 2: Machine Learning (Coming Soon)
- [ ] SQLite database for historical storage
- [ ] Technical indicators (RSI, MACD, Bollinger Bands)
- [ ] External factors integration (Fed rates, USD index)
- [ ] Time series forecasting models

### Phase 3: AI Enhancement
- [ ] LSTM/GRU neural networks
- [ ] Sentiment analysis integration
- [ ] Multi-factor prediction models
- [ ] Real-time prediction validation

## 🔧 Technical Details

### API Endpoints
- **Real-Time**: `https://api.tanshuapi.com/api/gold/v1/london`
- **Historical**: `https://api.tanshuapi.com/api/precious_metals_history/v1/kline_data`

### Error Handling
Comprehensive error code support with bilingual descriptions:
- 10001: Invalid API Key
- 10002: No request permission
- 10003: API Key expired
- 10007: Request limit exceeded
- And more...

### Performance Optimizations
- **Shared API Cache**: Prevents duplicate calls between functions
- **Smart Refresh**: Manual vs automatic refresh strategies  
- **Memory Efficient**: Optimized data structures
- **Thread-Safe**: Background data collection

## 📈 Usage Examples

### Basic Price Monitoring
```python
from gold_predictor import GoldPricePredictor

predictor = GoldPricePredictor()
price, source, data = predictor.get_current_gold_price()
print(f"Current Gold: ${price:.2f}/oz from {source}")
```

### Historical Data Collection
```python
# Get last 30 days of XAU data
success, data, msg = predictor.fetch_historical_data(
    product='XAU', 
    data_type='1',  # Daily
    limit=30
)
```

### GUI Application
```python
# Launch full GUI application
python gold_gui.py
```

## 🤝 Contributing

This project is designed for educational and research purposes. Future enhancements will focus on AI-powered prediction capabilities.

## 📄 License

Educational/Research Use

## 📞 Support

For questions about implementation or AI enhancement strategies, refer to the documentation files in the `docs/` directory.

---

**Built with ❤️ for real-time precious metals analysis and AI-powered market prediction.**
