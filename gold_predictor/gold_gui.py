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
                           QProgressBar, QSplitter, QTableWidget, QTableWidgetItem)
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
            
            result = {
                'current_price_usd': usd_price,
                'current_london_data': london_data,
                'source': source,
                'market_info': market_info,
                'schedule': schedule,
                'exchange_rate': self.predictor.usd_gbp_rate,
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
        
        # Tab 2: API Information
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
        self.error_description_label.setStyleSheet("color: #87CEEB; font-weight: normal; word-wrap: true;")
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
                self.error_description_label.setStyleSheet("color: #FFB6C1; font-weight: normal; word-wrap: true;")
            else:
                self.error_status_label.setText("✅ No errors detected")
                self.error_status_label.setStyleSheet("color: #90EE90; font-weight: bold;")
                self.error_code_label.setText("Error Code: None")
                self.error_description_label.setText("Description: All systems operational")
                self.error_description_label.setStyleSheet("color: #87CEEB; font-weight: normal; word-wrap: true;")
            
            # Update raw response
            raw_response = self.predictor.get_raw_api_response()
            self.raw_response_text.setPlainText(json.dumps(raw_response, indent=2, ensure_ascii=False))
            
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
            self.error_description_label.setStyleSheet("color: #FFB6C1; font-weight: normal; word-wrap: true;")
        else:
            # Show generic error if no specific API error code
            self.error_status_label.setText("❌ General Error")
            self.error_status_label.setStyleSheet("color: #FF6B6B; font-weight: bold;")
            self.error_code_label.setText("Error Code: N/A")
            self.error_description_label.setText(f"Description: {error_message}")
            self.error_description_label.setStyleSheet("color: #FFB6C1; font-weight: normal; word-wrap: true;")
    
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
