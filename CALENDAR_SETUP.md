# 📅 Google Calendar Integration Setup

This guide will help you set up Google Calendar integration for your Telegram bot.

## 🔧 Prerequisites

1. A Google Account
2. Access to Google Cloud Console
3. Your bot already running

## 📋 Step-by-Step Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Create Project" (or select existing project)
3. Give your project a name (e.g., "Telegram Calendar Bot")
4. Click "Create"

### 2. Enable Google Calendar API

1. In your project, go to "APIs & Services" → "Library"
2. Search for "Google Calendar API"
3. Click on it and press "Enable"

### 3. Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Choose "External" user type and click "Create"
3. Fill in the required fields:
   - **App name**: Your bot name
   - **User support email**: Your email
   - **Developer contact email**: Your email
4. Click "Save and Continue"
5. Skip "Scopes" for now (click "Save and Continue")
6. Skip "Test users" (click "Save and Continue")
7. Review and click "Back to Dashboard"

### 4. Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Choose "Desktop application"
4. Give it a name (e.g., "Calendar Bot Client")
5. Click "Create"
6. **Download the JSON file** and save it as `credentials.json` in your bot directory

### 5. Set Up Bot Commands

1. Start your bot and use `/calendar_setup`
2. Follow the authentication link provided
3. Sign in with your Google account
4. Copy the authorization code
5. Use `/calendar_auth YOUR_CODE_HERE` in the bot

## 🎉 You're Ready!

Now you can:

- **View Events**: `/calendar_events`
- **Create Meetings**: `/create_meeting Meeting with John tomorrow at 2pm`
- **Smart Detection**: Just say "I have a call with Sarah at 3pm" and the bot will offer to add it!

## 📁 File Structure

Your bot directory should now include:
```
├── main.py
├── calendar_handler.py
├── credentials.json          # ← Downloaded from Google Cloud
├── token.pickle             # ← Created after authentication
└── ...other files
```

## 🔒 Security Notes

- Keep `credentials.json` and `token.pickle` private
- Don't commit these files to version control
- Add them to your `.gitignore`:
  ```
  credentials.json
  token.pickle
  ```

## 🆘 Troubleshooting

**"Credentials not found" error:**
- Ensure `credentials.json` is in the bot directory
- Check the file name is exactly `credentials.json`

**Authentication fails:**
- Make sure you copied the entire authorization code
- Try generating a new auth URL with `/calendar_setup`

**"Access blocked" error:**
- Your OAuth consent screen needs to be published
- Or add your email as a test user in the consent screen

## 💡 Tips

- The bot can understand natural language like:
  - "Meeting with team tomorrow at 2pm"
  - "Doctor appointment next Friday at 10:30am"
  - "Call mom tonight at 7pm"
  
- Events are created in your default timezone (Asia/Phnom_Penh)
- Reminders are automatically set (1 day before + 15 minutes before)

Happy scheduling! 🗓️✨ 