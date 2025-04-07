import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, CallbackQueryHandler,
    MessageHandler, Filters, ConversationHandler
)
from config import Config
from database import Session, init_db
from models import User, Task
import datetime

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TaskBot:
    def __init__(self):
        self.updater = Updater(Config.TOKEN, use_context=True)
        self.dp = self.updater.dispatcher
        
        # Initialize database
        init_db()
        
        # Set up handlers
        self.setup_handlers()
    
    def setup_handlers(self):
        self.dp.add_handler(CommandHandler("start", self.start))
        self.dp.add_handler(CommandHandler("tasks", self.list_tasks))
        self.dp.add_handler(CommandHandler("balance", self.show_balance))
        self.dp.add_handler(CommandHandler("withdraw", self.withdraw))
        
        # Admin commands
        self.dp.add_handler(CommandHandler(
            "addtask", 
            self.add_task, 
            filters=Filters.user(Config.ADMIN_IDS)
        ))
    
    def start(self, update: Update, context):
        user = update.effective_user
        session = Session()
        
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        
        if not db_user:
            new_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                registered_at=datetime.datetime.now()
            )
            session.add(new_user)
            session.commit()
            welcome_msg = "Welcome to TaskEarnBot! You've been registered."
        else:
            welcome_msg = f"Welcome back, {user.first_name}!"
        
        session.close()
        
        update.message.reply_text(
            f"{welcome_msg}\n\n"
            "Available commands:\n"
            "/tasks - Browse available tasks\n"
            "/balance - Check your earnings\n"
            "/withdraw - Request a payout"
        )
    
    # Add other handler methods here...

    def run(self):
        self.updater.start_polling()
        self.updater.idle()

if __name__ == '__main__':
    bot = TaskBot()
    bot.run()
