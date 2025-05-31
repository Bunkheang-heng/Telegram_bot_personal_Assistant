import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from calendar_handler import CalendarHandler
from config import ENABLE_CALENDAR_REMINDERS, REMINDER_MINUTES_BEFORE, REMINDER_CHECK_INTERVAL_MINUTES, REMINDER_AT_EVENT_TIME

logger = logging.getLogger(__name__)

# Initialize calendar handler
calendar_handler = CalendarHandler()
calendar_handler.load_credentials()

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

def get_calendar_handler():
    """Get the calendar handler instance."""
    return calendar_handler 