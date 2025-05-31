import logging
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from ai_handler import AIHandler
from services import ExternalServices
from config import ENABLE_ENHANCED_DAILY, ENABLE_CALENDAR_REMINDERS, REMINDER_MINUTES_BEFORE, REMINDER_CHECK_INTERVAL_MINUTES, REMINDER_AT_EVENT_TIME
from calendar_handler import CalendarHandler

logger = logging.getLogger(__name__)

# Global variables
USER_CHAT_ID = None
ai_handler = AIHandler()
services = ExternalServices()
calendar_handler = CalendarHandler()

# Load existing credentials if available
calendar_handler.load_credentials()

# Set calendar handler in AI handler for calendar-aware responses
ai_handler.set_calendar_handler(calendar_handler)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    global USER_CHAT_ID
    USER_CHAT_ID = update.effective_chat.id
    
    welcome_message = (
        '👋 **Welcome back, Bunkheang!**\n\n'
        '🤖 **Your Personal AI Assistant is Ready**\n\n'
        '✨ **What I can help you with today:**\n'
        '📅 Manage your calendar and schedule meetings\n'
        '🌤️ Check weather in Phnom Penh or anywhere else\n'
        '💬 Have intelligent conversations about your projects\n'
        '🎯 Get daily motivation and productivity tips\n'
        '📚 Help with your Computer Science studies\n'
        '💼 Assist with your development work\n\n'
        '🕐 **Daily Check-ins:** Every day at 5:10 PM\n'
        '🧠 **Smart Features:** I know your background and preferences\n\n'
        '💬 **Just talk to me naturally!** I understand your context and can help with anything.'
    )
    
    # Create personalized quick actions
    keyboard = [
        [
            InlineKeyboardButton("🌤️ Phnom Penh Weather", callback_data="weather"),
            InlineKeyboardButton("📅 My Calendar", callback_data="calendar_events")
        ],
        [
            InlineKeyboardButton("💡 Daily Motivation", callback_data="motivation"),
            InlineKeyboardButton("🧘 Quick Meditation", callback_data="meditation")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message, 
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    logger.info(f"Personal assistant activated for Bunkheang (Chat ID: {USER_CHAT_ID})")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help information about available commands."""
    help_text = (
        "🤖 **Bunkheang's Personal Assistant Guide**\n\n"
        
        "**📅 AI Calendar Management:**\n"
        "• *'I have class tomorrow at 8AM'* - AI will create the event\n"
        "• *'Remove all my meetings'* - AI will delete matching events\n"
        "• *'Clear my schedule completely'* - AI will clear all events\n"
        "• *'What's on my schedule today?'* - AI answers with your real calendar\n"
        "• *'Am I free tomorrow afternoon?'* - AI checks your actual availability\n"
        "• I can directly manage your calendar without confirmation prompts!\n\n"
        
        "**⏰ Smart Reminders:**\n"
        "• I'll automatically text you 15 minutes before events\n"
        "• I'll also text you when events are starting\n"
        "• No setup needed - reminders work automatically!\n"
        "• `/reminders` - View and test reminder settings\n\n"
        
        "**🌤️ Weather & Location:**\n"
        "• `/weather` - Phnom Penh weather (your default)\n"
        "• `/weather [city]` - Any city worldwide\n"
        "• Perfect for planning your day!\n\n"
        
        "**💬 Smart Conversations:**\n"
        "• Ask about your CS projects and coursework\n"
        "• Get help with coding problems\n"
        "• Discuss your development work\n"
        "• I know your background, schedule, and experience!\n\n"
        
        "**🎯 Daily Productivity:**\n"
        "• `/motivation` - Personalized motivation\n"
        "• `/meditation` - Quick mindfulness break\n"
        "• `/quote` - Inspirational thoughts\n"
        "• `/status` - Check your assistant status\n\n"
        
        "**🧠 Natural Language Examples:**\n"
        "• *'Schedule a team meeting for Monday at 2PM'*\n"
        "• *'Delete all my class events'*\n"
        "• *'I want to remove my schedule and start fresh'*\n"
        "• *'What's the weather like for my morning run?'*\n"
        "• *'Help me prepare for my presentation'*\n\n"
        
        "**⚙️ Manual Commands (if needed):**\n"
        "• `/create_meeting` - Manual event creation\n"
        "• `/calendar_events` - View calendar\n"
        "• `/calendar_setup` - Set up calendar authentication\n"
        "• `/reminders` - Calendar reminder settings\n"
        "• `/stop` - Pause daily check-ins\n"
        "• `/start` - Reactivate your assistant\n\n"
        
        "💡 **Remember:** Just talk to me naturally! I can understand context, check your real calendar, and perform actions directly without needing confirmation for most tasks."
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get weather for specified city or default city."""
    city = ' '.join(context.args) if context.args else None
    
    # Handle both regular messages and callback queries
    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text("🌤️ Fetching weather information...")
    else:
        await update.message.reply_text("🌤️ Fetching weather information...")
    
    weather_data = await services.get_weather(city)
    weather_message = services.format_weather_message(weather_data)
    
    if update.callback_query:
        await query.edit_message_text(weather_message, parse_mode='Markdown')
    else:
        await update.message.reply_text(weather_message, parse_mode='Markdown')

async def quote_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get an inspirational quote."""
    await update.message.reply_text("💭 Finding inspiration...")
    
    quote_data = await services.get_inspirational_quote()
    
    if quote_data["success"]:
        quote_message = (
            f"✨ **Daily Inspiration**\n\n"
            f"*\"{quote_data['text']}\"*\n\n"
            f"— **{quote_data['author']}**"
        )
    else:
        quote_message = f"❌ {quote_data['message']}"
    
    await update.message.reply_text(quote_message, parse_mode='Markdown')

async def fact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get a random interesting fact."""
    await update.message.reply_text("🧠 Fetching an interesting fact...")
    
    fact_data = await services.get_random_fact()
    
    if fact_data["success"]:
        fact_message = (
            f"🤓 **Did You Know?**\n\n"
            f"{fact_data['text']}"
        )
    else:
        fact_message = f"❌ {fact_data['message']}"
    
    await update.message.reply_text(fact_message, parse_mode='Markdown')

async def joke_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get a clean, funny joke."""
    jokes = [
        "Why don't scientists trust atoms? Because they make up everything! 😄",
        "Why did the scarecrow win an award? He was outstanding in his field! 🌾",
        "Why don't eggs tell jokes? They'd crack each other up! 🥚",
        "What do you call a fake noodle? An impasta! 🍝",
        "Why did the coffee file a police report? It got mugged! ☕",
        "What do you call a bear with no teeth? A gummy bear! 🐻",
        "Why don't skeletons fight each other? They don't have the guts! 💀",
        "What's the best thing about Switzerland? I don't know, but the flag is a big plus! 🇨🇭",
        "Why did the math book look so sad? Because it had too many problems! 📚",
        "What do you call a dinosaur that crashes his car? Tyrannosaurus Wrecks! 🦕"
    ]
    
    joke = random.choice(jokes)
    await update.message.reply_text(f"😄 **Here's a joke for you:**\n\n{joke}")

async def motivation_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a motivational message."""
    motivational_messages = [
        "🔥 **You've got this!** Every expert was once a beginner. Keep pushing forward!",
        "💪 **Believe in yourself!** You are stronger than you think and more capable than you imagine.",
        "🌟 **Today is your day!** Make it count, make it matter, make it amazing!",
        "🚀 **Chase your dreams!** The future belongs to those who believe in the beauty of their dreams.",
        "⭐ **You are unstoppable!** Success is not final, failure is not fatal - it's courage that counts!",
        "🎯 **Focus on progress!** You don't have to be perfect, you just have to be better than yesterday.",
        "💎 **You are valuable!** Remember that diamonds are formed under pressure. Shine bright!",
        "🌈 **Stay positive!** Positive thoughts breed positive results. You're creating your reality!",
        "🦋 **Embrace change!** Just when the caterpillar thought the world was over, it became a butterfly.",
        "🏆 **You're a champion!** Champions are made when nobody's watching. Keep training your greatness!"
    ]
    
    message = random.choice(motivational_messages)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text(message, parse_mode='Markdown')

async def meditation_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provide a quick mindfulness exercise."""
    meditation_message = (
        "🧘‍♀️ **2-Minute Mindfulness Break**\n\n"
        "Let's take a moment to center ourselves:\n\n"
        "1️⃣ **Breathe** - Take 3 deep breaths\n"
        "   • Inhale for 4 counts\n"
        "   • Hold for 4 counts\n"
        "   • Exhale for 6 counts\n\n"
        "2️⃣ **Notice** - What do you feel right now?\n"
        "   • Physical sensations\n"
        "   • Emotions present\n"
        "   • Thoughts passing by\n\n"
        "3️⃣ **Gratitude** - Name 3 things you're grateful for today\n\n"
        "4️⃣ **Intention** - Set a positive intention for the rest of your day\n\n"
        "🌸 *Take your time. You deserve this moment of peace.*"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(meditation_message, parse_mode='Markdown')
    else:
        await update.message.reply_text(meditation_message, parse_mode='Markdown')

async def stop_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop daily messages."""
    global USER_CHAT_ID
    USER_CHAT_ID = None
    await update.message.reply_text(
        '❌ Daily messages have been disabled.\n'
        'You can still use all commands and chat with AI anytime!\n'
        'Use /start to enable daily messages again.'
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check status of daily messages and features."""
    global USER_CHAT_ID
    
    status_message = "📊 **Bot Status Report**\n\n"
    
    if USER_CHAT_ID:
        status_message += "✅ **Daily Messages:** Enabled\n"
        status_message += "📅 **Schedule:** 5:10 PM daily\n"
        status_message += "🌟 **Enhanced Mode:** Active\n\n"
    else:
        status_message += "❌ **Daily Messages:** Disabled\n\n"
    
    status_message += "🔧 **Available Features:**\n"
    status_message += "🤖 AI Chat: ✅ Active\n"
    status_message += f"🌤️ Weather: {'✅ Active' if services.session else '❌ Unavailable'}\n"
    status_message += "💡 Quotes: ✅ Active\n"
    status_message += "🧠 Facts: ✅ Active\n"
    status_message += "😄 Jokes: ✅ Active\n"
    status_message += "🧘 Meditation: ✅ Active\n\n"
    
    status_message += "💬 **Usage Tip:** Try any command or just chat naturally!"
    
    await update.message.reply_text(status_message, parse_mode='Markdown')

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard button presses."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "weather":
        await weather_command(update, context)
    elif query.data == "quote":
        await quote_command(update, context)
    elif query.data == "fact":
        await fact_command(update, context)
    elif query.data == "joke":
        await joke_command(update, context)
    elif query.data == "motivation":
        await motivation_command(update, context)
    elif query.data == "meditation":
        await meditation_command(update, context)
    elif query.data == "calendar_events":
        await calendar_events(update, context)
    elif query.data == "test_reminders":
        await test_reminders_manually(update, context)
    # Calendar-related callbacks
    elif query.data in ["create_confirmed", "create_cancelled", "quick_create"]:
        await handle_meeting_confirmation(update, context)
    elif query.data == "just_chat":
        # Handle original message as regular chat
        original_message = context.user_data.get('original_message', '')
        if original_message:
            # Clear calendar data
            context.user_data.pop('pending_meeting', None)
            context.user_data.pop('original_message', None)
            
            await query.edit_message_text("💬 Sure! Let me respond to your message...")
            
            # Generate AI response for original message
            response = await ai_handler.generate_response(original_message, update.effective_user.first_name)
            chunks = ai_handler.split_long_message(response)
            
            for chunk in chunks:
                await query.message.reply_text(chunk)
                if len(chunks) > 1:
                    await asyncio.sleep(0.5)
        else:
            await query.edit_message_text("💬 Let's continue our conversation!")

# Calendar Integration Commands
async def calendar_setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set up Google Calendar authentication."""
    try:
        await update.message.reply_text("🔄 Setting up calendar authentication...")
        
        auth_message = calendar_handler.get_authentication_url()
        await update.message.reply_text(auth_message)
        
    except Exception as e:
        logger.error(f"Calendar setup error: {e}")
        await update.message.reply_text(f"❌ Error setting up calendar: {str(e)}")

async def calendar_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Complete calendar authentication with authorization code."""
    try:
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide the authorization code.\n"
                "Usage: `/calendar_auth YOUR_CODE_HERE`"
            )
            return
        
        auth_code = ' '.join(context.args)
        await update.message.reply_text("🔄 Authenticating with Google Calendar...")
        
        result = calendar_handler.authenticate_with_code(auth_code)
        await update.message.reply_text(result)
        
    except Exception as e:
        logger.error(f"Calendar auth error: {e}")
        await update.message.reply_text(f"❌ Authentication error: {str(e)}")

async def calendar_events(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show upcoming calendar events."""
    try:
        # Handle both regular messages and callback queries
        if update.callback_query:
            query = update.callback_query
            await query.edit_message_text("📅 Fetching your upcoming events...")
            message_handler = query.message
        else:
            await update.message.reply_text("📅 Fetching your upcoming events...")
            message_handler = update.message
        
        events_text = await calendar_handler.get_upcoming_events()
        
        if update.callback_query:
            await query.edit_message_text(events_text, parse_mode='Markdown')
        else:
            await message_handler.reply_text(events_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Calendar events error: {e}")
        error_msg = f"❌ Error fetching events: {str(e)}"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await update.message.reply_text(error_msg)

async def create_meeting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a calendar event from natural language input."""
    try:
        if not context.args:
            await update.message.reply_text(
                "📅 **Create Meeting**\n\n"
                "Tell me about your meeting and I'll add it to your calendar!\n\n"
                "**Examples:**\n"
                "• `Meeting with John tomorrow at 2pm`\n"
                "• `Team standup every day at 9am`\n"
                "• `Doctor appointment next Friday at 10:30am`\n"
                "• `Call mom tonight at 7pm`\n"
                "• `Presentation on Monday at 3pm for 2 hours`\n\n"
                "**Usage:** `/create_meeting YOUR_MEETING_DETAILS`",
                parse_mode='Markdown'
            )
            return
        
        meeting_request = ' '.join(context.args)
        
        # Show typing indicator
        await update.message.reply_chat_action(ChatAction.TYPING)
        await update.message.reply_text("🤖 Understanding your meeting request...")
        
        # Parse the meeting request
        meeting_details = await calendar_handler.parse_meeting_request(meeting_request)
        
        if not meeting_details:
            await update.message.reply_text(
                "❌ I couldn't understand your meeting request. Please try again with more details.\n\n"
                "Example: `Meeting with team tomorrow at 2pm`"
            )
            return
        
        # Show confirmation with meeting details
        confirmation_text = (
            f"📅 **Meeting Details Preview:**\n\n"
            f"📝 **Title:** {meeting_details['title']}\n"
            f"📆 **Date:** {meeting_details['date']}\n"
            f"🕐 **Time:** {meeting_details['start_time']} - {meeting_details['end_time']}\n"
        )
        
        if meeting_details.get('description'):
            confirmation_text += f"📝 **Description:** {meeting_details['description']}\n"
        
        confirmation_text += "\nShall I create this event in your calendar?"
        
        # Create confirmation buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ Create Event", callback_data=f"create_confirmed"),
                InlineKeyboardButton("❌ Cancel", callback_data="create_cancelled")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Store meeting details in context for confirmation
        context.user_data['pending_meeting'] = meeting_details
        
        await update.message.reply_text(
            confirmation_text, 
            reply_markup=reply_markup, 
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Create meeting error: {e}")
        await update.message.reply_text(f"❌ Error creating meeting: {str(e)}")

async def handle_meeting_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle meeting creation confirmation."""
    query = update.callback_query
    await query.answer()
    
    if query.data in ["create_confirmed", "quick_create"]:
        try:
            meeting_details = context.user_data.get('pending_meeting')
            if not meeting_details:
                await query.edit_message_text("❌ Meeting details not found. Please try creating the meeting again.")
                return
            
            await query.edit_message_text("🔄 Creating calendar event...")
            
            result = await calendar_handler.create_calendar_event(meeting_details)
            await query.edit_message_text(result, parse_mode='Markdown')
            
            # Clear pending meeting
            context.user_data.pop('pending_meeting', None)
            context.user_data.pop('original_message', None)
            
        except Exception as e:
            logger.error(f"Meeting confirmation error: {e}")
            await query.edit_message_text(f"❌ Error creating event: {str(e)}")
    
    elif query.data == "create_cancelled":
        await query.edit_message_text("❌ Meeting creation cancelled.")
        context.user_data.pop('pending_meeting', None)
        context.user_data.pop('original_message', None)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle general text messages."""
    try:
        user_message = update.message.text
        user_name = update.effective_user.first_name
        
        logger.info(f"Received message from {user_name}: {user_message}")
        
        # Let AI detect and handle calendar actions first
        if calendar_handler.is_authenticated:
            calendar_action = await ai_handler.detect_calendar_action(user_message)
            
            if calendar_action:
                await update.message.reply_chat_action(ChatAction.TYPING)
                
                # Execute the calendar action
                result = await ai_handler.execute_calendar_action(calendar_action, user_message)
                
                # Send the result
                chunks = ai_handler.split_long_message(result)
                for chunk in chunks:
                    await update.message.reply_text(chunk, parse_mode='Markdown')
                    if len(chunks) > 1:
                        await asyncio.sleep(0.5)
                
                logger.info(f"Calendar action executed for {user_name}: {calendar_action.get('action')}")
                return
        
        # If no calendar action detected, handle as regular AI conversation
        await update.message.reply_chat_action(ChatAction.TYPING)
        
        # Generate AI response with calendar context
        response = await ai_handler.generate_response(user_message, user_name)
        
        # Split long messages
        chunks = ai_handler.split_long_message(response)
        
        # Send response chunks
        for chunk in chunks:
            await update.message.reply_text(chunk)
            if len(chunks) > 1:
                await asyncio.sleep(0.5)  # Brief pause between chunks
        
        logger.info(f"AI response sent to {user_name}")
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text(
            "Sorry, I encountered an error processing your message. Please try again."
        )

def get_user_chat_id():
    """Get the current user chat ID."""
    return USER_CHAT_ID

async def send_daily_hi(application) -> None:
    """Send the enhanced daily message with weather, quote, and greeting."""
    global USER_CHAT_ID
    if not USER_CHAT_ID:
        return
    
    try:
        # Get time-based greeting
        greeting = services.get_greeting_based_on_time()
        
        # Start building the daily message
        daily_message = f"{greeting}, Bunkheang! 👋\n\n"
        daily_message += "🤖 **Your Daily Assistant Check-in**\n\n"
        
        if ENABLE_ENHANCED_DAILY:
            # Add weather information for Phnom Penh
            weather_data = await services.get_weather()
            if weather_data["success"]:
                daily_message += "🌤️ **Phnom Penh Weather Today:**\n"
                daily_message += f"🌡️ {weather_data['temperature']}°C ({weather_data['description']})\n"
                daily_message += f"💧 Humidity: {weather_data['humidity']}%\n\n"
            
            # Add inspirational quote
            quote_data = await services.get_inspirational_quote()
            if quote_data["success"]:
                daily_message += "✨ **Daily Motivation for You:**\n"
                daily_message += f"*\"{quote_data['text']}\"*\n"
                daily_message += f"— {quote_data['author']}\n\n"
        
        daily_message += "💬 How was your day? Need help with anything? I'm here whenever you need me!"
        
        # Create personalized quick action buttons
        keyboard = [
            [
                InlineKeyboardButton("📅 My Schedule", callback_data="calendar_events"),
                InlineKeyboardButton("🌤️ Weather Update", callback_data="weather")
            ],
            [
                InlineKeyboardButton("🎯 Motivation Boost", callback_data="motivation"),
                InlineKeyboardButton("🧘 Wind Down", callback_data="meditation")
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
                text="Hi Bunkheang! 👋 Hope you're having a great day!\n\n💬 Your personal assistant is here if you need anything!"
            )
        except Exception as fallback_error:
            logger.error(f"Error sending fallback daily message: {fallback_error}")

async def send_calendar_reminders(application) -> None:
    """Check for upcoming events and send reminders."""
    global USER_CHAT_ID
    if not USER_CHAT_ID or not calendar_handler.is_authenticated:
        return
    
    try:
        from config import REMINDER_MINUTES_BEFORE, REMINDER_AT_EVENT_TIME
        
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

async def reminder_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show and configure calendar reminder settings."""
    try:
        if not calendar_handler.is_authenticated:
            await update.message.reply_text(
                "❌ Calendar not set up. Use /calendar_setup first.",
                parse_mode='Markdown'
            )
            return
        
        # Show current settings
        settings_message = (
            "⚙️ **Calendar Reminder Settings**\n\n"
            f"🔔 **Reminders Enabled:** {'✅ Yes' if ENABLE_CALENDAR_REMINDERS else '❌ No'}\n"
            f"⏰ **Reminder Time:** {REMINDER_MINUTES_BEFORE} minutes before events\n"
            f"🕐 **At Event Time:** {'✅ Yes' if REMINDER_AT_EVENT_TIME else '❌ No'}\n"
            f"🔄 **Check Interval:** Every {REMINDER_CHECK_INTERVAL_MINUTES} minutes\n\n"
        )
        
        if ENABLE_CALENDAR_REMINDERS:
            reminder_at_text = "I'll also text you when events start" if REMINDER_AT_EVENT_TIME else "No notifications at event start time"
            settings_message += (
                "📱 **How it works:**\n"
                f"• I'll text you {REMINDER_MINUTES_BEFORE} minutes before each event\n"
                f"• {reminder_at_text}\n"
                f"• I check for upcoming events every {REMINDER_CHECK_INTERVAL_MINUTES} minutes\n\n"
                "💡 **To change settings, edit config.py and restart the bot**"
            )
        else:
            settings_message += (
                "ℹ️ Calendar reminders are currently disabled.\n"
                "To enable them, set ENABLE_CALENDAR_REMINDERS = True in config.py"
            )
        
        # Test reminders button
        keyboard = []
        if ENABLE_CALENDAR_REMINDERS:
            keyboard.append([
                InlineKeyboardButton("🧪 Test Reminders", callback_data="test_reminders")
            ])
        
        keyboard.append([
            InlineKeyboardButton("📅 View Calendar", callback_data="calendar_events"),
            InlineKeyboardButton("➕ Add Event", callback_data="quick_add_event")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            settings_message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error showing reminder settings: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def test_reminders_manually(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually test the reminder system."""
    try:
        if not calendar_handler.is_authenticated:
            error_msg = "❌ Calendar not authenticated"
            if update.callback_query:
                await update.callback_query.edit_message_text(error_msg)
            elif update.message:
                await update.message.reply_text(error_msg)
            return
        
        # Send initial message
        initial_msg = "🧪 Testing reminder system..."
        if update.callback_query:
            await update.callback_query.edit_message_text(initial_msg)
        elif update.message:
            await update.message.reply_text(initial_msg)
        
        # Get events that would need reminders (with a wider time window for testing)
        events_needing_reminders = await calendar_handler.get_events_needing_reminders(
            minutes_before=60,  # Look 60 minutes ahead for testing
            at_event_time=True
        )
        
        if not events_needing_reminders:
            result_message = (
                "✅ **Reminder Test Complete**\n\n"
                "No upcoming events found in the next hour that need reminders.\n\n"
                "💡 Try creating a test event for a few minutes from now to see how reminders work!"
            )
        else:
            result_message = f"✅ **Reminder Test Complete**\n\n"
            result_message += f"Found {len(events_needing_reminders)} upcoming events that would trigger reminders:\n\n"
            
            for event in events_needing_reminders:
                time_str = event['start_datetime'].strftime('%I:%M %p')
                result_message += f"📅 **{event['title']}** at {time_str}\n"
                result_message += f"   ⏰ Reminder type: {event['reminder_type']}\n"
                result_message += f"   🕐 In {event['minutes_until']} minutes\n\n"
            
            result_message += "🔄 **The reminder system is working and will automatically send notifications!**"
        
        # Send result message
        if update.callback_query:
            await update.callback_query.edit_message_text(result_message, parse_mode='Markdown')
        elif update.message:
            await update.message.reply_text(result_message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error testing reminders: {e}")
        error_msg = f"❌ Error testing reminders: {str(e)}"
        
        try:
            if update.callback_query:
                await update.callback_query.edit_message_text(error_msg)
            elif update.message:
                await update.message.reply_text(error_msg)
        except Exception as fallback_error:
            logger.error(f"Error sending error message: {fallback_error}") 