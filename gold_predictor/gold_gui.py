#!/usr/bin/env python3
"""
Gold Price Predictor GUI - Real-time Tanshu API Integration
Complete GUI application with live gold prices from Shanghai Gold Exchange
"""

import sys
import os
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QTextEdit, QPushButton, 
                           QTabWidget, QStatusBar, QGroupBox, QGridLayout,
                           QProgressBar, QSplitter, QTableWidget, QTableWidgetItem,
                           QScrollArea)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPalette, QColor
import json

# Matplotlib for charts
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.dates as mdates
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    print("⚠️ Matplotlib not available. Charts will be disabled.")
    MATPLOTLIB_AVAILABLE = False

# Import our gold predictor and technical indicators
from gold_predictor import GoldPricePredictor
from technical_indicators import TechnicalIndicatorsEngine

class GoldDataWorker(QThread):
    """Background worker for gold price data collection"""
    data_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, predictor, force_refresh=False, fetch_historical=True, fetch_market_factors=True, refresh_type="full"):
        super().__init__()
        self.predictor = predictor
        self.running = True
        self.force_refresh = force_refresh
        self.fetch_historical = fetch_historical
        self.fetch_market_factors = fetch_market_factors
        self.refresh_type = refresh_type  # "full", "price_only", "market_factors"
        
    def run(self):
        """Collect gold price data in background thread"""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"\n🔄 [{timestamp}] Starting {self.refresh_type} refresh...")
            
            # Always get current price and basic info (lightweight)
            usd_price, source, london_data = self.predictor.get_current_gold_price(self.force_refresh)
            
            # Get schedule info (lightweight)
            schedule = self.predictor.get_trading_schedule_info()
            
            # Initialize optional data
            market_info = None
            market_factors = None
            prediction_signals = None
            historical_data = None
            
            if self.refresh_type in ["full", "market_factors"]:
                print(f"📊 [{timestamp}] Fetching market factors...")
                
                # Extract gold data for reuse
                gold_data = {
                    'current_price': usd_price,
                    'change': london_data.get('change', '0'),
                    'change_percent': london_data.get('change_percent', '0%'),
                    'timestamp': london_data.get('timestamp')
                }
                
                # Get detailed market info (pass gold data to avoid duplicate calls)
                market_info = self.predictor.get_detailed_market_info(self.force_refresh, gold_data)
                
                # Get market factors including DXY (pass already-fetched gold price data)
                gold_price_data = (usd_price, source, london_data)
                market_factors = self.predictor.get_market_factors(gold_price_data)
                
                # Get prediction signals
                prediction_signals = self.predictor.get_prediction_signals()
            
            if self.refresh_type == "full" and self.fetch_historical:
                print(f"📈 [{timestamp}] Fetching historical data...")
                try:
                    success, hist_data, msg = self.predictor.fetch_historical_data(
                        product='XAU', 
                        data_type='1',  # daily data
                        limit=80,       # 80 days needed for technical indicators
                        force=self.force_refresh
                    )
                    if success:
                        historical_data = hist_data
                    else:
                        print(f"⚠️ [{timestamp}] Historical data fetch failed: {msg}")
                except Exception as e:
                    print(f"⚠️ [{timestamp}] Historical data error: {e}")
            
            result = {
                'current_price_usd': usd_price,
                'current_london_data': london_data,
                'source': source,
                'market_info': market_info,
                'schedule': schedule,
                'market_factors': market_factors,
                'prediction_signals': prediction_signals,
                'historical_data': historical_data,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'refresh_type': self.refresh_type
            }
            
            print(f"✅ [{timestamp}] {self.refresh_type.title()} refresh completed")
            self.data_updated.emit(result)
            
        except Exception as e:
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"❌ [{timestamp}] Refresh error: {e}")
            self.error_occurred.emit(str(e))

class GoldPredictorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.predictor = GoldPricePredictor()
        self.technical_engine = TechnicalIndicatorsEngine()  # Add technical indicators engine
        self.data_worker = None
        self.initial_load_complete = False  # Flag to track first load
        self.cached_historical_data = None  # Cache historical data to avoid repeated API calls
        
        # Multi-tier refresh tracking
        self.last_market_factors_refresh = None
        self.last_technical_indicators_refresh = None
        self.market_factors_interval = 600  # 10 minutes in seconds
        self.refresh_count = 0  # Track refresh cycles
        
        self.init_ui()
        self.setup_timer()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Gold Price Predictor - Real-time London Gold API")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set dark theme with improved contrast
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
            QGroupBox {
                color: #ffffff;
                border: 2px solid #666;
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
                background-color: #353535;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #e0e0e0;
            }
            QTableWidget {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #666;
                gridline-color: #555;
                selection-background-color: #0078d4;
                alternate-background-color: #383838;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #555;
                color: #ffffff;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QTableWidget QHeaderView::section {
                background-color: #505050;
                color: #ffffff;
                padding: 8px;
                border: 1px solid #666;
                font-weight: bold;
            }
            QTextEdit {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #666;
                selection-background-color: #0078d4;
            }
            QTabWidget::pane {
                border: 1px solid #666;
                background-color: #353535;
            }
            QTabWidget::tab-bar {
                left: 5px;
            }
            QTabBar::tab {
                background-color: #505050;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QTabBar::tab:hover {
                background-color: #606060;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton#refreshButton {
                background-color: #2196F3;
                color: white;
            }
            QPushButton#refreshButton:hover {
                background-color: #1976D2;
            }
            QPushButton#refreshButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton#toggleButton {
                background-color: #FF9800;
                color: white;
            }
            QPushButton#toggleButton:hover {
                background-color: #F57C00;
            }
            QPushButton#toggleButton:pressed {
                background-color: #E65100;
            }
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Header section
        header_group = QGroupBox("🏆 Real-Time London Gold & Precious Metals")
        header_layout = QVBoxLayout(header_group)
        
        # First row: USD and CNY prices side by side
        prices_layout = QHBoxLayout()
        
        # USD price section (left side)
        usd_section = QVBoxLayout()
        usd_price_layout = QHBoxLayout()
        usd_label = QLabel("💰 Gold Price (USD):")
        self.price_label = QLabel("Loading...")
        self.price_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #FFD700;")
        usd_price_layout.addWidget(usd_label)
        usd_price_layout.addWidget(self.price_label)
        usd_price_layout.addStretch()
        usd_section.addLayout(usd_price_layout)
        
        # CNY price section (right side)
        cny_section = QVBoxLayout()
        cny_price_layout = QHBoxLayout()
        cny_label = QLabel("💰 Gold Price (CNY):")
        self.cny_price_label = QLabel("Loading...")
        self.cny_price_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #FFD700;")  # Match USD color
        cny_price_layout.addWidget(cny_label)
        cny_price_layout.addWidget(self.cny_price_label)
        cny_price_layout.addStretch()
        cny_section.addLayout(cny_price_layout)
        
        # USD/CNY rate under CNY price
        rate_layout = QHBoxLayout()
        rate_label = QLabel("🔄 USD/CNY Rate:")
        self.usd_cny_rate_label = QLabel("Loading...")
        self.usd_cny_rate_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #87CEEB;")
        rate_layout.addWidget(rate_label)
        rate_layout.addWidget(self.usd_cny_rate_label)
        rate_layout.addStretch()
        cny_section.addLayout(rate_layout)
        
        # Add both sections to prices layout
        prices_layout.addLayout(usd_section)
        prices_layout.addLayout(cny_section)
        header_layout.addLayout(prices_layout)
        
        # Price data storage
        self.usd_price_data = None
        self.cny_price_data = None
        
        # Third row: Source and timestamp
        info_layout = QHBoxLayout()
        self.source_label = QLabel("Source: Loading...")
        self.source_label.setStyleSheet("color: #87CEEB; font-weight: bold;")
        self.timestamp_label = QLabel("Last Update: Loading...")
        self.timestamp_label.setStyleSheet("color: #DDA0DD; font-weight: bold;")
        info_layout.addWidget(self.source_label)
        info_layout.addWidget(self.timestamp_label)
        info_layout.addStretch()
        header_layout.addLayout(info_layout)
        
        # Fourth row: Trading status
        status_layout = QHBoxLayout()
        self.trading_status_label = QLabel("Trading Status: Loading...")
        self.trading_status_label.setStyleSheet("color: #90EE90; font-weight: bold;")
        self.london_time_label = QLabel("London Time: Loading...")
        self.london_time_label.setStyleSheet("color: #F0E68C; font-weight: bold;")
        status_layout.addWidget(self.trading_status_label)
        status_layout.addWidget(self.london_time_label)
        status_layout.addStretch()
        header_layout.addLayout(status_layout)
        
        main_layout.addWidget(header_group)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Tab 1: Market Data
        market_tab = QWidget()
        market_layout = QVBoxLayout(market_tab)
        
        # Technical Indicators Dashboard
        indicators_group = QGroupBox("🎯 Technical Analysis Dashboard")
        indicators_layout = QVBoxLayout(indicators_group)
        
        # Overall sentiment header
        sentiment_layout = QHBoxLayout()
        
        self.overall_sentiment_label = QLabel("Overall Signal: Loading...")
        self.overall_sentiment_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #FFD700; 
            background-color: #2b2b2b; 
            padding: 10px; 
            border: 2px solid #555; 
            border-radius: 5px;
            text-align: center;
        """)
        sentiment_layout.addWidget(self.overall_sentiment_label)
        
        self.sentiment_score_label = QLabel("Score: --")
        self.sentiment_score_label.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #87CEEB; 
            background-color: #1e1e1e; 
            padding: 10px; 
            border: 1px solid #555; 
            border-radius: 5px;
            min-width: 150px;
        """)
        sentiment_layout.addWidget(self.sentiment_score_label)
        
        indicators_layout.addLayout(sentiment_layout)
        
        # Technical indicators table
        self.indicators_table = QTableWidget()
        self.indicators_table.setColumnCount(5)
        self.indicators_table.setHorizontalHeaderLabels([
            "Indicator", "Value", "Signal", "Category", "Details"
        ])
        self.indicators_table.setAlternatingRowColors(True)
        self.indicators_table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                border: 1px solid #555;
                gridline-color: #555;
                color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #444;
            }
            QHeaderView::section {
                background-color: #1e1e1e;
                color: #FFD700;
                font-weight: bold;
                padding: 10px;
                border: none;
            }
        """)
        
        # Set column widths
        self.indicators_table.setColumnWidth(0, 120)  # Indicator
        self.indicators_table.setColumnWidth(1, 100)  # Value
        self.indicators_table.setColumnWidth(2, 80)   # Signal
        self.indicators_table.setColumnWidth(3, 120)  # Category
        self.indicators_table.setColumnWidth(4, 100)  # Details
        
        indicators_layout.addWidget(self.indicators_table)
        
        # Refresh button for technical analysis
        refresh_indicators_btn = QPushButton("🔄 Refresh Technical Analysis")
        refresh_indicators_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        refresh_indicators_btn.clicked.connect(self.refresh_technical_indicators)
        indicators_layout.addWidget(refresh_indicators_btn)
        
        market_layout.addWidget(indicators_group)
        
        # Historical Price Chart
        chart_group = QGroupBox("📊 Gold Price Trend")
        chart_main_layout = QVBoxLayout(chart_group)
        
        # Create horizontal layout for chart and statistics
        chart_content_layout = QHBoxLayout()
        
        # Chart container
        self.chart_widget = QWidget()
        self.chart_widget.setMinimumHeight(400)  # Increased from 300 to 400
        self.chart_widget.setStyleSheet("background-color: #2b2b2b; border: 1px solid #555;")
        chart_content_layout.addWidget(self.chart_widget, 3)  # Take 3/4 of space
        
        # Change statistics panel
        stats_widget = QWidget()
        stats_widget.setMaximumWidth(200)
        stats_widget.setStyleSheet("background-color: #1e1e1e; border: 1px solid #555; border-radius: 5px;")
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setSpacing(15)
        
        # Statistics title
        stats_title = QLabel("Price Changes")
        stats_title.setStyleSheet("color: #FFD700; font-size: 14px; font-weight: bold; text-align: center;")
        stats_layout.addWidget(stats_title)
        
        # 3-day change
        self.change_3day_label = QLabel("3-Day: --")
        self.change_3day_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; text-align: center;")
        stats_layout.addWidget(self.change_3day_label)
        
        # 7-day change
        self.change_7day_label = QLabel("7-Day: --")
        self.change_7day_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; text-align: center;")
        stats_layout.addWidget(self.change_7day_label)
        
        # 30-day change
        self.change_30day_label = QLabel("30-Day: --")
        self.change_30day_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; text-align: center;")
        stats_layout.addWidget(self.change_30day_label)
        
        stats_layout.addStretch()  # Push content to top
        chart_content_layout.addWidget(stats_widget, 1)  # Take 1/4 of space
        
        chart_main_layout.addLayout(chart_content_layout)
        
        # Chart status label
        self.chart_status_label = QLabel("📊 Loading historical data...")
        self.chart_status_label.setStyleSheet("color: #87CEEB; font-size: 11px; text-align: center;")
        chart_main_layout.addWidget(self.chart_status_label)
        
        market_layout.addWidget(chart_group)
        
        tab_widget.addTab(market_tab, "💰 Market Data")
        
        # Tab 2: Market Factors & Prediction
        factors_tab = QWidget()
        factors_layout = QVBoxLayout(factors_tab)
        
        # Create a scroll area for the factors
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Market Factors Grid Layout (2x3 grid for 5 factors + correlation)
        factors_grid_layout = QGridLayout()
        
        # DXY Section
        dxy_group = QGroupBox("📊 USD Index (DXY)")
        dxy_layout = QGridLayout(dxy_group)
        
        self.dxy_price_label = QLabel("Loading...")
        self.dxy_price_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFD700;")
        self.dxy_change_label = QLabel("Loading...")
        self.dxy_change_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.dxy_timestamp_label = QLabel("Last Updated: Loading...")
        self.dxy_timestamp_label.setStyleSheet("color: #87CEEB; font-size: 9px;")
        
        dxy_layout.addWidget(QLabel("Price:"), 0, 0)
        dxy_layout.addWidget(self.dxy_price_label, 0, 1)
        dxy_layout.addWidget(QLabel("Change:"), 1, 0)
        dxy_layout.addWidget(self.dxy_change_label, 1, 1)
        dxy_layout.addWidget(self.dxy_timestamp_label, 2, 0, 1, 2)
        
        # US 10Y Treasury Section
        us10y_group = QGroupBox("📈 10-Year Treasury")
        us10y_layout = QGridLayout(us10y_group)
        
        self.us10y_price_label = QLabel("Loading...")
        self.us10y_price_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFD700;")
        self.us10y_change_label = QLabel("Loading...")
        self.us10y_change_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.us10y_timestamp_label = QLabel("Last Updated: Loading...")
        self.us10y_timestamp_label.setStyleSheet("color: #87CEEB; font-size: 9px;")
        
        us10y_layout.addWidget(QLabel("Yield:"), 0, 0)
        us10y_layout.addWidget(self.us10y_price_label, 0, 1)
        us10y_layout.addWidget(QLabel("Change:"), 1, 0)
        us10y_layout.addWidget(self.us10y_change_label, 1, 1)
        us10y_layout.addWidget(self.us10y_timestamp_label, 2, 0, 1, 2)
        
        # TIPS Section
        tips_group = QGroupBox("📉 10-Year TIPS")
        tips_layout = QGridLayout(tips_group)
        
        self.tips_price_label = QLabel("Loading...")
        self.tips_price_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFD700;")
        self.tips_change_label = QLabel("Loading...")
        self.tips_change_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.tips_timestamp_label = QLabel("Last Updated: Loading...")
        self.tips_timestamp_label.setStyleSheet("color: #87CEEB; font-size: 9px;")
        
        tips_layout.addWidget(QLabel("Yield:"), 0, 0)
        tips_layout.addWidget(self.tips_price_label, 0, 1)
        tips_layout.addWidget(QLabel("Change:"), 1, 0)
        tips_layout.addWidget(self.tips_change_label, 1, 1)
        tips_layout.addWidget(self.tips_timestamp_label, 2, 0, 1, 2)
        
        # VIX Section
        vix_group = QGroupBox("📊 Volatility Index (VIX)")
        vix_layout = QGridLayout(vix_group)
        
        self.vix_price_label = QLabel("Loading...")
        self.vix_price_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFD700;")
        self.vix_change_label = QLabel("Loading...")
        self.vix_change_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.vix_timestamp_label = QLabel("Last Updated: Loading...")
        self.vix_timestamp_label.setStyleSheet("color: #87CEEB; font-size: 9px;")
        
        vix_layout.addWidget(QLabel("Index:"), 0, 0)
        vix_layout.addWidget(self.vix_price_label, 0, 1)
        vix_layout.addWidget(QLabel("Change:"), 1, 0)
        vix_layout.addWidget(self.vix_change_label, 1, 1)
        vix_layout.addWidget(self.vix_timestamp_label, 2, 0, 1, 2)
        
        # GLD Section
        gld_group = QGroupBox("🥇 Gold ETF (GLD)")
        gld_layout = QGridLayout(gld_group)
        
        self.gld_price_label = QLabel("Loading...")
        self.gld_price_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFD700;")
        self.gld_change_label = QLabel("Loading...")
        self.gld_change_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.gld_timestamp_label = QLabel("Last Updated: Loading...")
        self.gld_timestamp_label.setStyleSheet("color: #87CEEB; font-size: 9px;")
        
        gld_layout.addWidget(QLabel("Price:"), 0, 0)
        gld_layout.addWidget(self.gld_price_label, 0, 1)
        gld_layout.addWidget(QLabel("Change:"), 1, 0)
        gld_layout.addWidget(self.gld_change_label, 1, 1)
        gld_layout.addWidget(self.gld_timestamp_label, 2, 0, 1, 2)
        
        # Multi-Factor Correlation Analysis
        correlation_group = QGroupBox("🔗 Multi-Factor Analysis")
        correlation_layout = QGridLayout(correlation_group)
        
        self.correlation_status_label = QLabel("Analyzing...")
        self.correlation_status_label.setStyleSheet("font-weight: bold; color: #98FB98;")
        self.correlation_strength_label = QLabel("Market Score: Loading...")
        self.correlation_strength_label.setStyleSheet("color: #FFB6C1; font-size: 11px;")
        self.gold_change_label = QLabel("Factors Tracked: 0")
        self.gold_change_label.setStyleSheet("color: #DDA0DD;")
        self.usd_change_label = QLabel("Confidence: 0%")
        self.usd_change_label.setStyleSheet("color: #87CEEB;")
        
        correlation_layout.addWidget(QLabel("Status:"), 0, 0)
        correlation_layout.addWidget(self.correlation_status_label, 0, 1)
        correlation_layout.addWidget(self.correlation_strength_label, 1, 0, 1, 2)
        correlation_layout.addWidget(self.gold_change_label, 2, 0)
        correlation_layout.addWidget(self.usd_change_label, 2, 1)
        
        # Arrange factors in 3x2 grid
        factors_grid_layout.addWidget(dxy_group, 0, 0)
        factors_grid_layout.addWidget(us10y_group, 0, 1)
        factors_grid_layout.addWidget(tips_group, 0, 2)
        factors_grid_layout.addWidget(vix_group, 1, 0)
        factors_grid_layout.addWidget(gld_group, 1, 1)
        factors_grid_layout.addWidget(correlation_group, 1, 2)
        
        scroll_layout.addLayout(factors_grid_layout)
        
        # Compact AI Prediction Section
        prediction_group = QGroupBox("🤖 AI Prediction")
        prediction_layout = QVBoxLayout(prediction_group)
        prediction_group.setMaximumHeight(200)  # Make it smaller
        
        # Compact recommendation display
        recommendation_layout = QHBoxLayout()
        self.recommendation_label = QLabel("HOLD")
        self.recommendation_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFD700; padding: 8px; border: 2px solid #666; border-radius: 5px;")
        self.confidence_label = QLabel("Confidence: 0%")
        self.confidence_label.setStyleSheet("font-size: 12px; color: #87CEEB;")
        
        recommendation_layout.addWidget(QLabel("Rec:"))
        recommendation_layout.addWidget(self.recommendation_label)
        recommendation_layout.addWidget(self.confidence_label)
        recommendation_layout.addStretch()
        
        prediction_layout.addLayout(recommendation_layout)
        
        # Compact signals list
        self.signals_text = QTextEdit()
        self.signals_text.setMaximumHeight(100)  # Smaller height
        self.signals_text.setStyleSheet("background-color: #404040; color: #ffffff; border: 1px solid #666; font-size: 10px;")
        prediction_layout.addWidget(QLabel("Active Signals:"))
        prediction_layout.addWidget(self.signals_text)
        
        scroll_layout.addWidget(prediction_group)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        factors_layout.addWidget(scroll_area)
        
        tab_widget.addTab(factors_tab, "🎯 Market Factors")
        
        # Tab 3: API Information
        api_tab = QWidget()
        api_layout = QVBoxLayout(api_tab)
        
        # API status
        api_group = QGroupBox("🔌 API Status & Usage")
        api_layout_grid = QGridLayout(api_group)
        
        self.api_status_label = QLabel("API Status: Loading...")
        self.api_status_label.setStyleSheet("color: #90EE90; font-weight: bold;")
        self.monthly_limit_label = QLabel("Monthly Limit: 600 requests")
        self.monthly_limit_label.setStyleSheet("color: #FFB6C1; font-weight: bold;")
        self.optimal_interval_label = QLabel("Optimal Interval: Loading...")
        self.optimal_interval_label.setStyleSheet("color: #98FB98; font-weight: bold;")
        self.trading_days_label = QLabel("Trading Days Remaining: Loading...")
        self.trading_days_label.setStyleSheet("color: #DDA0DD; font-weight: bold;")
        
        api_layout_grid.addWidget(self.api_status_label, 0, 0)
        api_layout_grid.addWidget(self.monthly_limit_label, 0, 1)
        api_layout_grid.addWidget(self.optimal_interval_label, 1, 0)
        api_layout_grid.addWidget(self.trading_days_label, 1, 1)
        
        api_layout.addWidget(api_group)
        
        # Error Status Section
        error_group = QGroupBox("⚠️ Error Status & Diagnostics")
        error_layout = QVBoxLayout(error_group)
        
        self.error_status_label = QLabel("✅ No errors detected")
        self.error_status_label.setStyleSheet("color: #90EE90; font-weight: bold;")
        
        self.error_code_label = QLabel("Error Code: None")
        self.error_code_label.setStyleSheet("color: #DDA0DD; font-weight: bold;")
        
        self.error_description_label = QLabel("Description: All systems operational")
        self.error_description_label.setStyleSheet("color: #87CEEB; font-weight: normal;")
        self.error_description_label.setWordWrap(True)
        
        error_layout.addWidget(self.error_status_label)
        error_layout.addWidget(self.error_code_label)
        error_layout.addWidget(self.error_description_label)
        
        api_layout.addWidget(error_group)
        
        # Raw API responses - Multiple sections for each data source
        raw_main_group = QGroupBox("📄 Raw API Responses")
        raw_main_layout = QVBoxLayout(raw_main_group)
        
        # Create scroll area for all API responses
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Create grid layout with 3 columns, 2 rows (like Market Factors)
        # Row 1: Gold, DXY, USD/CNY
        row1_layout = QHBoxLayout()
        
        # 1. Gold Price (XAU=)
        gold_group = QGroupBox("🏆 Gold Spot Price (XAU=)")
        gold_layout = QVBoxLayout(gold_group)
        self.gold_response_text = QTextEdit()
        self.gold_response_text.setMaximumHeight(150)  # Increased from 120
        self.gold_response_text.setStyleSheet("font-family: 'Courier New'; font-size: 12px;")  # Increased from 10px
        gold_layout.addWidget(self.gold_response_text)
        row1_layout.addWidget(gold_group)
        
        # 2. US Dollar Index (DXY)
        dxy_group = QGroupBox("💵 US Dollar Index (.DXY)")
        dxy_layout = QVBoxLayout(dxy_group)
        self.dxy_response_text = QTextEdit()
        self.dxy_response_text.setMaximumHeight(150)  # Increased from 120
        self.dxy_response_text.setStyleSheet("font-family: 'Courier New'; font-size: 12px;")  # Increased from 10px
        dxy_layout.addWidget(self.dxy_response_text)
        row1_layout.addWidget(dxy_group)
        
        # 3. USD/CNY Exchange Rate
        usdcny_group = QGroupBox("🇨🇳 USD/CNY Exchange Rate")
        usdcny_layout = QVBoxLayout(usdcny_group)
        self.usdcny_response_text = QTextEdit()
        self.usdcny_response_text.setMaximumHeight(150)  # Increased from 120
        self.usdcny_response_text.setStyleSheet("font-family: 'Courier New'; font-size: 12px;")  # Increased from 10px
        usdcny_layout.addWidget(self.usdcny_response_text)
        row1_layout.addWidget(usdcny_group)
        
        scroll_layout.addLayout(row1_layout)
        
        # Row 2: US10Y, TIPS, VIX
        row2_layout = QHBoxLayout()
        
        # 4. 10-Year Treasury Yield
        us10y_group = QGroupBox("📈 10-Year Treasury Yield (US10Y)")
        us10y_layout = QVBoxLayout(us10y_group)
        self.us10y_response_text = QTextEdit()
        self.us10y_response_text.setMaximumHeight(150)  # Increased from 120
        self.us10y_response_text.setStyleSheet("font-family: 'Courier New'; font-size: 12px;")  # Increased from 10px
        us10y_layout.addWidget(self.us10y_response_text)
        row2_layout.addWidget(us10y_group)
        
        # 5. 10-Year TIPS Yield
        tips_group = QGroupBox("📊 10-Year TIPS Yield (US10YTIP)")
        tips_layout = QVBoxLayout(tips_group)
        self.tips_response_text = QTextEdit()
        self.tips_response_text.setMaximumHeight(150)  # Increased from 120
        self.tips_response_text.setStyleSheet("font-family: 'Courier New'; font-size: 12px;")  # Increased from 10px
        tips_layout.addWidget(self.tips_response_text)
        row2_layout.addWidget(tips_group)
        
        # 6. Volatility Index (VIX)
        vix_group = QGroupBox("⚡ Volatility Index (VIX)")
        vix_layout = QVBoxLayout(vix_group)
        self.vix_response_text = QTextEdit()
        self.vix_response_text.setMaximumHeight(150)  # Increased from 120
        self.vix_response_text.setStyleSheet("font-family: 'Courier New'; font-size: 12px;")  # Increased from 10px
        vix_layout.addWidget(self.vix_response_text)
        row2_layout.addWidget(vix_group)
        
        scroll_layout.addLayout(row2_layout)
        
        # Row 3: GLD (single box, centered)
        row3_layout = QHBoxLayout()
        row3_layout.addStretch()  # Left spacing
        
        # 7. Gold ETF (GLD) - centered in its own row
        gld_group = QGroupBox("🏅 Gold ETF (GLD)")
        gld_layout = QVBoxLayout(gld_group)
        self.gld_response_text = QTextEdit()
        self.gld_response_text.setMaximumHeight(150)  # Increased from 120
        self.gld_response_text.setStyleSheet("font-family: 'Courier New'; font-size: 12px;")  # Increased from 10px
        gld_layout.addWidget(self.gld_response_text)
        gld_group.setMaximumWidth(400)  # Limit width so it doesn't stretch too much
        row3_layout.addWidget(gld_group)
        
        row3_layout.addStretch()  # Right spacing
        scroll_layout.addLayout(row3_layout)
        
        # Setup scroll area
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(500)  # Increased from 400 to accommodate larger boxes
        raw_main_layout.addWidget(scroll_area)
        
        api_layout.addWidget(raw_main_group)
        
        tab_widget.addTab(api_tab, "🔌 API Info")
        
        main_layout.addWidget(tab_widget)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("🔄 Refresh Now")
        self.refresh_button.setObjectName("refreshButton")
        self.refresh_button.clicked.connect(self.manual_refresh)
        
        self.toggle_timer_button = QPushButton("⏸️ Pause Auto-Refresh")
        self.toggle_timer_button.setObjectName("toggleButton")
        self.toggle_timer_button.clicked.connect(self.toggle_auto_refresh)
        
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.toggle_timer_button)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #1e1e1e;
                color: #ffffff;
                border-top: 1px solid #555;
                font-size: 12px;
                padding: 2px;
            }
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Gold Price Predictor with Real-time Tanshu API")
    
    def create_price_chart(self, historical_data):
        """Create a price chart from historical data"""
        if not MATPLOTLIB_AVAILABLE:
            self.chart_status_label.setText("📊 Matplotlib not available - charts disabled")
            return
            
        try:
            # Clear existing chart
            for child in self.chart_widget.findChildren(FigureCanvas):
                child.deleteLater()
            
            # Parse historical data
            if not historical_data or 'data' not in historical_data or 'list' not in historical_data['data']:
                self.chart_status_label.setText("📊 Could not parse historical data")
                return
                
            data_list = historical_data['data']['list']
            
            if not data_list:
                self.chart_status_label.setText("📊 No historical data available")
                return
            
            # Extract dates and prices
            dates = []
            prices = []
            
            for i, item in enumerate(data_list):
                try:
                    # The API returns 'day_time' instead of 'date' for timestamp
                    timestamp_field = 'day_time' if 'day_time' in item else 'date'
                    timestamp = int(item[timestamp_field])
                    date = datetime.fromtimestamp(timestamp)
                    dates.append(date)
                    
                    # Use closing price (API returns it as string)
                    price = float(item['close'])
                    prices.append(price)
                    
                except (ValueError, KeyError):
                    continue
            
            if not dates or not prices:
                self.chart_status_label.setText("📊 Could not parse historical data")
                return
            
            # Sort by date (oldest to newest)
            combined = list(zip(dates, prices))
            combined.sort(key=lambda x: x[0])
            dates, prices = zip(*combined)
            
            # Create matplotlib figure with better sizing
            fig = Figure(figsize=(10, 5), facecolor='#2b2b2b')  # Increased height from 4 to 5
            ax = fig.add_subplot(111)
            
            # Style the plot
            ax.set_facecolor('#2b2b2b')
            ax.plot(dates, prices, color='#FFD700', linewidth=2, marker='o', markersize=4)
            ax.set_title('Gold Price Trend', color='white', fontsize=14, fontweight='bold')
            ax.set_xlabel('Date', color='white', fontsize=11)
            ax.set_ylabel('Price (USD/oz)', color='white', fontsize=11)
            
            # Format dates on x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            
            # Style ticks and grid
            ax.tick_params(colors='white', labelsize=9)
            ax.grid(True, alpha=0.3, color='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['right'].set_color('white')
            ax.spines['left'].set_color('white')
            
            # Rotate date labels for better readability
            fig.autofmt_xdate()
            
            # Tight layout with padding to prevent label cutoff
            fig.tight_layout(pad=2.0)  # Added padding
            
            # Create canvas and add to widget
            canvas = FigureCanvas(fig)
            canvas.setParent(self.chart_widget)
            canvas.setGeometry(0, 0, self.chart_widget.width(), self.chart_widget.height())
            canvas.show()
            
            # Update status and change statistics
            price_change = prices[-1] - prices[0] if len(prices) > 1 else 0
            change_percent = (price_change / prices[0] * 100) if len(prices) > 1 and prices[0] != 0 else 0
            change_color = "#FF4444" if price_change >= 0 else "#00FF00"  # Red for positive, Green for negative
            self.chart_status_label.setText(
                f"📊 30-Day Total Change: <span style='color: {change_color};'>${price_change:+.2f} ({change_percent:+.1f}%)</span>"
            )
            
            # Calculate 3-day and 7-day changes
            self.update_change_statistics(prices, dates)
            
        except Exception as e:
            print(f"❌ Error creating chart: {e}")
            self.chart_status_label.setText(f"📊 Chart error: {str(e)}")
            
    def update_change_statistics(self, prices, dates):
        """Update 3-day and 7-day change statistics"""
        try:
            current_price = prices[-1] if prices else 0
            
            # Calculate 3-day change
            if len(prices) >= 4:  # Need at least 4 data points
                price_3days_ago = prices[-4]
                change_3day = current_price - price_3days_ago
                change_3day_percent = (change_3day / price_3days_ago * 100) if price_3days_ago != 0 else 0
                change_3day_color = "#FF4444" if change_3day >= 0 else "#00FF00"
                self.change_3day_label.setText(f"3-Day: <span style='color: {change_3day_color};'>${change_3day:+.2f}<br>({change_3day_percent:+.1f}%)</span>")
                self.change_3day_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; text-align: center;")
            else:
                self.change_3day_label.setText("3-Day: --")
                
            # Calculate 7-day change  
            if len(prices) >= 8:  # Need at least 8 data points
                price_7days_ago = prices[-8]
                change_7day = current_price - price_7days_ago
                change_7day_percent = (change_7day / price_7days_ago * 100) if price_7days_ago != 0 else 0
                change_7day_color = "#FF4444" if change_7day >= 0 else "#00FF00"
                self.change_7day_label.setText(f"7-Day: <span style='color: {change_7day_color};'>${change_7day:+.2f}<br>({change_7day_percent:+.1f}%)</span>")
                self.change_7day_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; text-align: center;")
            else:
                self.change_7day_label.setText("7-Day: --")
                
            # Calculate 30-day change (full period)
            if len(prices) >= 2:  # Need at least 2 data points
                price_30days_ago = prices[0]  # First price in the dataset
                change_30day = current_price - price_30days_ago
                change_30day_percent = (change_30day / price_30days_ago * 100) if price_30days_ago != 0 else 0
                change_30day_color = "#FF4444" if change_30day >= 0 else "#00FF00"
                self.change_30day_label.setText(f"30-Day: <span style='color: {change_30day_color};'>${change_30day:+.2f}<br>({change_30day_percent:+.1f}%)</span>")
                self.change_30day_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; text-align: center;")
            else:
                self.change_30day_label.setText("30-Day: --")
                
        except Exception as e:
            print(f"❌ Error updating change statistics: {e}")
            self.change_3day_label.setText("3-Day: --")
            self.change_7day_label.setText("7-Day: --")
            self.change_30day_label.setText("30-Day: --")
    
    def setup_timer(self):
        """Setup auto-refresh timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(30000)  # 30 seconds
        self.timer_active = True
        
        # Initial data load
        self.refresh_data()
    
    def refresh_data(self, force_refresh=False):
        """Smart multi-tier refresh system"""
        if self.data_worker and self.data_worker.isRunning():
            return  # Don't start new request if one is already running
        
        from datetime import datetime, timedelta
        now = datetime.now()
        self.refresh_count += 1
        
        # Determine what type of refresh to perform
        refresh_type = "price_only"  # Default: just price and trading status
        fetch_historical = False
        fetch_market_factors = False
        
        # First load: get everything
        if not self.initial_load_complete or force_refresh:
            refresh_type = "full"
            fetch_historical = True
            fetch_market_factors = True
            print(f"🚀 [{now.strftime('%H:%M:%S')}] Initial/Force refresh - fetching all data")
            
        # Market factors refresh (every 10 minutes)
        elif (self.last_market_factors_refresh is None or 
              (now - self.last_market_factors_refresh).total_seconds() >= self.market_factors_interval):
            refresh_type = "market_factors"
            fetch_market_factors = True
            self.last_market_factors_refresh = now
            print(f"📊 [{now.strftime('%H:%M:%S')}] Market factors refresh (every 10 min)")
            
        # Regular price refresh (every 30 seconds)
        else:
            print(f"💰 [{now.strftime('%H:%M:%S')}] Price-only refresh (30 sec interval)")
        
        # Update status
        if force_refresh:
            self.status_bar.showMessage(f"Force refreshing data... (#{self.refresh_count})")
        else:
            self.status_bar.showMessage(f"Refresh #{self.refresh_count} - {refresh_type}")
            
        self.refresh_button.setEnabled(False)
        
        # Create worker with appropriate settings
        self.data_worker = GoldDataWorker(
            self.predictor, 
            force_refresh, 
            fetch_historical, 
            fetch_market_factors,
            refresh_type
        )
        self.data_worker.data_updated.connect(self.update_display)
        self.data_worker.error_occurred.connect(self.handle_error)
        self.data_worker.finished.connect(lambda: self.refresh_button.setEnabled(True))
        self.data_worker.start()
    
    def update_display(self, data):
        """Update the GUI with new data"""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime('%H:%M:%S')
            refresh_type = data.get('refresh_type', 'unknown')
            
            print(f"🔄 [{timestamp}] Updating display for {refresh_type} refresh...")
            
            # Always update price and basic info
            usd_price = data['current_price_usd']
            source = data['source']
            
            # Store USD price data
            self.usd_price_data = usd_price
            
            # Update USD price display
            self.price_label.setText(f"${usd_price:.2f}/oz")
            
            # Calculate and display CNY conversion
            try:
                conversion = self.predictor.financial_scraper.convert_gold_to_cny_per_gram(usd_price)
                if conversion:
                    self.cny_price_data = conversion
                    self.cny_price_label.setText(f"¥{conversion['cny_per_gram']:.2f}/g")
                    self.usd_cny_rate_label.setText(f"{conversion['usd_cny_rate']:.4f}")
                else:
                    self.cny_price_label.setText("Conversion Failed")
                    self.usd_cny_rate_label.setText("N/A")
            except Exception as e:
                print(f"⚠️ [{timestamp}] CNY conversion failed: {e}")
                self.cny_price_label.setText("Conversion Error")
                self.usd_cny_rate_label.setText("N/A")
            
            self.source_label.setText(f"📊 Source: {source}")
            self.timestamp_label.setText(f"⏰ Last Update: {data['timestamp']}")
            
            # Always update trading status
            schedule = data['schedule']
            trading_status = "✅ OPEN" if schedule['is_trading_hours'] else "❌ CLOSED"
            self.trading_status_label.setText(f"🏪 Trading Status: {trading_status}")
            self.london_time_label.setText(f"🇬🇧 London Time: {schedule['london_time'].strftime('%H:%M:%S')}")
            
            # Update market factors and other data only if available
            if data.get('market_factors') and refresh_type in ["full", "market_factors"]:
                print(f"📊 [{timestamp}] Updating market factors...")
                self.update_market_factors(data)
                
                # Update API info
                self.optimal_interval_label.setText(f"⏱️ Optimal Interval: {schedule['optimal_interval_minutes']} minutes")
                self.trading_days_label.setText(f"📅 Trading Days Left: ~{schedule['estimated_trading_days_remaining']}")
                
                # Update API status
                api_status = "🟢 Active" if schedule['is_trading_hours'] else "🟡 Paused (Outside hours)"
                self.api_status_label.setText(f"API Status: {api_status}")
                
                # Update error status - check for API errors
                error_info = self.predictor.get_last_error_info()
                if error_info:
                    self.error_status_label.setText("❌ API Error Detected")
                    self.error_status_label.setStyleSheet("color: #FF6B6B; font-weight: bold;")
                    self.error_code_label.setText(f"Error Code: {error_info['error_code']}")
                    self.error_description_label.setText(f"Description: {error_info['description']}")
                    self.error_description_label.setStyleSheet("color: #FFB6C1; font-weight: normal;")
                else:
                    self.error_status_label.setText("✅ No errors detected")
                    self.error_status_label.setStyleSheet("color: #90EE90; font-weight: bold;")
                    self.error_code_label.setText("Error Code: None")
                    self.error_description_label.setText("Description: All systems operational")
                    self.error_description_label.setStyleSheet("color: #87CEEB; font-weight: normal;")
                
                # Update raw API responses for all data sources
                raw_response = self.predictor.get_raw_api_response()
                self.update_raw_api_sections(raw_response)
            
            # Update historical price chart and cache historical data (only on full refresh)
            if data.get('historical_data') and refresh_type == "full":
                print(f"📈 [{timestamp}] Updating historical chart and technical indicators...")
                self.cached_historical_data = data['historical_data']  # Cache for technical indicators
                self.create_price_chart(data['historical_data'])
                
                # Update technical indicators dashboard (use cached data)
                self.update_technical_indicators()
                
                # Mark initial load as complete after first successful update
                if not self.initial_load_complete:
                    self.initial_load_complete = True
                    self.last_technical_indicators_refresh = datetime.now()
                    
            elif refresh_type == "full" and 'historical_data' in data:
                self.chart_status_label.setText("📊 No historical data available")
            
            # For price-only refreshes, technical indicators use cached data (no refresh needed)
            elif refresh_type == "price_only" and hasattr(self, 'cached_historical_data') and self.cached_historical_data:
                # Technical indicators don't need updating for price-only refresh
                print(f"💰 [{timestamp}] Price-only refresh - technical indicators using cached data")
            
            self.status_bar.showMessage(f"✅ {refresh_type.title()} refresh completed at {data['timestamp']}")
            
        except Exception as e:
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"❌ [{timestamp}] Display update error: {str(e)}")
            self.handle_error(f"Display update error: {str(e)}")
    
    def update_technical_indicators(self):
        """Update the technical indicators dashboard"""
        try:
            # Debug: Check if technical engine exists
            if not hasattr(self, 'technical_engine') or self.technical_engine is None:
                self.overall_sentiment_label.setText("Error: Technical engine not initialized")
                return
            
            # Get comprehensive analysis (use cached data if available)
            analysis_result = self.technical_engine.get_comprehensive_analysis(
                days=80, 
                historical_data=self.cached_historical_data
            )
            
            # Handle the result properly
            if analysis_result is None:
                self.overall_sentiment_label.setText("Error: Unable to get analysis")
                return
            
            # Check if we got a tuple with data
            if isinstance(analysis_result, tuple) and len(analysis_result) == 2:
                table_data, overall_data = analysis_result
                
                if table_data is None:
                    self.overall_sentiment_label.setText(f"Error: {overall_data}")
                    return
            else:
                self.overall_sentiment_label.setText(f"Error: Invalid analysis format (got {type(analysis_result)})")
                return
            
            # Update overall sentiment
            if not isinstance(overall_data, dict):
                self.overall_sentiment_label.setText("Error: Invalid overall data format")
                return
                
            sentiment = overall_data.get('sentiment', 'Unknown')
            icon = overall_data.get('icon', '📊')
            score = overall_data.get('score', 0.0)
            current_price = overall_data.get('current_price', 0.0)
            
            # Color coding for sentiment
            sentiment_colors = {
                "Strong Buy": "#00FF00",    # Bright green
                "Buy": "#90EE90",           # Light green
                "Neutral": "#FFD700",       # Gold
                "Sell": "#FFA500",          # Orange
                "Strong Sell": "#FF4444"    # Red
            }
            
            sentiment_color = sentiment_colors.get(sentiment, "#FFD700")
            
            self.overall_sentiment_label.setText(f"{icon} {sentiment}")
            self.overall_sentiment_label.setStyleSheet(f"""
                font-size: 18px; 
                font-weight: bold; 
                color: {sentiment_color}; 
                background-color: #2b2b2b; 
                padding: 10px; 
                border: 2px solid #555; 
                border-radius: 5px;
                text-align: center;
            """)
            
            self.sentiment_score_label.setText(f"Score: {score:+.2f}")
            
            # Update indicators table
            self.indicators_table.setRowCount(len(table_data))
            
            for row, indicator_info in enumerate(table_data):
                # Indicator name
                indicator_item = QTableWidgetItem(indicator_info['indicator'])
                indicator_item.setForeground(QColor(255, 255, 255))
                self.indicators_table.setItem(row, 0, indicator_item)
                
                # Value
                value_item = QTableWidgetItem(indicator_info['value'])
                value_item.setForeground(QColor(255, 215, 0))  # Gold color
                self.indicators_table.setItem(row, 1, value_item)
                
                # Signal icon
                signal_item = QTableWidgetItem(indicator_info['icon'])
                self.indicators_table.setItem(row, 2, signal_item)
                
                # Category with color coding
                category = indicator_info['category']
                category_item = QTableWidgetItem(category)
                # Convert hex color to QColor for setForeground
                if category == "Strong Buy":
                    category_item.setForeground(QColor(0, 255, 0))
                elif category == "Buy":
                    category_item.setForeground(QColor(144, 238, 144))
                elif category == "Neutral":
                    category_item.setForeground(QColor(255, 215, 0))
                elif category == "Sell":
                    category_item.setForeground(QColor(255, 165, 0))
                elif category == "Strong Sell":
                    category_item.setForeground(QColor(255, 68, 68))
                else:
                    category_item.setForeground(QColor(255, 215, 0))
                self.indicators_table.setItem(row, 3, category_item)
                
                # Details/Extra info
                extra_info = indicator_info.get('extra', '')
                details_item = QTableWidgetItem(extra_info)
                details_item.setForeground(QColor(135, 206, 235))  # Sky blue
                self.indicators_table.setItem(row, 4, details_item)
            
            # Resize columns to content
            self.indicators_table.resizeColumnsToContents()
            
        except Exception as e:
            error_msg = f"Technical indicators error: {str(e)}"
            self.overall_sentiment_label.setText(error_msg)
            print(f"❌ {error_msg}")
            # Also print the full traceback for debugging
            import traceback
            traceback.print_exc()
    
    def refresh_technical_indicators(self):
        """Manual refresh of technical indicators"""
        self.overall_sentiment_label.setText("🔄 Refreshing analysis...")
        self.sentiment_score_label.setText("Score: --")
        
        # Force refresh with new data
        try:
            # Clear cache for fresh data
            self.technical_engine = TechnicalIndicatorsEngine()
            self.update_technical_indicators()
        except Exception as e:
            self.overall_sentiment_label.setText(f"Refresh Error: {str(e)}")
            print(f"❌ Manual refresh error: {e}")
    
    def update_market_factors(self, data):
        """Update all market factors display with individual sections"""
        try:
            market_factors = data.get('market_factors', {})
            prediction_signals = data.get('prediction_signals', {})
            
            # Check for enhanced financial data
            enhanced_data = market_factors.get('financial_instruments', {})
            
            if enhanced_data:
                # Enhanced multi-factor display mode - populate individual factor sections
                from datetime import datetime as dt
                
                # Update each factor section individually
                for symbol, factor_data in enhanced_data.items():
                    name = factor_data.get('name', symbol)
                    price = factor_data.get('price', 'N/A')  # Use 'price' not 'current_price'
                    change = factor_data.get('change_percent', '0%')
                    
                    # Determine color based on change direction (red for positive, green for negative)
                    if isinstance(change, str) and change != '0%':
                        if change.startswith('+'):
                            change_color = "#FF6B6B"  # Red for positive
                        elif change.startswith('-'):
                            change_color = "#00FF00"  # Green for negative
                        else:
                            change_color = "#FFD700"  # Gold for neutral
                    else:
                        change_color = "#FFD700"
                    
                    timestamp_text = f"Updated: {dt.now().strftime('%H:%M:%S')}"
                    
                    # Update specific factor labels based on symbol
                    if symbol == 'DXY':
                        self.dxy_price_label.setText(str(price))
                        self.dxy_change_label.setText(str(change))
                        self.dxy_change_label.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {change_color};")
                        self.dxy_timestamp_label.setText(timestamp_text)
                        
                    elif symbol == 'US10Y':
                        self.us10y_price_label.setText(f"{price}%")
                        self.us10y_change_label.setText(str(change))
                        self.us10y_change_label.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {change_color};")
                        self.us10y_timestamp_label.setText(timestamp_text)
                        
                    elif symbol == 'TIPS':
                        self.tips_price_label.setText(f"{price}%")
                        self.tips_change_label.setText(str(change))
                        self.tips_change_label.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {change_color};")
                        self.tips_timestamp_label.setText(timestamp_text)
                        
                    elif symbol == 'VIX':
                        self.vix_price_label.setText(str(price))
                        self.vix_change_label.setText(str(change))
                        self.vix_change_label.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {change_color};")
                        self.vix_timestamp_label.setText(timestamp_text)
                        
                    elif symbol == 'GLD':
                        self.gld_price_label.setText(f"${price}")
                        self.gld_change_label.setText(str(change))
                        self.gld_change_label.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {change_color};")
                        self.gld_timestamp_label.setText(timestamp_text)
                
                # Update multi-factor correlation analysis
                market_impact = market_factors.get('market_impact', {})
                overall_score = market_impact.get('overall_score', 0)
                confidence = market_impact.get('confidence', 0)
                recommendation = market_impact.get('recommendation', 'NEUTRAL')
                
                if recommendation == 'BUY':
                    self.correlation_status_label.setText("📈 BULLISH SIGNAL")
                    self.correlation_status_label.setStyleSheet("font-weight: bold; color: #00FF00;")
                elif recommendation == 'SELL':
                    self.correlation_status_label.setText("📉 BEARISH SIGNAL")
                    self.correlation_status_label.setStyleSheet("font-weight: bold; color: #FF6B6B;")
                else:
                    self.correlation_status_label.setText("➡️ NEUTRAL")
                    self.correlation_status_label.setStyleSheet("font-weight: bold; color: #FFD700;")
                
                self.correlation_strength_label.setText(f"Market Score: {overall_score:.2f}")
                self.gold_change_label.setText(f"Factors Tracked: {len(enhanced_data)}")
                self.usd_change_label.setText(f"Analysis Confidence: {confidence}%")
                
                # Color code confidence
                if confidence >= 70:
                    conf_color = "#00FF00"
                elif confidence >= 40:
                    conf_color = "#FFD700"
                else:
                    conf_color = "#FF6B6B"
                self.usd_change_label.setStyleSheet(f"color: {conf_color};")
                
            else:
                # Legacy DXY-only display mode
                dxy_price = market_factors.get('dxy_price', 0)
                dxy_change_pct = market_factors.get('dxy_change_percent', '0%')
                dxy_timestamp = market_factors.get('dxy_timestamp', 'N/A')
                
                if dxy_price > 0:
                    self.dxy_price_label.setText(f"{dxy_price:.3f}")
                    
                    # Color code DXY change (using requested color scheme)
                    if '+' in dxy_change_pct:
                        self.dxy_change_label.setText(f"{dxy_change_pct}")
                        self.dxy_change_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #FF6B6B;")  # Red for positive
                    elif '-' in dxy_change_pct:
                        self.dxy_change_label.setText(f"{dxy_change_pct}")
                        self.dxy_change_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #00FF00;")  # Green for negative
                    else:
                        self.dxy_change_label.setText(f"{dxy_change_pct}")
                        self.dxy_change_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #FFD700;")
                    
                    # Format timestamp
                    if dxy_timestamp != 'N/A':
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(dxy_timestamp.replace('Z', '+00:00'))
                            formatted_time = dt.strftime('%H:%M:%S')
                            self.dxy_timestamp_label.setText(f"Updated: {formatted_time}")
                        except:
                            self.dxy_timestamp_label.setText(f"Updated: {dxy_timestamp[:19]}")
                    else:
                        self.dxy_timestamp_label.setText("Updated: N/A")
                else:
                    self.dxy_price_label.setText("Unavailable")
                    self.dxy_change_label.setText("N/A")
                    self.dxy_timestamp_label.setText("Updated: Error")
                
                # Set other factors to loading state in legacy mode
                for prefix in ['us10y', 'tips', 'vix', 'gld']:
                    getattr(self, f'{prefix}_price_label').setText("Unavailable")
                    getattr(self, f'{prefix}_change_label').setText("N/A")
                    getattr(self, f'{prefix}_timestamp_label').setText("Legacy Mode")
                
                # Legacy correlation analysis
                correlation = market_factors.get('correlation_signal')
                if correlation:
                    if correlation['inverse_relationship']:
                        self.correlation_status_label.setText("✅ Normal Inverse")
                        self.correlation_status_label.setStyleSheet("font-weight: bold; color: #00FF00;")
                    else:
                        self.correlation_status_label.setText("⚠️ Unusual Pattern")
                        self.correlation_status_label.setStyleSheet("font-weight: bold; color: #FFB6C1;")
                    
                    strength = correlation['strength']
                    self.correlation_strength_label.setText(f"Strength: {strength:.3f}")
                    
                    gold_change = correlation['gold_change_pct']
                    dxy_change = correlation['dxy_change_pct']
                    
                    # Using requested color scheme
                    gold_color = "#FF6B6B" if gold_change > 0 else "#00FF00"
                    dxy_color = "#FF6B6B" if dxy_change > 0 else "#00FF00"
                    
                    self.gold_change_label.setText(f"Gold Change: {gold_change:+.2f}%")
                    self.gold_change_label.setStyleSheet(f"color: {gold_color};")
                    
                    self.usd_change_label.setText(f"USD Change: {dxy_change:+.2f}%")
                    self.usd_change_label.setStyleSheet(f"color: {dxy_color};")
                else:
                    self.correlation_status_label.setText("Analyzing...")
                    self.correlation_strength_label.setText("Strength: Calculating...")
                    self.gold_change_label.setText("Gold Change: Loading...")
                    self.usd_change_label.setText("USD Change: Loading...")

            # Update prediction signals (common for both modes)
            recommendation = prediction_signals.get('recommendation', 'HOLD')
            confidence = prediction_signals.get('confidence', 0)
            signals = prediction_signals.get('signals', [])
            
            # Color code recommendation
            if recommendation == 'BUY':
                rec_color = "#00FF00"  # Green
                rec_bg = "background-color: #2d5a2d;"
            elif recommendation == 'SELL':
                rec_color = "#FF6B6B"  # Red
                rec_bg = "background-color: #5a2d2d;"
            else:  # HOLD
                rec_color = "#FFD700"  # Gold
                rec_bg = "background-color: #5a5a2d;"
            
            self.recommendation_label.setText(recommendation)
            self.recommendation_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {rec_color}; padding: 8px; border: 2px solid #666; border-radius: 5px; {rec_bg}")
            
            # Only show confidence in AI prediction section (remove duplicate)
            if confidence >= 50:
                conf_color = "#00FF00"  # High confidence - green
            elif confidence >= 25:
                conf_color = "#FFD700"  # Medium confidence - yellow
            else:
                conf_color = "#FF6B6B"  # Low confidence - red
            
            self.confidence_label.setText(f"Confidence: {confidence}%")
            self.confidence_label.setStyleSheet(f"font-size: 12px; color: {conf_color};")
            
            # Enhanced signals text with factor analysis
            signals_list = []
            
            # Add main signals
            if signals:
                signals_list.extend([f"• {signal}" for signal in signals])
            
            # Add factor analysis if available
            factor_analysis = prediction_signals.get('factor_analysis', {})
            if factor_analysis:
                signals_list.append("\n🔍 Factor Impact:")
                for symbol, analysis in factor_analysis.items():
                    impact = analysis['impact_on_gold']
                    significance = analysis['significance']
                    change_pct = analysis['change_percent']
                    
                    # Use emoji based on impact
                    if impact == 'bullish':
                        emoji = "📈"
                    elif impact == 'bearish':
                        emoji = "📉"
                    else:
                        emoji = "➡️"
                    
                    signals_list.append(f"  {emoji} {symbol}: {impact.upper()} ({change_pct:+.2f}%)")
            
            # Overall score if available
            overall_score = prediction_signals.get('overall_score')
            if overall_score is not None:
                signals_list.append(f"\n📊 Market Score: {overall_score:.2f}")
            
            if not signals_list:
                signals_list = ["• No significant signals detected", "• Market conditions stable", "• Continue monitoring"]
            
            signals_text = "\n".join(signals_list)
            self.signals_text.setPlainText(signals_text)
            
        except Exception as e:
            print(f"Error updating market factors: {e}")
            import traceback
            traceback.print_exc()
            # Set default values on error
            self.dxy_price_label.setText("Error")
            self.correlation_status_label.setText("Error")
            self.recommendation_label.setText("ERROR")
            self.signals_text.setPlainText(f"Error loading prediction data: {str(e)}")
            
        except Exception as e:
            print(f"Error updating market factors: {e}")
            # Set default values on error
            self.dxy_price_label.setText("Error")
            self.correlation_status_label.setText("Error")
            self.recommendation_label.setText("ERROR")
            self.signals_text.setPlainText(f"Error loading prediction data: {str(e)}")
    
    def update_raw_api_sections(self, raw_response):
        """Update individual raw API response sections"""
        try:
            if 'sources' in raw_response:
                sources = raw_response['sources']
                
                # 1. Gold Price (XAU=)
                if 'XAU_Gold' in sources:
                    self.gold_response_text.setPlainText(json.dumps(sources['XAU_Gold'], indent=2, ensure_ascii=False))
                else:
                    self.gold_response_text.setPlainText('{"error": "Gold data not available"}')
                
                # 2. US Dollar Index (DXY)
                if 'DXY_Index' in sources:
                    self.dxy_response_text.setPlainText(json.dumps(sources['DXY_Index'], indent=2, ensure_ascii=False))
                else:
                    self.dxy_response_text.setPlainText('{"error": "DXY data not available"}')
                
                # 3. USD/CNY Exchange Rate  
                if 'USD_CNY' in sources:
                    self.usdcny_response_text.setPlainText(json.dumps(sources['USD_CNY'], indent=2, ensure_ascii=False))
                else:
                    self.usdcny_response_text.setPlainText('{"error": "USD/CNY data not available"}')
                
                # 4. 10-Year Treasury Yield
                if 'US10Y_Data' in sources:
                    self.us10y_response_text.setPlainText(json.dumps(sources['US10Y_Data'], indent=2, ensure_ascii=False))
                else:
                    self.us10y_response_text.setPlainText('{"error": "US10Y data not available"}')
                
                # 5. 10-Year TIPS Yield
                if 'US10YTIP_Data' in sources:
                    self.tips_response_text.setPlainText(json.dumps(sources['US10YTIP_Data'], indent=2, ensure_ascii=False))
                else:
                    self.tips_response_text.setPlainText('{"error": "TIPS data not available"}')
                
                # 6. Volatility Index (VIX)
                if 'VIX_Data' in sources:
                    self.vix_response_text.setPlainText(json.dumps(sources['VIX_Data'], indent=2, ensure_ascii=False))
                else:
                    self.vix_response_text.setPlainText('{"error": "VIX data not available"}')
                
                # 7. Gold ETF (GLD)
                if 'GLD_Data' in sources:
                    self.gld_response_text.setPlainText(json.dumps(sources['GLD_Data'], indent=2, ensure_ascii=False))
                else:
                    self.gld_response_text.setPlainText('{"error": "GLD data not available"}')
            else:
                # Fallback if response format is unexpected
                error_text = json.dumps(raw_response, indent=2, ensure_ascii=False)
                self.gold_response_text.setPlainText(error_text)
                self.dxy_response_text.setPlainText('{"error": "Unexpected response format"}')
                self.usdcny_response_text.setPlainText('{"error": "Unexpected response format"}')
                self.us10y_response_text.setPlainText('{"error": "Unexpected response format"}')
                self.tips_response_text.setPlainText('{"error": "Unexpected response format"}')
                self.vix_response_text.setPlainText('{"error": "Unexpected response format"}')
                self.gld_response_text.setPlainText('{"error": "Unexpected response format"}')
                
        except Exception as e:
            error_msg = f'{{"error": "Failed to update API sections: {str(e)}"}}'
            self.gold_response_text.setPlainText(error_msg)
            self.dxy_response_text.setPlainText(error_msg)
            self.usdcny_response_text.setPlainText(error_msg)
            self.us10y_response_text.setPlainText(error_msg)
            self.tips_response_text.setPlainText(error_msg)
            self.vix_response_text.setPlainText(error_msg)
            self.gld_response_text.setPlainText(error_msg)
    
    def handle_error(self, error_message):
        """Handle errors from data collection"""
        self.status_bar.showMessage(f"❌ Error: {error_message}")
        print(f"Error: {error_message}")
        
        # Update error display with current error information
        error_info = self.predictor.get_last_error_info()
        if error_info:
            self.error_status_label.setText("❌ API Error Detected")
            self.error_status_label.setStyleSheet("color: #FF6B6B; font-weight: bold;")
            self.error_code_label.setText(f"Error Code: {error_info['error_code']}")
            self.error_description_label.setText(f"Description: {error_info['description']}")
            self.error_description_label.setStyleSheet("color: #FFB6C1; font-weight: normal;")
        else:
            # Show generic error if no specific API error code
            self.error_status_label.setText("❌ General Error")
            self.error_status_label.setStyleSheet("color: #FF6B6B; font-weight: bold;")
            self.error_code_label.setText("Error Code: N/A")
            self.error_description_label.setText(f"Description: {error_message}")
            self.error_description_label.setStyleSheet("color: #FFB6C1; font-weight: normal;")
    
    def manual_refresh(self):
        """Manual refresh button handler - forces fresh API call"""
        self.refresh_data(force_refresh=True)
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh timer"""
        if self.timer_active:
            self.timer.stop()
            self.toggle_timer_button.setText("▶️ Resume Auto-Refresh")
            self.timer_active = False
            self.status_bar.showMessage("Auto-refresh paused")
        else:
            self.timer.start(30000)
            self.toggle_timer_button.setText("⏸️ Pause Auto-Refresh")
            self.timer_active = True
            self.status_bar.showMessage("Auto-refresh resumed")
    
    def closeEvent(self, event):
        """Handle application close"""
        if self.data_worker and self.data_worker.isRunning():
            self.data_worker.quit()
            self.data_worker.wait()
        event.accept()
    
    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        # Resize chart canvas if it exists
        if hasattr(self, 'chart_widget'):
            for canvas in self.chart_widget.findChildren(FigureCanvas):
                canvas.setGeometry(0, 0, self.chart_widget.width(), self.chart_widget.height())

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Gold Price Predictor")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Gold Analytics")
    
    # Create and show main window
    window = GoldPredictorGUI()
    window.show()
    
    print("🚀 Gold Price Predictor GUI Started!")
    print("📊 Real-time data from London Gold Market")
    print("⏰ Auto-refresh every 30 seconds")
    print("🔌 Smart API usage during London trading hours")
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
