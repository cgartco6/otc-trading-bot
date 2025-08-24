import time
import requests
import json
import numpy as np
from datetime import datetime
import logging
from config.settings import Config

logger = logging.getLogger(__name__)

class PocketOptionClient:
    def __init__(self, demo_mode=True):
        self.demo_mode = demo_mode
        self.base_url = Config.API_DEMO_URL if demo_mode else Config.API_REAL_URL
        self.connected = False
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Price history for simulation
        self.price_history = {}
        for asset in Config.ASSETS:
            # Start with realistic prices
            if "USD" in asset and "BTC" not in asset and "ETH" not in asset:
                self.price_history[asset] = 1.0 + np.random.uniform(0.05, 0.3)  # Forex pairs
            elif "BTC" in asset:
                self.price_history[asset] = 50000 + np.random.uniform(-5000, 5000)  # Bitcoin
            elif "ETH" in asset:
                self.price_history[asset] = 3000 + np.random.uniform(-300, 300)  # Ethereum
            else:
                self.price_history[asset] = 100 + np.random.uniform(-10, 10)  # Other assets
        
    def connect(self):
        """Simulate connecting to API"""
        logger.info("Connecting to Pocket Option API...")
        
        # In a real implementation, this would:
        # 1. Authenticate with the API
        # 2. Get account information
        # 3. Establish a WebSocket connection for real-time data
        
        try:
            # Simulate connection delay
            time.sleep(1)
            
            # For demo purposes, we'll simulate a successful connection
            self.connected = True
            logger.info("Connected successfully to Pocket Option API!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to API: {e}")
            return False
            
    def get_current_price(self, asset):
        """Get current price for an asset (simulated)"""
        if not self.connected:
            logger.warning("Not connected to API. Cannot get price.")
            return None
            
        # In a real implementation, this would call the actual API
        # For simulation, we generate realistic price movements
        
        # Get the last price for this asset
        current_price = self.price_history.get(asset, 1.0)
        
        # Generate random but realistic price movement based on asset type
        if "BTC" in asset or "ETH" in asset:
            # Crypto has higher volatility
            change = np.random.normal(0, 0.002) * current_price
        else:
            # Forex has lower volatility
            change = np.random.normal(0, 0.0002) * current_price
            
        # Add the change to the current price
        new_price = current_price + change
        self.price_history[asset] = new_price
        
        return {
            'asset': asset,
            'price': new_price,
            'timestamp': datetime.now(),
            'volume': np.random.randint(100, 1000)  # Simulated volume
        }
        
    def place_trade(self, asset, amount, direction, expiry):
        """Place a trade (simulated)"""
        if not self.connected:
            logger.warning("Not connected to API. Cannot place trade.")
            return {'success': False, 'error': 'Not connected'}
            
        # In real implementation, this would call the Pocket Option API
        logger.info(f"Placing trade: {asset}, {direction}, ${amount}, {expiry}s expiry")
        
        # Simulate trade processing time
        time.sleep(0.5)
        
        # Simulate trade outcome 
        # In demo mode, use a higher win rate for testing
        if self.demo_mode:
            win_chance = 0.65  # 65% win rate in demo
        else:
            win_chance = 0.55  # More conservative in real mode
            
        win = np.random.random() < win_chance
        
        # Calculate payout based on direction
        if win:
            payout = amount * 0.92  # 92% payout
            outcome = "win"
        else:
            payout = -amount  # Lose the entire amount
            outcome = "loss"
            
        # Simulate occasional API errors
        if np.random.random() < 0.02:  # 2% chance of error
            return {
                'success': False,
                'error': 'API timeout',
                'outcome': 'error'
            }
            
        return {
            'success': True,
            'outcome': outcome,
            'payout': payout,
            'balance': 1000  # Simulated balance
        }
        
    def get_balance(self):
        """Get current account balance (simulated)"""
        if not self.connected:
            return 0
            
        # In a real implementation, this would call the API
        # For simulation, we'll return a fixed value
        return 1000 if self.demo_mode else self.balance
        
    def disconnect(self):
        """Disconnect from API"""
        self.connected = False
        self.session.close()
        logger.info("Disconnected from Pocket Option API.")
