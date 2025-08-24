import os
from datetime import time

class Config:
    # API Settings
    API_DEMO_URL = "https://api.pocketoption.com/demo"
    API_REAL_URL = "https://api.pocketoption.com"
    
    # Telegram Settings
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your_bot_token_here')
    TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', '@your_channel_here')
    TELEGRAM_GROUP_ID = os.getenv('TELEGRAM_GROUP_ID', '-1001234567890')
    
    # Trading parameters
    INITIAL_BALANCE = 10.0
    TRADE_AMOUNT = 0.10
    ASSETS = ["EURUSD", "GBPUSD", "USDJPY", "BTCUSD", "ETHUSD"]
    EXPIRY_TIME = 60
    TRADE_TYPE = "binary"
    
    # Model parameters
    CONFIDENCE_THRESHOLD = 0.65
    RETRAIN_INTERVAL = 100
    WARMUP_PERIOD = 50
    
    # Risk management
    MAX_DAILY_LOSS = 0.5
    MAX_DRAWDOWN = 1.0
    STOP_LOSS_STREAK = 5
    
    # Data collection
    TICK_HISTORY = 1000
    
    # Trading schedule
    TRADING_HOURS = {
        "start": time(8, 0),   # 8:00 AM
        "end": time(20, 0)     # 8:00 PM
    }
