"""
Email Automation Service for Telegram Bot

This module handles email automation including:
- AI-powered natural language parsing
- Immediate and scheduled email sending
- Pending email management
"""

import logging
import smtplib
import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import pytz

import google.generativeai as genai
from config import (
    GEMINI_API_KEY, 
    EMAIL_SMTP_SERVER, 
    EMAIL_SMTP_PORT,
    EMAIL_USERNAME, 
    EMAIL_PASSWORD,
    EMAIL_FROM_NAME,
    ENABLE_EMAIL_AUTOMATION
)

logger = logging.getLogger(__name__)

class EmailService:
    """Handles email automation with AI-powered natural language processing."""
    
    def __init__(self):
        """Initialize the email service."""
        self.smtp_server = EMAIL_SMTP_SERVER
        self.smtp_port = EMAIL_SMTP_PORT
        self.username = EMAIL_USERNAME
        self.password = EMAIL_PASSWORD
        self.from_name = EMAIL_FROM_NAME
        self.enabled = ENABLE_EMAIL_AUTOMATION
        self.timezone = pytz.timezone('Asia/Phnom_Penh')
        
        # File to store pending emails
        self.pending_emails_file = 'pending_emails.json'
        
        # Initialize Gemini for email parsing
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.gemini_model = None
            logger.warning("Gemini API key not found - email parsing will be limited")
        
        logger.info(f"Email service initialized (enabled: {self.enabled})")
    
    def is_available(self) -> bool:
        """Check if email service is available and configured."""
        return self.enabled and bool(self.username and self.password)
    
    async def parse_email_request(self, user_message: str) -> Optional[Dict[str, Any]]:
        """
        Parse natural language email request using AI.
        
        Args:
            user_message (str): Natural language email request
            
        Returns:
            Dict: Parsed email details or None if parsing fails
        """
        if not self.gemini_model:
            return None
        
        try:
            # Get current Phnom Penh time for context
            current_time = datetime.now(self.timezone)
            current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S %A')
            
            prompt = f"""
            Parse this email request and extract the following information:
            
            CURRENT TIME: {current_time_str} (Phnom Penh time, Cambodia - UTC+7)
            
            - recipient_email: Email address to send to
            - subject: Email subject line
            - body: Email content/message
            - send_time: When to send (use current time above for calculations)
            - priority: urgent, normal, or low
            
            User request: "{user_message}"
            
            SEND_TIME RULES:
            - If user says "now", "immediately", "right away" → use "now"
            - If user specifies time today → use "YYYY-MM-DD HH:MM" format with today's date
            - If user says "tomorrow at X" → use tomorrow's date with specified time
            - If user says "in X minutes/hours" → calculate from current time
            - If user says "at X PM/AM" without date → assume today if time hasn't passed, tomorrow if it has
            - If user says specific date → use that date
            - If no time specified → use "now"
            
            EXAMPLES:
            "Send email to john@example.com about meeting now" → "now"
            "Email sarah@company.com reminder tomorrow at 9 AM" → "2025-05-31 09:00" (tomorrow's date)
            "Send message to team@work.com in 2 hours" → calculate 2 hours from current time
            "Email boss@company.com at 3 PM today" → "2025-05-31 15:00" (today's date)
            "Send to friend@email.com on Friday at 10 AM" → use Friday's date with 10:00
            
            Return ONLY a JSON object with these fields:
            {{
                "recipient_email": "email@example.com",
                "subject": "Subject line", 
                "body": "Email content based on user's message",
                "send_time": "now" or "YYYY-MM-DD HH:MM",
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
                
                email_data = json.loads(response_text.strip())
                
                # Validate required fields
                if not email_data.get('recipient_email') or not email_data.get('subject'):
                    return None
                
                # Validate email format
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, email_data['recipient_email']):
                    return None
                
                logger.info(f"Successfully parsed email request")
                return email_data
                
        except (json.JSONDecodeError, KeyError, Exception) as e:
            logger.error(f"Error parsing email request: {e}")
            return None
    
    def validate_email_address(self, email: str) -> bool:
        """Validate email address format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    def parse_send_time(self, send_time_str: str) -> Optional[datetime]:
        """
        Parse send time string to datetime object.
        
        Args:
            send_time_str (str): Time string like "now", "2024-01-15 14:30", etc.
            
        Returns:
            datetime: Parsed datetime or None if invalid
        """
        if not send_time_str or send_time_str.lower() == "now":
            return datetime.now(self.timezone)
        
        logger.info(f"Attempting to parse send_time: '{send_time_str}'")
        
        try:
            # Remove any extra whitespace
            send_time_str = send_time_str.strip()
            
            # Try parsing YYYY-MM-DD HH:MM format
            if len(send_time_str) == 16 and ' ' in send_time_str:  # "2024-01-15 14:30"
                try:
                    dt = datetime.strptime(send_time_str, '%Y-%m-%d %H:%M')
                    result = self.timezone.localize(dt)
                    logger.info(f"Successfully parsed YYYY-MM-DD HH:MM format: {result}")
                    return result
                except ValueError:
                    pass
            
            # Try parsing YYYY-MM-DD format (assume noon)
            if len(send_time_str) == 10 and '-' in send_time_str:  # "2024-01-15"
                try:
                    dt = datetime.strptime(send_time_str, '%Y-%m-%d')
                    dt = dt.replace(hour=12)  # Default to noon
                    result = self.timezone.localize(dt)
                    logger.info(f"Successfully parsed YYYY-MM-DD format (noon): {result}")
                    return result
                except ValueError:
                    pass
            
            # Try parsing HH:MM format (assume today)
            if ':' in send_time_str and len(send_time_str) <= 5:  # "14:30"
                try:
                    today = datetime.now(self.timezone).date()
                    time_part = datetime.strptime(send_time_str, '%H:%M').time()
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
                    dt = datetime.strptime(send_time_str, fmt)
                    result = self.timezone.localize(dt)
                    logger.info(f"Successfully parsed with format '{fmt}': {result}")
                    return result
                except ValueError:
                    continue
            
            # If we get here, all parsing attempts failed
            logger.warning(f"Failed to parse send_time '{send_time_str}' with all attempted formats")
            return None
                
        except Exception as e:
            logger.error(f"Error parsing send_time '{send_time_str}': {e}")
            return None
    
    async def send_email_now(self, recipient: str, subject: str, body: str) -> Dict[str, Any]:
        """
        Send an email immediately.
        
        Args:
            recipient (str): Recipient email address
            subject (str): Email subject
            body (str): Email body
            
        Returns:
            Dict: Success status and message
        """
        if not self.is_available():
            return {
                "success": False,
                "message": "Email service not configured or disabled"
            }
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = formataddr((self.from_name, self.username))
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                text = msg.as_string()
                server.sendmail(self.username, recipient, text)
            
            logger.info(f"Email sent successfully to {recipient}")
            return {
                "success": True,
                "message": f"Email sent successfully to {recipient}"
            }
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {
                "success": False,
                "message": f"Failed to send email: {str(e)}"
            }
    
    def save_pending_email(self, email_data: Dict[str, Any], scheduled_time: datetime) -> str:
        """
        Save email to pending list for scheduled sending.
        
        Args:
            email_data (Dict): Email information
            scheduled_time (datetime): When to send the email
            
        Returns:
            str: Unique email ID
        """
        # Generate unique ID
        email_id = f"email_{int(datetime.now().timestamp())}"
        
        # Prepare email record
        email_record = {
            "id": email_id,
            "recipient": email_data['recipient_email'],
            "subject": email_data['subject'],
            "body": email_data['body'],
            "priority": email_data.get('priority', 'normal'),
            "scheduled_time": scheduled_time.isoformat(),
            "created_time": datetime.now(self.timezone).isoformat(),
            "status": "pending"
        }
        
        # Load existing pending emails
        pending_emails = self.load_pending_emails()
        
        # Add new email
        pending_emails[email_id] = email_record
        
        # Save back to file
        with open(self.pending_emails_file, 'w') as f:
            json.dump(pending_emails, f, indent=2)
        
        logger.info(f"Email {email_id} saved for scheduled sending at {scheduled_time}")
        return email_id
    
    def load_pending_emails(self) -> Dict[str, Any]:
        """Load pending emails from file."""
        if os.path.exists(self.pending_emails_file):
            try:
                with open(self.pending_emails_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {}
    
    def get_pending_emails(self) -> List[Dict[str, Any]]:
        """Get all pending emails sorted by scheduled time."""
        pending_emails = self.load_pending_emails()
        
        # Filter only pending emails and sort by scheduled time
        pending_list = []
        for email in pending_emails.values():
            if email['status'] == 'pending':
                pending_list.append(email)
        
        # Sort by scheduled time
        pending_list.sort(key=lambda x: x['scheduled_time'])
        return pending_list
    
    async def check_and_send_scheduled_emails(self) -> List[Dict[str, Any]]:
        """
        Check for emails that need to be sent and send them.
        
        Returns:
            List[Dict]: List of sent emails with results
        """
        if not self.is_available():
            return []
        
        current_time = datetime.now(self.timezone)
        pending_emails = self.load_pending_emails()
        sent_emails = []
        
        for email_id, email_data in pending_emails.items():
            if email_data['status'] != 'pending':
                continue
            
            # Check if it's time to send
            scheduled_time = datetime.fromisoformat(email_data['scheduled_time'])
            
            if scheduled_time <= current_time:
                # Send the email
                result = await self.send_email_now(
                    email_data['recipient'],
                    email_data['subject'],
                    email_data['body']
                )
                
                # Update status
                if result['success']:
                    email_data['status'] = 'sent'
                    email_data['sent_time'] = current_time.isoformat()
                else:
                    email_data['status'] = 'failed'
                    email_data['error'] = result['message']
                
                sent_emails.append({
                    "email_id": email_id,
                    "recipient": email_data['recipient'],
                    "subject": email_data['subject'],
                    "result": result
                })
        
        # Save updated pending emails
        if sent_emails:
            with open(self.pending_emails_file, 'w') as f:
                json.dump(pending_emails, f, indent=2)
        
        return sent_emails
    
    def cancel_pending_email(self, email_id: str) -> bool:
        """Cancel a pending email."""
        pending_emails = self.load_pending_emails()
        
        if email_id in pending_emails and pending_emails[email_id]['status'] == 'pending':
            pending_emails[email_id]['status'] = 'cancelled'
            
            with open(self.pending_emails_file, 'w') as f:
                json.dump(pending_emails, f, indent=2)
            
            logger.info(f"Email {email_id} cancelled")
            return True
        
        return False
    
    def cleanup_old_emails(self, days_old: int = 7):
        """Clean up old sent/cancelled emails."""
        cutoff_date = datetime.now(self.timezone) - timedelta(days=days_old)
        pending_emails = self.load_pending_emails()
        
        emails_to_remove = []
        for email_id, email_data in pending_emails.items():
            if email_data['status'] in ['sent', 'failed', 'cancelled']:
                created_time = datetime.fromisoformat(email_data['created_time'])
                if created_time < cutoff_date:
                    emails_to_remove.append(email_id)
        
        for email_id in emails_to_remove:
            del pending_emails[email_id]
        
        if emails_to_remove:
            with open(self.pending_emails_file, 'w') as f:
                json.dump(pending_emails, f, indent=2)
            
            logger.info(f"Cleaned up {len(emails_to_remove)} old emails")
    
    def format_email_preview(self, email_data: Dict[str, Any]) -> str:
        """Format email data for preview."""
        return (
            f"📧 **Email Preview**\n\n"
            f"👤 **To:** {email_data['recipient_email']}\n"
            f"📝 **Subject:** {email_data['subject']}\n"
            f"💬 **Message:**\n{email_data['body']}\n\n"
            f"⏰ **Send Time:** {email_data['send_time']}\n"
            f"🔹 **Priority:** {email_data.get('priority', 'normal').title()}"
        ) 