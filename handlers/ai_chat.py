import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from ai_handler import AIHandler

logger = logging.getLogger(__name__)

# Initialize AI handler
ai_handler = AIHandler()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle general text messages."""
    try:
        user_message = update.message.text
        user_name = update.effective_user.first_name
        
        logger.info(f"Received message from {user_name}: {user_message}")
        
        # Import calendar handler here to avoid circular imports
        from handlers.calendar_commands import get_calendar_handler
        calendar_handler = get_calendar_handler()
        
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
        
        # Check for reminder actions FIRST (before emails to avoid conflicts)
        reminder_action = await ai_handler.detect_reminder_action(user_message)
        
        if reminder_action:
            await update.message.reply_chat_action(ChatAction.TYPING)
            
            # Execute the reminder action
            result = await ai_handler.execute_reminder_action(reminder_action, user_message)
            
            # Send the result
            chunks = ai_handler.split_long_message(result)
            for chunk in chunks:
                await update.message.reply_text(chunk, parse_mode='Markdown')
                if len(chunks) > 1:
                    await asyncio.sleep(0.5)
            
            logger.info(f"Reminder action executed for {user_name}: {reminder_action.get('action')}")
            return
        
        # Check for email actions
        email_action = await ai_handler.detect_email_action(user_message)
        
        if email_action:
            await update.message.reply_chat_action(ChatAction.TYPING)
            
            # Execute the email action
            result = await ai_handler.execute_email_action(email_action, user_message)
            
            # Send the result
            chunks = ai_handler.split_long_message(result)
            for chunk in chunks:
                await update.message.reply_text(chunk, parse_mode='Markdown')
                if len(chunks) > 1:
                    await asyncio.sleep(0.5)
            
            logger.info(f"Email action executed for {user_name}: {email_action.get('action')}")
            return
        
        # If no calendar or email action detected, handle as regular AI conversation
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

def get_ai_handler():
    """Get the AI handler instance."""
    return ai_handler 