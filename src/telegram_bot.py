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
        self.enabled = True if self.bot_token and self.bot_token != 'your_bot_token_here' else False
        
    def send_message(self, text, chat_id=None, parse_mode='HTML'):
        """Send message to Telegram"""
        if not self.enabled:
            logger.warning("Telegram bot is not enabled. Set TELEGRAM_BOT_TOKEN to enable.")
            return False
            
        chat_id = chat_id or self.channel_id
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        
        try:
            response = requests.post(url, data=payload, timeout=10)
            if response.status_code == 200:
                logger.info("Telegram message sent successfully")
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def send_signal(self, asset, direction, confidence, price):
        """Send trading signal to channel"""
        if not self.enabled:
            return False
            
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
        if not self.enabled:
            return False
            
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
        if not self.enabled:
            return False
            
        profit_emoji = "📈" if report_data['total_profit'] >= 0 else "📉"
        text = f"""
{profit_emoji} <b>DAILY TRADING REPORT</b> {profit_emoji}

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
        if not self.enabled:
            return False
            
        text = f"""
🚨 <b>BOT ERROR ALERT</b> 🚨

<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
<b>Error:</b> <code>{error_message[:100]}...</code>

#ErrorAlert #CheckBot
        """
        return self.send_message(text, self.group_id)
        
    def send_startup_message(self, demo_mode, balance, assets):
        """Send bot startup message"""
        if not self.enabled:
            return False
            
        text = f"""
🤖 <b>Trading Bot Started</b> 🤖

<b>Mode:</b> {'DEMO' if demo_mode else 'LIVE'}
<b>Balance:</b> ${balance:.2f}
<b>Assets:</b> {', '.join(assets)}
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

#BotStarted #TradingBot
        """
        return self.send_message(text, self.group_id)
        
    def send_shutdown_message(self, performance_stats):
        """Send bot shutdown message"""
        if not self.enabled:
            return False
            
        text = f"""
🛑 <b>Trading Bot Stopped</b> 🛑

<b>Total Trades:</b> {performance_stats['total_trades']}
<b>Win Rate:</b> {performance_stats['win_rate']:.1f}%
<b>Total Profit:</b> ${performance_stats['total_profit']:.2f}
<b>Final Balance:</b> ${performance_stats.get('final_balance', 0):.2f}

#BotStopped #TradingBot
        """
        return self.send_message(text, self.group_id)
