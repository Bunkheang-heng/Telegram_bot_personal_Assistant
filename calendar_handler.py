"""
Google Calendar Integration for Telegram Bot

This module handles Google Calendar API interactions including:
- OAuth authentication
- Event creation from natural language
- Calendar event management
"""

import os
import logging
import re
import json
import pytz
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pickle

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import google.generativeai as genai
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

class CalendarHandler:
    """Handles Google Calendar operations including event management and reminders."""
    
    def __init__(self):
        """Initialize the calendar handler."""
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.credentials_file = 'client_secret_39809033512-ih2j51pmr16tvufr8ctaah6tc3fo1isg.apps.googleusercontent.com.json'
        self.token_file = 'token.pickle'
        self.creds = None
        self.service = None
        self.is_authenticated = False
        self.timezone = pytz.timezone('Asia/Phnom_Penh')
        
        # Initialize Gemini for meeting parsing
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.gemini_model = None
            logger.warning("Gemini API key not found - meeting parsing will be limited")
        
        # Track sent reminders to avoid duplicates
        self.sent_reminders = set()
        self.reminder_file = 'sent_reminders.json'
        self.load_sent_reminders()
        
        logger.info("Calendar handler initialized")
    
    def get_authentication_url(self) -> str:
        """
        Get the OAuth authentication URL for Google Calendar.
        
        Returns:
            str: Authentication URL or error message
        """
        try:
            # Check if credentials.json exists
            if not os.path.exists('credentials.json'):
                return ("❌ Google Calendar credentials not found!\n\n"
                       "📋 To set up calendar integration:\n"
                       "1. Go to https://console.cloud.google.com/\n"
                       "2. Create/select a project\n"
                       "3. Enable Google Calendar API\n"
                       "4. Create OAuth 2.0 credentials\n"
                       "5. Download as 'credentials.json'\n"
                       "6. Place in bot directory\n\n"
                       "📖 Full guide: https://developers.google.com/calendar/api/quickstart/python")
            
            # Try automatic authentication first
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                
                # Use run_local_server for automatic authentication
                self.creds = flow.run_local_server(port=0)
                
                # Save credentials for future use
                with open('token.pickle', 'wb') as token:
                    pickle.dump(self.creds, token)
                
                # Build service
                self.service = build('calendar', 'v3', credentials=self.creds)
                self.is_authenticated = True
                
                logger.info("Calendar authentication successful (automatic)")
                return "✅ Calendar authentication successful! You can now create events and view your calendar."
                
            except Exception as auto_error:
                logger.warning(f"Automatic auth failed, using manual method: {auto_error}")
                
                # Fallback to manual code-based authentication
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                
                # Generate authorization URL for manual flow
                auth_url, _ = flow.authorization_url(
                    prompt='consent',
                    access_type='offline',
                    include_granted_scopes='true'
                )
                
                return (f"🔐 Calendar Authentication Required\n\n"
                       f"Click this link to authenticate:\n{auth_url}\n\n"
                       f"After authorization, copy the code and use /calendar_auth CODE_HERE")
            
        except Exception as e:
            logger.error(f"Error in authentication: {e}")
            return f"❌ Error setting up authentication: {str(e)}"
    
    def authenticate_with_code(self, auth_code: str) -> str:
        """
        Complete OAuth authentication with authorization code.
        
        Args:
            auth_code (str): Authorization code from Google
            
        Returns:
            str: Success or error message
        """
        try:
            # Load credentials and create flow
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', self.SCOPES)
            
            # Exchange authorization code for credentials
            flow.fetch_token(code=auth_code)
            self.creds = flow.credentials
            
            # Save credentials for future use
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)
            
            # Build service
            self.service = build('calendar', 'v3', credentials=self.creds)
            self.is_authenticated = True
            
            logger.info("Calendar authentication successful")
            return "✅ Calendar authentication successful! You can now create events."
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return f"❌ Authentication failed: {str(e)}"
    
    def load_credentials(self) -> bool:
        """
        Load saved credentials if available.
        
        Returns:
            bool: True if credentials loaded successfully
        """
        try:
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    self.creds = pickle.load(token)
                
                # Refresh credentials if expired
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                    # Save refreshed credentials
                    with open('token.pickle', 'wb') as token:
                        pickle.dump(self.creds, token)
                
                if self.creds and self.creds.valid:
                    self.service = build('calendar', 'v3', credentials=self.creds)
                    self.is_authenticated = True
                    logger.info("Calendar credentials loaded successfully")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            return False
    
    async def parse_meeting_request(self, user_message: str) -> Optional[Dict]:
        """
        Parse natural language meeting request using AI.
        
        Args:
            user_message (str): User's meeting request
            
        Returns:
            Dict: Parsed meeting details or None if parsing fails
        """
        if not self.gemini_model:
            return self._fallback_parse(user_message)
        
        try:
            # Get accurate Phnom Penh time
            current_time = datetime.now(self.timezone)
            prompt = f"""Parse this meeting request and extract the details.

CURRENT DATE/TIME: {current_time.strftime('%Y-%m-%d %H:%M:%S %A')} (Phnom Penh time, Cambodia - UTC+7)

User request: "{user_message}"

Extract and return ONLY a JSON object with these fields:
{{
    "title": "meeting title/subject",
    "date": "YYYY-MM-DD",
    "start_time": "HH:MM",
    "end_time": "HH:MM", 
    "duration_minutes": 60,
    "description": "additional details",
    "attendees": ["email1@example.com"]
}}

Rules:
- Use the CURRENT DATE/TIME above for all time calculations
- If no specific time given, suggest a reasonable time during business hours
- If no end time given, assume 1 hour duration
- If date is relative (today, tomorrow, next week), convert to actual date based on current time
- If no date given, assume it's for today or next business day
- If no title given, create a descriptive one
- Return only valid JSON, no explanations

Examples:
"Meeting with John tomorrow at 2pm" → date: tomorrow's date, start_time: "14:00", title: "Meeting with John"
"Team standup every day at 9am" → date: tomorrow's date, start_time: "09:00", title: "Team standup"
"Call mom later" → reasonable evening time, title: "Call mom"
"""
            
            response = self.gemini_model.generate_content(prompt)
            
            if response.text:
                # Clean response and extract JSON
                json_text = response.text.strip()
                if json_text.startswith('```json'):
                    json_text = json_text[7:-3]
                elif json_text.startswith('```'):
                    json_text = json_text[3:-3]
                
                parsed_data = json.loads(json_text)
                logger.info(f"AI parsed meeting: {parsed_data}")
                return parsed_data
            
        except Exception as e:
            logger.error(f"AI parsing error: {e}")
            return self._fallback_parse(user_message)
    
    def _fallback_parse(self, user_message: str) -> Optional[Dict]:
        """
        Fallback parsing without AI using regex patterns.
        
        Args:
            user_message (str): User's meeting request
            
        Returns:
            Dict: Basic parsed meeting details
        """
        try:
            # Simple regex patterns for common formats
            time_pattern = r'(\d{1,2}):?(\d{0,2})\s*(am|pm|AM|PM)?'
            date_patterns = [
                r'tomorrow',
                r'today',
                r'next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
                r'(\d{1,2})/(\d{1,2})',
                r'(\d{1,2})-(\d{1,2})'
            ]
            
            # Extract time
            time_match = re.search(time_pattern, user_message)
            start_time = "14:00"  # Default 2 PM
            
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                period = time_match.group(3)
                
                if period and period.lower() == 'pm' and hour != 12:
                    hour += 12
                elif period and period.lower() == 'am' and hour == 12:
                    hour = 0
                
                start_time = f"{hour:02d}:{minute:02d}"
            
            # Extract date using Phnom Penh timezone
            now_pp = datetime.now(self.timezone)
            tomorrow = now_pp + timedelta(days=1)
            event_date = tomorrow.strftime('%Y-%m-%d')
            
            if 'today' in user_message.lower():
                event_date = now_pp.strftime('%Y-%m-%d')
            
            # Extract title (simple approach)
            title = "Meeting"
            if 'meeting' in user_message.lower():
                title = "Meeting"
            elif 'call' in user_message.lower():
                title = "Call"
            elif 'presentation' in user_message.lower():
                title = "Presentation"
            
            return {
                "title": title,
                "date": event_date,
                "start_time": start_time,
                "end_time": self._add_hour(start_time),
                "duration_minutes": 60,
                "description": f"Created from: {user_message}",
                "attendees": []
            }
            
        except Exception as e:
            logger.error(f"Fallback parsing error: {e}")
            return None
    
    def _add_hour(self, time_str: str) -> str:
        """Add one hour to a time string."""
        try:
            hour, minute = map(int, time_str.split(':'))
            hour = (hour + 1) % 24
            return f"{hour:02d}:{minute:02d}"
        except:
            return "15:00"  # Default fallback
    
    async def create_calendar_event(self, meeting_details: Dict) -> str:
        """
        Create a Google Calendar event.
        
        Args:
            meeting_details (Dict): Parsed meeting details
            
        Returns:
            str: Success message with event details or error message
        """
        if not self.is_authenticated:
            return "❌ Please authenticate with Google Calendar first using `/calendar_setup`"
        
        try:
            # Build event object
            start_datetime = f"{meeting_details['date']}T{meeting_details['start_time']}:00"
            end_datetime = f"{meeting_details['date']}T{meeting_details['end_time']}:00"
            
            event = {
                'summary': meeting_details['title'],
                'description': meeting_details.get('description', ''),
                'start': {
                    'dateTime': start_datetime,
                    'timeZone': 'Asia/Phnom_Penh',  # Cambodia timezone
                },
                'end': {
                    'dateTime': end_datetime,
                    'timeZone': 'Asia/Phnom_Penh',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 15},       # 15 min before
                    ],
                },
            }
            
            # Add attendees if specified
            if meeting_details.get('attendees'):
                event['attendees'] = [{'email': email} for email in meeting_details['attendees']]
            
            # Create the event
            created_event = self.service.events().insert(
                calendarId='primary', 
                body=event,
                sendUpdates='all' if meeting_details.get('attendees') else 'none'
            ).execute()
            
            # Format success message
            event_link = created_event.get('htmlLink')
            formatted_date = datetime.strptime(meeting_details['date'], '%Y-%m-%d').strftime('%A, %B %d, %Y')
            
            success_msg = (
                f"✅ **Calendar Event Created!**\n\n"
                f"📅 **{meeting_details['title']}**\n"
                f"📆 {formatted_date}\n"
                f"🕐 {meeting_details['start_time']} - {meeting_details['end_time']}\n"
            )
            
            if meeting_details.get('description'):
                success_msg += f"📝 {meeting_details['description']}\n"
            
            if event_link:
                success_msg += f"\n🔗 [View in Calendar]({event_link})"
            
            logger.info(f"Calendar event created: {created_event.get('id')}")
            return success_msg
            
        except HttpError as error:
            logger.error(f"Calendar API error: {error}")
            return f"❌ Calendar error: {error}"
        except Exception as e:
            logger.error(f"Event creation error: {e}")
            return f"❌ Failed to create event: {str(e)}"
    
    async def get_upcoming_events(self, max_results: int = 10) -> str:
        """
        Get upcoming calendar events.
        
        Args:
            max_results (int): Maximum number of events to return
            
        Returns:
            str: Formatted list of upcoming events
        """
        if not self.is_authenticated:
            return "❌ Please authenticate with Google Calendar first using `/calendar_setup`"
        
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                return "📅 No upcoming events found."
            
            response = "📅 **Upcoming Events:**\n\n"
            
            for event in events[:max_results]:
                start = event['start'].get('dateTime', event['start'].get('date'))
                title = event.get('summary', 'No title')
                
                # Format datetime
                if 'T' in start:
                    dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    formatted_time = dt.strftime('%m/%d %H:%M')
                else:
                    formatted_time = start
                
                response += f"• **{title}**\n  📅 {formatted_time}\n\n"
            
            return response
            
        except HttpError as error:
            logger.error(f"Calendar API error: {error}")
            return f"❌ Calendar error: {error}"
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            return f"❌ Failed to get events: {str(e)}"

    async def get_events_data(self, max_results: int = 10, days_ahead: int = 7) -> List[Dict]:
        """
        Get upcoming calendar events as structured data for AI processing.
        
        Args:
            max_results (int): Maximum number of events to return
            days_ahead (int): Number of days ahead to look for events
            
        Returns:
            List[Dict]: List of event dictionaries with structured data
        """
        if not self.is_authenticated:
            return []
        
        try:
            # Get events from now until days_ahead
            now = datetime.utcnow()
            end_time = now + timedelta(days=days_ahead)
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now.isoformat() + 'Z',
                timeMax=end_time.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            structured_events = []
            
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                # Parse datetime
                if 'T' in start:
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                    is_all_day = False
                else:
                    start_dt = datetime.strptime(start, '%Y-%m-%d')
                    end_dt = datetime.strptime(end, '%Y-%m-%d')
                    is_all_day = True
                
                structured_event = {
                    'title': event.get('summary', 'No title'),
                    'description': event.get('description', ''),
                    'start_datetime': start_dt,
                    'end_datetime': end_dt,
                    'is_all_day': is_all_day,
                    'location': event.get('location', ''),
                    'attendees': [attendee.get('email', '') for attendee in event.get('attendees', [])],
                    'event_id': event.get('id', ''),
                    'html_link': event.get('htmlLink', '')
                }
                
                structured_events.append(structured_event)
            
            logger.info(f"Retrieved {len(structured_events)} calendar events for AI processing")
            return structured_events
            
        except HttpError as error:
            logger.error(f"Calendar API error: {error}")
            return []
        except Exception as e:
            logger.error(f"Error getting events data: {e}")
            return []

    async def delete_event(self, event_id: str) -> str:
        """
        Delete a specific calendar event.
        
        Args:
            event_id (str): The ID of the event to delete
            
        Returns:
            str: Success or error message
        """
        if not self.is_authenticated:
            return "❌ Please authenticate with Google Calendar first"
        
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            logger.info(f"Calendar event deleted: {event_id}")
            return "✅ Event deleted successfully"
            
        except HttpError as error:
            logger.error(f"Calendar API error deleting event: {error}")
            return f"❌ Error deleting event: {error}"
        except Exception as e:
            logger.error(f"Error deleting event: {e}")
            return f"❌ Failed to delete event: {str(e)}"

    async def clear_all_events(self, days_ahead: int = 30) -> str:
        """
        Clear all upcoming events (use with caution).
        
        Args:
            days_ahead (int): Number of days ahead to clear events
            
        Returns:
            str: Success message with count of deleted events
        """
        if not self.is_authenticated:
            return "❌ Please authenticate with Google Calendar first"
        
        try:
            # Get all events in the specified timeframe
            events = await self.get_events_data(max_results=100, days_ahead=days_ahead)
            
            if not events:
                return "📅 No upcoming events found to delete"
            
            deleted_count = 0
            failed_count = 0
            
            for event in events:
                try:
                    self.service.events().delete(
                        calendarId='primary',
                        eventId=event['event_id']
                    ).execute()
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete event {event['event_id']}: {e}")
                    failed_count += 1
            
            result_message = f"✅ Successfully deleted {deleted_count} events"
            if failed_count > 0:
                result_message += f"\n⚠️ Failed to delete {failed_count} events"
            
            logger.info(f"Bulk delete completed: {deleted_count} deleted, {failed_count} failed")
            return result_message
            
        except Exception as e:
            logger.error(f"Error clearing events: {e}")
            return f"❌ Failed to clear events: {str(e)}"

    async def delete_events_by_title(self, title_pattern: str, days_ahead: int = 30) -> str:
        """
        Delete events matching a specific title pattern.
        
        Args:
            title_pattern (str): Pattern to match in event titles (case insensitive)
            days_ahead (int): Number of days ahead to search
            
        Returns:
            str: Success message with details
        """
        if not self.is_authenticated:
            return "❌ Please authenticate with Google Calendar first"
        
        try:
            events = await self.get_events_data(max_results=100, days_ahead=days_ahead)
            
            matching_events = [
                event for event in events 
                if title_pattern.lower() in event['title'].lower()
            ]
            
            if not matching_events:
                return f"📅 No events found matching '{title_pattern}'"
            
            deleted_count = 0
            failed_count = 0
            
            for event in matching_events:
                try:
                    self.service.events().delete(
                        calendarId='primary',
                        eventId=event['event_id']
                    ).execute()
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete event {event['event_id']}: {e}")
                    failed_count += 1
            
            result_message = f"✅ Deleted {deleted_count} events matching '{title_pattern}'"
            if failed_count > 0:
                result_message += f"\n⚠️ Failed to delete {failed_count} events"
            
            logger.info(f"Pattern delete completed: {deleted_count} deleted, {failed_count} failed")
            return result_message
            
        except Exception as e:
            logger.error(f"Error deleting events by pattern: {e}")
            return f"❌ Failed to delete events: {str(e)}"

    def load_sent_reminders(self):
        """Load sent reminders from file."""
        if os.path.exists(self.reminder_file):
            with open(self.reminder_file, 'r') as f:
                self.sent_reminders = set(json.load(f))
        else:
            self.sent_reminders = set()

    def save_sent_reminders(self):
        """Save sent reminders to file."""
        with open(self.reminder_file, 'w') as f:
            json.dump(list(self.sent_reminders), f)

    async def get_events_needing_reminders(self, minutes_before: int = 15, at_event_time: bool = True) -> List[Dict[str, Any]]:
        """
        Get events that need reminders to be sent.
        
        Args:
            minutes_before (int): Minutes before event to send reminder
            at_event_time (bool): Whether to also send reminder at event time
            
        Returns:
            List[Dict]: Events needing reminders with reminder types
        """
        if not self.is_authenticated:
            return []
        
        try:
            now = datetime.now(self.timezone)
            # Look ahead for events in the next hour
            end_time = now + timedelta(hours=1)
            
            # Get upcoming events
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now.isoformat(),
                timeMax=end_time.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            events_needing_reminders = []
            
            for event in events:
                event_id = event['id']
                
                # Parse event datetime
                start = event['start']
                if 'dateTime' in start:
                    # Regular event with time
                    event_datetime = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                    if event_datetime.tzinfo is None:
                        event_datetime = self.timezone.localize(event_datetime)
                    is_all_day = False
                else:
                    # All-day event
                    event_date = datetime.strptime(start['date'], '%Y-%m-%d').date()
                    event_datetime = self.timezone.localize(datetime.combine(event_date, datetime.min.time()))
                    is_all_day = True
                
                # Skip past events
                if event_datetime <= now:
                    continue
                
                # Check if we need to send reminder before event
                minutes_until_event = (event_datetime - now).total_seconds() / 60
                
                # Create unique reminder IDs
                before_reminder_id = f"{event_id}_before_{minutes_before}"
                at_time_reminder_id = f"{event_id}_at_time"
                
                reminder_needed = False
                reminder_type = None
                
                # Check for "before" reminder
                if (minutes_before <= minutes_until_event <= minutes_before + 5 and 
                    before_reminder_id not in self.sent_reminders):
                    reminder_needed = True
                    reminder_type = 'before'
                    reminder_id = before_reminder_id
                
                # Check for "at time" reminder
                elif (at_event_time and 0 <= minutes_until_event <= 5 and 
                      at_time_reminder_id not in self.sent_reminders):
                    reminder_needed = True
                    reminder_type = 'at_time'
                    reminder_id = at_time_reminder_id
                
                if reminder_needed:
                    event_info = {
                        'id': event_id,
                        'title': event.get('summary', 'Untitled Event'),
                        'description': event.get('description', ''),
                        'location': event.get('location', ''),
                        'start_datetime': event_datetime,
                        'is_all_day': is_all_day,
                        'reminder_type': reminder_type,
                        'reminder_id': reminder_id,
                        'minutes_until': int(minutes_until_event)
                    }
                    events_needing_reminders.append(event_info)
            
            return events_needing_reminders
            
        except Exception as e:
            logger.error(f"Error getting events needing reminders: {e}")
            return []

    def format_reminder_message(self, event: Dict[str, Any]) -> str:
        """
        Format a reminder message for an event.
        
        Args:
            event (Dict): Event information with reminder details
            
        Returns:
            str: Formatted reminder message
        """
        title = event['title']
        location = event['location']
        start_time = event['start_datetime']
        reminder_type = event['reminder_type']
        minutes_until = event['minutes_until']
        
        # Format time
        if event['is_all_day']:
            time_str = "All day"
        else:
            time_str = start_time.strftime('%I:%M %p')
        
        # Create reminder message based on type
        if reminder_type == 'before':
            if minutes_until <= 1:
                time_msg = "in less than a minute"
            elif minutes_until < 60:
                time_msg = f"in {minutes_until} minutes"
            else:
                time_msg = f"in {minutes_until // 60} hour(s) and {minutes_until % 60} minutes"
                
            message = f"⏰ **Upcoming Event Reminder**\n\n"
            message += f"📅 **{title}**\n"
            message += f"🕐 **Starting {time_msg}** at {time_str}\n"
        else:  # at_time
            message = f"🔔 **Event Starting Now!**\n\n"
            message += f"📅 **{title}**\n"
            message += f"🕐 **Time:** {time_str}\n"
        
        # Add location if available
        if location:
            message += f"📍 **Location:** {location}\n"
        
        # Add description if available
        if event['description'] and len(event['description']) < 200:
            message += f"📝 **Details:** {event['description']}\n"
        
        # Add motivational message
        if reminder_type == 'before':
            message += f"\n💪 Time to prepare! You've got this, Bunkheang!"
        else:
            message += f"\n🚀 It's time! Let's make it great!"
        
        return message

    def mark_reminder_sent(self, reminder_id: str):
        """
        Mark a reminder as sent to avoid duplicates.
        
        Args:
            reminder_id (str): Unique identifier for the reminder
        """
        self.sent_reminders.add(reminder_id)
        self.save_sent_reminders()

    def cleanup_old_reminders(self, days_old: int = 7):
        """
        Clean up old reminder records to prevent file from growing too large.
        
        Args:
            days_old (int): Remove reminders older than this many days
        """
        # For now, we'll just clear all if the set gets too large
        # In a more sophisticated implementation, we'd parse the dates from IDs
        if len(self.sent_reminders) > 1000:
            self.sent_reminders.clear()
            self.save_sent_reminders()
            logger.info("Cleaned up old reminder records") 