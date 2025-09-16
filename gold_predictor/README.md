# 🏆 Gold Price Predictor - Real-Time AI System

A comprehensive AI-powered gold price prediction system with real-time market factor analysis, dual-currency USD/CNY display, and historical price charting.

## ✨ Features

### 🔴 **Real-Time Data Sources**
- **CNBC Web Scraping** for live gold spot prices (XAU=)
- **Multi-Factor Analysis** (DXY, US10Y, TIPS, VIX, GLD, USD/CNY)
- **Unified Data Pipeline** with consistent scraping methodology
- **Historical API Support** (Tanshu API for 30-day charts)

### 📊 **Professional GUI Interface**
- **Dual Currency Display** (USD and CNY side-by-side)
- **Historical Charts** (30-day trend visualization with matplotlib)
- **Color-Coded Changes** (Red=positive, Green=negative)
- **Multi-Tab Layout** (Current Prices, Market Factors, API Info)
- **Real-Time Updates** with manual refresh controls
- **Raw API Responses** (7-section layout showing all data sources)

### 🔧 **Advanced Data Management**
- **Web Scraping Resilience** with retry logic and error handling
- **Currency Conversion** (automatic USD to CNY calculation)
- **Chart Integration** with proper data parsing and visualization
- **Consolidated Scraping** (single module for all financial instruments)

## 🚀 Complete Setup Guide

### Prerequisites

**System Requirements:**
- Python 3.7 or higher
- Windows/macOS/Linux (cross-platform compatible)
- Internet connection for real-time data scraping

### Step 1: Clone the Repository

```bash
# Clone the repository to your local machine
git clone https://github.com/your-username/AI-Test.git

# Navigate to the project directory
cd AI-Test/gold_predictor
```

### Step 2: Install Dependencies

```bash
# Install all required Python packages
pip install -r requirements.txt
```

**Alternative manual installation:**
```bash
pip install PyQt5 requests beautifulsoup4 matplotlib numpy pandas scikit-learn python-dotenv
```

### Step 3: Run the Application

**Windows:**
```powershell
python gold_gui.py
# or
py gold_gui.py
```

**macOS/Linux:**
```bash
python3 gold_gui.py
```

### Step 4: Verify Installation

The application should start and display:
1. ✅ Gold price data from CNBC
2. ✅ Market factors (DXY, US10Y, etc.)
3. ✅ Historical 30-day chart
4. ✅ Real-time updates every 30 seconds

## 🛠️ Troubleshooting

### Common Issues

**Issue: "PyQt5 not found"**
```bash
# Solution: Install PyQt5
pip install PyQt5
```

**Issue: "Module not found" errors**
```bash
# Solution: Ensure you're in the correct directory
cd AI-Test/gold_predictor
python gold_gui.py
```

**Issue: "No data displayed"**
- Check internet connection
- Wait 30-60 seconds for initial data load
- Check the API Info tab for error messages

**Issue: Charts not displaying**
```bash
# Solution: Install matplotlib
pip install matplotlib
```

### Virtual Environment (Recommended)

If you encounter dependency conflicts, create a virtual environment:

**Windows:**
```powershell
python -m venv gold_predictor_env
gold_predictor_env\Scripts\activate
pip install -r requirements.txt
python gold_gui.py
```

**macOS/Linux:**
```bash
python3 -m venv gold_predictor_env
source gold_predictor_env/bin/activate
pip install -r requirements.txt
python3 gold_gui.py
```

## 📁 Project Structure

```
gold_predictor/
├── gold_gui.py           # Main GUI application
├── gold_predictor.py     # Core prediction engine with CNBC integration
├── financial_scraper.py  # Unified CNBC web scraping module
├── README.md            # This comprehensive documentation
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template (optional)
├── docs/                # Documentation folder
│   ├── DEVELOPMENT_GUIDE.md     # Development status and features
│   ├── TECHNICAL_REFERENCE.md   # API documentation and error codes
│   ├── gold_price_factors.md    # Market factors analysis
│   └── README.md               # Documentation index
└── logs/                # Application logs (created automatically)
```

## 🔑 Key Components

### 1. Data Sources
- **Primary**: CNBC web scraping for live prices and market factors
- **Historical**: Tanshu API for 30-day historical charts
- **Instruments**: Gold (XAU), DXY, US10Y, TIPS, VIX, GLD, USD/CNY

### 2. Core Files
- **gold_gui.py**: Main application entry point
- **gold_predictor.py**: Core prediction logic and API handling
- **financial_scraper.py**: CNBC web scraping for all instruments

### 3. GUI Features
- **Current Prices Tab**: Real-time gold prices in USD and CNY
- **Market Factors Tab**: Live market indicators affecting gold prices
- **Historical Charts Tab**: 30-day price trend visualization
- **API Info Tab**: Raw API responses for debugging
- **Color Scheme**: Red for positive changes, green for negative changes

## ⚙️ Configuration

### Environment Variables (Optional)
Create a `.env` file in the project directory for custom settings:
```bash
# Optional: Custom API settings
TANSHU_API_KEY=your_api_key_here
REFRESH_INTERVAL=30
```

### Current Data Endpoints
- **CNBC Base URL**: `https://www.cnbc.com/quotes/`
- **Gold Price**: XAU= (Gold Spot)
- **Market Factors**: @DX.1 (DXY), @TNX.1 (US10Y), etc.
- **Update Method**: Manual refresh (button-triggered)

## 🔄 Recent Updates

### Latest Features (Current Version)
- **✅ Historical API Optimization**: Only loads on startup for better performance
- **✅ Clean Chart Titles**: Removed redundant date references
- **✅ Multi-Timeframe Statistics**: 3-day, 7-day, and 30-day change calculations
- **✅ Enhanced Chart Layout**: Increased height, proper label visibility
- **✅ Raw API Response**: 7-section grid showing all financial data sources
- **✅ Documentation Consolidation**: Streamlined from 8 to 4 MD files
- **✅ Cross-Platform Ready**: No local paths, ready for deployment

### Technical Improvements
- **Chart Height**: Increased from 300px to 400px for better visibility
- **Status Bar**: White text on dark background for improved readability
- **Statistics Panel**: 3-column layout with larger fonts for key metrics
- **Error Handling**: Robust fallback mechanisms for all data sources

## 🎯 Quick Testing Steps

After installation, follow these steps to verify everything works:

1. **Basic Startup Test**:
   ```bash
   # Navigate to project directory
   cd AI-Test/gold_predictor
   
   # Run application
   python gold_gui.py  # Windows/Linux
   python3 gold_gui.py # macOS
   ```

2. **Data Verification**:
   - Check "Current Prices" tab shows USD and CNY prices
   - Verify "Market Factors" tab displays DXY, US10Y, etc.
   - Test "Historical Charts" tab shows 30-day trend
   - Examine "API Info" tab for raw data from all 7 sources

3. **Refresh Functionality**:
   - Click refresh buttons to update real-time data
   - Observe color changes (red=positive, green=negative)
   - Check console output for any error messages

4. **Expected Behavior**:
   - Gold prices should load within 5-10 seconds
   - Charts should display properly formatted data
   - Currency conversion should show reasonable CNY values
   - All 7 raw API sections should display data

## 📚 Advanced Usage

### Debug Mode
To see detailed output and error messages:
```bash
# Run from command line to see console output
python gold_gui.py

# Console will show:
# - API scraping results
# - Error messages
# - Data processing status
# - Network request details
```

### Virtual Environment Setup
For isolated development:
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run application
python gold_gui.py
```

## 📖 Additional Documentation

For comprehensive technical documentation, see the **[docs/](docs/)** folder:
- **[DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md)**: Project status and feature development
- **[TECHNICAL_REFERENCE.md](docs/TECHNICAL_REFERENCE.md)**: API documentation and error codes
- **[gold_price_factors.md](docs/gold_price_factors.md)**: Market factors analysis
- **[README.md](docs/README.md)**: Documentation navigation

## 🤝 Contributing

This project is designed for educational and research purposes. When contributing:

1. Fork the repository
2. Create a feature branch
3. Test changes thoroughly
4. Update documentation as needed
5. Submit a pull request

## 📄 License & Disclaimer

This project is for educational and personal use. Please respect the terms of service of data providers (CNBC, Tanshu) when using their data. Not intended for commercial trading decisions.

## 📞 Support

### When to Seek Help
- Application won't start after following all steps
- Persistent network/scraping errors
- GUI display issues on your system
- Data accuracy concerns

### Information to Provide
1. **Python Version**: Run `python --version`
2. **Error Messages**: Copy full console output
3. **System Info**: OS version, display scaling
4. **Network Status**: Can you access CNBC.com manually?

### Self-Help Checklist
- [ ] Python 3.7+ installed and accessible
- [ ] All required packages installed (`pip list` to verify)
- [ ] Internet connection stable
- [ ] No corporate firewall blocking CNBC.com
- [ ] In correct project directory (`AI-Test/gold_predictor`)

---

**Built with ❤️ for real-time precious metals analysis and AI-powered market prediction.**
