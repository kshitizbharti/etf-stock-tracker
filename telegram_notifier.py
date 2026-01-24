import requests
import logging
from typing import List, Dict
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Send notifications via Telegram Bot API"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, message: str) -> bool:
        """Send a message to the configured Telegram chat
        
        Args:
            message: Message text to send
        
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("Telegram message sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def send_threshold_alert(self, item: Dict[str, any], threshold: float, item_type: str = "ETF") -> bool:
        """Send an alert for a single ETF or Stock crossing a threshold
        
        Args:
            item: Item data dict with name/symbol, price, change_percent
            threshold: The threshold that was crossed
            item_type: "ETF" or "STOCK"
        
        Returns:
            True if successful
        """
        # Get current time in IST
        ist = pytz.timezone('Asia/Kolkata')
        time_now = datetime.now(ist).strftime('%I:%M %p')
        
        if item_type == "STOCK":
            message = f"📉 <b>Stock Alert</b> 📉\n\n"
            message += f"<b>Stock:</b> {item.get('symbol', item.get('name'))}\n"
        else:
            message = f"🚨 <b>ETF Alert</b> 🚨\n\n"
            message += f"<b>ETF:</b> {item['name']}\n"
        
        message += f"<b>Change:</b> {item['change_percent']:.2f}%\n"
        if item.get('price'):
            message += f"<b>Price:</b> ₹{item['price']:.2f}\n"
        message += f"<b>Threshold:</b> {threshold}%\n"
        message += f"<b>Time:</b> {time_now}\n"
        
        return self.send_message(message)
    
    def send_daily_summary(self, etf_alerts: Dict[float, List[Dict]], stock_alerts: List[Dict], 
                           total_etfs_tracked: int, total_stocks_tracked: int) -> bool:
        """Send end-of-day summary of all ETF and stock alerts
        
        Args:
            etf_alerts: Dict mapping threshold to list of ETFs that crossed it
            stock_alerts: List of stocks that crossed -5%
            total_etfs_tracked: Total number of ETFs being tracked
            total_stocks_tracked: Total number of stocks being tracked
        
        Returns:
            True if successful
        """
        # Get current time in IST
        ist = pytz.timezone('Asia/Kolkata')
        time_now = datetime.now(ist).strftime('%I:%M %p, %d %b %Y')
        
        # Check if any items crossed thresholds
        has_etf_alerts = any(len(etfs) > 0 for etfs in etf_alerts.values())
        has_stock_alerts = len(stock_alerts) > 0
        
        if not has_etf_alerts and not has_stock_alerts:
            message = f"📊 <b>Daily Summary</b> 📊\n\n"
            message += f"✅ <b>No ETF or Stock crossed thresholds today</b>\n\n"
            message += f"ETFs tracked: {total_etfs_tracked}\n"
            message += f"Stocks tracked: {total_stocks_tracked}\n"
            message += f"Time: {time_now}"
        else:
            message = f"📊 <b>Daily Summary</b> 📊\n\n"
            
            # ETF Alerts
            if has_etf_alerts:
                message += f"<b>ETFs that crossed thresholds:</b>\n\n"
                sorted_thresholds = sorted(etf_alerts.keys(), reverse=True)
                
                for threshold in sorted_thresholds:
                    etfs = etf_alerts[threshold]
                    if etfs:
                        message += f"<b>📉 {threshold}% Threshold:</b>\n"
                        for etf in etfs:
                            message += f"  • {etf['name']}: {etf['change_percent']:.2f}%\n"
                        message += "\n"
            
            # Stock Alerts
            if has_stock_alerts:
                message += f"<b>Stocks down by 5% or more:</b>\n"
                for stock in stock_alerts:
                    message += f"  • {stock.get('symbol', stock.get('name'))}: {stock['change_percent']:.2f}%\n"
                message += "\n"
            
            message += f"ETFs tracked: {total_etfs_tracked}\n"
            message += f"Stocks tracked: {total_stocks_tracked}\n"
            message += f"Time: {time_now}"
        
        return self.send_message(message)
