import logging
import random
from telegram import Update
from telegram.ext import ContextTypes
from services import ExternalServices

logger = logging.getLogger(__name__)

# Initialize services
services = ExternalServices()

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get weather for specified city or default city."""
    city = ' '.join(context.args) if context.args else None
    
    # Handle both regular messages and callback queries
    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text("🌤️ Fetching weather information...")
    else:
        await update.message.reply_text("🌤️ Fetching weather information...")
    
    weather_data = await services.get_weather(city)
    weather_message = services.format_weather_message(weather_data)
    
    if update.callback_query:
        await query.edit_message_text(weather_message, parse_mode='Markdown')
    else:
        await update.message.reply_text(weather_message, parse_mode='Markdown')

async def quote_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get an inspirational quote."""
    await update.message.reply_text("💭 Finding inspiration...")
    
    quote_data = await services.get_inspirational_quote()
    
    if quote_data["success"]:
        quote_message = (
            f"✨ **Daily Inspiration**\n\n"
            f"*\"{quote_data['text']}\"*\n\n"
            f"— **{quote_data['author']}**"
        )
    else:
        quote_message = f"❌ {quote_data['message']}"
    
    await update.message.reply_text(quote_message, parse_mode='Markdown')

async def fact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get a random interesting fact."""
    await update.message.reply_text("🧠 Fetching an interesting fact...")
    
    fact_data = await services.get_random_fact()
    
    if fact_data["success"]:
        fact_message = (
            f"🤓 **Did You Know?**\n\n"
            f"{fact_data['text']}"
        )
    else:
        fact_message = f"❌ {fact_data['message']}"
    
    await update.message.reply_text(fact_message, parse_mode='Markdown')

async def joke_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get a clean, funny joke."""
    jokes = [
        "Why don't scientists trust atoms? Because they make up everything! 😄",
        "Why did the scarecrow win an award? He was outstanding in his field! 🌾",
        "Why don't eggs tell jokes? They'd crack each other up! 🥚",
        "What do you call a fake noodle? An impasta! 🍝",
        "Why did the coffee file a police report? It got mugged! ☕",
        "What do you call a bear with no teeth? A gummy bear! 🐻",
        "Why don't skeletons fight each other? They don't have the guts! 💀",
        "What's the best thing about Switzerland? I don't know, but the flag is a big plus! 🇨🇭",
        "Why did the math book look so sad? Because it had too many problems! 📚",
        "What do you call a dinosaur that crashes his car? Tyrannosaurus Wrecks! 🦕"
    ]
    
    joke = random.choice(jokes)
    await update.message.reply_text(f"😄 **Here's a joke for you:**\n\n{joke}")

async def motivation_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a motivational message."""
    motivational_messages = [
        "🔥 **You've absolutely got this, Bunkheang!** Remember when you thought coding was impossible? Look at you now! Keep that momentum going!",
        "💪 **Believe in yourself, my friend!** You've tackled complex algorithms and aced tough CS courses. This challenge is just another stepping stone!",
        "🌟 **Today is YOUR day, Bunkheang!** Whether it's debugging code or crushing assignments, you've got the skills to make it amazing!",
        "🚀 **Keep chasing those dreams!** From Cambodia to global opportunities - your coding journey is just getting started!",
        "⭐ **You are absolutely unstoppable!** Every project completed, every bug fixed, every concept mastered - you're building something incredible!",
        "🎯 **Focus on progress, not perfection!** Remember, even senior developers Google basic syntax. You're learning and growing every day!",
        "💎 **You are so valuable, Bunkheang!** Your unique perspective and determination in CS will open doors you haven't even imagined yet!",
        "🌈 **Stay positive, my friend!** Those late-night coding sessions and study marathons are building the future you want!",
        "🦋 **Embrace every challenge!** Just like debugging transforms messy code into something beautiful, challenges transform you into a stronger developer!",
        "🏆 **You're already a champion!** Look at everything you've accomplished in CS - and this is just the beginning of your journey!"
    ]
    
    message = random.choice(motivational_messages)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text(message, parse_mode='Markdown')

async def meditation_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provide a quick mindfulness exercise."""
    meditation_message = (
        "🧘‍♀️ **Quick mindfulness break for you, Bunkheang**\n\n"
        "Let's take a moment to reset your mind (especially after all that coding!):\n\n"
        "1️⃣ **Breathe deeply** - Take 3 slow breaths\n"
        "   • Inhale for 4 counts (fresh energy in)\n"
        "   • Hold for 4 counts (let it settle)\n"
        "   • Exhale for 6 counts (stress and bugs out!)\n\n"
        "2️⃣ **Check in with yourself** - What do you notice right now?\n"
        "   • How does your body feel after sitting at the computer?\n"
        "   • What emotions are present? Excitement? Stress?\n"
        "   • What thoughts are floating by?\n\n"
        "3️⃣ **Gratitude moment** - Name 3 wins from today\n"
        "   • Could be code that worked, concepts that clicked, or just making it through!\n\n"
        "4️⃣ **Set your intention** - What energy do you want for the rest of your day?\n"
        "   • Focused coding? Relaxed learning? Creative problem-solving?\n\n"
        "🌸 *Take your time, Bunkheang. Your mind deserves this break as much as your code deserves good logic.*"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(meditation_message, parse_mode='Markdown')
    else:
        await update.message.reply_text(meditation_message, parse_mode='Markdown') 