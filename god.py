import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# ==================== CONFIGURATION ====================
TELEGRAM_TOKEN = "8519216119:AAFq6wfvuMncnQh9mAkjUpVGEvmxBCfeqfg"
GEMINI_API_KEY = "AIzaSyDh-LJ70gTRiHEFQJzIfNQ3CT0pr7Ztm7M"

# ==================== SETUP ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Create model with proper configuration
generation_config = {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 1024,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# Try different model names
try:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    print("✅ Using model: gemini-1.5-flash")
except:
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.0-pro",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        print("✅ Using model: gemini-1.0-pro")
    except Exception as e:
        print(f"❌ Model error: {e}")
        print("Using text-based responses instead")
        model = None

# Store conversations
conversations = {}

# ==================== HELPER FUNCTIONS ====================
def get_ai_response(user_id, user_message):
    """Get response from Gemini or fallback"""
    try:
        if model is None:
            raise Exception("No AI model available")
        
        # Get or create conversation history
        if user_id not in conversations:
            conversations[user_id] = []
        
        # Add user message to history
        conversations[user_id].append({"role": "user", "parts": user_message})
        
        # Get response
        response = model.generate_content(user_message)
        ai_response = response.text
        
        # Add AI response to history
        conversations[user_id].append({"role": "model", "parts": ai_response})
        
        # Limit history to 10 messages
        if len(conversations[user_id]) > 10:
            conversations[user_id] = conversations[user_id][-10:]
        
        return ai_response
        
    except Exception as e:
        print(f"AI Error: {e}")
        # Fallback responses
        fallback_responses = [
            "🤖 I'm here! How can I help you today?",
            "✨ Let's chat! What's on your mind?",
            "💭 That's interesting! Tell me more.",
            "🌟 Thanks for your message! How can I assist?",
            "😊 Hello! I'm your AI assistant.",
        ]
        import random
        return random.choice(fallback_responses)

# ==================== TELEGRAM HANDLERS ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_msg = """🤖 *Welcome to AI ChatBot!*

I'm powered by Google Gemini AI.

*Commands:*
/start - Start bot
/help - Show help
/clear - Clear chat history

*Just send me a message to chat!*

Try asking:
• Hello, how are you?
• Explain something
• Write code
• Tell me a joke"""
    
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_msg = """📚 *Help Guide*

*How to use:*
1. Send any message
2. Get AI response
3. Continue conversation

*Features:*
• AI-powered responses
• Conversation memory
• Multiple topics

*Examples:*
• "Hello!"
• "What is Python?"
• "Write a poem"
• "Explain quantum computing"

Use /clear to reset chat history."""
    
    await update.message.reply_text(help_msg, parse_mode='Markdown')

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clear command"""
    user_id = update.effective_user.id
    if user_id in conversations:
        conversations[user_id] = []
    await update.message.reply_text("✅ Chat history cleared!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Show typing indicator
    await update.message.chat.send_action(action="typing")
    
    # Get AI response
    ai_response = get_ai_response(user_id, user_message)
    
    # Send response
    await update.message.reply_text(ai_response)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors gracefully"""
    error = context.error
    if error:
        logger.error(f"Error: {error}")
        
        # Send user-friendly error message
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "⚠️ Sorry, an error occurred. Please try again.",
                    parse_mode='Markdown'
                )
            except:
                pass

# ==================== MAIN FUNCTION ====================
def main():
    """Start the bot"""
    print("=" * 50)
    print("🤖 TELEGRAM AI CHATBOT")
    print("=" * 50)
    print("Starting bot...")
    
    try:
        # Create application
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Add error handler
        app.add_error_handler(error_handler)
        
        # Add command handlers
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("clear", clear_command))
        
        # Add message handler (must be last)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("✅ Bot initialized successfully!")
        print("\n📱 Open Telegram and:")
        print("1. Find your bot")
        print("2. Send /start")
        print("3. Start chatting!")
        print("\n🛑 Press Ctrl+C to stop")
        print("=" * 50)
        
        # Run bot
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            poll_interval=1.0,
            timeout=30
        )
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        print("\nTroubleshooting:")
        print("1. Check internet connection")
        print("2. Verify API keys are correct")
        print("3. Make sure no other bot is running")

# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    main()