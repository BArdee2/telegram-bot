import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from database import init_db, add_user, add_task, get_tasks, delete_task, update_task_status
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize database
init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    add_user(user.id, user.first_name, user.last_name, user.username)
    await update.message.reply_text(
        f'Hi {user.first_name}! I am your Task Manager Bot. 📝\n\n'
        'Commands:\n'
        '/addtask - Add a new task\n'
        '/viewtasks - View tasks\n'
        '/deletetask - Delete a task\n'
        '/help - Show help'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        'Task Manager Bot Help:\n\n'
        '/addtask - Add a new task\n'
        '/viewtasks - View all your tasks\n'
        '/deletetask - Delete a task\n'
        '/help - Show this help message'
    )

async def add_task_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt user to enter a new task."""
    await update.message.reply_text('Please enter your task:')
    return 'WAITING_TASK'

async def receive_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Receive and store the task entered by the user."""
    user_id = update.message.from_user.id
    task_text = update.message.text
    
    task_id = add_task(user_id, task_text)
    if task_id:
        await update.message.reply_text(f'✅ Task added successfully! (ID: {task_id})')
    else:
        await update.message.reply_text('❌ Failed to add task. Please try again.')
    return -1  # End conversation

async def view_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display all tasks for the user."""
    user_id = update.message.from_user.id
    tasks = get_tasks(user_id)
    
    if not tasks:
        await update.message.reply_text('You have no tasks yet!')
        return
    
    tasks_list = []
    for task in tasks:
        status = "✓" if task['completed'] else "✗"
        tasks_list.append(f"{task['id']}. [{status}] {task['text']}")
    
    await update.message.reply_text(
        '📋 Your Tasks:\n\n' + '\n'.join(tasks_list),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Complete", callback_data='complete')],
            [InlineKeyboardButton("❌ Incomplete", callback_data='incomplete')]
        ])
    )

async def delete_task_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt user to enter task ID to delete."""
    user_id = update.message.from_user.id
    tasks = get_tasks(user_id)
    
    if not tasks:
        await update.message.reply_text('You have no tasks to delete!')
        return
    
    tasks_list = []
    for task in tasks:
        status = "✓" if task['completed'] else "✗"
        tasks_list.append(f"{task['id']}. [{status}] {task['text']}")
    
    await update.message.reply_text(
        'Select a task to delete:\n\n' + '\n'.join(tasks_list) + 
        '\n\nReply with the task ID you want to delete.'
    )
    return 'WAITING_DELETE'

async def receive_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete the task with the specified ID."""
    user_id = update.message.from_user.id
    try:
        task_id = int(update.message.text)
        
        if delete_task(user_id, task_id):
            await update.message.reply_text(f'🗑️ Task {task_id} deleted successfully!')
        else:
            await update.message.reply_text(f'❌ Task {task_id} not found!')
    except ValueError:
        await update.message.reply_text('⚠️ Please enter a valid task ID (number).')
    
    return -1  # End conversation

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data in ('complete', 'incomplete'):
        user_id = query.from_user.id
        tasks = get_tasks(user_id)
        
        if not tasks:
            await query.edit_message_text(text='You have no tasks!')
            return
        
        keyboard = []
        for task in tasks:
            keyboard.append([InlineKeyboardButton(
                f"{task['id']}. {task['text']}", 
                callback_data=f"task_{task['id']}_{query.data}"
            )])
        
        keyboard.append([InlineKeyboardButton("Cancel", callback_data='cancel')])
        
        await query.edit_message_text(
            text=f'Select a task to mark as {query.data}:',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def task_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle task completion/incompletion."""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'cancel':
        await view_tasks(update, context)
        return
    
    _, task_id, action = query.data.split('_')
    task_id = int(task_id)
    user_id = query.from_user.id
    
    update_task_status(user_id, task_id, action == 'complete')
    await query.edit_message_text(text=f'Task {task_id} marked as {action}!')
    await view_tasks(update, context)

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
    
    application = Application.builder().token(token).build()

    # Add conversation handler for adding tasks
    from telegram.ext import ConversationHandler
    add_task_handler = ConversationHandler(
        entry_points=[CommandHandler('addtask', add_task_cmd)],
        states={
            'WAITING_TASK': [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_task)],
        },
        fallbacks=[CommandHandler('cancel', help_command)],
    )

    # Add conversation handler for deleting tasks
    delete_task_handler = ConversationHandler(
        entry_points=[CommandHandler('deletetask', delete_task_cmd)],
        states={
            'WAITING_DELETE': [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_delete)],
        },
        fallbacks=[CommandHandler('cancel', help_command)],
    )

    # Register command handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(add_task_handler)
    application.add_handler(CommandHandler('viewtasks', view_tasks))
    application.add_handler(delete_task_handler)
    
    # Register button callbacks
    application.add_handler(CallbackQueryHandler(button_callback, pattern='^(complete|incomplete)$'))
    application.add_handler(CallbackQueryHandler(task_action_callback, pattern='^task_'))
    
    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()