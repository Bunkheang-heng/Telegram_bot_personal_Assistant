#!/usr/bin/env python3
"""
Startup script for PythonAnywhere deployment
"""
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main bot
from main import main

if __name__ == '__main__':
    try:
        print("Starting Bunkheang's Personal Assistant Bot...")
        main()
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Bot error: {e}")
        raise
