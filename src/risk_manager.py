import pandas as pd
from datetime import datetime, time
import logging
from config.settings import Config

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self):
        self.balance = Config.INITIAL_BALANCE
        self.initial_balance = Config.INITIAL_BALANCE
        self.trades = []
        self.consecutive_losses = 0
        self.daily_profit = 0
        self.last_trade_time = None
        self.daily_trades = 0
        self.max_daily_trades = 50  # Limit daily trades to prevent over-trading
        
    def can_trade(self, prediction_confidence):
        """Check if we're allowed to trade based on risk rules"""
        current_time = datetime.now()
        
        # Check if we've exceeded daily loss limit
        if self.daily_profit <= -Config.MAX_DAILY_LOSS:
            logger.warning("Daily loss limit exceeded. Stopping trading for today.")
            return False
            
        # Check if we've exceeded maximum drawdown
        if self.balance <= self.initial_balance - Config.MAX_DRAWDOWN:
            logger.warning("Maximum drawdown exceeded. Stopping trading.")
            return False
            
        # Check if we've hit too many consecutive losses
        if self.consecutive_losses >= Config.STOP_LOSS_STREAK:
            logger.warning("Too many consecutive losses. Taking a break.")
            return False
            
        # Check confidence threshold
        if prediction_confidence < Config.CONFIDENCE_THRESHOLD:
            return False
            
        # Check if we've exceeded daily trade limit
        if self.daily_trades >= self.max_daily_trades:
            logger.warning("Daily trade limit exceeded.")
            return False
            
        # Check trading hours
        current_time_obj = current_time.time()
        if not (Config.TRADING_HOURS["start"] <= current_time_obj <= Config.TRADING_HOURS["end"]):
            logger.warning("Outside trading hours.")
            return False
            
        # If it's a new day, reset daily counters
        if self.last_trade_time and self.last_trade_time.date() != current_time.date():
            self.daily_profit = 0
            self.daily_trades = 0
            self.consecutive_losses = 0
            logger.info("New trading day started. Reset daily counters.")
            
        return True
    
    def record_trade(self, amount, outcome, profit):
        """Record trade results and update balances"""
        self.balance += profit
        self.daily_profit += profit
        self.daily_trades += 1
        
        trade_record = {
            'time': datetime.now(),
            'amount': amount,
            'outcome': outcome,
            'profit': profit,
            'balance': self.balance,
            'daily_profit': self.daily_profit,
            'daily_trades': self.daily_trades
        }
        
        self.trades.append(trade_record)
        self.last_trade_time = datetime.now()
        
        if outcome == 'win':
            self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1
            
        logger.info(f"Trade recorded: {outcome}, Profit: ${profit:.2f}, Balance: ${self.balance:.2f}")
        return trade_record
        
    def get_performance_stats(self):
        """Calculate performance statistics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'win_rate': 0,
                'total_profit': 0,
                'profit_percentage': 0,
                'consecutive_losses': self.consecutive_losses,
                'daily_profit': self.daily_profit,
                'daily_trades': self.daily_trades
            }
            
        wins = [t for t in self.trades if t['outcome'] == 'win']
        total_profit = self.balance - self.initial_balance
        profit_percentage = (total_profit / self.initial_balance) * 100
        
        return {
            'total_trades': len(self.trades),
            'winning_trades': len(wins),
            'win_rate': (len(wins) / len(self.trades)) * 100 if self.trades else 0,
            'total_profit': total_profit,
            'profit_percentage': profit_percentage,
            'consecutive_losses': self.consecutive_losses,
            'daily_profit': self.daily_profit,
            'daily_trades': self.daily_trades
        }
        
    def get_daily_trades(self, date=None):
        """Get trades for a specific date (default: today)"""
        if date is None:
            date = datetime.now().date()
            
        return [t for t in self.trades if t['time'].date() == date]
