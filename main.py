"""
Diia Telegram Bot - Main Entry Point
"""
import asyncio
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import after loading env
from bot.bot import main

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("🤖 Starting Diia Telegram Bot...")
        print("=" * 60)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped by user")

