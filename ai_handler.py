import logging
import json
import os
import pytz
import google.generativeai as genai
from config import GEMINI_API_KEY, MODEL_NAME, MAX_MESSAGE_LENGTH
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AIHandler:
    """Handles AI conversations using Google Gemini."""
    
    def __init__(self):
        """Initialize the AI handler with Gemini configuration."""
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel(MODEL_NAME)
            self.is_available = True
            logger.info(f"AI Handler initialized with model: {MODEL_NAME}")
        else:
            self.model = None
            self.is_available = False
            logger.error("GEMINI_API_KEY not found - AI features disabled")
        
        # Load user profile
        self.user_profile = self.load_user_profile()
        
        # Calendar handler will be injected
        self.calendar_handler = None
        
        # Set Phnom Penh timezone
        self.timezone = pytz.timezone('Asia/Phnom_Penh')
    
    def load_user_profile(self) -> dict:
        """
        Load user profile information from bunkheang_profile.json.
        
        Returns:
            dict: User profile data or empty dict if file not found
        """
        try:
            profile_path = "bunkheang_profile.json"
            if os.path.exists(profile_path):
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                logger.info("User profile loaded successfully")
                return profile
            else:
                logger.warning("Profile file not found - using default settings")
                return {}
        except Exception as e:
            logger.error(f"Error loading user profile: {e}")
            return {}
    
    def get_profile_context(self) -> str:
        """
        Generate a context string from the user profile for AI prompting.
        
        Returns:
            str: Formatted profile context
        """
        if not self.user_profile:
            return ""
        
        context_parts = []
        
        # Basic info
        if self.user_profile.get('name'):
            context_parts.append(f"User name: {self.user_profile['name']}")
        
        if self.user_profile.get('location'):
            context_parts.append(f"Location: {self.user_profile['location']}")
        
        # Education
        if education := self.user_profile.get('education', {}).get('current'):
            edu_info = []
            for edu in education:
                edu_info.append(f"{edu.get('level')} in {edu.get('major')} at {edu.get('institution')}")
            context_parts.append(f"Education: {'; '.join(edu_info)}")
        
        # Skills
        if skills := self.user_profile.get('skills'):
            context_parts.append(f"Technical skills: {', '.join(skills[:10])}")  # Limit to first 10
        
        # Experience
        if experience := self.user_profile.get('experience'):
            exp_info = []
            for exp in experience[:2]:  # Limit to 2 most recent
                exp_info.append(f"{exp.get('role')} at {exp.get('organization')}")
            context_parts.append(f"Experience: {'; '.join(exp_info)}")
        
        # Interests
        if interests := self.user_profile.get('interests'):
            context_parts.append(f"Interests: {', '.join(interests)}")
        
        # Awards (recent ones)
        if awards := self.user_profile.get('awards'):
            context_parts.append(f"Recent achievements: {'; '.join(awards[:3])}")
        
        return "\n".join(context_parts)

    async def get_calendar_context(self, user_message: str) -> str:
        """
        Get calendar context if the message seems calendar-related.
        
        Args:
            user_message (str): The user's message
            
        Returns:
            str: Formatted calendar context or empty string
        """
        if not self.calendar_handler or not self.calendar_handler.is_authenticated:
            return ""
        
        # Check if message is calendar-related
        calendar_keywords = [
            'schedule', 'calendar', 'free', 'busy', 'available', 'appointment', 
            'meeting', 'event', 'today', 'tomorrow', 'next week', 'weekend',
            'morning', 'afternoon', 'evening', 'monday', 'tuesday', 'wednesday',
            'thursday', 'friday', 'saturday', 'sunday', 'plans', 'agenda'
        ]
        
        is_calendar_query = any(keyword in user_message.lower() for keyword in calendar_keywords)
        
        if not is_calendar_query:
            return ""
        
        try:
            # Get upcoming events for context
            events = await self.calendar_handler.get_events_data(max_results=10, days_ahead=7)
            
            if not events:
                return "\nCalendar Context: No upcoming events in the next 7 days."
            
            # Format events for AI context
            calendar_context = "\nCalendar Context - Upcoming Events:"
            today = self.get_current_phnom_penh_time().date()
            
            for event in events[:5]:  # Limit to 5 most relevant events
                event_date = event['start_datetime'].date()
                
                # Determine relative time
                if event_date == today:
                    date_str = "Today"
                elif event_date == today + timedelta(days=1):
                    date_str = "Tomorrow"
                elif event_date < today + timedelta(days=7):
                    date_str = event['start_datetime'].strftime('%A')  # Day of week
                else:
                    date_str = event['start_datetime'].strftime('%B %d')
                
                # Format time
                if event['is_all_day']:
                    time_str = "All day"
                else:
                    time_str = event['start_datetime'].strftime('%I:%M %p')
                
                calendar_context += f"\n- {event['title']} - {date_str} at {time_str}"
                
                if event['location']:
                    calendar_context += f" ({event['location']})"
            
            return calendar_context
            
        except Exception as e:
            logger.error(f"Error getting calendar context: {e}")
            return ""

    async def generate_response(self, user_message: str, user_name: str = None) -> str:
        """
        Generate a response to the user's message using Gemini AI with profile context.
        
        Args:
            user_message (str): The user's input message
            user_name (str): Optional user name for personalization
            
        Returns:
            str: The AI-generated response
            
        Raises:
            Exception: If there's an error generating the response
        """
        if not self.is_available:
            raise Exception("AI features are not available - missing API key")
        
        try:
            # Build enhanced prompt with profile context
            profile_context = self.get_profile_context()
            
            # Get calendar context if relevant
            calendar_context = await self.get_calendar_context(user_message)
            
            # Get accurate Phnom Penh time
            current_time = self.format_time_for_ai()
            
            enhanced_prompt = f"""You are Bunkheang's personal AI assistant. Here's what you know about him:

{profile_context}{calendar_context}

CURRENT TIME: {current_time}

Important guidelines:
- Write like you're having a natural conversation with a friend
- NO bullet points, NO asterisks, NO excessive formatting
- Use simple paragraphs and line breaks for structure
- Only use emojis naturally in conversation (1-2 per response max)
- Keep responses conversational, helpful, and easy to read on mobile
- Reference his background naturally without making it obvious you're reading from a profile
- If calendar context is provided, use it to answer schedule-related questions naturally
- For calendar queries like "am I free tomorrow?" or "what's on my schedule?", refer to the calendar context
- Use the CURRENT TIME above for any time-based responses or calculations

Calendar Management Abilities:
- I can directly create, delete, and manage calendar events
- I can clear entire schedules when requested
- I can answer questions about upcoming events using real calendar data
- When users ask about calendar management, let them know I can handle it directly

User message: {user_message}

Respond naturally and helpfully, as if you're a knowledgeable friend who knows Bunkheang well and has access to his calendar."""
            
            logger.info(f"Generating calendar-aware response for message: {user_message[:50]}...")
            response = self.model.generate_content(enhanced_prompt)
            
            if response.text:
                logger.info("Calendar-aware response generated successfully")
                return response.text.strip()
            else:
                raise Exception("Empty response from AI model")
                
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            raise
    
    def split_long_message(self, message: str) -> list:
        """
        Split long messages into chunks that fit Telegram's limits.
        
        Args:
            message (str): The message to split
            
        Returns:
            list: List of message chunks
        """
        if len(message) <= MAX_MESSAGE_LENGTH:
            return [message]
        
        chunks = []
        current_pos = 0
        
        while current_pos < len(message):
            # Find a good breaking point (prefer newlines, then spaces)
            end_pos = current_pos + MAX_MESSAGE_LENGTH
            
            if end_pos >= len(message):
                chunks.append(message[current_pos:])
                break
            
            # Try to break at a newline
            break_pos = message.rfind('\n', current_pos, end_pos)
            if break_pos == -1:
                # Try to break at a space
                break_pos = message.rfind(' ', current_pos, end_pos)
                if break_pos == -1:
                    # Force break at character limit
                    break_pos = end_pos
            
            chunks.append(message[current_pos:break_pos])
            current_pos = break_pos + 1 if break_pos < end_pos else break_pos
        
        logger.info(f"Split message into {len(chunks)} chunks")
        return chunks

    def set_calendar_handler(self, calendar_handler):
        """Set the calendar handler for calendar-aware responses."""
        self.calendar_handler = calendar_handler
        logger.info("Calendar handler set for AI - calendar-aware responses enabled")

    async def detect_calendar_action(self, user_message: str) -> dict:
        """
        Detect if the user wants to perform a calendar action.
        
        Args:
            user_message (str): The user's message
            
        Returns:
            dict: Action details or empty dict if no action detected
        """
        message_lower = user_message.lower()
        
        # More specific action patterns
        create_patterns = [
            'schedule a', 'add to calendar', 'create meeting', 'book appointment',
            'set reminder', 'plan meeting', 'i have class at', 'i have meeting at',
            'schedule meeting', 'book a', 'arrange meeting', 'set up meeting',
            'create appointment', 'can you set me', 'set me a', 'can you schedule',
            'can you create', 'can you add', 'can you book', 'set a schedule',
            'make me a', 'add a', 'put on my calendar', 'schedule for me'
        ]
        
        delete_patterns = [
            'remove my', 'delete my', 'cancel my', 'clear my schedule', 'remove my schedule',
            'delete all events', 'clear all events', 'remove all meetings', 'cancel all',
            'clear my calendar', 'remove everything', 'delete everything',
            'i want to remove all', 'delete all my', 'remove all of my',
            'remove all my meetings', 'delete all my meetings', 'cancel all my meetings',
            'clear all my events', 'remove all my events', 'delete all my events'
        ]
        
        # Exclude query patterns that shouldn't trigger actions
        query_patterns = [
            'what\'s on my', 'what do i have', 'am i free', 'do i have', 'check my',
            'show my', 'when is my', 'any meetings', 'any events today', 'any events tomorrow',
            'schedule today', 'schedule tomorrow', 'busy today', 'busy tomorrow'
        ]
        
        # First check if it's clearly a query (should not trigger action)
        if any(pattern in message_lower for pattern in query_patterns):
            return {}
        
        # Check for deletion actions
        if any(pattern in message_lower for pattern in delete_patterns):
            # Check if it's specifically targeting meetings/events type vs everything
            if 'all my meetings' in message_lower or 'all my events' in message_lower:
                # Extract the specific type to delete
                if 'meetings' in message_lower:
                    return {
                        'action': 'delete_pattern',
                        'pattern': 'meeting'
                    }
                elif 'events' in message_lower:
                    return {
                        'action': 'delete_pattern',
                        'pattern': 'event'
                    }
            elif 'clear my schedule' in message_lower or 'clear my calendar' in message_lower or 'clear all' in message_lower:
                # Check for confirmation words
                confirmation_words = ['yes', 'sure', 'confirm', 'definitely', 'absolutely']
                confirmed = any(word in message_lower for word in confirmation_words)
                return {
                    'action': 'clear_all',
                    'confirmed': confirmed
                }
            else:
                # Extract what they want to delete
                pattern = self._extract_delete_pattern(user_message)
                return {
                    'action': 'delete_pattern',
                    'pattern': pattern
                }
        
        # Check for creation actions
        if any(pattern in message_lower for pattern in create_patterns):
            return {
                'action': 'create'
            }
        
        return {}

    async def detect_email_action(self, user_message: str) -> dict:
        """
        Detect if the user wants to send an email.
        
        Args:
            user_message (str): The user's message
            
        Returns:
            dict: Email action details or empty dict if no action detected
        """
        message_lower = user_message.lower()
        
        # Email action patterns
        email_patterns = [
            'send email', 'email', 'send an email', 'send a message',
            'send to', 'email to', 'message to', 'write to',
            'send reminder', 'send notification', 'notify',
            'compose email', 'draft email', 'send mail'
        ]
        
        # Check if message contains email patterns and an email address
        import re
        email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        has_email_address = bool(re.search(email_regex, user_message))
        
        # Check for email action patterns
        has_email_pattern = any(pattern in message_lower for pattern in email_patterns)
        
        if has_email_pattern and has_email_address:
            return {
                'action': 'send_email',
                'message': user_message
            }
        
        return {}

    def _extract_delete_pattern(self, message: str) -> str:
        """Extract what the user wants to delete from the message."""
        # Simple extraction - look for common patterns
        message_lower = message.lower()
        
        # Look for specific event types
        if 'meeting' in message_lower:
            return 'meeting'
        elif 'class' in message_lower:
            return 'class'
        elif 'appointment' in message_lower:
            return 'appointment'
        elif 'call' in message_lower:
            return 'call'
        
        # Default to looking for quoted text or specific terms
        import re
        quoted_match = re.search(r'"([^"]*)"', message)
        if quoted_match:
            return quoted_match.group(1)
        
        return ''

    async def execute_calendar_action(self, action_info: dict, user_message: str) -> str:
        """
        Execute a calendar action based on the detected action.
        
        Args:
            action_info (dict): Action details from detect_calendar_action
            user_message (str): Original user message
            
        Returns:
            str: Result message
        """
        if not self.calendar_handler or not self.calendar_handler.is_authenticated:
            return "❌ Calendar not available. Please set up calendar authentication first."
        
        try:
            action = action_info.get('action')
            
            if action == 'clear_all':
                if action_info.get('confirmed'):
                    result = await self.calendar_handler.clear_all_events()
                    return f"🗑️ **Calendar Cleared**\n\n{result}"
                else:
                    return ("⚠️ **Clear All Events?**\n\n"
                           "This will delete ALL your upcoming events. "
                           "Please confirm by saying 'yes, I'm sure' or similar.")
            
            elif action == 'delete_pattern':
                pattern = action_info.get('pattern', '')
                if pattern:
                    result = await self.calendar_handler.delete_events_by_title(pattern)
                    return f"🗑️ **Events Deleted**\n\n{result}"
                else:
                    return "❌ Please specify what events you want to delete (e.g., 'delete all meetings')"
            
            elif action == 'create':
                # Parse and create the event
                meeting_details = await self.calendar_handler.parse_meeting_request(user_message)
                if meeting_details:
                    result = await self.calendar_handler.create_calendar_event(meeting_details)
                    return f"📅 **Event Created by AI**\n\n{result}"
                else:
                    return "❌ I couldn't understand the meeting details. Please provide more information."
            
            return "❌ Unknown calendar action"
            
        except Exception as e:
            logger.error(f"Error executing calendar action: {e}")
            return f"❌ Error performing calendar action: {str(e)}"

    async def execute_email_action(self, action_info: dict, user_message: str) -> str:
        """
        Execute an email action based on the detected action.
        
        Args:
            action_info (dict): Action details from detect_email_action
            user_message (str): Original user message
            
        Returns:
            str: Result message
        """
        try:
            # Import email service here to avoid circular imports
            from handlers.email_commands import get_email_service
            
            email_service = get_email_service()
            
            if not email_service.is_available():
                return ("❌ **Email service not configured**\n\n"
                       "To enable email automation, please set up your email credentials in the environment variables.")
            
            action = action_info.get('action')
            
            if action == 'send_email':
                # Parse the email request using AI
                email_data = await email_service.parse_email_request(user_message)
                
                if not email_data:
                    return ("❌ **Could not parse email request**\n\n"
                           "Please include the recipient email address and what you want to say.")
                
                # Debug: Log what Gemini parsed
                logger.info(f"Gemini parsed send_time as: '{email_data['send_time']}'")
                
                # Parse send time with better error handling
                send_time = None
                send_time_str = email_data['send_time']
                
                if send_time_str and send_time_str.lower() != 'now':
                    send_time = email_service.parse_send_time(send_time_str)
                    if send_time:
                        logger.info(f"Parsed send_time: {send_time}")
                    else:
                        logger.warning(f"Failed to parse send_time: '{send_time_str}', defaulting to 'now'")
                
                # Get current time for comparison
                current_time = datetime.now(email_service.timezone)
                logger.info(f"Current time: {current_time}")
                
                # Decision logic: schedule vs immediate send
                should_schedule = False
                if send_time:
                    # Handle same-minute race condition
                    current_minute = current_time.replace(second=0, microsecond=0)
                    scheduled_minute = send_time.replace(second=0, microsecond=0)
                    
                    if scheduled_minute == current_minute:
                        # If scheduled for current minute, move to next minute to avoid race condition
                        send_time = send_time.replace(minute=send_time.minute + 1, second=0, microsecond=0)
                        logger.info(f"Adjusted time to avoid race condition: {send_time}")
                    
                    if send_time > current_time:
                        should_schedule = True
                        time_diff_seconds = (send_time - current_time).total_seconds()
                        logger.info(f"Scheduling email for future time: {send_time} (in {time_diff_seconds:.0f} seconds)")
                    else:
                        logger.info(f"Sending email immediately (send_time: {send_time}, current: {current_time})")
                else:
                    logger.info(f"No valid send_time, sending immediately")
                
                if should_schedule:
                    # Schedule for later
                    email_id = email_service.save_pending_email(email_data, send_time)
                    time_str = send_time.strftime('%Y-%m-%d at %H:%M')
                    
                    return (f"⏰ **Email scheduled successfully!**\n\n"
                           f"📧 Your email to {email_data['recipient_email']} will be sent on {time_str}.\n"
                           f"📝 **Subject:** {email_data['subject']}\n"
                           f"🆔 **Email ID:** `{email_id}`")
                else:
                    # Send immediately
                    result = await email_service.send_email_now(
                        email_data['recipient_email'],
                        email_data['subject'],
                        email_data['body']
                    )
                    
                    if result['success']:
                        return (f"✅ **Email sent successfully!**\n\n"
                               f"📧 Your email to {email_data['recipient_email']} has been sent.\n"
                               f"📝 **Subject:** {email_data['subject']}")
                    else:
                        return f"❌ **Failed to send email**\n\n{result['message']}"
            
            return "❌ Unknown email action"
            
        except Exception as e:
            logger.error(f"Error executing email action: {e}")
            return f"❌ Error performing email action: {str(e)}"

    def get_current_phnom_penh_time(self) -> datetime:
        """Get current time in Phnom Penh timezone."""
        return datetime.now(self.timezone)
    
    def format_time_for_ai(self, dt: datetime = None) -> str:
        """Format datetime for AI with clear timezone information."""
        if dt is None:
            dt = self.get_current_phnom_penh_time()
        
        return (f"{dt.strftime('%Y-%m-%d %H:%M:%S %A')} "
                f"(Phnom Penh time, Cambodia - UTC+7)")

    async def detect_reminder_action(self, user_message: str) -> dict:
        """
        Detect if the user wants to set a personal reminder.
        
        Args:
            user_message (str): The user's message
            
        Returns:
            dict: Reminder action details or empty dict if no action detected
        """
        message_lower = user_message.lower()
        
        # Reminder action patterns (improved and expanded)
        reminder_patterns = [
            'remind me', 'reminds me', 'notify me', 'tell me', 'alert me',
            'set a reminder', 'set reminder', 'reminder',
            'wake me up', 'ping me', 'buzz me',
            'don\'t let me forget', 'make sure i remember',
            'you have to notify', 'you have to remind',
            'you have to tell', 'need to remind', 'need to notify'
        ]
        
        # Time-based patterns that strongly suggest reminders
        time_patterns = [
            r'at \d{1,2}:\d{2}(am|pm)?',  # "at 1:45", "at 2:05PM", "at 13:20"
            r'at \d{1,2}(am|pm)',         # "at 2pm", "at 9am"
            r'in \d+\s*(minute|hour|min|hr)',  # "in 30 minutes", "in 2 hours"
            r'tomorrow at \d',            # "tomorrow at 2"
            r'later today',
            r'tonight at',
            r'today at \d',               # "today at 3"
            r'\d{1,2}:\d{2}(am|pm)?.*remind',  # "2:05PM reminds me"
            r'\d{1,2}(am|pm).*remind'          # "2PM reminds me"
        ]
        
        # Special patterns for messages that start with time
        time_start_patterns = [
            r'^at \d{1,2}:\d{2}(am|pm)?',  # Message starts with "at 2:05PM"
            r'^at \d{1,2}(am|pm)',         # Message starts with "at 2pm"
            r'^\d{1,2}:\d{2}(am|pm)?',     # Message starts with "2:05PM"
        ]
        
        # Email patterns to exclude (these should go to email system instead)
        email_exclusion_patterns = [
            'send email', 'email to', 'email ', 'send to', 'compose email'
        ]
        
        # Calendar patterns to exclude (these should go to calendar system instead)
        calendar_exclusion_patterns = [
            'schedule', 'calendar', 'create meeting', 'add to calendar',
            'meeting with', 'appointment with', 'book ', 'i have class',
            'i have meeting', 'schedule meeting'
        ]
        
        # Check if it contains an email address (exclude from reminders)
        if '@' in user_message:
            logger.info(f"Message excluded from reminders due to email address: {user_message}")
            return {}
        
        # Check if it's an email or calendar request (exclude from reminders)
        if any(pattern in message_lower for pattern in email_exclusion_patterns):
            logger.info(f"Message excluded from reminders due to email pattern: {user_message}")
            return {}
        
        if any(pattern in message_lower for pattern in calendar_exclusion_patterns):
            logger.info(f"Message excluded from reminders due to calendar pattern: {user_message}")
            return {}
        
        # Check for explicit reminder patterns
        has_reminder_pattern = any(pattern in message_lower for pattern in reminder_patterns)
        
        # Check for time patterns (suggesting a reminder context)
        import re
        has_time_pattern = any(re.search(pattern, message_lower) for pattern in time_patterns)
        has_time_start_pattern = any(re.search(pattern, message_lower) for pattern in time_start_patterns)
        
        # Log detection results for debugging
        logger.info(f"Reminder detection for '{user_message}':")
        logger.info(f"  - reminder_pattern={has_reminder_pattern}")
        logger.info(f"  - time_pattern={has_time_pattern}")
        logger.info(f"  - time_start_pattern={has_time_start_pattern}")
        logger.info(f"  - contains 'me'={'me' in message_lower}")
        logger.info(f"  - contains 'i'={'i' in message_lower}")
        
        # Detect as reminder if:
        # 1. Has explicit reminder words, OR
        # 2. Has time pattern + personal context (contains "me" or "i"), OR
        # 3. Starts with time + has personal context (strong indicator)
        if has_reminder_pattern:
            logger.info(f"✅ Detected reminder action due to explicit reminder pattern")
            return {
                'action': 'set_reminder',
                'message': user_message
            }
        elif (has_time_pattern or has_time_start_pattern) and ('me' in message_lower or 'i' in message_lower):
            # Time pattern + personal context suggests reminder
            logger.info(f"✅ Detected reminder action due to time pattern + personal context")
            return {
                'action': 'set_reminder',
                'message': user_message
            }
        elif has_time_start_pattern and len(user_message) > 20:
            # Message starts with time and is reasonably long (likely a reminder)
            logger.info(f"✅ Detected reminder action due to time-start pattern + length")
            return {
                'action': 'set_reminder',
                'message': user_message
            }
        
        logger.info(f"❌ No reminder action detected for: {user_message}")
        return {}

    async def execute_reminder_action(self, action_info: dict, user_message: str) -> str:
        """
        Execute a reminder action based on the detected action.
        
        Args:
            action_info (dict): Action details from detect_reminder_action
            user_message (str): Original user message
            
        Returns:
            str: Result message
        """
        try:
            # Import reminder service here to avoid circular imports
            from reminder_service import ReminderService
            
            reminder_service = ReminderService()
            action = action_info.get('action')
            
            if action == 'set_reminder':
                # Parse the reminder request using AI
                reminder_data = await reminder_service.parse_reminder_request(user_message)
                
                if not reminder_data:
                    return ("❌ **Could not parse reminder request**\n\n"
                           "Please try again with a clearer format like:\n"
                           "• 'Remind me at 2 PM to do homework'\n"
                           "• 'At 1:20 PM notify me to play chess'\n"
                           "• 'In 30 minutes remind me to call mom'")
                
                # Debug: Log what Gemini parsed
                logger.info(f"Gemini parsed remind_time as: '{reminder_data['remind_time']}'")
                
                # Parse remind time with better error handling
                remind_time = None
                remind_time_str = reminder_data['remind_time']
                
                if remind_time_str and remind_time_str.lower() != 'now':
                    remind_time = reminder_service.parse_remind_time(remind_time_str)
                    if remind_time:
                        logger.info(f"Parsed remind_time: {remind_time}")
                    else:
                        logger.warning(f"Failed to parse remind_time: '{remind_time_str}', defaulting to 'now'")
                
                # Get current time for comparison
                current_time = datetime.now(reminder_service.timezone)
                logger.info(f"Current time: {current_time}")
                
                # Decision logic: schedule vs immediate reminder
                should_schedule = False
                if remind_time:
                    # Handle same-minute race condition
                    current_minute = current_time.replace(second=0, microsecond=0)
                    scheduled_minute = remind_time.replace(second=0, microsecond=0)
                    
                    if scheduled_minute == current_minute:
                        # If scheduled for current minute, move to next minute to avoid race condition
                        remind_time = remind_time.replace(minute=remind_time.minute + 1, second=0, microsecond=0)
                        logger.info(f"Adjusted remind time to avoid race condition: {remind_time}")
                    
                    if remind_time > current_time:
                        should_schedule = True
                        time_diff_seconds = (remind_time - current_time).total_seconds()
                        logger.info(f"Scheduling reminder for future time: {remind_time} (in {time_diff_seconds:.0f} seconds)")
                    else:
                        logger.info(f"Sending reminder immediately (remind_time: {remind_time}, current: {current_time})")
                else:
                    logger.info(f"No valid remind_time, sending immediately")
                
                if should_schedule:
                    # Schedule for later
                    reminder_id = reminder_service.save_pending_reminder(reminder_data, remind_time)
                    time_str = remind_time.strftime('%Y-%m-%d at %H:%M')
                    
                    return (f"⏰ **Reminder set successfully!**\n\n"
                           f"📝 I'll remind you: {reminder_data['reminder_text']}\n"
                           f"⏰ **Scheduled for:** {time_str}\n"
                           f"🆔 **Reminder ID:** `{reminder_id}`\n\n"
                           f"💡 I'll send you a friendly Telegram message at the right time!")
                else:
                    # Send immediately (this would be unusual for reminders, but handle it)
                    formatted_message = reminder_service.format_reminder_message(reminder_data['reminder_text'])
                    return f"🔔 **Immediate Reminder:**\n\n{formatted_message}"
            
            return "❌ Unknown reminder action"
            
        except Exception as e:
            logger.error(f"Error executing reminder action: {e}")
            return f"❌ Error setting reminder: {str(e)}" 