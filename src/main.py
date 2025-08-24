import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# Import our modules
from config.settings import Config
from src.data_manager import DataManager
from src.trading_model import TradingModel
from src.risk_manager import RiskManager
from src.api_client import PocketOptionClient
from src.telegram_bot import TelegramBot

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OTCTradingBot:
    def __init__(self, demo_mode=True):
        self.demo_mode = demo_mode
        self.client = PocketOptionClient(demo_mode)
        self.data_manager = DataManager()
        self.model = TradingModel()
        self.risk_manager = RiskManager()
        self.telegram_bot = TelegramBot()
        self.trade_count = 0
        self.running = False
        self.current_asset = Config.ASSETS[0]
        
    def connect(self):
        """Connect to the API and initialize components"""
        try:
            if not self.client.connect():
                logger.error("Failed to connect to API")
                self.telegram_bot.send_error_alert("Failed to connect to trading API")
                return False
                
            logger.info("Initializing trading bot...")
            logger.info(f"Starting balance: ${self.risk_manager.balance:.2f}")
            
            # Try to load previous model if exists
            try:
                self.model.load_model('data/models/trading_model.pkl')
                logger.info("Loaded previously trained model")
            except:
                logger.info("No previous model found, starting fresh")
            
            # Send startup message
            self.telegram_bot.send_startup_message(
                self.demo_mode,
                self.risk_manager.balance,
                Config.ASSETS
            )
            
            return True
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            self.telegram_bot.send_error_alert(f"Initialization error: {str(e)}")
            return False
        
    def run(self):
        """Main trading loop"""
        self.running = True
        logger.info("Starting trading bot...")
        
        last_report_time = datetime.now()
        last_retrain_time = datetime.now()
        
        while self.running:
            try:
                current_time = datetime.now()
                current_time_obj = current_time.time()
                start_time = Config.TRADING_HOURS["start"]
                end_time = Config.TRADING_HOURS["end"]
                
                # Check if we're within trading hours
                if not (start_time <= current_time_obj <= end_time):
                    # Outside trading hours, sleep longer
                    if (datetime.now() - last_report_time).seconds > 3600:  # Every hour
                        logger.info("Outside trading hours. Sleeping...")
                        last_report_time = datetime.now()
                    time.sleep(300)  # Sleep for 5 minutes
                    continue
                
                # Rotate assets periodically
                if self.trade_count % 10 == 0:
                    self.current_asset = np.random.choice(Config.ASSETS)
                    logger.info(f"Switched to asset: {self.current_asset}")
                
                # Get current market price
                tick_data = self.client.get_current_price(self.current_asset)
                if tick_data is None:
                    time.sleep(1)
                    continue
                
                # Process the tick and generate features
                features = self.data_manager.add_tick(tick_data)
                
                if features is not None:
                    # Make prediction if we have enough data
                    prediction = self.model.predict(features)
                    
                    # Check if we can trade based on risk rules
                    if self.risk_manager.can_trade(prediction):
                        # Determine trade direction based on prediction
                        direction = "call" if prediction > 0.5 else "put"
                        
                        # Send signal to Telegram
                        self.telegram_bot.send_signal(
                            self.current_asset, 
                            direction, 
                            prediction, 
                            tick_data['price']
                        )
                        
                        # Place the trade
                        trade_result = self.client.place_trade(
                            self.current_asset, 
                            Config.TRADE_AMOUNT, 
                            direction, 
                            Config.EXPIRY_TIME
                        )
                        
                        if trade_result.get('success', False):
                            # Record the trade
                            self.trade_count += 1
                            outcome = 1 if trade_result['outcome'] == 'win' else 0
                            trade_record = self.risk_manager.record_trade(
                                Config.TRADE_AMOUNT,
                                trade_result['outcome'],
                                trade_result['payout']
                            )
                            
                            # Add to training data
                            self.data_manager.add_label(outcome)
                            
                            # Send result to Telegram
                            self.telegram_bot.send_trade_result(
                                self.trade_count,
                                trade_result['outcome'],
                                trade_result['payout'],
                                self.risk_manager.balance,
                                prediction
                            )
                            
                            logger.info(
                                f"Trade #{self.trade_count}: {trade_result['outcome'].upper()}! "
                                f"Profit: ${trade_result['payout']:.2f} | "
                                f"Balance: ${self.risk_manager.balance:.2f} | "
                                f"Confidence: {prediction:.2%}"
                            )
                            
                            # Retrain model periodically (but not too often)
                            if (datetime.now() - last_retrain_time).seconds > 300:  # Every 5 minutes
                                X, y = self.data_manager.get_training_data()
                                if X is not None and y is not None and len(X) >= Config.WARMUP_PERIOD:
                                    logger.info("Retraining model...")
                                    if self.model.train(X, y):
                                        last_retrain_time = datetime.now()
                                        # Save model after training
                                        self.model.save_model('data/models/trading_model.pkl')
                    
                # Send daily report at the end of the day
                if current_time.hour == 23 and current_time.minute >= 55:
                    if (datetime.now() - last_report_time).seconds > 300:  # Only once every 5 minutes
                        self.generate_daily_report()
                        last_report_time = datetime.now()
                
                # Wait before next tick
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("Stopping bot...")
                self.running = False
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                self.telegram_bot.send_error_alert(str(e))
                time.sleep(5)
                
        # Save model before shutting down
        self.model.save_model('data/models/trading_model.pkl')
        self.generate_report()
        
    def generate_daily_report(self):
        """Generate and send daily performance report"""
        # Get today's trades
        today = datetime.now().date()
        todays_trades = self.risk_manager.get_daily_trades(today)
        
        if not todays_trades:
            return
            
        wins = [t for t in todays_trades if t['outcome'] == 'win']
        total_profit = sum(t['profit'] for t in todays_trades)
        
        report_data = {
            'total_trades': len(todays_trades),
            'winning_trades': len(wins),
            'win_rate': (len(wins) / len(todays_trades)) * 100 if todays_trades else 0,
            'total_profit': total_profit,
            'ending_balance': self.risk_manager.balance
        }
        
        self.telegram_bot.send_daily_report(report_data)
        
    def generate_report(self):
        """Generate final performance report"""
        logger.info("\n" + "="*50)
        logger.info("TRADING BOT PERFORMANCE REPORT")
        logger.info("="*50)
        
        # Get performance statistics
        stats = self.risk_manager.get_performance_stats()
        stats['final_balance'] = self.risk_manager.balance
        
        if stats['total_trades'] == 0:
            logger.info("No trades were executed.")
            return
            
        # Send final report to Telegram
        self.telegram_bot.send_shutdown_message(stats)
        
        logger.info(f"Total Trades: {stats['total_trades']}")
        logger.info(f"Win Rate: {stats['win_rate']:.1f}%")
        logger.info(f"Starting Balance: ${Config.INITIAL_BALANCE:.2f}")
        logger.info(f"Ending Balance: ${self.risk_manager.balance:.2f}")
        logger.info(f"Total Profit: ${stats['total_profit']:.2f} ({stats['profit_percentage']:.1f}%)")
        logger.info(f"Consecutive Losses: {self.risk_manager.consecutive_losses}")
        
        # Plot balance curve
        if len(self.risk_manager.trades) > 1:
            times = [t['time'] for t in self.risk_manager.trades]
            balances = [t['balance'] for t in self.risk_manager.trades]
            
            plt.figure(figsize=(10, 5))
            plt.plot(times, balances)
            plt.title('Account Balance Over Time')
            plt.xlabel('Time')
            plt.ylabel('Balance ($)')
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig('logs/balance_chart.png')
            logger.info("Balance chart saved as 'logs/balance_chart.png'")

# =============================================================================
# EXECUTION STARTS HERE
# =============================================================================
if __name__ == "__main__":
    # Initialize the bot in demo mode
    bot = OTCTradingBot(demo_mode=True)
    
    # Connect to the API
    if bot.connect():
        try:
            # Start the trading bot
            bot.run()
        except Exception as e:
            logger.error(f"Fatal error in bot execution: {e}")
            bot.telegram_bot.send_error_alert(f"Fatal error: {str(e)}")
        finally:
            # Ensure we generate a report even on crash
            bot.generate_report()
