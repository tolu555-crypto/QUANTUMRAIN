from quantumrain_bot.py import Update, InlineKeyboardButton, InlineKeyboardMarkup
from quantumrain_bot.py.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    ApplicationBuilder,
)
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

# Database setup
Base = declarative_base()
engine = create_engine("sqlite:///quantumrain.db")
Session = sessionmaker(bind=engine)
session = Session()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True)
    wallet_address = Column(String)
    is_farming = Column(Boolean, default=False)
    farm_start_time = Column(DateTime, nullable=True)
    rewards_collected = Column(Boolean, default=False)
    tasks_completed = Column(Boolean, default=False)

Base.metadata.create_all(engine)

# Farming Logic
def start(update: Update, context: CallbackContext) -> None:
    user = session.query(User).filter_by(telegram_id=str(update.message.chat_id)).first()
    if not user:
        new_user = User(telegram_id=str(update.message.chat_id))
        session.add(new_user)
        session.commit()
        update.message.reply_text(
            "Welcome to QuantumRain! 🌧️\n"
            "Start farming QuantumRain tokens by completing tasks!\n"
            "Use /register <WALLET_ADDRESS> to register your wallet."
        )
    else:
        update.message.reply_text("Welcome back to QuantumRain! 🌧️\nUse /farm to start farming!")

def register(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 1:
        update.message.reply_text("Usage: /register <WALLET_ADDRESS>")
        return

    wallet_address = context.args[0]
    user = session.query(User).filter_by(telegram_id=str(update.message.chat_id)).first()
    if user:
        user.wallet_address = wallet_address
        session.commit()
        update.message.reply_text("Your wallet address has been registered!")
    else:
        update.message.reply_text("Please start with /start first.")

def farm(update: Update, context: CallbackContext) -> None:
    user = session.query(User).filter_by(telegram_id=str(update.message.chat_id)).first()
    if not user:
        update.message.reply_text("Please start with /start first.")
        return

    if not user.tasks_completed:
        update.message.reply_text(
            "You need to complete the required tasks first!\n"
            "Use /tasks to see the tasks."
        )
        return

    if user.is_farming:
        update.message.reply_text("You are already farming!")
        return

    user.is_farming = True
    user.farm_start_time = datetime.now()
    user.rewards_collected = False
    session.commit()

    update.message.reply_text("Farming started! Come back in 8 hours to collect your tokens using /collect.")

def tasks(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Watch Ad", callback_data="watch_ad")],
        [InlineKeyboardButton("Complete Survey", callback_data="complete_survey")],
        [InlineKeyboardButton("Follow Social Media", callback_data="follow_social")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Complete the following tasks to start farming:", reply_markup=reply_markup)

def task_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    user = session.query(User).filter_by(telegram_id=str(query.message.chat_id)).first()
    if not user:
        query.edit_message_text("Please start with /start first.")
        return

    if query.data == "watch_ad":
        query.edit_message_text("Ad watched successfully! ✅")
    elif query.data == "complete_survey":
        query.edit_message_text("Survey completed successfully! ✅")
    elif query.data == "follow_social":
        query.edit_message_text("Followed on social media! ✅")

    # Mark tasks as completed
    user.tasks_completed = True
    session.commit()

def collect(update: Update, context: CallbackContext) -> None:
    user = session.query(User).filter_by(telegram_id=str(update.message.chat_id)).first()
    if not user:
        update.message.reply_text("Please start with /start first.")
        return

    if not user.is_farming:
        update.message.reply_text("You are not farming currently. Start farming with /farm.")
        return

    elapsed_time = datetime.now() - user.farm_start_time
    if elapsed_time >= timedelta(hours=8):
        if user.rewards_collected:
            update.message.reply_text("You have already collected your tokens. Start farming again with /farm.")
        else:
            user.is_farming = False
            user.rewards_collected = True
            user.tasks_completed = False  # Reset tasks
            session.commit()
            update.message.reply_text("Congratulations! You have collected 5 QuantumRain tokens! 🌧️")
    else:
        hours_left = max(8 - elapsed_time.total_seconds() / 3600, 0)
        update.message.reply_text(f"Farming in progress. Time left: {hours_left:.2f} hours.")

def main():
    TOKEN = "8131325595:AAGnpQmdjJwdRTx-aq-R9g9nEVrnRZ3QmDQ"
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("register", register))
    dp.add_handler(CommandHandler("farm", farm))
    dp.add_handler(CommandHandler("tasks", tasks))
    dp.add_handler(CallbackQueryHandler(task_callback))
    dp.add_handler(CommandHandler("collect", collect))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
