# Personal AI Assistant Telegram Bot

A smart Telegram bot powered by Google Gemini AI that can answer questions and send daily reminders.

## 🌟 Features

- 🤖 **AI-Powered Conversations** - Ask anything using Google Gemini AI
- ⏰ **Daily Reminders** - Sends "hi" messages at 5:10 PM daily
- 💬 **Natural Language** - Just type your questions naturally
- 🧠 **Smart Responses** - Handles long responses and splits them automatically
- 📱 **User-Friendly Commands** - Easy to control and configure

## 🚀 What You Can Ask

- **General Questions**: "What's the weather like?", "Explain quantum physics"
- **Creative Tasks**: "Write a poem about cats", "Create a story"
- **Calculations**: "What's 15% of 240?", "Convert 100 miles to kilometers"
- **Planning**: "Help me plan a trip to Japan", "Suggest a workout routine"
- **Learning**: "Teach me about machine learning", "How do computers work?"
- **And much more!**

## 📋 Commands

- `/start` - Enable daily messages & see welcome menu
- `/help` - Show detailed help and examples
- `/stop` - Disable daily messages (but keep AI chat active)
- `/status` - Check if daily messages are enabled

## 🛠️ Setup

1. **Install dependencies:**
   ```bash
   pip install --user -r requirements.txt
   ```

2. **Environment Variables:**
   Your `.env` file should contain:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token
   GEMINI_API_KEY=your_gemini_api_key
   MODEL_NAME=gemini-2.0-flash
   ```

3. **Run the bot:**
   ```bash
   python main.py
   ```

## 💡 How to Use

1. **Start Conversations:**
   - Find your bot: `@yourmom99_bot`
   - Send `/start` to activate all features
   - Just type any question to get AI responses!

2. **Daily Messages:**
   - Enable with `/start` command
   - Get friendly reminders at 5:10 PM daily
   - Disable anytime with `/stop`

3. **Ask Questions:**
   - No special format needed - just type naturally
   - Get intelligent responses powered by Gemini AI
   - Long responses are automatically split for readability

## 🎯 Example Conversations

**User**: "Explain artificial intelligence in simple terms"  
**Bot**: *Provides a clear, easy-to-understand explanation*

**User**: "What's 25 * 87 + 145?"  
**Bot**: *Calculates and explains: "25 * 87 + 145 = 2,320"*

**User**: "Write a haiku about programming"  
**Bot**: *Creates a beautiful haiku about coding*

## ⚙️ Technical Details

- **AI Model**: Google Gemini 2.0 Flash
- **Scheduling**: APScheduler for reliable daily messages
- **Message Handling**: Automatic text splitting for long responses
- **Error Handling**: Graceful error handling with user-friendly messages
- **Logging**: Comprehensive logging for monitoring

## 🔧 Running in Background

To keep the bot running continuously:

```bash
# Option 1: Using nohup
nohup python main.py &

# Option 2: Using screen
screen -S telegram_bot
python main.py
# Press Ctrl+A, then D to detach
```

## 📝 Important Notes

- The bot needs to stay running to send scheduled messages
- AI responses require a valid Gemini API key
- Users can chat with AI even if daily messages are disabled
- The bot uses your local timezone for scheduling
- Restart requires running `/start` again for daily messages

## 🛑 Stopping the Bot

- **Foreground**: Press `Ctrl+C`
- **Background**: Find process with `ps aux | grep python` and kill it
- **Screen session**: Reattach with `screen -r telegram_bot` then `Ctrl+C` 