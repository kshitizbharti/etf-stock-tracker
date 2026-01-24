#!/usr/bin/env python3
"""
Standalone ETF Tracker Script
Can be run independently without FastAPI server
Perfect for GitHub Actions or scheduled tasks
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging
from datetime import datetime
import pytz

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from etf_tracker import ETFTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run ETF tracking"""
    
    # Get credentials from environment
    telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not telegram_token or not telegram_chat_id:
        logger.error("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env or environment")
        sys.exit(1)
    
    # Create tracker instance
    tracker = ETFTracker(telegram_token, telegram_chat_id)
    
    # Check if it's market hours
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    logger.info(f"Current time (IST): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Is market hours: {tracker.is_market_hours()}")
    
    # Check if we should run (market hours check)
    if tracker.is_market_hours():
        logger.info("Market is open - checking ETF and stock prices...")
        tracker.check_all_prices()
        logger.info(f"Price check completed. Tracked {tracker.total_etfs_tracked} ETFs and {tracker.total_stocks_tracked} stocks")
    else:
        logger.info("Market is closed - skipping price check")
    
    # If it's 3:30 PM or later, send daily summary
    if now.hour == 15 and now.minute >= 30:
        logger.info("Sending daily summary...")
        tracker.send_daily_summary()
    
    # If it's before 9:00 AM on a weekday, reset tracking
    if now.hour < 9 and now.weekday() < 5:
        logger.info("Resetting daily tracking...")
        tracker.reset_daily_tracking()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error in standalone tracker: {e}", exc_info=True)
        sys.exit(1)
