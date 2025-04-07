from database import SessionLocal, init_db
from models import User, Task, UserTask, Transaction
from sqlalchemy.orm import Session

import logging
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    CallbackContext,
)
from config import Config

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
TASK_SELECTION, TASK_PROOF, WITHDRAWAL = range(3)

class TaskBot:
    def __init__(self):
        init_db()
        self.application = Application.builder().token(Config.TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("tasks", self.list_tasks))
        self.application.add_handler(CommandHandler("balance", self.show_balance))
        self.application.add_handler(CommandHandler("withdraw", self.withdraw))
        
        task_conv = ConversationHandler(
            entry_points=[CommandHandler('tasks', self.list_tasks)],
            states={
                TASK_SELECTION: [CallbackQueryHandler(self.select_task)],
                TASK_PROOF: [MessageHandler(filters.TEXT | filters.PHOTO, self.submit_proof)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel_task)]
        )
        self.application.add_handler(task_conv)
        
        self.application.add_handler(
            CommandHandler("addtask", self.add_task, filters=filters.User(Config.ADMIN_IDS))
        )
    
    async def start(self, update: Update, context: CallbackContext):
        user = update.effective_user
        session = SessionLocal()
        
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
        
        await update.message.reply_text(
            f"{welcome_msg}\n\n"
            "Available commands:\n"
            "/tasks - Browse available tasks\n"
            "/balance - Check your earnings\n"
            "/withdraw - Request a payout"
        )
    
    async def list_tasks(self, update: Update, context: CallbackContext):
        session = SessionLocal()
        tasks = session.query(Task).filter_by(is_active=True).all()
        session.close()
        
        if not tasks:
            await update.message.reply_text("No tasks available at the moment. Check back later!")
            return ConversationHandler.END
        
        keyboard = [
            [InlineKeyboardButton(f"{task.title} (${task.reward})", callback_data=f"task_{task.id}")]
            for task in tasks
        ]
        keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
        
        await update.message.reply_text(
            "Available Tasks:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return TASK_SELECTION
    
    async def select_task(self, update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel":
            await query.edit_message_text("Task selection cancelled.")
            return ConversationHandler.END
        
        task_id = int(query.data.split("_")[1])
        session = SessionLocal()
        task = session.query(Task).get(task_id)
        session.close()
        
        if not task:
            await query.edit_message_text("This task is no longer available.")
            return ConversationHandler.END
        
        context.user_data['current_task'] = task.id
        
        await query.edit_message_text(
            f"Task: {task.title}\n"
            f"Reward: ${task.reward}\n\n"
            f"Description: {task.description}\n\n"
            "Please submit your proof of completion (text description or photo):"
        )
        
        return TASK_PROOF
    
    async def submit_proof(self, update: Update, context: CallbackContext):
        user = update.effective_user
        task_id = context.user_data.get('current_task')
        
        if not task_id:
            await update.message.reply_text("No task selected. Start over with /tasks")
            return ConversationHandler.END
        
        session = SessionLocal()
        
        user_task = UserTask(
            user_id=user.id,
            task_id=task_id,
            status='pending',
            submitted_at=datetime.datetime.now(),
            proof=str(update.message.text or "photo submitted")
        )
        session.add(user_task)
        session.commit()
        session.close()
        
        await update.message.reply_text(
            "Your submission has been received and is under review.\n"
            "You'll be notified when it's approved."
        )
        
        return ConversationHandler.END
    
    async def show_balance(self, update: Update, context: CallbackContext):
        user = update.effective_user
        session = SessionLocal()
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        session.close()
        
        if db_user:
            await update.message.reply_text(
                f"Your current balance: ${db_user.balance:.2f}\n"
                f"Minimum withdrawal: ${Config.MIN_WITHDRAWAL:.2f}"
            )
        else:
            await update.message.reply_text("Please /start the bot first.")
    
    async def withdraw(self, update: Update, context: CallbackContext):
        user = update.effective_user
        session = SessionLocal()
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        
        if not db_user:
            await update.message.reply_text("Please /start the bot first.")
            return
        
        if db_user.balance < Config.MIN_WITHDRAWAL:
            await update.message.reply_text(
                f"Your balance (${db_user.balance:.2f}) is below the "
                f"minimum withdrawal amount (${Config.MIN_WITHDRAWAL:.2f})"
            )
            return
        
        keyboard = [
            [InlineKeyboardButton("PayPal", callback_data="withdraw_paypal")],
            [InlineKeyboardButton("Bank Transfer", callback_data="withdraw_bank")],
            [InlineKeyboardButton("Cancel", callback_data="cancel")]
        ]
        
        await update.message.reply_text(
            "Select withdrawal method:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        context.user_data['withdraw_amount'] = db_user.balance
        return WITHDRAWAL
    
    async def add_task(self, update: Update, context: CallbackContext):
        if not context.args:
            await update.message.reply_text("Usage: /addtask <title>|<description>|<reward>|<type>")
            return
        
        try:
            title, desc, reward, task_type = ' '.join(context.args).split('|')
            reward = float(reward)
            
            session = SessionLocal()
            new_task = Task(
                title=title.strip(),
                description=desc.strip(),
                reward=reward,
                task_type=task_type.strip(),
                is_active=True
            )
            session.add(new_task)
            session.commit()
            session.close()
            
            await update.message.reply_text("New task added successfully!")
        except Exception as e:
            await update.message.reply_text(f"Error adding task: {str(e)}")
    
    async def cancel_task(self, update: Update, context: CallbackContext):
        await update.message.reply_text("Operation cancelled.")
        return ConversationHandler.END
    
    def run(self):
        self.application.run_polling()

if __name__ == '__main__':
    bot = TaskBot()
    bot.run()
