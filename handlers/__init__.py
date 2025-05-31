# Handlers package for Personal AI Assistant Bot
# This package contains organized handler modules for different functionality

# Import all handlers that main.py needs
from .basic_commands import (
    start, help_command, stop_messages, status, 
    get_user_chat_id, set_user_chat_id
)

from .external_services import (
    weather_command, quote_command, fact_command, joke_command,
    motivation_command, meditation_command
)

from .calendar_commands import (
    calendar_setup, calendar_auth, calendar_events, create_meeting,
    reminder_settings, get_calendar_handler
)

from .ai_chat import (
    handle_message, get_ai_handler
)

from .callback_handlers import (
    handle_callback_query
)

from .scheduled_tasks import (
    send_daily_hi, send_calendar_reminders, send_scheduled_emails, send_scheduled_reminders
)

from .email_commands import (
    email_command, pending_emails_command, cancel_email_command,
    handle_email_confirmation, get_email_service
)

# Export all functions
__all__ = [
    # Basic commands
    'start', 'help_command', 'stop_messages', 'status', 'get_user_chat_id', 'set_user_chat_id',
    
    # AI chat
    'handle_message', 'get_ai_handler',
    
    # External services
    'weather_command', 'quote_command', 'fact_command', 'joke_command',
    'motivation_command', 'meditation_command',
    
    # Calendar integration
    'calendar_setup', 'calendar_auth', 'calendar_events', 'create_meeting',
    'reminder_settings', 'get_calendar_handler',
    
    # Email automation
    'email_command', 'pending_emails_command', 'cancel_email_command',
    
    # Callback handlers
    'handle_callback_query',
    
    # Scheduled tasks
    'send_daily_hi', 'send_calendar_reminders', 'send_scheduled_emails', 'send_scheduled_reminders'
] 