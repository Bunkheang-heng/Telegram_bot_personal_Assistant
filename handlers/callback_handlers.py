import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from handlers.external_services import (
    weather_command, quote_command, fact_command, joke_command, 
    motivation_command, meditation_command
)
from handlers.calendar_commands import (
    calendar_events, handle_meeting_confirmation, test_reminders_manually
)
from handlers.ai_chat import get_ai_handler
from handlers.email_commands import handle_email_confirmation

logger = logging.getLogger(__name__)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard button presses."""
    query = update.callback_query
    await query.answer()
    
    # Email confirmation callbacks
    if query.data.startswith("email_"):
        parts = query.data.split("_")
        if len(parts) >= 3:
            action = parts[1]  # "send" or "cancel"
            message_id = "_".join(parts[2:])  # Rest is message ID
            await handle_email_confirmation(update, context, action, message_id)
        return
    
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
            ai_handler = get_ai_handler()
            response = await ai_handler.generate_response(original_message, update.effective_user.first_name)
            chunks = ai_handler.split_long_message(response)
            
            for chunk in chunks:
                await query.message.reply_text(chunk)
                if len(chunks) > 1:
                    await asyncio.sleep(0.5)
        else:
            await query.edit_message_text("💬 Let's continue our conversation!") 