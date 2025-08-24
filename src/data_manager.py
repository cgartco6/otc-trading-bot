import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import StandardScaler
import logging
from config.settings import Config

logger = logging.getLogger(__name__)

class DataManager:
    def __init__(self):
        self.ticks = pd.DataFrame(columns=['timestamp', 'price', 'volume', 'asset'])
        self.features = pd.DataFrame()
        self.labels = pd.Series(dtype=float)
        self.scaler = StandardScaler()
        
    def add_tick(self, tick_data):
        """Add new tick data to our history"""
        new_tick = pd.DataFrame([{
            'timestamp': datetime.now(),
            'price': tick_data['price'],
            'volume': tick_data.get('volume', 0),
            'asset': tick_data.get('asset', 'UNKNOWN')
        }])
        
        self.ticks = pd.concat([self.ticks, new_tick], ignore_index=True)
        
        # Keep only the most recent ticks
        if len(self.ticks) > Config.TICK_HISTORY:
            self.ticks = self.ticks.iloc[-Config.TICK_HISTORY:]
            
        return self.generate_features(tick_data['asset'])
    
    def generate_features(self, asset):
        """Generate features from tick data for a specific asset"""
        # Filter ticks for the specific asset
        asset_ticks = self.ticks[self.ticks['asset'] == asset]
        
        if len(asset_ticks) < 20:  # Need minimum data for features
            return None
            
        # Calculate simple features
        recent = asset_ticks.iloc[-20:]  # Last 20 ticks
        
        # Price velocity and acceleration
        price_changes = recent['price'].diff().dropna()
        velocity = price_changes.mean() if len(price_changes) > 0 else 0
        acceleration = price_changes.diff().mean() if len(price_changes) > 1 else 0
        
        # Micro technical indicators
        current_price = recent['price'].iloc[-1]
        min_20 = recent['price'].min()
        max_20 = recent['price'].max()
        
        # Micro RSI (simplified)
        gains = price_changes[price_changes > 0].sum() if len(price_changes) > 0 else 0
        losses = -price_changes[price_changes < 0].sum() if len(price_changes) > 0 else 0
        micro_rsi = gains / (gains + losses) if (gains + losses) > 0 else 0.5
        
        # Volume spike detection
        avg_volume = recent['volume'].mean()
        current_volume = recent['volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # Create feature vector
        features = pd.DataFrame([{
            'velocity': velocity,
            'acceleration': acceleration,
            'micro_rsi': micro_rsi,
            'volume_ratio': volume_ratio,
            'price_position': (current_price - min_20) / (max_20 - min_20) if max_20 != min_20 else 0.5,
            'hour_of_day': datetime.now().hour,
            'minute_of_hour': datetime.now().minute,
            'day_of_week': datetime.now().weekday()
        }])
        
        # Store features for training
        self.features = pd.concat([self.features, features], ignore_index=True)
        if len(self.features) > Config.TICK_HISTORY:
            self.features = self.features.iloc[-Config.TICK_HISTORY:]
            
        return features
    
    def add_label(self, outcome):
        """Add training label (1 for success, 0 for failure)"""
        self.labels = pd.concat([self.labels, pd.Series([outcome])], ignore_index=True)
        if len(self.labels) > Config.TICK_HISTORY:
            self.labels = self.labels.iloc[-Config.TICK_HISTORY:]
            
    def get_training_data(self):
        """Get features and labels for training"""
        # Ensure we have matching lengths
        min_len = min(len(self.features), len(self.labels))
        if min_len == 0:
            return None, None
            
        X = self.features.iloc[-min_len:]
        y = self.labels.iloc[-min_len:]
        
        return X, y
