"""
Simple Flask server to run bot on Render (Web Service)
"""
import asyncio
import threading
import logging
from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app for health checks
app = Flask(__name__)
CORS(app)

# Bot status
bot_status = {"running": False, "error": None}

def run_bot():
    """Run bot in background thread"""
    try:
        from bot.bot import main
        bot_status["running"] = True
        logger.info("Starting bot...")
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Bot error: {e}")
        bot_status["error"] = str(e)
        bot_status["running"] = False

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        "status": "ok",
        "service": "Diia Telegram Bot",
        "bot_running": bot_status["running"],
        "error": bot_status["error"]
    })

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask server
    port = int(os.getenv("PORT", 10000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port)

