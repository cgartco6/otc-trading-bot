import requests
import logging
from datetime import datetime
from config.settings import Config

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.channel_id = Config.TELEGRAM_CHANNEL_ID
        self.group_id = Config.TELEGRAM_GROUP_ID
        
    def send_message(self, text, chat_id=None, parse_mode='HTML'):
        """Send message to Telegram"""
        if not self.bot_token or self.bot_token == 'your_bot_token_here':
            logger.warning("Telegram bot token not configured")
            return False
            
        chat_id = chat_id or self.channel_id
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        
        try:
            response = requests.post(url, data=payload, timeout=10)
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def send_signal(self, asset, direction, confidence, price):
        """Send trading signal to channel"""
        emoji = "🟢" if direction == "call" else "🔴"
        text = f"""
{emoji} <b>TRADING SIGNAL</b> {emoji}

<b>Asset:</b> {asset}
<b>Direction:</b> {direction.upper()}
<b>Price:</b> {price:.5f}
<b>Confidence:</b> {confidence:.2%}
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

#TradingSignal #{asset.replace('/', '')} #{direction}
        """
        return self.send_message(text, self.channel_id)
    
    def send_trade_result(self, trade_number, outcome, profit, balance, confidence):
        """Send trade result to group"""
        emoji = "✅" if outcome == "win" else "❌"
        text = f"""
{emoji} <b>TRADE RESULT</b> {emoji}

<b>Trade:</b> #{trade_number}
<b>Result:</b> {outcome.upper()}
<b>Profit:</b> ${profit:.2f}
<b>Balance:</b> ${balance:.2f}
<b>Confidence:</b> {confidence:.2%}

#TradeResult #{outcome}
        """
        return self.send_message(text, self.group_id)
    
    def send_daily_report(self, report_data):
        """Send daily report to channel"""
        text = f"""
📊 <b>DAILY TRADING REPORT</b> 📊

<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}
<b>Total Trades:</b> {report_data['total_trades']}
<b>Winning Trades:</b> {report_data['winning_trades']}
<b>Win Rate:</b> {report_data['win_rate']:.1f}%
<b>Total Profit:</b> ${report_data['total_profit']:.2f}
<b>Ending Balance:</b> ${report_data['ending_balance']:.2f}

#DailyReport #TradingBot
        """
        return self.send_message(text, self.channel_id)
    
    def send_error_alert(self, error_message):
        """Send error alert to group"""
        text = f"""
🚨 <b>BOT ERROR ALERT</b> 🚨

<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
<b>Error:</b> <code>{error_message[:100]}...</code>

#ErrorAlert #CheckBot
        """
        return self.send_message(text, self.group_id)
