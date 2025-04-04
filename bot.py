from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters
import random
import json
import asyncio

# Load or initialize leaderboard
def load_leaderboard():
    try:
        with open("leaderboard.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_leaderboard(data):
    with open("leaderboard.json", "w") as f:
        json.dump(data, f)

leaderboard = load_leaderboard()

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome to MiniGameBot! Play games and earn points! Use /play to start.")

async def play(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Rock-Paper-Scissors", callback_data='rps')],
        [InlineKeyboardButton("Guess the Number", callback_data='guess')],
        [InlineKeyboardButton("Dice Roll", callback_data='dice')],
        [InlineKeyboardButton("Math Quiz", callback_data='math')],
        [InlineKeyboardButton("Word Scramble", callback_data='scramble')],
        [InlineKeyboardButton("Trivia", callback_data='trivia')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose a game:", reply_markup=reply_markup)

async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_name = query.from_user.first_name
    
    if query.data == "rps":
        await query.message.reply_text("Choose: Rock, Paper, or Scissors (type your choice)")
        context.user_data['game'] = 'rps'
    elif query.data == "guess":
        number = random.randint(1, 10)
        context.user_data['game'] = 'guess'
        context.user_data['number'] = number
        await query.message.reply_text("Guess a number between 1 and 10")
    elif query.data == "dice":
        context.user_data['game'] = 'dice'
        await query.message.reply_text("Type 'roll' to roll a dice (1-6).")
    elif query.data == "math":
        num1, num2 = random.randint(1, 10), random.randint(1, 10)
        context.user_data['game'] = 'math'
        context.user_data['answer'] = num1 + num2
        await query.message.reply_text(f"Solve: {num1} + {num2} = ?")
    elif query.data == "scramble":
        word_list = ["python", "telegram", "leaderboard", "challenge", "minigame"]
        word = random.choice(word_list)
        scrambled = "".join(random.sample(word, len(word)))
        context.user_data['game'] = 'scramble'
        context.user_data['word'] = word
        await query.message.reply_text(f"Unscramble this word: {scrambled}")
    elif query.data == "trivia":
        trivia_questions = {
            "What is the capital of France?": "Paris",
            "Who wrote 'Harry Potter'?": "J.K. Rowling",
            "What is 5 + 7?": "12",
            "Which planet is known as the Red Planet?": "Mars"
        }
        question, answer = random.choice(list(trivia_questions.items()))
        context.user_data['game'] = 'trivia'
        context.user_data['answer'] = answer.lower()
        await query.message.reply_text(question)

async def handle_message(update: Update, context: CallbackContext):
    user_name = update.message.from_user.first_name
    text = update.message.text.strip().lower()

    if 'game' not in context.user_data:
        return

    game = context.user_data['game']

    if game == 'rps':
        choices = ["rock", "paper", "scissors"]
        if text not in choices:
            await update.message.reply_text("Invalid choice! Choose Rock, Paper, or Scissors.")
            return
        bot_choice = random.choice(choices)
        result = determine_rps_winner(text, bot_choice)
        if result == "win":
            leaderboard[user_name] = leaderboard.get(user_name, 0) + 10
        save_leaderboard(leaderboard)
        await update.message.reply_text(f"You chose {text}. Bot chose {bot_choice}. Result: {result}!")
    elif game == 'guess':
        if not text.isdigit():
            await update.message.reply_text("Please enter a number!")
            return
        user_guess = int(text)
        number = context.user_data['number']
        if user_guess == number:
            leaderboard[user_name] = leaderboard.get(user_name, 0) + 10
            await update.message.reply_text(f"Correct! The number was {number}. You earned 10 points!")
        else:
            await update.message.reply_text(f"Wrong! The number was {number}. Better luck next time!")
        save_leaderboard(leaderboard)
    elif game == 'scramble':
        if text == context.user_data['word']:
            leaderboard[user_name] = leaderboard.get(user_name, 0) + 10
            await update.message.reply_text("Correct! You earned 10 points!")
        else:
            await update.message.reply_text("Wrong answer! Try again!")
        save_leaderboard(leaderboard)
    elif game == 'trivia':
        if text == context.user_data['answer']:
            leaderboard[user_name] = leaderboard.get(user_name, 0) + 10
            await update.message.reply_text("Correct! You earned 10 points!")
        else:
            await update.message.reply_text("Wrong answer! Better luck next time!")
        save_leaderboard(leaderboard)
    
    context.user_data.clear()

def determine_rps_winner(user, bot):
    if user == bot:
        return "draw"
    elif (user == "rock" and bot == "scissors") or (user == "scissors" and bot == "paper") or (user == "paper" and bot == "rock"):
        return "win"
    else:
        return "lose"

async def show_leaderboard(update: Update, context: CallbackContext):
    if not leaderboard:
        await update.message.reply_text("No scores yet!")
        return
    scores = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    text = "Leaderboard:\n" + "\n".join(f"{x[0]}: {x[1]} points" for x in scores[:10])
    await update.message.reply_text(text)

def main():
    app = Application.builder().token("7838583284:AAHbenYrK1BvgZX5cghNsxSqqD09R2x2NNQ").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CommandHandler("leaderboard", show_leaderboard))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
