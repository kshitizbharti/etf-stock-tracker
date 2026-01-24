import logging
from typing import Dict, List, Set
from datetime import datetime
import pytz
from etf_scraper import ETFScraper
from telegram_notifier import TelegramNotifier

logger = logging.getLogger(__name__)

class ETFTracker:
    """Main ETF and Stock tracking logic with threshold monitoring"""
    
    def __init__(self, telegram_token: str, telegram_chat_id: str):
        self.scraper = ETFScraper()
        self.notifier = TelegramNotifier(telegram_token, telegram_chat_id)
        
        # Thresholds to monitor for ETFs (negative percentages)
        self.etf_thresholds = [-2.5, -3.5, -5.0, -8.0, -10.0]
        
        # Stock threshold (only -5% for stocks)
        self.stock_threshold = -5.0
        
        # Track which ETFs/stocks have been alerted and at what threshold
        # Format: {symbol: threshold_alerted_at}
        self.alerted_items: Dict[str, float] = {}
        
        # Store all alerts for daily summary
        self.daily_etf_alerts: Dict[float, List[Dict]] = {t: [] for t in self.etf_thresholds}
        self.daily_stock_alerts: List[Dict] = []
        
        self.total_etfs_tracked = 0
        self.total_stocks_tracked = 0
    
    def reset_daily_tracking(self):
        """Reset tracking for a new day"""
        logger.info("Resetting daily tracking")
        self.alerted_items = {}
        self.daily_etf_alerts = {t: [] for t in self.etf_thresholds}
        self.daily_stock_alerts = []
        self.total_etfs_tracked = 0
        self.total_stocks_tracked = 0
    
    def check_etf_prices(self):
        """Main function to check ETF prices and send alerts"""
        try:
            logger.info("Starting ETF price check")
            
            # Fetch current ETF data
            etf_data = self.scraper.fetch_etf_data()
            
            if not etf_data:
                logger.warning("No ETF data fetched")
                return
            
            self.total_etfs_tracked = len(etf_data)
            logger.info(f"Tracking {self.total_etfs_tracked} ETFs")
            
            # Check each ETF
            for etf in etf_data:
                etf_name = etf['name']
                change_percent = etf['change_percent']
                
                # Find the most negative threshold this ETF crosses
                crossed_threshold = None
                for threshold in sorted(self.etf_thresholds, reverse=True):
                    if change_percent <= threshold:
                        crossed_threshold = threshold
                
                # Check if we should alert
                if crossed_threshold is not None:
                    should_alert = False
                    
                    if etf_name not in self.alerted_items:
                        # First time crossing any threshold - ALERT
                        should_alert = True
                    elif self.alerted_items[etf_name] > crossed_threshold:
                        # Crossed a MORE NEGATIVE threshold than before - ALERT
                        should_alert = True
                        logger.info(f"ETF {etf_name} crossed new threshold {crossed_threshold}% (was {self.alerted_items[etf_name]}%)")
                    # else: Already alerted at same or more negative threshold - SKIP
                    
                    if should_alert:
                        logger.info(f"ETF {etf_name} alert at {crossed_threshold}% threshold: {change_percent}%")
                        
                        # Send alert
                        self.notifier.send_threshold_alert(etf, crossed_threshold, item_type="ETF")
                        
                        # Mark as alerted at this threshold
                        self.alerted_items[etf_name] = crossed_threshold
                        
                        # Add to daily summary (avoid duplicates)
                        if not any(e['name'] == etf_name for e in self.daily_etf_alerts[crossed_threshold]):
                            self.daily_etf_alerts[crossed_threshold].append(etf.copy())
            
            logger.info("ETF price check completed")
            
        except Exception as e:
            logger.error(f"Error in check_etf_prices: {e}", exc_info=True)
    
    def check_stock_prices(self):
        """Check stock prices for -5% threshold"""
        try:
            logger.info("Starting stock price check")
            
            # Fetch current stock data
            stock_data = self.scraper.fetch_stock_data()
            
            if not stock_data:
                logger.warning("No stock data fetched")
                return
            
            self.total_stocks_tracked = len(stock_data)
            logger.info(f"Tracking {self.total_stocks_tracked} stocks")
            
            # Check each stock for -5% threshold only
            for stock in stock_data:
                stock_symbol = stock['symbol']
                change_percent = stock['change_percent']
                
                # Check if stock crossed -5% threshold
                if change_percent <= self.stock_threshold:
                    should_alert = False
                    
                    if stock_symbol not in self.alerted_items:
                        # First time crossing -5% - ALERT
                        should_alert = True
                    # If already alerted, don't alert again (stocks only have one threshold)
                    
                    if should_alert:
                        logger.info(f"Stock {stock_symbol} alert at -5% threshold: {change_percent}%")
                        
                        # Send alert
                        self.notifier.send_threshold_alert(stock, self.stock_threshold, item_type="STOCK")
                        
                        # Mark as alerted
                        self.alerted_items[stock_symbol] = self.stock_threshold
                        
                        # Add to daily summary
                        if not any(s['symbol'] == stock_symbol for s in self.daily_stock_alerts):
                            self.daily_stock_alerts.append(stock.copy())
            
            logger.info("Stock price check completed")
            
        except Exception as e:
            logger.error(f"Error in check_stock_prices: {e}", exc_info=True)
    
    def check_all_prices(self):
        """Check both ETFs and stocks"""
        self.check_etf_prices()
        self.check_stock_prices()
    
    def send_daily_summary(self):
        """Send end-of-day summary"""
        try:
            logger.info("Sending daily summary")
            self.notifier.send_daily_summary(
                self.daily_etf_alerts, 
                self.daily_stock_alerts,
                self.total_etfs_tracked,
                self.total_stocks_tracked
            )
            logger.info("Daily summary sent")
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}", exc_info=True)
    
    def is_market_hours(self) -> bool:
        """Check if current time is within market hours (9:15 AM - 3:15 PM IST, Mon-Fri)"""
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        
        # Check if it's a weekday (Monday = 0, Friday = 4)
        if now.weekday() > 4:  # Saturday = 5, Sunday = 6
            return False
        
        # Check if it's within market hours (9:15 AM to 3:15 PM)
        market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_end = now.replace(hour=15, minute=15, second=0, microsecond=0)
        
        return market_start <= now <= market_end
