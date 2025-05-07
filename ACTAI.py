import os
import asyncio
from aiohttp import web
from openai import OpenAI
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# AI Configuration
AI_CONFIG = {
    "name": "ACT-AI",
    "builder": "ACT Students Developer Team",
    "purpose": (
        "Official digital assistant for American College of Technology\n"
        "• Bridging academic knowledge and job readiness\n"
        "• Offering degree programs and professional training\n"
        "• Cybersecurity, Project Management, and IT courses\n"
        "• International master's degree partnerships\n"
        "• Career development and skills enhancement"
    ),
    "restrictions": [
        "STRICTLY ACT-related information only",
        "Never share student data without valid ID",
        "No external/non-institution discussions",
        "Payment info only through secure portal",
        "Maximum response length: 300 characters",
        "Redirect personal queries to admin office"
    ]
}

def format_message(header: str, content: str) -> str:
    return (
        f"🎓 ACT-AI | ACT\n"
        f"{'-'*30}\n"
        f"🚩 {header}\n"
        f"{'-'*30}\n"
        f"{content}\n\n"
        f"🔗 www.act.edu.et"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = format_message(
        "WELCOME TO ACT �",
        (
            "Official digital assistant for American College of Technology\n"
            "• Student registration & payment assistance\n"
            "• Academic schedule management\n"
            "• Exam date notifications (Mid/Final)\n"
            "• Secure grade verification system\n"
            "• School event announcements\n\n"
            "🔐 Secure Services Available:\n"
            "1. Registration Status\n"
            "2. Fee Payment Portal\n"
            "3. Class Schedules\n"
            "4. Exam Timetables\n"
            "5. Grade Verification\n\n"
            "Type /help for assistance options"
        )
    )
    await update.message.reply_text(welcome_msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()
    print(f"Message from {update.effective_user.first_name}: {user_message}")

    # Pre-defined responses
    if any(keyword in user_message for keyword in ["cybersecurity", "training"]):
        response = format_message(
            "CYBERSECURITY TRAINING 🔒",
            "Next class starts tomorrow at 2:00 PM!\n📍 ACT Building 2nd Floor\n📞 0944150000\n\n🔖 ACT students get 50% discount!\n📲 Paid students join: t.me/cyber_classes_act"
        )
        await update.message.reply_text(response)
        return

    if "course" in user_message and ("fee" in user_message or "price" in user_message):
        response = format_message(
            "COURSE FEES 💳",
            "Computer Science: 15,000 Br/half-year\nBusiness Administration: 15,000 Br/half-year\n\nCybersecurity Training: 18,500 Br\n🔖 ACT students: 50% discount!"
        )
        await update.message.reply_text(response)
        return

    if "certificate" in user_message or "completion" in user_message:
        response = format_message(
            "CERTIFICATE UPDATE 🎓",
            "Cybersecurity & Project Management certificates available from May 2, 2025!\n📍 Collect from ACT Administration Office"
        )
        await update.message.reply_text(response)
        return

    if "master" in user_message or "international" in user_message:
        response = format_message(
            "MASTER'S PROGRAMS 🌍",
            "International Master's with 75% scholarship!\n✅ MIU programs\n✅ Consciousness-Based Education\n✅ Global Networking\n📞 0944150000"
        )
        await update.message.reply_text(response)
        return

    # Grade verification flow
    if any(keyword in user_message for keyword in ["grade", "result", "mark"]):
        if not context.user_data.get('verified'):
            await update.message.reply_text(
                format_message(
                    "SECURE GRADE ACCESS 🔒",
                    "Please provide your Student ID (Format: ACT-XXXX-XX):"
                )
            )
            context.user_data['awaiting_id'] = True
            return

        await update.message.reply_text(
    format_message(
        "ACADEMIC RECORDS 📚",
        ("Student ID: ACT-2023-45\n"
         "Current GPA: 3.8/4.0\n"
         "Completed Credits: 120\n"
         "Program: BSc in Computer Science\n\n"
         "ℹ️ Official transcripts: registrar@act.edu.et")
    )
)
        context.user_data['awaiting_id'] = False
        return

    # ID verification handling
    if context.user_data.get('awaiting_id'):
        if user_message.startswith("act-") and len(user_message) == 10:
            context.user_data['verified'] = True
            await update.message.reply_text(
                format_message(
                    "VERIFICATION SUCCESS ✅",
                    f"ID Validated: {user_message.upper()}\n\nHow can I assist?\n1. Check grades\n2. View schedule\n3. Payment status\n4. Course info"
                )
            )
        else:
            await update.message.reply_text(
                format_message(
                    "INVALID ID FORMAT ❌",
                    "Please use ACT Student ID format:\nExample: ACT-2023-01\n📞 Contact admin: 0944150000"
                )
            )
        context.user_data['awaiting_id'] = False  # Reset after attempt
        return

    # OpenAI fallback
    client = OpenAI(api_key=OPENAI_API_KEY)
    system_message = format_message(
        "ACADEMIC ASSISTANT PROTOCOL",
        f"You are {AI_CONFIG['name']}, created by {AI_CONFIG['builder']}\nPURPOSE: {AI_CONFIG['purpose']}\nRULES: {'; '.join(AI_CONFIG['restrictions'])}\n\nACT INFO: {get_act_info()}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=300
        )

        bot_reply = response.choices[0].message.content
        await update.message.reply_text(
            format_message("ACT RESPONSE 📌", bot_reply)
        )

    except Exception as e:
        await update.message.reply_text(
            format_message(
                "SYSTEM ERROR ⚠️",
                "Technical difficulty encountered\nPlease try again later or\n📞 Contact support: 0944150000"
            )
        )

def get_act_info():
    return (
        "ACT Academy offers:\n"
        "- Cybersecurity Training\n- Project Management\n- Oracle Database\n- UI/UX Design\n"
        "📍 Location: 4 Kilo, Addis Ababa\n"
        "📞 Contact: 0944150000\n"
        "🌐 Website: www.act.edu.et\n"
        "📢 Telegram: t.me/act_official_channel\n"
        "Mission: Equip youth with digital skills for employment\n"
        "Programs: Degree, Masters, Short-term training\n"
        "Partnerships: Coursera, MIU\n"
        "Upcoming Events: Cybersecurity classes starting soon!"
    )

# ... (keep webhook handlers and main function same as before, just update print statements)



# Webhook handlers
async def webhook_handler(request):
    """Handle incoming Telegram updates via webhook"""
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return web.Response()

async def health_check(request):
    """Health check endpoint for Render monitoring"""
    return web.Response(text="OK")

async def main():
    global application
    # Initialize application with webhook config
    application = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .updater(None)  # Disable polling
        .build()
    )
    
    # MUST initialize before adding handlers
    await application.initialize()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start application components
    await application.start()

    # Configure web server
    app = web.Application()
    app.router.add_post('/webhook', webhook_handler)
    app.router.add_get('/health', health_check)

    port = int(os.environ.get("PORT", 5000))
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Start web server
    site = web.TCPSite(runner, host='0.0.0.0', port=port)
    await site.start()

    # Set webhook AFTER server starts
    webhook_url = f"https://ACTAIBOT.onrender.com/webhook"
    try:
        await application.bot.set_webhook(webhook_url)
        print(f"✅ Webhook set: {webhook_url}")
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        raise

    print("🎓 LIBA Assistant ACTIVE")
    
    # Keep running until interrupted
    try:
        await asyncio.Event().wait()
    finally:
        # Proper cleanup
        await application.stop()
        await application.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🔵 Service shutdown initiated")
