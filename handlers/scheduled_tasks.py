import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import ENABLE_ENHANCED_DAILY, REMINDER_MINUTES_BEFORE, REMINDER_AT_EVENT_TIME
from handlers.basic_commands import get_user_chat_id
from handlers.calendar_commands import get_calendar_handler
from services import ExternalServices

logger = logging.getLogger(__name__)

async def send_daily_hi(application) -> None:
    """Send the enhanced daily message with weather, quote, and greeting."""
    USER_CHAT_ID = get_user_chat_id()
    if not USER_CHAT_ID:
        return
    
    try:
        services = ExternalServices()
        
        # Get time-based greeting
        greeting = services.get_greeting_based_on_time()
        
        # Start building the daily message
        daily_message = f"{greeting} Bunkheang! 👋\n\n"
        daily_message += "🤖 **Your daily check-in is here, my friend!**\n\n"
        
        if ENABLE_ENHANCED_DAILY:
            # Add weather information for Phnom Penh
            weather_data = await services.get_weather()
            if weather_data["success"]:
                daily_message += "🌤️ **Phnom Penh Weather (for your plans):**\n"
                daily_message += f"🌡️ {weather_data['temperature']}°C - {weather_data['description']}\n"
                daily_message += f"💧 Humidity: {weather_data['humidity']}% (perfect for campus or coding!)\n\n"
            
            # Add inspirational quote
            quote_data = await services.get_inspirational_quote()
            if quote_data["success"]:
                daily_message += "✨ **Today's motivation boost for you:**\n"
                daily_message += f"*\"{quote_data['text']}\"*\n"
                daily_message += f"— {quote_data['author']}\n\n"
        
        daily_message += "💬 How did your day go, Bunkheang? Made progress on your projects? Need help with anything? I'm here for whatever you need - coding problems, planning tomorrow, or just a chat!"
        
        # Create personalized quick action buttons for Bunkheang
        keyboard = [
            [
                InlineKeyboardButton("📅 Tomorrow's Schedule", callback_data="calendar_events"),
                InlineKeyboardButton("🌤️ Weather Update", callback_data="weather")
            ],
            [
                InlineKeyboardButton("💪 Boost My Energy", callback_data="motivation"),
                InlineKeyboardButton("🧘 Help Me Unwind", callback_data="meditation")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await application.bot.send_message(
            chat_id=USER_CHAT_ID,
            text=daily_message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        logger.info(f"Daily personal check-in sent to Bunkheang (Chat ID: {USER_CHAT_ID})")
        
    except Exception as e:
        logger.error(f"Error sending daily message: {e}")
        # Fallback to simple message
        try:
            await application.bot.send_message(
                chat_id=USER_CHAT_ID,
                text="Hey Bunkheang! 👋 Hope your day was productive!\n\n💬 Your assistant is here if you need anything - just let me know!"
            )
        except Exception as fallback_error:
            logger.error(f"Error sending fallback daily message: {fallback_error}")

async def send_calendar_reminders(application) -> None:
    """Check for upcoming events and send reminders."""
    USER_CHAT_ID = get_user_chat_id()
    if not USER_CHAT_ID:
        return
    
    try:
        calendar_handler = get_calendar_handler()
        if not calendar_handler.is_authenticated:
            return
        
        # Get events needing reminders
        events_needing_reminders = await calendar_handler.get_events_needing_reminders(
            minutes_before=REMINDER_MINUTES_BEFORE,
            at_event_time=REMINDER_AT_EVENT_TIME
        )
        
        # Send reminders for each event
        for event in events_needing_reminders:
            try:
                # Format reminder message
                reminder_message = calendar_handler.format_reminder_message(event)
                
                # Send reminder
                await application.bot.send_message(
                    chat_id=USER_CHAT_ID,
                    text=reminder_message,
                    parse_mode='Markdown'
                )
                
                # Mark reminder as sent
                calendar_handler.mark_reminder_sent(event['reminder_id'])
                
                logger.info(f"Calendar reminder sent: {event['title']} ({event['reminder_type']})")
                
            except Exception as e:
                logger.error(f"Error sending individual reminder for {event['title']}: {e}")
        
        # Clean up old reminders occasionally
        if len(events_needing_reminders) > 0:
            calendar_handler.cleanup_old_reminders()
            
    except Exception as e:
        logger.error(f"Error in calendar reminder check: {e}")

async def send_scheduled_emails(application) -> None:
    """Check for scheduled emails and send them."""
    try:
        # Import here to avoid circular imports
        from handlers.email_commands import get_email_service
        
        email_service = get_email_service()
        
        if not email_service.is_available():
            return
        
        # Check and send scheduled emails
        sent_emails = await email_service.check_and_send_scheduled_emails()
        
        # Notify user about sent emails (optional)
        USER_CHAT_ID = get_user_chat_id()
        if sent_emails and USER_CHAT_ID:
            for email_info in sent_emails:
                if email_info['result']['success']:
                    logger.info(f"Scheduled email sent: {email_info['subject']} to {email_info['recipient']}")
                    
                    # Optional: Send notification to user
                    notification = (
                        f"📧 **Email sent successfully!**\n\n"
                        f"👤 **To:** {email_info['recipient']}\n"
                        f"📝 **Subject:** {email_info['subject']}"
                    )
                    
                    try:
                        await application.bot.send_message(
                            chat_id=USER_CHAT_ID,
                            text=notification,
                            parse_mode='Markdown'
                        )
                    except Exception as notify_error:
                        logger.error(f"Error sending email notification: {notify_error}")
                else:
                    logger.error(f"Failed to send scheduled email: {email_info['result']['message']}")
        
        # Cleanup old emails occasionally (once a day)
        import random
        if random.randint(1, 1440) == 1:  # 1 in 1440 chance (once per day on average)
            email_service.cleanup_old_emails()
            
    except Exception as e:
        logger.error(f"Error in scheduled email check: {e}")

async def send_scheduled_reminders(application) -> None:
    """Check for and send scheduled personal reminders."""
    USER_CHAT_ID = get_user_chat_id()
    if not USER_CHAT_ID:
        return
    
    try:
        # Import reminder service here to avoid circular imports
        from reminder_service import ReminderService
        
        reminder_service = ReminderService()
        
        # Get reminders that need to be sent
        reminders_to_send = await reminder_service.check_and_send_scheduled_reminders()
        
        # Send each reminder
        for reminder in reminders_to_send:
            try:
                # Format the friendly reminder message
                formatted_message = reminder_service.format_reminder_message(reminder['reminder_text'])
                
                # Send reminder
                await application.bot.send_message(
                    chat_id=USER_CHAT_ID,
                    text=formatted_message
                )
                
                logger.info(f"Personal reminder sent: {reminder['reminder_id']}")
                
            except Exception as e:
                logger.error(f"Error sending individual reminder {reminder['reminder_id']}: {e}")
        
        # Clean up old reminders occasionally
        if len(reminders_to_send) > 0:
            reminder_service.cleanup_old_reminders()
            
    except Exception as e:
        logger.error(f"Error in scheduled reminder check: {e}") 