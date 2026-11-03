"""Compatibility entry point: python index.py."""
import logging

import telegram_bot
from app import app

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    if app.config['TELEGRAM_BOT_TOKEN']:
        telegram_bot.start_polling(app)
    app.run(host='127.0.0.1', port=5050, debug=False)
