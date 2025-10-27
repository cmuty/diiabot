"""
Simple Flask server to run bot on Render (Web Service)
"""
import asyncio
import logging
from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from multiprocessing import Process

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app for health checks
app = Flask(__name__)
CORS(app)

# Bot status
bot_status = {"running": True, "error": None}

def run_bot():
    """Run bot in separate process"""
    try:
        from bot.bot import main
        logger.info("Starting bot in separate process...")
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Bot error: {e}")

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        "status": "ok",
        "service": "Diia Telegram Bot",
        "bot_running": bot_status["running"]
    })

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    # Start bot in separate process
    bot_process = Process(target=run_bot, daemon=True)
    bot_process.start()
    
    # Start Flask server
    port = int(os.getenv("PORT", 10000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port)

