"""
Email Commands Handler for Telegram Bot

This module handles email-related commands and interactions.
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from email_service import EmailService

logger = logging.getLogger(__name__)

# Initialize email service
email_service = EmailService()

async def email_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /email command for natural language email requests."""
    try:
        if not email_service.is_available():
            await update.message.reply_text(
                "❌ **Email service not configured**\n\n"
                "To enable email automation, please set up your email credentials in the environment variables:\n"
                "• EMAIL_USERNAME\n"
                "• EMAIL_PASSWORD\n"
                "• EMAIL_SMTP_SERVER (optional, defaults to Gmail)\n"
                "• EMAIL_SMTP_PORT (optional, defaults to 587)",
                parse_mode='Markdown'
            )
            return
        
        # Get the email request from the command arguments
        if context.args:
            email_request = ' '.join(context.args)
        else:
            await update.message.reply_text(
                "📧 **Email Automation**\n\n"
                "Tell me what email you want to send in natural language!\n\n"
                "**Examples:**\n"
                "• `/email Send john@example.com about meeting tomorrow at 9 AM`\n"
                "• `/email Email team@company.com project update now`\n"
                "• `/email Send reminder to client@business.com about deadline Friday at 2 PM`\n\n"
                "**Usage:** `/email [your natural language request]`",
                parse_mode='Markdown'
            )
            return
        
        # Show processing message
        processing_msg = await update.message.reply_text("🤖 Processing your email request...")
        
        # Parse the email request using AI
        email_data = await email_service.parse_email_request(email_request)
        
        if not email_data:
            await processing_msg.edit_text(
                "❌ **Could not parse email request**\n\n"
                "Please try again with a clearer format:\n"
                "• Include the recipient email address\n"
                "• Specify what the email should say\n"
                "• Optionally mention when to send it\n\n"
                "**Example:** `/email Send john@example.com reminder about meeting tomorrow`",
                parse_mode='Markdown'
            )
            return
        
        # Parse send time
        send_time = email_service.parse_send_time(email_data['send_time'])
        if not send_time:
            send_time = datetime.now(email_service.timezone)
            email_data['send_time'] = 'now'
        
        # Show preview and confirmation
        preview_text = email_service.format_email_preview(email_data)
        
        # Create confirmation buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ Send", callback_data=f"email_send_{update.message.message_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"email_cancel_{update.message.message_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Store email data for confirmation callback
        context.bot_data[f"email_data_{update.message.message_id}"] = {
            'email_data': email_data,
            'send_time': send_time
        }
        
        await processing_msg.edit_text(
            f"{preview_text}\n\n" + 
            "❓ **Confirm sending this email?**",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error in email command: {e}")
        await update.message.reply_text(
            f"❌ **Error processing email request:** {str(e)}",
            parse_mode='Markdown'
        )

async def pending_emails_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show pending scheduled emails."""
    try:
        if not email_service.is_available():
            await update.message.reply_text(
                "❌ Email service not configured.",
                parse_mode='Markdown'
            )
            return
        
        pending_emails = email_service.get_pending_emails()
        
        if not pending_emails:
            await update.message.reply_text(
                "📭 **No pending emails**\n\n"
                "You don't have any emails scheduled for later.\n"
                "Use `/email` to schedule new emails!",
                parse_mode='Markdown'
            )
            return
        
        # Format pending emails list
        message = "📬 **Pending Scheduled Emails**\n\n"
        
        for i, email in enumerate(pending_emails[:10], 1):  # Limit to 10 emails
            scheduled_time = datetime.fromisoformat(email['scheduled_time'])
            time_str = scheduled_time.strftime('%Y-%m-%d %H:%M')
            
            message += (
                f"**{i}.** `{email['id']}`\n"
                f"👤 **To:** {email['recipient']}\n"
                f"📝 **Subject:** {email['subject'][:50]}{'...' if len(email['subject']) > 50 else ''}\n"
                f"⏰ **Scheduled:** {time_str}\n"
                f"🔹 **Priority:** {email['priority'].title()}\n\n"
            )
        
        if len(pending_emails) > 10:
            message += f"... and {len(pending_emails) - 10} more emails\n\n"
        
        message += "💡 Use `/cancel_email <email_id>` to cancel a scheduled email"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error showing pending emails: {e}")
        await update.message.reply_text(
            f"❌ **Error:** {str(e)}",
            parse_mode='Markdown'
        )

async def cancel_email_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel a pending email."""
    try:
        if not context.args:
            await update.message.reply_text(
                "📧 **Cancel Scheduled Email**\n\n"
                "**Usage:** `/cancel_email <email_id>`\n\n"
                "Use `/pending_emails` to see your scheduled emails and their IDs.",
                parse_mode='Markdown'
            )
            return
        
        email_id = context.args[0]
        
        if email_service.cancel_pending_email(email_id):
            await update.message.reply_text(
                f"✅ **Email cancelled successfully**\n\n"
                f"Email `{email_id}` has been cancelled and will not be sent.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ **Could not cancel email**\n\n"
                f"Email `{email_id}` was not found or already sent.\n"
                f"Use `/pending_emails` to see your current scheduled emails.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error cancelling email: {e}")
        await update.message.reply_text(
            f"❌ **Error:** {str(e)}",
            parse_mode='Markdown'
        )

async def handle_email_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, message_id: str) -> None:
    """Handle email confirmation callbacks."""
    try:
        query = update.callback_query
        await query.answer()
        
        # Get stored email data
        email_key = f"email_data_{message_id}"
        if email_key not in context.bot_data:
            await query.edit_message_text(
                "❌ **Email session expired**\n\n"
                "Please use `/email` command again to send emails.",
                parse_mode='Markdown'
            )
            return
        
        stored_data = context.bot_data[email_key]
        email_data = stored_data['email_data']
        send_time = stored_data['send_time']
        
        if action == "send":
            # Check if immediate or scheduled
            current_time = datetime.now(email_service.timezone)
            
            if email_data['send_time'].lower() == 'now' or send_time <= current_time:
                # Send immediately
                result = await email_service.send_email_now(
                    email_data['recipient_email'],
                    email_data['subject'],
                    email_data['body']
                )
                
                if result['success']:
                    await query.edit_message_text(
                        f"✅ **Email sent successfully!**\n\n"
                        f"📧 Your email to {email_data['recipient_email']} has been sent.\n"
                        f"📝 **Subject:** {email_data['subject']}",
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text(
                        f"❌ **Failed to send email**\n\n"
                        f"{result['message']}",
                        parse_mode='Markdown'
                    )
            else:
                # Schedule for later
                email_id = email_service.save_pending_email(email_data, send_time)
                time_str = send_time.strftime('%Y-%m-%d at %H:%M')
                
                await query.edit_message_text(
                    f"⏰ **Email scheduled successfully!**\n\n"
                    f"📧 Your email to {email_data['recipient_email']} will be sent on {time_str}.\n"
                    f"📝 **Subject:** {email_data['subject']}\n"
                    f"🆔 **Email ID:** `{email_id}`\n\n"
                    f"💡 Use `/pending_emails` to view all scheduled emails\n"
                    f"💡 Use `/cancel_email {email_id}` to cancel if needed",
                    parse_mode='Markdown'
                )
        
        elif action == "cancel":
            await query.edit_message_text(
                "❌ **Email cancelled**\n\n"
                "The email will not be sent. Use `/email` to create a new email.",
                parse_mode='Markdown'
            )
        
        # Clean up stored data
        if email_key in context.bot_data:
            del context.bot_data[email_key]
            
    except Exception as e:
        logger.error(f"Error in email confirmation: {e}")
        await query.edit_message_text(
            f"❌ **Error:** {str(e)}",
            parse_mode='Markdown'
        )

# Email service getter for other modules
def get_email_service():
    """Get the email service instance."""
    return email_service 