"""
Personal Reminder Service for Telegram Bot

This module handles personal reminder/notification scheduling for direct Telegram messages.
"""

import logging
import json
import os
import re
import pytz
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import google.generativeai as genai
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

class ReminderService:
    """Handles personal reminder scheduling and delivery via Telegram messages."""
    
    def __init__(self):
        """Initialize the reminder service."""
        self.timezone = pytz.timezone('Asia/Phnom_Penh')
        
        # File to store pending reminders
        self.pending_reminders_file = 'pending_reminders.json'
        
        # Initialize Gemini for reminder parsing
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.gemini_model = None
            logger.warning("Gemini API key not found - reminder parsing will be limited")
        
        logger.info("Reminder service initialized")
    
    async def parse_reminder_request(self, user_message: str) -> Optional[Dict[str, Any]]:
        """
        Parse natural language reminder request using AI.
        
        Args:
            user_message (str): Natural language reminder request
            
        Returns:
            Dict: Parsed reminder details or None if parsing fails
        """
        if not self.gemini_model:
            return None
        
        try:
            # Get current Phnom Penh time for context
            current_time = datetime.now(self.timezone)
            current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S %A')
            
            prompt = f"""
            Parse this reminder request and extract the following information:
            
            CURRENT TIME: {current_time_str} (Phnom Penh time, Cambodia - UTC+7)
            
            - reminder_text: What to remind about (the main message content)
            - remind_time: When to send the reminder (use current time above for calculations)
            - priority: urgent, normal, or low
            
            User request: "{user_message}"
            
            REMIND_TIME RULES:
            - If user says "now", "immediately", "right away" → use "now"
            - If user specifies time today → use "YYYY-MM-DD HH:MM" format with today's date
            - If user says "tomorrow at X" → use tomorrow's date with specified time
            - If user says "in X minutes/hours" → calculate from current time
            - If user says "at X PM/AM" without date → assume today if time hasn't passed, tomorrow if it has
            - If user says specific date → use that date
            - If no time specified → use "now"
            
            EXAMPLES:
            "at 2PM today, you have to notify me that I need to do home work" → remind_time: "2025-05-31 14:00", reminder_text: "Time to do your homework!"
            "remind me in 30 minutes to call mom" → calculate 30 minutes from current time, reminder_text: "Time to call mom!"
            "at 1:20PM notify me that I need to play chess" → remind_time: "2025-05-31 13:20", reminder_text: "Time to play chess!"
            "tomorrow at 9 AM remind me about the meeting" → remind_time: "2025-06-01 09:00", reminder_text: "Don't forget about the meeting!"
            
            Return ONLY a JSON object with these fields:
            {{
                "reminder_text": "Friendly reminder message to send",
                "remind_time": "now" or "YYYY-MM-DD HH:MM",
                "priority": "normal"
            }}
            """
            
            response = self.gemini_model.generate_content(prompt)
            
            if response and response.text:
                # Clean up response and parse JSON
                response_text = response.text.strip()
                
                # Remove markdown code blocks if present
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.startswith('```'):
                    response_text = response_text[3:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                
                reminder_data = json.loads(response_text.strip())
                
                # Validate required fields
                if not reminder_data.get('reminder_text') or not reminder_data.get('remind_time'):
                    return None
                
                logger.info(f"Successfully parsed reminder request")
                return reminder_data
                
        except (json.JSONDecodeError, KeyError, Exception) as e:
            logger.error(f"Error parsing reminder request: {e}")
            return None
    
    def parse_remind_time(self, remind_time_str: str) -> Optional[datetime]:
        """
        Parse remind time string to datetime object.
        
        Args:
            remind_time_str (str): Time string like "now", "2024-01-15 14:30", etc.
            
        Returns:
            datetime: Parsed datetime or None if invalid
        """
        if not remind_time_str or remind_time_str.lower() == "now":
            return datetime.now(self.timezone)
        
        logger.info(f"Attempting to parse remind_time: '{remind_time_str}'")
        
        try:
            # Remove any extra whitespace
            remind_time_str = remind_time_str.strip()
            
            # Try parsing YYYY-MM-DD HH:MM format
            if len(remind_time_str) == 16 and ' ' in remind_time_str:  # "2024-01-15 14:30"
                try:
                    dt = datetime.strptime(remind_time_str, '%Y-%m-%d %H:%M')
                    result = self.timezone.localize(dt)
                    logger.info(f"Successfully parsed YYYY-MM-DD HH:MM format: {result}")
                    return result
                except ValueError:
                    pass
            
            # Try parsing YYYY-MM-DD format (assume noon)
            if len(remind_time_str) == 10 and '-' in remind_time_str:  # "2024-01-15"
                try:
                    dt = datetime.strptime(remind_time_str, '%Y-%m-%d')
                    dt = dt.replace(hour=12)  # Default to noon
                    result = self.timezone.localize(dt)
                    logger.info(f"Successfully parsed YYYY-MM-DD format (noon): {result}")
                    return result
                except ValueError:
                    pass
            
            # Try parsing HH:MM format (assume today)
            if ':' in remind_time_str and len(remind_time_str) <= 5:  # "14:30"
                try:
                    today = datetime.now(self.timezone).date()
                    time_part = datetime.strptime(remind_time_str, '%H:%M').time()
                    dt = datetime.combine(today, time_part)
                    result = self.timezone.localize(dt)
                    logger.info(f"Successfully parsed HH:MM format (today): {result}")
                    return result
                except ValueError:
                    pass
            
            # Try parsing more flexible formats
            formats_to_try = [
                '%Y-%m-%d %I:%M %p',  # "2024-01-15 2:30 PM"
                '%Y-%m-%d %H:%M:%S',  # "2024-01-15 14:30:00"
                '%m/%d/%Y %H:%M',     # "01/15/2024 14:30"
                '%m/%d/%Y %I:%M %p',  # "01/15/2024 2:30 PM"
                '%B %d, %Y %H:%M',    # "January 15, 2024 14:30"
                '%B %d, %Y %I:%M %p', # "January 15, 2024 2:30 PM"
            ]
            
            for fmt in formats_to_try:
                try:
                    dt = datetime.strptime(remind_time_str, fmt)
                    result = self.timezone.localize(dt)
                    logger.info(f"Successfully parsed with format '{fmt}': {result}")
                    return result
                except ValueError:
                    continue
            
            # If we get here, all parsing attempts failed
            logger.warning(f"Failed to parse remind_time '{remind_time_str}' with all attempted formats")
            return None
                
        except Exception as e:
            logger.error(f"Error parsing remind_time '{remind_time_str}': {e}")
            return None
    
    def save_pending_reminder(self, reminder_data: Dict[str, Any], scheduled_time: datetime) -> str:
        """
        Save reminder to pending list for scheduled sending.
        
        Args:
            reminder_data (Dict): Reminder information
            scheduled_time (datetime): When to send the reminder
            
        Returns:
            str: Unique reminder ID
        """
        # Generate unique ID
        reminder_id = f"reminder_{int(datetime.now().timestamp())}"
        
        # Prepare reminder record
        reminder_record = {
            "id": reminder_id,
            "reminder_text": reminder_data['reminder_text'],
            "priority": reminder_data.get('priority', 'normal'),
            "scheduled_time": scheduled_time.isoformat(),
            "created_time": datetime.now(self.timezone).isoformat(),
            "status": "pending"
        }
        
        # Load existing pending reminders
        pending_reminders = self.load_pending_reminders()
        
        # Add new reminder
        pending_reminders[reminder_id] = reminder_record
        
        # Save back to file
        with open(self.pending_reminders_file, 'w') as f:
            json.dump(pending_reminders, f, indent=2)
        
        logger.info(f"Reminder {reminder_id} saved for scheduled sending at {scheduled_time}")
        return reminder_id
    
    def load_pending_reminders(self) -> Dict[str, Any]:
        """Load pending reminders from file."""
        if os.path.exists(self.pending_reminders_file):
            try:
                with open(self.pending_reminders_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {}
    
    def get_pending_reminders(self) -> List[Dict[str, Any]]:
        """Get all pending reminders sorted by scheduled time."""
        pending_reminders = self.load_pending_reminders()
        
        # Filter only pending reminders and sort by scheduled time
        pending_list = []
        for reminder in pending_reminders.values():
            if reminder['status'] == 'pending':
                pending_list.append(reminder)
        
        # Sort by scheduled time
        pending_list.sort(key=lambda x: x['scheduled_time'])
        return pending_list
    
    async def check_and_send_scheduled_reminders(self) -> List[Dict[str, Any]]:
        """
        Check for reminders that need to be sent and return them.
        
        Returns:
            List[Dict]: List of reminders that should be sent now
        """
        current_time = datetime.now(self.timezone)
        pending_reminders = self.load_pending_reminders()
        reminders_to_send = []
        
        for reminder_id, reminder_data in pending_reminders.items():
            if reminder_data['status'] != 'pending':
                continue
            
            # Check if it's time to send
            scheduled_time = datetime.fromisoformat(reminder_data['scheduled_time'])
            
            if scheduled_time <= current_time:
                # Mark as sent
                reminder_data['status'] = 'sent'
                reminder_data['sent_time'] = current_time.isoformat()
                
                reminders_to_send.append({
                    "reminder_id": reminder_id,
                    "reminder_text": reminder_data['reminder_text'],
                    "priority": reminder_data.get('priority', 'normal'),
                    "scheduled_time": scheduled_time
                })
        
        # Save updated pending reminders
        if reminders_to_send:
            with open(self.pending_reminders_file, 'w') as f:
                json.dump(pending_reminders, f, indent=2)
        
        return reminders_to_send
    
    def cancel_pending_reminder(self, reminder_id: str) -> bool:
        """Cancel a pending reminder."""
        pending_reminders = self.load_pending_reminders()
        
        if reminder_id in pending_reminders and pending_reminders[reminder_id]['status'] == 'pending':
            pending_reminders[reminder_id]['status'] = 'cancelled'
            
            with open(self.pending_reminders_file, 'w') as f:
                json.dump(pending_reminders, f, indent=2)
            
            logger.info(f"Reminder {reminder_id} cancelled")
            return True
        
        return False
    
    def cleanup_old_reminders(self, days_old: int = 7):
        """Clean up old sent/cancelled reminders."""
        cutoff_date = datetime.now(self.timezone) - timedelta(days=days_old)
        pending_reminders = self.load_pending_reminders()
        
        reminders_to_remove = []
        for reminder_id, reminder_data in pending_reminders.items():
            if reminder_data['status'] in ['sent', 'cancelled']:
                created_time = datetime.fromisoformat(reminder_data['created_time'])
                if created_time < cutoff_date:
                    reminders_to_remove.append(reminder_id)
        
        for reminder_id in reminders_to_remove:
            del pending_reminders[reminder_id]
        
        if reminders_to_remove:
            with open(self.pending_reminders_file, 'w') as f:
                json.dump(pending_reminders, f, indent=2)
            
            logger.info(f"Cleaned up {len(reminders_to_remove)} old reminders")
    
    def format_reminder_message(self, reminder_text: str) -> str:
        """
        Format a friendly reminder message for Bunkheang.
        
        Args:
            reminder_text (str): The reminder content
            
        Returns:
            str: Formatted friendly reminder message
        """
        return f"Hey Bunkheang! {reminder_text} 👋 {self._get_encouraging_message()}"
    
    def _get_encouraging_message(self) -> str:
        """Get a random encouraging message to add to reminders."""
        import random
        messages = [
            "You know, balancing work and studies can be tricky, but you've totally got this!",
            "Perfect timing! Hope you're having a productive day!",
            "Time flies when you're coding, doesn't it? 😄",
            "Another step towards your goals - keep it up!",
            "Hope this reminder finds you in a good mood!",
            "You're doing great managing everything, Bunkheang!",
            "Let's tackle this next task together!",
            "Remember, every small step counts towards your big dreams!"
        ]
        return random.choice(messages)
    
    def format_reminder_preview(self, reminder_data: Dict[str, Any]) -> str:
        """Format reminder data for preview."""
        return (
            f"⏰ **Reminder Preview**\n\n"
            f"📝 **Message:** {reminder_data['reminder_text']}\n"
            f"⏰ **Remind Time:** {reminder_data['remind_time']}\n"
            f"🔹 **Priority:** {reminder_data.get('priority', 'normal').title()}"
        ) 