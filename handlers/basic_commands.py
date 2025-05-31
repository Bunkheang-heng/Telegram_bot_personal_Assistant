import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Global variables
USER_CHAT_ID = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    global USER_CHAT_ID
    USER_CHAT_ID = update.effective_chat.id
    
    welcome_message = (
        '👋 **Hey Bunkheang! Your assistant is back online**\n\n'
        '🤖 Ready to help you crush your goals today, my friend!\n\n'
        '✨ **Here\'s what I\'ve got ready for you:**\n'
        '📅 Keep your crazy schedule organized (I know how busy you get!)\n'
        '🌤️ Your daily Phnom Penh weather (perfect for those campus walks)\n'
        '💻 Chat about your CS projects and coding challenges\n'
        '🎯 Keep you motivated through those late study sessions\n'
        '📚 Help with university coursework and development work\n'
        '💼 Support your professional growth and side projects\n\n'
        '🕐 **Your Daily Check-in:** Every evening at 5:10 PM (our routine!)\n'
        '🧠 **I remember everything:** Your background, preferences, and goals\n\n'
        '💬 **Just talk to me like you always do!** I\'m here for whatever you need, Bunkheang.'
    )
    
    # Create personalized quick actions for Bunkheang
    keyboard = [
        [
            InlineKeyboardButton("🌤️ Phnom Penh Weather", callback_data="weather"),
            InlineKeyboardButton("📅 My Schedule Today", callback_data="calendar_events")
        ],
        [
            InlineKeyboardButton("💪 Motivate Me", callback_data="motivation"),
            InlineKeyboardButton("🧘 Quick Break", callback_data="meditation")
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
        "🤖 **Your Personal Assistant Manual, Bunkheang**\n\n"
        
        "**📅 Smart Calendar (The way you like it):**\n"
        "• *'I have Database class tomorrow at 8AM'* - I'll add it instantly\n"
        "• *'Remove all my meetings today'* - Consider it done\n"
        "• *'Clear my entire schedule'* - Fresh start, I got you\n"
        "• *'What's my day looking like?'* - I'll tell you everything\n"
        "• *'Am I free tomorrow afternoon?'* - Real-time availability check\n"
        "• No confirmations needed - I know what you want!\n\n"
        
        "**📧 Email Magic (Because you're always busy):**\n"
        "• `/email Send prof@university.edu about assignment extension tomorrow 9 AM`\n"
        "• `/email Email team@hackathon.com project update now`\n"
        "• `/pending_emails` - See what's queued up\n"
        "• `/cancel_email <id>` - Changed your mind? No problem\n"
        "• Just tell me who, what, and when - I handle the rest!\n\n"
        
        "**⏰ Your Personal Reminder System:**\n"
        "• I'll text you 15 minutes before every event (never miss class again!)\n"
        "• Plus a heads-up right when things start\n"
        "• Works automatically - no setup needed\n"
        "• `/reminders` - Check how it's working for you\n\n"
        
        "**🌤️ Weather (For your daily plans):**\n"
        "• `/weather` - Phnom Penh updates (your home base)\n"
        "• `/weather [any city]` - Planning a trip?\n"
        "• Perfect for deciding on that morning jog!\n\n"
        
        "**💬 Real Talk (Like we always do):**\n"
        "• Discuss your CS assignments and projects\n"
        "• Debug coding problems together\n"
        "• Talk through your career plans\n"
        "• I know your background - no need to explain everything!\n\n"
        
        "**🎯 Daily Motivation (For those tough days):**\n"
        "• `/motivation` - When you need a push\n"
        "• `/meditation` - Take a breather\n"
        "• `/quote` - Some wisdom\n"
        "• `/status` - Check how everything's running\n\n"
        
        "**🧠 Just Talk Naturally (Examples):**\n"
        "• *'Schedule team meeting for Monday 2PM in the lab'*\n"
        "• *'Delete all my study sessions this week'*\n"
        "• *'Email my professor about the project deadline tomorrow'*\n"
        "• *'What's the weather for my campus walk?'*\n"
        "• *'Help me prep for my algorithm presentation'*\n\n"
        
        "**⚙️ If You Need Manual Control:**\n"
        "• `/create_meeting` - Step-by-step event creation\n"
        "• `/calendar_events` - Full calendar view\n"
        "• `/calendar_setup` - Fix calendar connection\n"
        "• `/stop` - Pause our daily chats\n"
        "• `/start` - Get me back online\n\n"
        
        "💡 **Remember Bunkheang:** Just talk to me normally! I understand your context, know your schedule, and can handle most things without asking for confirmation. I'm here to make your life easier, not add more steps!"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def stop_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop daily messages."""
    global USER_CHAT_ID
    USER_CHAT_ID = None
    await update.message.reply_text(
        '😴 **Okay Bunkheang, I\'ll pause our daily check-ins**\n\n'
        'I\'m still here for everything else though! Chat with me anytime.\n'
        'Hit /start when you want our evening routine back.'
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check status of daily messages and features."""
    global USER_CHAT_ID
    
    status_message = "📊 **System Status Report for Bunkheang**\n\n"
    
    if USER_CHAT_ID:
        status_message += "✅ **Daily Check-ins:** Active (5:10 PM routine)\n"
        status_message += "🤝 **Personal Assistant Mode:** Full engagement\n"
        status_message += "🎯 **Enhanced Features:** All systems go\n\n"
    else:
        status_message += "😴 **Daily Check-ins:** Paused (you asked me to stop)\n\n"
    
    # Import services here to avoid circular imports
    from services import ExternalServices
    services = ExternalServices()
    
    status_message += "🔧 **Your Available Tools:**\n"
    status_message += "🤖 AI Conversations: ✅ Ready to chat\n"
    status_message += f"🌤️ Weather Updates: {'✅ Phnom Penh ready' if services.session else '❌ Connection issue'}\n"
    status_message += "💡 Daily Quotes: ✅ Inspiration loaded\n"
    status_message += "🧠 Random Facts: ✅ Knowledge ready\n"
    status_message += "😄 Humor Mode: ✅ Jokes on standby\n"
    status_message += "🧘 Mindfulness: ✅ Calm moments available\n\n"
    
    status_message += "💬 **Ready when you are!** Just say what you need, Bunkheang."
    
    await update.message.reply_text(status_message, parse_mode='Markdown')

def get_user_chat_id():
    """Get the current user chat ID."""
    return USER_CHAT_ID

def set_user_chat_id(chat_id):
    """Set the user chat ID."""
    global USER_CHAT_ID
    USER_CHAT_ID = chat_id 