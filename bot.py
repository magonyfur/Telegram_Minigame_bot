import logging
import random
import time
from collections import deque
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Game states
(
    MENU, RPS, GUESS_NUMBER, TRIVIA, MATH, 
    WORD_SCRAMBLE, TICTACTOE, HANGMAN, MEMORY, 
    DICE, REVERSE, ANAGRAM, RIDDLE, WORD_CHAIN, 
    SLOTS, BLACKJACK, EMOJI_PICT, MATH_CHALLENGE
) = range(18)

# Game configurations
GAME_CONFIG = {
    "MAX_ATTEMPTS": 5,
    "MAX_MATH_PROBLEMS": 5,
    "MAX_HANGMAN_TRIES": 6,
    "MEMORY_SIZE": 4,
    "BLACKJACK_TARGET": 21,
    "SLOT_SYMBOLS": ["🍒", "🍊", "🍋", "💎", "7️⃣", "🔔"]
}

TRIVIA_CATEGORIES = {
    "Science": {
        "What is the chemical symbol for gold?": "Au",
        "How many elements are in the periodic table?": "118",
        "What is the hardest natural substance on Earth?": "Diamond"
    },
    "Geography": {
        "Which country has the most natural lakes?": "Canada",
        "What is the smallest country in the world?": "Vatican City",
        "Which river is the longest in the world?": "Nile"
    }
}

WORD_LISTS = {
    "Animals": ["elephant", "giraffe", "kangaroo", "octopus", "rhinoceros"],
    "Countries": ["canada", "brazil", "japan", "australia", "egypt"]
}

EMOJI_PHRASES = {
    "🐝🍯": "honey",
    "🌧️🌈": "rainbow",
    "🚀🌕": "moon landing"
}

RIDDLES = {
    "What has keys but can't open locks?": "piano",
    "The more you take, the more you leave behind. What am I?": "footsteps"
}

HANGMAN_STAGES = [
    """
     ------
     |    |
     |
     |
     |
     |
    ---
    """,
    # Add 5 more stages...
]

class GameBot:
    def __init__(self):
        self.application = Application.builder().token("YOUR_TOKEN").build()
        self.setup_handlers()

    # ------------------ Core Functions ------------------
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "👋 Welcome to GameBot!\nUse /menu to see available games!"
        )

    async def menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        keyboard = [
            ["🎮 Rock-Paper-Scissors", "🔢 Number Guesser"],
            ["❓ Trivia Quiz", "🧮 Math Challenge"],
            ["🔠 Word Scramble", "🎲 Dice Roll"],
            ["⭕ Tic-Tac-Toe", "💀 Hangman"],
            ["🧠 Memory Game", "🔀 Reverse Word"],
            ["🔤 Anagram", "🤔 Riddle"],
            ["🔗 Word Chain", "🎰 Slot Machine"],
            ["🃏 Blackjack", "🎨 Emoji Pictionary"]
        ]
        await self.send_reply(update, "Main Menu:", keyboard)
        return MENU

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("Operation cancelled!", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    # ------------------ All Mini-Games ------------------
    # Rock-Paper-Scissors
    async def rock_paper_scissors(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        choices = ["✊", "✋", "✌️"]
        if update.message.text == "🎮 Rock-Paper-Scissors":
            return await self.send_game_start(update, choices, "Choose your move:", RPS)
        
        user_choice = update.message.text
        bot_choice = random.choice(choices)
        result = self.determine_rps_winner(user_choice, bot_choice)
        await update.message.reply_text(
            f"{result}\nYour move: {user_choice}\nBot's move: {bot_choice}",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    def determine_rps_winner(self, user: str, bot: str) -> str:
        if user == bot:
            return "It's a tie! 🤝"
        wins = [("✊", "✌️"), ("✋", "✊"), ("✌️", "✋")]
        return "You win! 🎉" if (user, bot) in wins else "Bot wins! 😎"

    # Number Guesser
    async def start_guess(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        context.user_data.update({
            "number": random.randint(1, 100),
            "attempts": 0
        })
        await update.message.reply_text(
            f"I'm thinking of a number between 1-100!\nYou have {GAME_CONFIG['MAX_ATTEMPTS']} attempts!"
        )
        return GUESS_NUMBER

    async def handle_guess(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            guess = int(update.message.text)
        except ValueError:
            await update.message.reply_text("Please enter a number!")
            return GUESS_NUMBER

        context.user_data["attempts"] += 1
        target = context.user_data["number"]
        remaining = GAME_CONFIG["MAX_ATTEMPTS"] - context.user_data["attempts"]

        if guess == target:
            await update.message.reply_text(f"🎉 Correct! Guessed in {context.user_data['attempts']} tries!")
            return ConversationHandler.END
        hint = "⬆️ Higher!" if guess < target else "⬇️ Lower!"
        if remaining > 0:
            await update.message.reply_text(f"{hint} {remaining} tries left!")
            return GUESS_NUMBER
        await update.message.reply_text(f"Game Over! Number was {target}")
        return ConversationHandler.END

    # Trivia Quiz
    async def start_trivia(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        category = random.choice(list(TRIVIA_CATEGORIES.keys()))
        context.user_data.update({
            "questions": list(TRIVIA_CATEGORIES[category].items()),
            "score": 0,
            "category": category
        })
        random.shuffle(context.user_data["questions"])
        return await self.ask_question(update, context)

    async def ask_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        if not context.user_data["questions"]:
            await update.message.reply_text(
                f"Quiz Complete! Score: {context.user_data['score']}/"
                f"{len(TRIVIA_CATEGORIES[context.user_data['category']])}"
            )
            return ConversationHandler.END
        question, answer = context.user_data["questions"].pop()
        context.user_data["current_answer"] = answer
        await update.message.reply_text(f"Category: {context.user_data['category']}\nQ: {question}")
        return TRIVIA

    async def handle_trivia(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        if update.message.text.lower() == context.user_data["current_answer"].lower():
            context.user_data["score"] += 1
            await update.message.reply_text("✅ Correct!")
        else:
            await update.message.reply_text(f"❌ Wrong! Answer: {context.user_data['current_answer']}")
        return await self.ask_question(update, context)

    # Math Challenge
    async def math_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        operations = ['+', '-', '*']
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        op = random.choice(operations)
        problem = f"{a} {op} {b}"
        answer = eval(problem)
        context.user_data["math_answer"] = answer
        await update.message.reply_text(f"Solve: {problem} = ?")
        return MATH_CHALLENGE

    async def check_math(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            if int(update.message.text) == context.user_data["math_answer"]:
                await update.message.reply_text("✅ Correct!")
            else:
                await update.message.reply_text(f"❌ Wrong! Answer: {context.user_data['math_answer']}")
        except ValueError:
            await update.message.reply_text("Please enter a number!")
            return MATH_CHALLENGE
        return ConversationHandler.END

    # Word Scramble
    async def word_scramble(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        category = random.choice(list(WORD_LISTS.keys()))
        word = random.choice(WORD_LISTS[category])
        scrambled = ''.join(random.sample(word, len(word)))
        context.user_data.update({
            "answer": word,
            "attempts": 3,
            "category": category
        })
        await update.message.reply_text(
            f"🔤 Word Scramble ({category})\n"
            f"Unscramble: {scrambled}\n"
            f"Attempts left: 3"
        )
        return WORD_SCRAMBLE

    async def check_scramble(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        if update.message.text.lower() == context.user_data["answer"]:
            await update.message.reply_text("🎉 Correct!")
            return ConversationHandler.END
        
        context.user_data["attempts"] -= 1
        if context.user_data["attempts"] > 0:
            await update.message.reply_text(
                f"❌ Wrong! Attempts left: {context.user_data['attempts']}"
            )
            return WORD_SCRAMBLE
        
        await update.message.reply_text(
            f"💥 Game Over! The word was {context.user_data['answer']}"
        )
        return ConversationHandler.END

    # Tic-Tac-Toe
    async def tic_tac_toe(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        if "board" not in context.user_data:
            context.user_data.update({
                "board": [" "] * 9,
                "player": "❌",
                "bot": "⭕"
            })
            await self.send_board(update, context)
            return TICTACTOE
        
        try:
            pos = int(update.message.text) - 1
            if context.user_data["board"][pos] != " ":
                await update.message.reply_text("Invalid move!")
                return TICTACTOE
            
            context.user_data["board"][pos] = context.user_data["player"]
            if self.check_win(context.user_data["board"], context.user_data["player"]):
                await self.send_board(update, context)
                await update.message.reply_text("🎉 You win!")
                return ConversationHandler.END
            
            # Bot move
            empty = [i for i, x in enumerate(context.user_data["board"]) if x == " "]
            if empty:
                bot_pos = random.choice(empty)
                context.user_data["board"][bot_pos] = context.user_data["bot"]
                if self.check_win(context.user_data["board"], context.user_data["bot"]):
                    await self.send_board(update, context)
                    await update.message.reply_text("😎 Bot wins!")
                    return ConversationHandler.END
            
            await self.send_board(update, context)
            if " " not in context.user_data["board"]:
                await update.message.reply_text("🤝 It's a tie!")
                return ConversationHandler.END
            return TICTACTOE
        
        except ValueError:
            await update.message.reply_text("Please enter a number 1-9!")
            return TICTACTOE

    def check_win(self, board, player):
        wins = [[0,1,2], [3,4,5], [6,7,8],
                [0,3,6], [1,4,7], [2,5,8],
                [0,4,8], [2,4,6]]
        return any(all(board[i] == player for i in line) for line in wins)

    async def send_board(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        board = context.user_data["board"]
        text = (
            f"{board[0]} | {board[1]} | {board[2]}\n"
            "---------\n"
            f"{board[3]} | {board[4]} | {board[5]}\n"
            "---------\n"
            f"{board[6]} | {board[7]} | {board[8]}"
        )
        await update.message.reply_text(text)

    # ------------------ Hangman ------------------
    async def start_hangman(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        word = random.choice(sum(WORD_LISTS.values(), [])).upper()
        context.user_data.update({
            "hangman_word": word,
            "guessed_letters": [],
            "wrong_attempts": 0
        })
        await self.display_hangman(update, context)
        return HANGMAN

    async def display_hangman(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        word = context.user_data["hangman_word"]
        display = [letter if letter in context.user_data["guessed_letters"] else "_" for letter in word]
        stage = HANGMAN_STAGES[context.user_data["wrong_attempts"]]
        await update.message.reply_text(
            f"{' '.join(display)}\n\n"
            f"Wrong guesses: {context.user_data['wrong_attempts']}/{GAME_CONFIG['MAX_HANGMAN_TRIES']}\n"
            f"{stage}\n"
            "Guess a letter:"
        )

    async def handle_hangman(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        guess = update.message.text.upper()
        word = context.user_data["hangman_word"]
        
        if not guess.isalpha() or len(guess) != 1:
            await update.message.reply_text("Please enter a single letter!")
            return HANGMAN
            
        if guess in context.user_data["guessed_letters"]:
            await update.message.reply_text("Already guessed that letter!")
            return HANGMAN
            
        context.user_data["guessed_letters"].append(guess)
        
        if guess not in word:
            context.user_data["wrong_attempts"] += 1
            
        if context.user_data["wrong_attempts"] >= GAME_CONFIG["MAX_HANGMAN_TRIES"]:
            await update.message.reply_text(f"💀 Game Over! The word was {word}")
            return ConversationHandler.END
            
        if all(letter in context.user_data["guessed_letters"] for letter in word):
            await update.message.reply_text(f"🎉 Congratulations! You guessed {word}!")
            return ConversationHandler.END
            
        await self.display_hangman(update, context)
        return HANGMAN

    # ------------------ Memory Game ------------------
    async def start_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        symbols = random.sample(["🐶", "🐱", "🐭", "🐹"] * 2, GAME_CONFIG["MEMORY_SIZE"] * 2)
        random.shuffle(symbols)
        context.user_data.update({
            "memory_board": symbols,
            "revealed": [False] * (GAME_CONFIG["MEMORY_SIZE"] * 2),
            "first_choice": None
        })
        await self.display_memory(update, context)
        return MEMORY

    async def display_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        board = [
            f"{i+1}. {'🟦' if not context.user_data['revealed'][i] else context.user_data['memory_board'][i]}"
            for i in range(len(context.user_data["memory_board"]))
        ]
        text = "Memory Board:\n" + "\n".join([f"{board[i]}   {board[i+1]}" for i in range(0, len(board), 2)])
        await update.message.reply_text(text + "\nEnter position (1-8):")

    async def handle_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            pos = int(update.message.text) - 1
            if not 0 <= pos < len(context.user_data["memory_board"]):
                raise ValueError
        except ValueError:
            await update.message.reply_text("Please enter a valid position (1-8)!")
            return MEMORY
            
        if context.user_data["revealed"][pos]:
            await update.message.reply_text("Position already revealed!")
            return MEMORY
            
        if context.user_data["first_choice"] is None:
            context.user_data["first_choice"] = pos
            context.user_data["revealed"][pos] = True
            await self.display_memory(update, context)
            return MEMORY
        else:
            first_pos = context.user_data["first_choice"]
            second_pos = pos
            context.user_data["revealed"][second_pos] = True
            await self.display_memory(update, context)
            
            if context.user_data["memory_board"][first_pos] != context.user_data["memory_board"][second_pos]:
                await update.message.reply_text("No match! Try again.")
                context.user_data["revealed"][first_pos] = False
                context.user_data["revealed"][second_pos] = False
                
            context.user_data["first_choice"] = None
            
            if all(context.user_data["revealed"]):
                await update.message.reply_text("🎉 All matches found!")
                return ConversationHandler.END
                
            return MEMORY

    # ------------------ Dice Roll ------------------
    async def dice_roll(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("🎲 Guess if the roll will be HIGH (4-6) or LOW (1-3):")
        return DICE

    async def handle_dice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        guess = update.message.text.lower()
        if guess not in ["high", "low"]:
            await update.message.reply_text("Please type 'high' or 'low'!")
            return DICE
            
        roll = random.randint(1, 6)
        result = "high" if roll > 3 else "low"
        if guess == result:
            await update.message.reply_text(f"🎉 Correct! Rolled {roll}")
        else:
            await update.message.reply_text(f"❌ Wrong! Rolled {roll}")
        return ConversationHandler.END

    # ------------------ Reverse Word ------------------
    async def start_reverse(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        word = random.choice(sum(WORD_LISTS.values(), []))
        context.user_data.update({
            "reversed_word": word[::-1],
            "original_word": word,
            "attempts": 3
        })
        await update.message.reply_text(
            f"🔀 Reverse Challenge!\n"
            f"Guess the original word: {context.user_data['reversed_word']}\n"
            f"Attempts left: 3"
        )
        return REVERSE

    async def handle_reverse(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        guess = update.message.text.lower()
        if guess == context.user_data["original_word"]:
            await update.message.reply_text("🎉 Correct!")
            return ConversationHandler.END
            
        context.user_data["attempts"] -= 1
        if context.user_data["attempts"] > 0:
            await update.message.reply_text(f"❌ Wrong! Attempts left: {context.user_data['attempts']}")
            return REVERSE
            
        await update.message.reply_text(f"💥 Game Over! The word was {context.user_data['original_word']}")
        return ConversationHandler.END

    # ------------------ Anagram ------------------
    async def start_anagram(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        category = random.choice(list(WORD_LISTS.keys()))
        word = random.choice(WORD_LISTS[category])
        shuffled = ''.join(random.sample(word, len(word)))
        context.user_data.update({
            "anagram": shuffled,
            "answer": word,
            "category": category,
            "attempts": 3
        })
        await update.message.reply_text(
            f"🔤 Anagram ({category})\n"
            f"Unscramble: {shuffled}\n"
            f"Attempts left: 3"
        )
        return ANAGRAM

    async def handle_anagram(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        guess = update.message.text.lower()
        if guess == context.user_data["answer"]:
            await update.message.reply_text("🎉 Correct!")
            return ConversationHandler.END
            
        context.user_data["attempts"] -= 1
        if context.user_data["attempts"] > 0:
            await update.message.reply_text(f"❌ Wrong! Attempts left: {context.user_data['attempts']}")
            return ANAGRAM
            
        await update.message.reply_text(f"💥 Game Over! The word was {context.user_data['answer']}")
        return ConversationHandler.END

    # ------------------ Riddle ------------------
    async def start_riddle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        riddle, answer = random.choice(list(RIDDLES.items()))
        context.user_data.update({
            "current_riddle": riddle,
            "riddle_answer": answer.lower(),
            "attempts": 2
        })
        await update.message.reply_text(
            f"🤔 Riddle Time!\n{riddle}\n"
            f"Attempts left: 2"
        )
        return RIDDLE

    async def handle_riddle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        guess = update.message.text.lower()
        if guess == context.user_data["riddle_answer"]:
            await update.message.reply_text("🎉 Correct!")
            return ConversationHandler.END
            
        context.user_data["attempts"] -= 1
        if context.user_data["attempts"] > 0:
            await update.message.reply_text(f"❌ Wrong! Attempts left: {context.user_data['attempts']}")
            return RIDDLE
            
        await update.message.reply_text(f"💡 The answer was: {context.user_data['riddle_answer']}")
        return ConversationHandler.END

    # ------------------ Word Chain ------------------
    async def start_word_chain(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        context.user_data.update({
            "last_letter": random.choice("abcdefghijklmnopqrstuvwxyz"),
            "used_words": [],
            "score": 0
        })
        await update.message.reply_text(
            f"🔗 Word Chain\n"
            f"Start with: {context.user_data['last_letter'].upper()}\n"
            "Enter a valid word:"
        )
        return WORD_CHAIN

    async def handle_word_chain(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        word = update.message.text.lower()
        last_letter = context.user_data["last_letter"]
        
        if not word.isalpha():
            await update.message.reply_text("Please enter a valid word!")
            return WORD_CHAIN
            
        if word in context.user_data["used_words"]:
            await update.message.reply_text("Word already used!")
            return WORD_CHAIN
            
        if word[0] != last_letter:
            await update.message.reply_text(f"Must start with {last_letter.upper()}!")
            return WORD_CHAIN
            
        # Add real dictionary check here
        context.user_data["used_words"].append(word)
        context.user_data["last_letter"] = word[-1]
        context.user_data["score"] += 1
        
        await update.message.reply_text(
            f"✅ Valid! Next letter: {word[-1].upper()}\n"
            f"Score: {context.user_data['score']}"
        )
        return WORD_CHAIN

    # ------------------ Slot Machine ------------------
    async def slot_machine(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        reels = [random.choice(GAME_CONFIG["SLOT_SYMBOLS"]) for _ in range(3)]
        payout = 0
        
        if reels[0] == reels[1] == reels[2]:
            payout = 10 if reels[0] == "💎" else 5
        elif reels[0] == reels[1] or reels[1] == reels[2]:
            payout = 2
            
        await update.message.reply_text(
            f"🎰 Slot Machine\n"
            f"{' '.join(reels)}\n"
            f"Payout: {payout} coins!"
        )
        return ConversationHandler.END

    # ------------------ Blackjack ------------------
    async def start_blackjack(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        deck = [2,3,4,5,6,7,8,9,10,10,10,10,11] * 4
        random.shuffle(deck)
        
        context.user_data.update({
            "deck": deck,
            "player_hand": [deck.pop(), deck.pop()],
            "dealer_hand": [deck.pop()],
            "status": "playing"
        })
        await self.display_blackjack(update, context)
        return BLACKJACK

    async def display_blackjack(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        player = context.user_data["player_hand"]
        dealer = context.user_data["dealer_hand"]
        player_total = sum(player)
        text = (
            f"🃏 Blackjack\n"
            f"Dealer's hand: {dealer[0]} ?\n"
            f"Your hand: {player} = {player_total}\n"
            "Hit or Stand?"
        )
        await update.message.reply_text(text)

    async def handle_blackjack(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        choice = update.message.text.lower()
        if choice not in ["hit", "stand"]:
            await update.message.reply_text("Please type 'hit' or 'stand'!")
            return BLACKJACK
            
        if choice == "hit":
            context.user_data["player_hand"].append(context.user_data["deck"].pop())
            player_total = sum(context.user_data["player_hand"])
            
            if player_total > 21:
                await update.message.reply_text(f"Bust! You got {player_total}")
                return ConversationHandler.END
                
            await self.display_blackjack(update, context)
            return BLACKJACK
        else:
            # Dealer's turn
            dealer_hand = context.user_data["dealer_hand"]
            while sum(dealer_hand) < 17:
                dealer_hand.append(context.user_data["deck"].pop())
                
            player_total = sum(context.user_data["player_hand"])
            dealer_total = sum(dealer_hand)
            
            result = ""
            if dealer_total > 21 or player_total > dealer_total:
                result = "You win! 🎉"
            elif player_total == dealer_total:
                result = "Push! 🤝"
            else:
                result = "Dealer wins! 😎"
                
            await update.message.reply_text(
                f"Dealer's hand: {dealer_hand} = {dealer_total}\n"
                f"{result}"
            )
            return ConversationHandler.END

    # ------------------ Emoji Pictionary ------------------
    async def start_emoji_pictionary(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        emoji, answer = random.choice(list(EMOJI_PHRASES.items()))
        context.user_data.update({
            "emoji_phrase": emoji,
            "pictionary_answer": answer.lower(),
            "hints_given": 0
        })
        await update.message.reply_text(
            f"🎨 Emoji Pictionary\n"
            f"What phrase do these emojis represent?\n{emoji}"
        )
        return EMOJI_PICT

    async def handle_emoji_pictionary(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        guess = update.message.text.lower()
        if guess == context.user_data["pictionary_answer"]:
            await update.message.reply_text("🎉 Correct!")
            return ConversationHandler.END
        await update.message.reply_text("❌ Incorrect. Try again!")
        return EMOJI_PICT

    # Update setup_handlers
    def setup_handlers(self):
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.menu)],
                RPS: [MessageHandler(filters.TEXT, self.rock_paper_scissors)],
                GUESS_NUMBER: [MessageHandler(filters.TEXT, self.handle_guess)],
                TRIVIA: [MessageHandler(filters.TEXT, self.handle_trivia)],
                MATH_CHALLENGE: [MessageHandler(filters.TEXT, self.check_math)],
                WORD_SCRAMBLE: [MessageHandler(filters.TEXT, self.check_scramble)],
                TICTACTOE: [MessageHandler(filters.TEXT, self.tic_tac_toe)],
                HANGMAN: [MessageHandler(filters.TEXT, self.handle_hangman)],
                MEMORY: [MessageHandler(filters.TEXT, self.handle_memory)],
                DICE: [MessageHandler(filters.TEXT, self.handle_dice)],
                REVERSE: [MessageHandler(filters.TEXT, self.handle_reverse)],
                ANAGRAM: [MessageHandler(filters.TEXT, self.handle_anagram)],
                RIDDLE: [MessageHandler(filters.TEXT, self.handle_riddle)],
                WORD_CHAIN: [MessageHandler(filters.TEXT, self.handle_word_chain)],
                SLOTS: [MessageHandler(filters.TEXT, self.slot_machine)],
                BLACKJACK: [MessageHandler(filters.TEXT, self.handle_blackjack)],
                EMOJI_PICT: [MessageHandler(filters.TEXT, self.handle_emoji_pictionary)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            map_to_parent={ConversationHandler.END: MENU}
        )

        self.application.add_handler(conv_handler)
        self.application.add_handler(CommandHandler("menu", self.menu))

    def run(self):
        self.application.run_polling()

if __name__ == "__main__":
    bot = GameBot()
    bot.run()