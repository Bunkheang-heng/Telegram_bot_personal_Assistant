import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MODEL_NAME = os.getenv('MODEL_NAME', 'gemini-2.0-flash')

# External API Keys
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', '')  # Optional for weather features
DEFAULT_CITY = os.getenv('DEFAULT_CITY', 'New York')  # Default city for weather

# Email Configuration
EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME', '')  # Your email address
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')  # App password for Gmail
EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME', 'Personal Assistant')
ENABLE_EMAIL = bool(EMAIL_USERNAME and EMAIL_PASSWORD)

# Timeout Settings
CONNECT_TIMEOUT = 30.0
READ_TIMEOUT = 30.0
WRITE_TIMEOUT = 30.0
POOL_TIMEOUT = 30.0

# Scheduling Settings
DAILY_MESSAGE_HOUR = 17  # 5 PM
DAILY_MESSAGE_MINUTE = 10

# Calendar Reminder Settings
ENABLE_CALENDAR_REMINDERS = True
REMINDER_MINUTES_BEFORE = 15  # Send reminder 15 minutes before event
REMINDER_CHECK_INTERVAL_MINUTES = 5  # Check for upcoming events every 5 minutes
REMINDER_AT_EVENT_TIME = True  # Also send reminder exactly at event time

# Message Settings
MAX_MESSAGE_LENGTH = 4000

# Feature Flags
ENABLE_VOICE = True
ENABLE_WEATHER = bool(WEATHER_API_KEY)
ENABLE_ENHANCED_DAILY = True
ENABLE_EMAIL_AUTOMATION = ENABLE_EMAIL

# URLs and Endpoints
WEATHER_API_URL = "http://api.weatherstack.com/current"
QUOTES_API_URL = "https://api.quotable.io/random"
FACTS_API_URL = "https://uselessfacts.jsph.pl/random.json"

# Validate required environment variables
def validate_config():
    """Validate that all required configuration is present."""
    missing_vars = []
    
    if not TELEGRAM_BOT_TOKEN:
        missing_vars.append('TELEGRAM_BOT_TOKEN')
    
    if not GEMINI_API_KEY:
        missing_vars.append('GEMINI_API_KEY')
    
    # Email is optional, but warn if enabled without proper config
    if ENABLE_EMAIL_AUTOMATION:
        if not EMAIL_USERNAME:
            missing_vars.append('EMAIL_USERNAME (for email automation)')
        if not EMAIL_PASSWORD:
            missing_vars.append('EMAIL_PASSWORD (for email automation)')
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return True 