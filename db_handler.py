from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from datetime import datetime
# Import your SQLite database handling functions
from db_handler import create_connection, create_table, insert_message

# Telegram Bot Token
BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

# Initialize the SQLite database connection
database = "telegram_chat.db"
conn = create_connection(database)
create_table(conn)

# Function to handle messages
def handle_messages(update, context):
    username = update.effective_user.username
    timestamp = datetime.now().isoformat()
    message_text = update.message.text

    # Insert message into the database
    insert_message(conn, (username, timestamp, message_text))

def main():
    # Create Updater and pass it your bot's token.
    updater = Updater(BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Handle messages
    dp.add_handler(MessageHandler(Filters.text & (~Filters.command), handle_messages))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()