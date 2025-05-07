import os
import json
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

# // ADD INFO HERE: Edit this section to update bot knowledge
# ================= KNOWLEDGE CONFIGURATION =================
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

KNOWLEDGE = {
    "courses": {
        "computer_science": {
            "price": 15000,
            "currency": "Br/half-year",
            "discount": "50% for ACT students"
        },
        "business_administration": {
            "price": 15000,
            "currency": "Br/half-year"
        },
        "cybersecurity_training": {
            "price": 1500,
            "schedule": "Next class starts tomorrow at 2:00 PM",
            "location": "ACT Building 2nd Floor",
            "discount": "50% for ACT students"
        }
    },
    "contacts": {
        "phone": "0944150000",
        "email": "registrar@act.edu.et",
        "website": "www.act.edu.et",
        "telegram": "t.me/act_official_channel"
    },
    "certificates": {
        "availability": "May 2, 2025",
        "collection": "ACT Administration Office"
    },
    "masters_programs": {
        "scholarship": "75%",
        "partners": "MIU programs",
        "features": [
            "Consciousness-Based Education",
            "Global Networking"
        ]
    }
}
# ================= UPDATE AREA END =================

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
        "WELCOME TO ACT",
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

    # Pre-defined responses using KNOWLEDGE data
    if any(keyword in user_message for keyword in ["cybersecurity", "training"]):
        cyber = KNOWLEDGE['courses']['cybersecurity_training']
        response = format_message(
            "CYBERSECURITY TRAINING 🔒",
            f"{cyber['schedule']}\n📍 {cyber['location']}\n"
            f"📞 {KNOWLEDGE['contacts']['phone']}\n\n"
            f"🔖 {cyber['discount']}\n"
            "📲 Paid students join: t.me/cyber_classes_act"
        )
        await update.message.reply_text(response)
        return

    if "course" in user_message and ("fee" in user_message or "price" in user_message):
        courses = KNOWLEDGE['courses']
        response_content = "\n".join(
            [f"{name.replace('_', ' ').title()}: {data['price']} {data.get('currency', 'Br')}"
             for name, data in courses.items()]
        )
        response = format_message(
            "COURSE FEES 💳",
            f"{response_content}\n\n🔖 Discounts: {courses['cybersecurity_training']['discount']}"
        )
        await update.message.reply_text(response)
        return

    if "certificate" in user_message or "completion" in user_message:
        cert = KNOWLEDGE['certificates']
        response = format_message(
            "CERTIFICATE UPDATE 🎓",
            f"Available from {cert['availability']}\n📍 {cert['collection']}"
        )
        await update.message.reply_text(response)
        return

    if "master" in user_message or "international" in user_message:
        masters = KNOWLEDGE['masters_programs']
        response = format_message(
            "MASTER'S PROGRAMS 🌍",
            f"International Master's with {masters['scholarship']} scholarship!\n"
            f"✅ {masters['partners']}\n"
            f"✅ {'\n✅ '.join(masters['features'])}\n"
            f"📞 {KNOWLEDGE['contacts']['phone']}"
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
                 f"ℹ️ Official transcripts: {KNOWLEDGE['contacts']['email']}")
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
                    f"Please use ACT Student ID format:\nExample: ACT-2023-01\n📞 Contact admin: {KNOWLEDGE['contacts']['phone']}"
                )
            )
        context.user_data['awaiting_id'] = False
        return

    # OpenAI fallback with dynamic knowledge
    client = OpenAI(api_key=OPENAI_API_KEY)
    system_message = format_message(
        "ACADEMIC ASSISTANT PROTOCOL",
        f"You are {AI_CONFIG['name']}, created by {AI_CONFIG['builder']}\n"
        f"PURPOSE: {AI_CONFIG['purpose']}\n"
        f"RULES: {'; '.join(AI_CONFIG['restrictions'])}\n\n"
        f"CURRENT KNOWLEDGE:\n{json.dumps(KNOWLEDGE, indent=2)}"
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
                f"Technical difficulty encountered\nPlease try again later or\n📞 Contact support: {KNOWLEDGE['contacts']['phone']}"
            )
        )

async def update_knowledge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Admin authentication
    ADMIN_ID = os.getenv("ADMIN_ID", "")
    if str(update.effective_user.id) != ADMIN_ID:
        await update.message.reply_text("❌ Administrator authorization required")
        return

    try:
        # Parse JSON update
        new_data = json.loads(update.message.text.split(' ', 1)[1])
        global KNOWLEDGE
        KNOWLEDGE.update(new_data)
        
        await update.message.reply_text(
            format_message(
                "KNOWLEDGE UPDATED ✅",
                "New information successfully loaded!\n\n"
                f"Updated sections: {', '.join(new_data.keys())}"
            )
        )
    except Exception as e:
        await update.message.reply_text(
            format_message(
                "UPDATE FAILED ❌",
                f"Error: {str(e)}\n\nValid format:\n/update_knowledge {{\"courses\": {{\"computer_science\": {{\"price\": 20000}}}}"
            )
        )

# Webhook handlers and main function remain same
async def webhook_handler(request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return web.Response()

async def health_check(request):
    return web.Response(text="OK")

async def main():
    global application
    application = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .updater(None)
        .build()
    )
    
    await application.initialize()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("update_knowledge", update_knowledge))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    await application.start()
    app = web.Application()
    app.router.add_post('/webhook', webhook_handler)
    app.router.add_get('/health', health_check)

    port = int(os.environ.get("PORT", 5000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host='0.0.0.0', port=port)
    await site.start()

    webhook_url = f"https://ACTAIBOT.onrender.com/webhook"
    try:
        await application.bot.set_webhook(webhook_url)
        print(f"✅ Webhook set: {webhook_url}")
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        raise

    print("🎓 ACT-AI Assistant ACTIVE")
    
    try:
        await asyncio.Event().wait()
    finally:
        await application.stop()
        await application.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🔵 Service shutdown initiated")
