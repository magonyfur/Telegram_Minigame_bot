import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler

TOKEN = "YOUR_BOT_TOKEN_HERE"

def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Rock-Paper-Scissors", callback_data='rps')],
        [InlineKeyboardButton("Guess the Number", callback_data='guess')],
        [InlineKeyboardButton("Roll a Dice", callback_data='dice')],
        [InlineKeyboardButton("Coin Flip", callback_data='coin')],
        [InlineKeyboardButton("Math Quiz", callback_data='math')],
        [InlineKeyboardButton("Word Scramble", callback_data='scramble')],
        [InlineKeyboardButton("Trivia", callback_data='trivia')],
        [InlineKeyboardButton("Even or Odd", callback_data='evenodd')],
        [InlineKeyboardButton("Hangman", callback_data='hangman')],
        [InlineKeyboardButton("Anagram Challenge", callback_data='anagram')],
        [InlineKeyboardButton("Fast Typing Test", callback_data='typing')],
        [InlineKeyboardButton("Wordle", callback_data='wordle')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Choose a minigame:", reply_markup=reply_markup)

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    if query.data == 'wordle':
        words = ["apple", "brave", "crane", "drape", "eagle", "flute", "grape", "house", "ivory", "jumbo", "knots", "lemon", "mango", "night", "ocean", "piano", "quiet", "raven", "snake", "tiger", "urban", "vivid", "waltz", "xenon", "yacht", "zebra"]
        wordle_word = random.choice(words)
        context.user_data['wordle_word'] = wordle_word
        context.user_data['wordle_attempts'] = []
        query.message.reply_text("Wordle has started! Guess a 5-letter word using /wordle <word>")

def wordle_guess(update: Update, context: CallbackContext):
    if 'wordle_word' not in context.user_data:
        update.message.reply_text("Start a new Wordle game by selecting it from the menu!")
        return
    
    wordle_word = context.user_data['wordle_word']
    user_word = context.args[0].lower() if context.args else ""
    
    if len(user_word) != 5:
        update.message.reply_text("Please enter a 5-letter word.")
        return
    
    feedback = ""
    for i in range(5):
        if user_word[i] == wordle_word[i]:
            feedback += "🟩"  # Correct position
        elif user_word[i] in wordle_word:
            feedback += "🟨"  # Right letter, wrong position
        else:
            feedback += "⬜"  # Wrong letter
    
    context.user_data['wordle_attempts'].append((user_word, feedback))
    attempts_left = 6 - len(context.user_data['wordle_attempts'])
    
    update.message.reply_text(f"{user_word.upper()} → {feedback}\nAttempts left: {attempts_left}")
    
    if user_word == wordle_word:
        update.message.reply_text("🎉 Congratulations! You guessed the word correctly!")
        del context.user_data['wordle_word']
        del context.user_data['wordle_attempts']
    elif attempts_left == 0:
        update.message.reply_text(f"Game Over! The word was {wordle_word.upper()}.")
        del context.user_data['wordle_word']
        del context.user_data['wordle_attempts']

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(CommandHandler("wordle", wordle_guess))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
