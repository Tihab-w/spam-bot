"""
Telegram Bot Integration
SRS Section: 4.2, 4.3
Real-world integration with Telegram messaging platform
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_client import SpamClassifierClient
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ============================================
# CONFIGURATION - UPDATE THIS!
# ============================================
TELEGRAM_BOT_TOKEN = "8790418576:AAHtJsDPOPW_Kj2hUWeqoWMvJM1ShdZ-mTY"  # Replace with your real token!
API_SERVER_URL = "http://localhost:5000"

# Initialize spam classifier client
spam_client = SpamClassifierClient(API_SERVER_URL)

class TelegramSpamFilter:
    """
    Telegram Bot with integrated spam filtering
    """
    
    def __init__(self, token: str):
        self.token = token
        self.app = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = (
            "SHIELD *Spam Classifier AI Bot*\n\n"
            "I monitor messages and detect spam in real-time!\n\n"
            "*Commands:*\n"
            "/start - Show this message\n"
            "/check <message> - Check if a message is spam\n"
            "/status - Check system status\n"
            "/help - Show help\n\n"
            "Add me to your group to automatically filter spam messages!"
        )
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "BOT *Spam Classifier AI Help*\n\n"
            "I use machine learning to detect spam messages.\n\n"
            "*How to use:*\n"
            "- Send any message to check if it's spam\n"
            "- Use /check followed by a message\n"
            "- Add me to groups for automatic filtering\n\n"
            "*Confidence Levels:*\n"
            "HIGH 90-100%: Very high confidence\n"
            "MED 70-89%: High confidence\n"
            "LOW 50-69%: Moderate confidence\n"
            "CRIT Below 50%: Low confidence"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def check_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /check command"""
        message_text = ' '.join(context.args)
        
        if not message_text:
            await update.message.reply_text(
                "Please provide a message to check.\n"
                "Example: /check Free iPhone giveaway!"
            )
            return
        
        # Call spam classifier API
        try:
            result = spam_client.classify(message_text)
        except Exception as e:
            await update.message.reply_text(
                f"ERR Cannot connect to spam classifier server.\n"
                f"Make sure app.py is running on {API_SERVER_URL}"
            )
            return
        
        if not result.get('success'):
            await update.message.reply_text(
                "ERR Sorry, couldn't classify the message right now."
            )
            return
        
        # Format response
        confidence = result['confidence']
        if confidence > 90:
            emoji = "CRIT" if result['result'] == 'SPAM' else "HIGH"
        elif confidence > 70:
            emoji = "LOW" if result['result'] == 'SPAM' else "HIGH"
        else:
            emoji = "MED"
        
        response = (
            f"{emoji} *Classification Result*\n\n"
            f"*Result:* {result['result']}\n"
            f"*Confidence:* {confidence}%\n"
            f"*Explanation:* {result.get('explanation', 'N/A')}\n"
        )
        
        if result.get('top_indicators'):
            response += "\n*Key Indicators:*\n"
            for indicator in result['top_indicators'][:3]:
                direction = "WARN" if indicator['indicates_spam'] else "OK"
                response += f"{direction} `{indicator['word']}`\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            health = spam_client.health_check()
        except:
            await update.message.reply_text(
                "ERR Cannot connect to API server.\n"
                "Make sure app.py is running!"
            )
            return
        
        status_emoji = "OK" if health.get('status') == 'healthy' else "ERR"
        response = (
            f"{status_emoji} *System Status*\n\n"
            f"*Server:* {health.get('status', 'Unknown')}\n"
            f"*Model:* {'Loaded' if health.get('model_loaded') else 'Not loaded'}\n"
            f"*Version:* {health.get('version', 'N/A')}"
        )
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle incoming messages - MAIN INTEGRATION POINT
        """
        message_text = update.message.text
        
        # Skip empty messages
        if not message_text or not message_text.strip():
            return
        
        # Classify message
        try:
            result = spam_client.classify(message_text)
        except:
            # If API is down, let message through
            return
        
        if not result.get('success'):
            return
        
        # Action Logic based on confidence
        if result['result'] == 'SPAM' and result['confidence'] > 80:
            # High confidence spam - delete and warn
            try:
                await update.message.delete()
                warning = await update.message.reply_text(
                    f"WARN Spam message detected and removed!\n"
                    f"Confidence: {result['confidence']}%"
                )
                await asyncio.sleep(10)
                await warning.delete()
            except:
                # If can't delete (not admin), just warn
                await update.message.reply_text(
                    f"WARN Spam detected! Confidence: {result['confidence']}%\n"
                    f"Make bot admin to auto-delete spam."
                )
        elif result['result'] == 'SPAM' and result['confidence'] > 50:
            # Moderate confidence - flag
            await update.message.reply_text(
                f"WARN *Potential Spam Detected*\n"
                f"Confidence: {result['confidence']}%\n"
                f"{result.get('explanation', '')}",
                parse_mode='Markdown'
            )
        # Legitimate messages pass through silently
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        print(f"Bot Error: {context.error}")
    
    def run(self):
        """Start the bot"""
        # Validate token
        if "YOUR_BOT_TOKEN" in self.token or "YOUR_TOKEN" in self.token:
            print("\n" + "=" * 50)
            print("ERROR: Bot token not configured!")
            print("=" * 50)
            print("\nPlease follow these steps:")
            print("1. Open Telegram and search for @BotFather")
            print("2. Send: /newbot")
            print("3. Choose a name for your bot")
            print("4. Choose a username ending with 'bot'")
            print("5. Copy the token provided")
            print("6. Replace TELEGRAM_BOT_TOKEN in this file")
            print("\nExample: TELEGRAM_BOT_TOKEN = '123456:ABC...'")
            print("=" * 50)
            return
        
        print("\n" + "=" * 50)
        print("TELEGRAM SPAM FILTER BOT")
        print("=" * 50)
        print(f"API Server: {API_SERVER_URL}")
        print("=" * 50)
        
        # Check API connection
        try:
            health = spam_client.health_check()
            if health.get('status') == 'healthy':
                print("API Server: CONNECTED")
            else:
                print("API Server: NOT HEALTHY - Check if app.py is running")
        except:
            print("API Server: NOT REACHABLE - Start app.py first!")
            print("Run: python app.py")
        
        print("=" * 50)
        
        # Build application
        self.app = Application.builder().token(self.token).build()
        
        # Register handlers
        self.app.add_handler(CommandHandler('start', self.start_command))
        self.app.add_handler(CommandHandler('help', self.help_command))
        self.app.add_handler(CommandHandler('check', self.check_command))
        self.app.add_handler(CommandHandler('status', self.status_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.app.add_error_handler(self.error_handler)
        
        print("\n[BOT] Starting Telegram Bot...")
        print("[BOT] Press Ctrl+C to stop\n")
        
        # Start polling
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


# ==================== MAIN ====================

if __name__ == "__main__":
    bot = TelegramSpamFilter(TELEGRAM_BOT_TOKEN)
    bot.run()