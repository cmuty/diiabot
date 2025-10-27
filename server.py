"""
Flask server to run bot on Render with webhook support
"""
import asyncio
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
CORS(app)

# Global bot and dispatcher instances
bot = None
dp = None
db = None

async def setup_bot():
    """Initialize bot, dispatcher and database"""
    global bot, dp, db
    
    from bot.handlers import router
    from database.models import Database
    
    # Initialize bot and dispatcher
    bot_token = os.getenv("BOT_TOKEN")
    bot = Bot(token=bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Initialize database
    db_url = os.getenv("DATABASE_URL", "database/diia.db")
    
    # Create directory for SQLite if needed
    if not db_url.startswith("postgresql"):
        os.makedirs(os.path.dirname(db_url), exist_ok=True)
    
    db = Database(db_url)
    await db.init_db()
    
    # Register router with middleware to pass db and bot
    @router.message.middleware()
    @router.callback_query.middleware()
    async def db_middleware(handler, event, data):
        data['db'] = db
        data['bot'] = bot
        return await handler(event, data)
    
    dp.include_router(router)
    
    # Set webhook
    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
        logger.info(f"Webhook set to: {webhook_url}")
    else:
        logger.warning("WEBHOOK_URL not set!")
    
    logger.info("Bot initialized!")

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        "status": "ok",
        "service": "Diia Telegram Bot",
        "mode": "webhook"
    })

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return jsonify({"status": "ok"}), 200

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Handle incoming updates from Telegram"""
    if request.method == "POST":
        try:
            update_data = request.get_json()
            update = Update(**update_data)
            await dp.feed_update(bot, update)
            return jsonify({"ok": True}), 200
        except Exception as e:
            logger.error(f"Error processing update: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": False}), 405

if __name__ == "__main__":
    # Initialize bot before starting Flask
    asyncio.run(setup_bot())
    
    # Start Flask server
    port = int(os.getenv("PORT", 10000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port)

