# Email Automation Setup Guide

## 📧 Overview

The Personal Assistant Bot now includes powerful email automation capabilities that allow you to send emails using natural language commands. The system uses AI to parse your requests and can send emails immediately or schedule them for later.

## 🔧 Setup Requirements

### 1. Environment Variables

Add these variables to your `.env` file:

```bash
# Email Configuration (Required for email automation)
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_FROM_NAME=Personal Assistant
```

### 2. Gmail App Password Setup

For Gmail users, you'll need to create an App Password:

1. Go to your Google Account settings
2. Navigate to Security → 2-Step Verification
3. At the bottom, select "App passwords"
4. Generate a new app password for "Mail"
5. Use this 16-character password as your `EMAIL_PASSWORD`

**Note:** Regular Gmail passwords won't work - you must use an App Password.

### 3. Other Email Providers

For other email providers, update the SMTP settings:

- **Outlook/Hotmail:** `smtp-mail.outlook.com:587`
- **Yahoo:** `smtp.mail.yahoo.com:587`
- **Custom SMTP:** Set your provider's SMTP server and port

## 🚀 Usage

### Natural Language Commands

The bot understands natural language email requests:

```
/email Send john@example.com about meeting tomorrow at 9 AM
/email Email team@company.com project update now
/email Send reminder to client@business.com about deadline Friday at 2 PM
```

### Direct Chat Integration

You can also just chat naturally:

```
"Email professor@university.edu about assignment extension tomorrow"
"Send john@example.com a reminder about our meeting"
"Email the team about the project update"
```

### Command Reference

- `/email [natural language request]` - Send or schedule an email
- `/pending_emails` - View all scheduled emails
- `/cancel_email <email_id>` - Cancel a scheduled email

## 🤖 AI Features

### Smart Parsing

The AI automatically extracts:
- **Recipient:** Email address from your message
- **Subject:** Generated based on content
- **Body:** Your message content
- **Send Time:** "now" or scheduled time
- **Priority:** Normal, urgent, or low

### Scheduling

Examples of time expressions the AI understands:
- "now" - Send immediately
- "tomorrow at 9 AM" - Schedule for next day
- "Friday at 2 PM" - Schedule for specific day
- "2024-01-15 14:30" - Exact date and time

### Confirmation System

For manual `/email` commands, the bot shows a preview and asks for confirmation before sending.

## 📱 Example Workflows

### Immediate Email
```
User: /email Send john@example.com meeting reminder now
Bot: [Shows preview with Send/Cancel buttons]
User: [Clicks Send]
Bot: ✅ Email sent successfully!
```

### Scheduled Email
```
User: Email team@company.com project update tomorrow at 9 AM
Bot: ⏰ Email scheduled successfully!
      📧 Your email will be sent on 2024-01-16 at 09:00
      🆔 Email ID: email_1705123456
```

### Managing Scheduled Emails
```
User: /pending_emails
Bot: [Shows list of scheduled emails]

User: /cancel_email email_1705123456
Bot: ✅ Email cancelled successfully
```

## 🔒 Security & Privacy

- Email credentials are stored securely in environment variables
- Pending emails are stored locally in `pending_emails.json`
- The bot only sends emails you explicitly request
- All email data is processed locally on your system

## 🛠️ Troubleshooting

### Common Issues

1. **"Email service not configured"**
   - Check your `.env` file has all required email variables
   - Verify EMAIL_USERNAME and EMAIL_PASSWORD are set

2. **"Failed to send email: Authentication failed"**
   - For Gmail, ensure you're using an App Password, not your regular password
   - Check that 2-Step Verification is enabled on your Google account

3. **"Could not parse email request"**
   - Include a valid email address in your message
   - Be more specific about what you want to send

### Testing Setup

Test your email configuration:
```
/email Send yourself@gmail.com test message now
```

## 📋 Features Summary

✅ **Natural Language Processing** - Understands conversational email requests  
✅ **Immediate Sending** - Send emails instantly  
✅ **Smart Scheduling** - Schedule emails for later delivery  
✅ **AI-Powered Parsing** - Automatically extracts recipient, subject, and content  
✅ **Confirmation System** - Preview emails before sending  
✅ **Pending Email Management** - View and cancel scheduled emails  
✅ **Multiple Email Providers** - Works with Gmail, Outlook, Yahoo, and custom SMTP  
✅ **Secure Configuration** - Environment variable-based setup  
✅ **Background Processing** - Automatic sending of scheduled emails  

## 🔄 Integration

The email automation integrates seamlessly with existing bot features:
- Works alongside calendar management
- Maintains the same natural conversation style
- Follows the same security and privacy principles
- Uses the same AI engine for understanding context 