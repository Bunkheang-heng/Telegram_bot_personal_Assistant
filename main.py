#!/usr/bin/env python3
"""
Personal AI Assistant Telegram Bot

A smart Telegram bot powered by Google Gemini AI that can answer questions 
and send daily reminders.
"""

import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Import our modules
from config import (
    TELEGRAM_BOT_TOKEN, 
    CONNECT_TIMEOUT, 
    READ_TIMEOUT, 
    WRITE_TIMEOUT, 
    POOL_TIMEOUT,
    validate_config
)
from handlers import (
    start, help_command, stop_messages, status, handle_message,
    weather_command, quote_command, fact_command, joke_command,
    motivation_command, meditation_command, handle_callback_query,
    calendar_setup, calendar_auth, calendar_events, create_meeting,
    reminder_settings, get_calendar_handler, get_ai_handler,
    email_command, pending_emails_command, cancel_email_command
)
from scheduler import BotScheduler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    """Main bot class that orchestrates all components."""
    
    def __init__(self):
        """Initialize the bot with all components."""
        self.application = None
        self.scheduler = BotScheduler()
        
    def create_application(self):
        """Create and configure the Telegram application."""
        self.application = (
            Application.builder()
            .token(TELEGRAM_BOT_TOKEN)
            .connect_timeout(CONNECT_TIMEOUT)
            .read_timeout(READ_TIMEOUT)
            .write_timeout(WRITE_TIMEOUT)
            .pool_timeout(POOL_TIMEOUT)
            .build()
        )
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", start))
        self.application.add_handler(CommandHandler("help", help_command))
        self.application.add_handler(CommandHandler("stop", stop_messages))
        self.application.add_handler(CommandHandler("status", status))
        
        # Add enhanced feature commands
        self.application.add_handler(CommandHandler("weather", weather_command))
        self.application.add_handler(CommandHandler("quote", quote_command))
        self.application.add_handler(CommandHandler("fact", fact_command))
        self.application.add_handler(CommandHandler("joke", joke_command))
        self.application.add_handler(CommandHandler("motivation", motivation_command))
        self.application.add_handler(CommandHandler("meditation", meditation_command))
        
        # Add calendar integration commands
        self.application.add_handler(CommandHandler("calendar_setup", calendar_setup))
        self.application.add_handler(CommandHandler("calendar_auth", calendar_auth))
        self.application.add_handler(CommandHandler("calendar_events", calendar_events))
        self.application.add_handler(CommandHandler("create_meeting", create_meeting))
        self.application.add_handler(CommandHandler("reminders", reminder_settings))
        
        # Add email automation commands
        self.application.add_handler(CommandHandler("email", email_command))
        self.application.add_handler(CommandHandler("pending_emails", pending_emails_command))
        self.application.add_handler(CommandHandler("cancel_email", cancel_email_command))
        
        # Add callback query handler for inline buttons
        self.application.add_handler(CallbackQueryHandler(handle_callback_query))
        
        # Add message handler for AI conversations (should be last)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
        )
        
        logger.info("Application created and all handlers registered")
    
    async def start_bot(self):
        """Start the bot and all its components."""
        try:
            # Validate configuration
            validate_config()
            
            # Create application
            self.create_application()
            
            # Clean up any existing webhook
            await self.application.bot.delete_webhook(drop_pending_updates=True)
            logger.info("Cleaned up existing webhook")
            
            # Connect calendar handler to AI handler for calendar-aware responses
            calendar_handler = get_calendar_handler()
            ai_handler = get_ai_handler()
            ai_handler.set_calendar_handler(calendar_handler)
            
            # Set up scheduler
            self.scheduler.setup_all_jobs(self.application)
            self.scheduler.start()
            
            # Initialize and start the application
            await self.application.initialize()
            logger.info("Enhanced bot initialized successfully")
            
            await self.application.start()
            await self.application.updater.start_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
            logger.info("Enhanced bot started and polling...")
            
            # Keep running until interrupted
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
                
        except Exception as e:
            logger.error(f"Error during bot operation: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources when shutting down."""
        try:
            if self.scheduler.is_running:
                self.scheduler.stop()
            
            if self.application:
                await self.application.stop()
                await self.application.shutdown()
            
            logger.info("Bot cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def main():
    """Main function to run the bot."""
    try:
        bot = TelegramBot()
        asyncio.run(bot.start_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == '__main__':
    main()
