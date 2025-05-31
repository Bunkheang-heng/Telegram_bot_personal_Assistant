# Project Structure

This project has been refactored into a modular structure for better maintainability and organization.

## 📁 File Organization

```
Personal_Assistance/
├── main.py                 # Main entry point and bot orchestration
├── config.py              # Configuration and environment variables
├── handlers.py            # Telegram command and message handlers
├── ai_handler.py          # AI/Gemini integration and response handling
├── scheduler.py           # Scheduling functionality for daily messages
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (API keys)
├── README.md             # Project documentation
└── project_structure.md  # This file
```

## 🗂️ Module Descriptions

### `main.py`
- **Purpose**: Entry point and main bot orchestration
- **Classes**: `TelegramBot` - Main bot class that coordinates all components
- **Functions**: Application setup, startup, cleanup
- **Dependencies**: All other modules

### `config.py`
- **Purpose**: Centralized configuration management
- **Contains**: Environment variables, timeout settings, scheduling config
- **Functions**: `validate_config()` - Validates required environment variables
- **No external dependencies** (except dotenv)

### `handlers.py`
- **Purpose**: All Telegram bot command and message handlers
- **Functions**: 
  - `start()` - Welcome message and enable daily messages
  - `help_command()` - Show help information
  - `stop_messages()` - Disable daily messages
  - `status()` - Check daily message status
  - `handle_message()` - Process user messages with AI
  - `send_daily_hi()` - Send scheduled daily message
- **Dependencies**: `ai_handler`, Telegram API

### `ai_handler.py`
- **Purpose**: AI conversation handling using Google Gemini
- **Classes**: `AIHandler` - Manages AI responses and message processing
- **Functions**:
  - `generate_response()` - Get AI response from Gemini
  - `split_long_message()` - Split long responses for Telegram limits
- **Dependencies**: `google.generativeai`, `config`

### `scheduler.py`
- **Purpose**: Scheduling system for recurring tasks
- **Classes**: `BotScheduler` - Manages APScheduler for daily messages
- **Functions**:
  - `setup_daily_messages()` - Configure daily message job
  - `start()` / `stop()` - Control scheduler lifecycle
  - `get_jobs()` - View scheduled jobs
- **Dependencies**: `apscheduler`, `handlers`

## 🔄 Data Flow

```
User Message → handlers.py → ai_handler.py → Gemini API
                ↓
            Response → Telegram User

Scheduled Time → scheduler.py → handlers.py → Telegram User
```

## 🏗️ Benefits of This Structure

### ✅ **Separation of Concerns**
- Each file has a single responsibility
- Easy to locate specific functionality
- Reduced code coupling

### ✅ **Maintainability**
- Changes to AI logic only affect `ai_handler.py`
- Scheduling changes isolated to `scheduler.py`
- Configuration changes centralized in `config.py`

### ✅ **Testability**
- Each module can be tested independently
- Easy to mock dependencies
- Clear interfaces between components

### ✅ **Scalability**
- Easy to add new handlers to `handlers.py`
- Simple to extend AI capabilities in `ai_handler.py`
- New scheduled tasks can be added to `scheduler.py`

### ✅ **Readability**
- Main logic is clear and concise in `main.py`
- Related functionality is grouped together
- Well-documented interfaces

## 🚀 Adding New Features

### Adding a New Command
1. Add handler function to `handlers.py`
2. Register handler in `main.py` → `create_application()`

### Adding AI Features
1. Extend `AIHandler` class in `ai_handler.py`
2. Update handler calls in `handlers.py`

### Adding Scheduled Tasks
1. Add task function to `handlers.py`
2. Register in `scheduler.py` → `BotScheduler`

### Adding Configuration
1. Add setting to `config.py`
2. Update validation in `validate_config()` 