import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import DAILY_MESSAGE_HOUR, DAILY_MESSAGE_MINUTE, ENABLE_CALENDAR_REMINDERS, REMINDER_CHECK_INTERVAL_MINUTES, ENABLE_EMAIL_AUTOMATION
from handlers import send_daily_hi, send_calendar_reminders, send_scheduled_emails, send_scheduled_reminders

logger = logging.getLogger(__name__)

class BotScheduler:
    """Handles scheduling of daily messages and other recurring tasks."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        logger.info("Scheduler initialized")
    
    def setup_daily_messages(self, application):
        """
        Set up the daily message job.
        
        Args:
            application: The Telegram application instance
        """
        try:
            # Add the daily hi message job
            self.scheduler.add_job(
                send_daily_hi,
                'cron',
                hour=DAILY_MESSAGE_HOUR,
                minute=DAILY_MESSAGE_MINUTE,
                args=[application],
                id='daily_hi_message',
                name='Daily Hi Message',
                replace_existing=True
            )
            
            logger.info(f"Daily message job scheduled for {DAILY_MESSAGE_HOUR:02d}:{DAILY_MESSAGE_MINUTE:02d}")
            
        except Exception as e:
            logger.error(f"Error setting up daily messages: {e}")
            raise

    def setup_calendar_reminders(self, application):
        """
        Set up calendar reminder checking job.
        
        Args:
            application: The Telegram application instance
        """
        if not ENABLE_CALENDAR_REMINDERS:
            logger.info("Calendar reminders disabled in config")
            return
            
        try:
            # Add calendar reminder checking job
            self.scheduler.add_job(
                send_calendar_reminders,
                'interval',
                minutes=REMINDER_CHECK_INTERVAL_MINUTES,
                args=[application],
                id='calendar_reminders',
                name='Calendar Reminders Check',
                replace_existing=True
            )
            
            logger.info(f"Calendar reminder job scheduled (checking every {REMINDER_CHECK_INTERVAL_MINUTES} minutes)")
            
        except Exception as e:
            logger.error(f"Error setting up calendar reminders: {e}")
            raise

    def setup_email_automation(self, application):
        """
        Set up email automation checking job.
        
        Args:
            application: The Telegram application instance
        """
        if not ENABLE_EMAIL_AUTOMATION:
            logger.info("Email automation disabled in config")
            return
            
        try:
            # Add email checking job (every minute)
            self.scheduler.add_job(
                send_scheduled_emails,
                'interval',
                minutes=1,
                args=[application],
                id='email_automation',
                name='Scheduled Email Check',
                replace_existing=True
            )
            
            logger.info("Email automation job scheduled (checking every minute)")
            
        except Exception as e:
            logger.error(f"Error setting up email automation: {e}")
            raise

    def setup_reminder_automation(self, application):
        """
        Set up reminder automation checking job.
        
        Args:
            application: The Telegram application instance
        """
        try:
            # Add reminder checking job (every minute)
            self.scheduler.add_job(
                send_scheduled_reminders,
                'interval',
                minutes=1,
                args=[application],
                id='reminder_automation',
                name='Scheduled Reminder Check',
                replace_existing=True
            )
            
            logger.info("Reminder automation job scheduled (checking every minute)")
            
        except Exception as e:
            logger.error(f"Error setting up reminder automation: {e}")
            raise

    def setup_all_jobs(self, application):
        """
        Set up all scheduled jobs.
        
        Args:
            application: The Telegram application instance
        """
        self.setup_daily_messages(application)
        self.setup_calendar_reminders(application)
        self.setup_email_automation(application)
        self.setup_reminder_automation(application)

    def start(self):
        """Start the scheduler."""
        try:
            if not self.is_running:
                self.scheduler.start()
                self.is_running = True
                logger.info("Scheduler started successfully")
            else:
                logger.warning("Scheduler is already running")
                
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise
    
    def stop(self):
        """Stop the scheduler."""
        try:
            if self.is_running:
                self.scheduler.shutdown()
                self.is_running = False
                logger.info("Scheduler stopped")
            else:
                logger.warning("Scheduler is not running")
                
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
            raise
    
    def get_jobs(self):
        """Get all scheduled jobs."""
        return self.scheduler.get_jobs()
    
    def is_scheduler_running(self):
        """Check if scheduler is running."""
        return self.is_running and self.scheduler.running 