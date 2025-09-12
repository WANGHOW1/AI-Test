#!/usr/bin/env python3
"""
Gold Price Predictor GUI - Real-time Tanshu API Integration
Complete GUI application with live gold prices from Shanghai Gold Exchange
"""

import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QTextEdit, QPushButton, 
                           QTabWidget, QStatusBar, QGroupBox, QGridLayout,
                           QProgressBar, QSplitter, QTableWidget, QTableWidgetItem,
                           QScrollArea)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPalette, QColor
import json

# Import our gold predictor
from gold_predictor import GoldPricePredictor

class GoldDataWorker(QThread):
    """Background worker for gold price data collection"""
    data_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, predictor, force_refresh=False):
        super().__init__()
        self.predictor = predictor
        self.running = True
        self.force_refresh = force_refresh
        
    def run(self):
        """Collect gold price data in background thread"""
        try:
            # Get current price (with force_refresh if manual)
            usd_price, source, london_data = self.predictor.get_current_gold_price(self.force_refresh)
            
            # Get detailed market info (will use same cached data)
            market_info = self.predictor.get_detailed_market_info(self.force_refresh)
            
            # Get schedule info
            schedule = self.predictor.get_trading_schedule_info()
            
            # Get market factors including DXY
            market_factors = self.predictor.get_market_factors()
            
            # Get prediction signals
            prediction_signals = self.predictor.get_prediction_signals()
            
            result = {
                'current_price_usd': usd_price,
                'current_london_data': london_data,
                'source': source,
                'market_info': market_info,
                'schedule': schedule,
                'exchange_rate': self.predictor.usd_gbp_rate,
                'market_factors': market_factors,
                'prediction_signals': prediction_signals,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.data_updated.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(str(e))

class GoldPredictorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.predictor = GoldPricePredictor()
        self.data_worker = None
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
        header_layout = QGridLayout(header_group)
        
        # Current price display
        self.price_label = QLabel("Loading...")
        self.price_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #FFD700;")
        header_layout.addWidget(QLabel("💰 Current Gold Price:"), 0, 0)
        header_layout.addWidget(self.price_label, 0, 1)
        
        # Source and timestamp with better colors
        self.source_label = QLabel("Source: Loading...")
        self.source_label.setStyleSheet("color: #87CEEB; font-weight: bold;")
        self.timestamp_label = QLabel("Last Update: Loading...")
        self.timestamp_label.setStyleSheet("color: #DDA0DD; font-weight: bold;")
        header_layout.addWidget(self.source_label, 1, 0)
        header_layout.addWidget(self.timestamp_label, 1, 1)
        
        # Trading status with distinctive colors
        self.trading_status_label = QLabel("Trading Status: Loading...")
        self.trading_status_label.setStyleSheet("color: #90EE90; font-weight: bold;")
        self.london_time_label = QLabel("London Time: Loading...")
        self.london_time_label.setStyleSheet("color: #F0E68C; font-weight: bold;")
        header_layout.addWidget(self.trading_status_label, 2, 0)
        header_layout.addWidget(self.london_time_label, 2, 1)
        
        main_layout.addWidget(header_group)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Tab 1: Market Data
        market_tab = QWidget()
        market_layout = QVBoxLayout(market_tab)
        
        # Gold products table
        products_group = QGroupBox("📊 London Precious Metals Market")
        products_layout = QVBoxLayout(products_group)
        
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(7)
        self.products_table.setHorizontalHeaderLabels([
            "Metal", "English Name", "USD Price", "Change %", "Daily Range", "Previous Close", "Last Update"
        ])
        self.products_table.setAlternatingRowColors(True)
        products_layout.addWidget(self.products_table)
        
        market_layout.addWidget(products_group)
        
        # Exchange rate info
        rate_group = QGroupBox("💱 Exchange Rate Information")
        rate_layout = QGridLayout(rate_group)
        
        self.exchange_rate_label = QLabel("1 USD = Loading... GBP")
        self.exchange_rate_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #87CEEB;")
        rate_layout.addWidget(QLabel("Current Exchange Rate:"), 0, 0)
        rate_layout.addWidget(self.exchange_rate_label, 0, 1)
        
        market_layout.addWidget(rate_group)
        
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
        
        # Raw API response
        raw_group = QGroupBox("📄 Raw API Response")
        raw_layout = QVBoxLayout(raw_group)
        
        self.raw_response_text = QTextEdit()
        self.raw_response_text.setMaximumHeight(300)
        raw_layout.addWidget(self.raw_response_text)
        
        api_layout.addWidget(raw_group)
        
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
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Gold Price Predictor with Real-time Tanshu API")
    
    def setup_timer(self):
        """Setup auto-refresh timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(30000)  # 30 seconds
        self.timer_active = True
        
        # Initial data load
        self.refresh_data()
    
    def refresh_data(self, force_refresh=False):
        """Refresh gold price data"""
        if self.data_worker and self.data_worker.isRunning():
            return  # Don't start new request if one is already running
        
        if force_refresh:
            self.status_bar.showMessage("Force refreshing gold price data...")
        else:
            self.status_bar.showMessage("Fetching gold price data...")
        self.refresh_button.setEnabled(False)
        
        self.data_worker = GoldDataWorker(self.predictor, force_refresh)
        self.data_worker.data_updated.connect(self.update_display)
        self.data_worker.error_occurred.connect(self.handle_error)
        self.data_worker.finished.connect(lambda: self.refresh_button.setEnabled(True))
        self.data_worker.start()
    
    def update_display(self, data):
        """Update the GUI with new data"""
        try:
            # Update main price display
            usd_price = data['current_price_usd']
            london_data = data['current_london_data']
            source = data['source']
            
            self.price_label.setText(f"${usd_price:.2f}/oz")
            self.source_label.setText(f"📊 Source: {source}")
            self.timestamp_label.setText(f"⏰ Last Update: {data['timestamp']}")
            
            # Update trading status
            schedule = data['schedule']
            trading_status = "✅ OPEN" if schedule['is_trading_hours'] else "❌ CLOSED"
            self.trading_status_label.setText(f"🏪 Trading Status: {trading_status}")
            self.london_time_label.setText(f"�� London Time: {schedule['london_time'].strftime('%H:%M:%S')}")
            
            # Update exchange rate
            exchange_rate = data['exchange_rate']
            self.exchange_rate_label.setText(f"1 USD = {exchange_rate:.4f} GBP")
            
            # Update products table
            market_info = data['market_info']
            if 'data' in market_info:
                self.update_products_table(market_info['data'])
            
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
            
            # Update raw response
            raw_response = self.predictor.get_raw_api_response()
            self.raw_response_text.setPlainText(json.dumps(raw_response, indent=2, ensure_ascii=False))
            
            # Update market factors (DXY and prediction)
            self.update_market_factors(data)
            
            self.status_bar.showMessage(f"✅ Updated successfully at {data['timestamp']}")
            
        except Exception as e:
            self.handle_error(f"Display update error: {str(e)}")
    
    def update_products_table(self, products_data):
        """Update the products table with London market data"""
        self.products_table.setRowCount(len(products_data))
        
        row = 0
        for product_code, product_info in products_data.items():
            # Metal code with proper styling
            metal_item = QTableWidgetItem(product_code)
            metal_item.setForeground(QColor(255, 255, 255))  # White text
            self.products_table.setItem(row, 0, metal_item)
            
            # English name
            name_item = QTableWidgetItem(product_info['name'])
            name_item.setForeground(QColor(255, 255, 255))  # White text
            self.products_table.setItem(row, 1, name_item)
            
            # USD Price with golden color
            price_item = QTableWidgetItem(f"${product_info['usd_price']}")
            price_item.setForeground(QColor(255, 215, 0))  # Gold color
            self.products_table.setItem(row, 2, price_item)
            
            # Color code the change percentage with better contrast
            change_item = QTableWidgetItem(product_info['change_percent'])
            if '+' in product_info['change_percent']:
                change_item.setForeground(QColor(0, 255, 0))  # Bright green text for positive
                change_item.setBackground(QColor(0, 80, 0, 80))  # Dark green background
            elif '-' in product_info['change_percent']:
                change_item.setForeground(QColor(255, 100, 100))  # Light red text for negative
                change_item.setBackground(QColor(80, 0, 0, 80))  # Dark red background
            else:
                change_item.setForeground(QColor(200, 200, 200))  # Light gray for neutral
            
            self.products_table.setItem(row, 3, change_item)
            
            # Daily range with cyan color
            daily_range = f"${product_info['low_price']} - ${product_info['high_price']}"
            range_item = QTableWidgetItem(daily_range)
            range_item.setForeground(QColor(135, 206, 235))  # Sky blue
            self.products_table.setItem(row, 4, range_item)
            
            # Previous close
            close_item = QTableWidgetItem(f"${product_info['previous_close']}")
            close_item.setForeground(QColor(255, 255, 255))  # White text
            self.products_table.setItem(row, 5, close_item)
            
            # Update time with light gray
            time_item = QTableWidgetItem(product_info['update_time'])
            time_item.setForeground(QColor(200, 200, 200))  # Light gray
            self.products_table.setItem(row, 6, time_item)
            
            row += 1
        
        # Adjust column widths
        self.products_table.resizeColumnsToContents()
    
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
