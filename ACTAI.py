import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
import os
import json
import re
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
ADMIN_ID = os.getenv("ADMIN_ID")  # Remove default value # Ensure ADMIN_ID is loaded
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

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
        "Never share student specific data like grades directly. Guide to official channels.", # Modified for clarity
        "No external/non-institution discussions",
        "Payment info only through secure portal",
        "Maximum response length: 300 characters (guideline for AI, actual API uses max_tokens)", # Clarification
        "Redirect personal queries to admin office"
    ]
}

KNOWLEDGE = {
    "courses": {
        "computer_science": {"price": 15000, "currency": "Br/half-year"},
        "business_administration": {"price": 15000, "currency": "Br/half-year"}, # Added currency for consistency
        "cybersecurity_training": {
            "price": 15000,
            "currency": "Br", # Added currency for consistency
            "schedule": "Next class starts tomorrow at 2:00 PM",
            "location": "ACT Building 2nd Floor",
            "discount": "50% for ACT students"
        }
    },
    "contacts": {
        "phone": "0911862300",
        "office_phone": "0955040404",  # NEW NUMBER ADDED
        "email": "registrar@act.edu.et",
        "website": "www.act.edu.et",
        "telegram": "t.me/act_official_channel"
    },
    "location": {  # NEW SECTION ADDED
        "main": "4 kilo back side of Abrhot Library",
        "directions": "Near 4 Kilo, behind Abrhot Library"
    },
    "contacts": {
        "phone": "0905040404",
        "email": "registrar@act.edu.et",
        "website": "www.act.edu.et",
        "telegram": "t.me/act_official_channel"
    },
    "certificates": {
        "availability": "Next Monday at Registrar Office",
        "collection": "ACT Main Campus, Ground Floor"
    },
    "masters_programs": {
        "scholarship": "40%",
        "partners": "Global University Alliance",
        "features": [
            "Flexible online learning",
            "Dual certification",
            "Thesis and research support"
        ]
    }
}
# ================= UPDATE AREA END =================

def deep_merge(target: dict, source: dict) -> dict:
    """Recursively merge nested dictionaries"""
    for key in source:
        if isinstance(source[key], dict) and isinstance(target.get(key), dict):
            target[key] = deep_merge(target[key], source[key])
        else:
            target[key] = source[key]
    return target
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
            "• Guidance on grade information access\n" # Modified
            "• School event announcements\n\n"
            "ℹ️ Services I can help with:\n"
            "1. Course Information & Fees\n"
            "2. Cybersecurity Training Details\n"
            "3. Master's Program Info\n"
            "4. Certificate Collection Info\n"
            "5. How to Access Grades (guidance)\n\n"
            "Type /help for assistance options or ask your question."
        )
    )
    await update.message.reply_text(welcome_msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()
    logger.info(f"Message from {update.effective_user.first_name} ({update.effective_user.id}): {user_message}")
    # Handle general ID input if awaited
    if context.user_data.get('awaiting_any_id'):
        if re.fullmatch(r"^ACT-\d{4}-\d{2}$", user_message, re.IGNORECASE):
            context.user_data['student_id'] = user_message.upper()
            context.user_data['id_verified_format'] = True
            await update.message.reply_text(
                format_message(
                    "ID VALIDATED ✅",
                    f"Student ID format recognized: {user_message.upper()}.\nHow can I assist you with services requiring an ID?"
                )
            )
        else:
            await update.message.reply_text(
                format_message(
                    "INVALID ID FORMAT ❌",
                    f"Please use the correct ACT Student ID format (e.g., ACT-1234-56).\n📞 Contact admin for help: {KNOWLEDGE['contacts']['phone']}"
                )
            )
        context.user_data['awaiting_any_id'] = False  # Consume the state
        return  # Exit after handling ID validation

    # Rest of your handle_message code below...


    # Pre-defined responses using KNOWLEDGE data
    if any(keyword in user_message for keyword in ["cybersecurity", "cyber security training"]):
        cyber = KNOWLEDGE['courses']['cybersecurity_training']
        response = format_message(
            "CYBERSECURITY TRAINING 🔒",
            f"🗓️ Schedule: {cyber['schedule']}\n📍 Location: {cyber['location']}\n"
            f"💰 Price: {cyber['price']} {cyber.get('currency', 'Br')}\n"
            f"📞 Contact: {KNOWLEDGE['contacts']['phone']}\n\n"
            f"🔖 Discount: {cyber['discount']}\n"
            "📲 Paid students join: t.me/cyber_classes_act (example link)"
        )
        await update.message.reply_text(response)
        return

    if "course" in user_message and ("fee" in user_message or "price" in user_message or "cost" in user_message):
        courses_data = KNOWLEDGE['courses']
        course_fee_details = []
        discount_details = []

        for name, data in courses_data.items():
            course_name_formatted = name.replace('_', ' ').title()
            price_info = f"• {course_name_formatted}: {data['price']} {data.get('currency', 'Br')}"
            course_fee_details.append(price_info)
            if 'discount' in data and data['discount']:
                discount_details.append(f"  - {course_name_formatted}: {data['discount']}")

        response_content = "Current Course Fees:\n" + "\n".join(course_fee_details)
        if discount_details:
            response_content += "\n\n🔖 Available Discounts:\n" + "\n".join(discount_details)
        else:
            response_content += "\n\n🔖 No specific course discounts are listed at the moment."

        response = format_message("COURSE FEES 💳", response_content)
        await update.message.reply_text(response)
        return

    if "certificate" in user_message or "completion" in user_message:
        cert = KNOWLEDGE['certificates']
        response = format_message(
            "CERTIFICATE UPDATE 🎓",
            f"Available from: {cert['availability']}\n📍 Collection Point: {cert['collection']}"
        )
        await update.message.reply_text(response)
        return

    if "master" in user_message or "international" in user_message or "postgraduate" in user_message:
        masters = KNOWLEDGE['masters_programs']
        features_list = '\n'.join([f"✅ {feature}" for feature in masters['features']])
        response = format_message(
            "MASTER'S PROGRAMS 🌍",
            f"International Master's with {masters['scholarship']} scholarship!\n"
            f"🤝 Partner: {masters['partners']}\n"
            f"{features_list}\n"
            f"📞 More Info: {KNOWLEDGE['contacts']['phone']}"
        )
        await update.message.reply_text(response)
        return

    # Grade information guidance flow
    if any(keyword in user_message for keyword in ["grade", "result", "mark", "gpa"]):
        if not context.user_data.get('id_verified_format'): # Check if a valid-format ID was provided earlier
            await update.message.reply_text(
                format_message(
                    "STUDENT ID REQUIRED 🔒",
                    "To discuss grade information access, I first need your Student ID.\n"
                    "Please provide your Student ID (Format: ACT-XXXX-XX):"
                )
            )
            context.user_data['awaiting_any_id'] = True # Set state to expect an ID next
        else: # ID format was previously verified
            student_id_on_record = context.user_data.get('student_id', 'Not Provided This Session')
            await update.message.reply_text(
                format_message(
                    "ACADEMIC RECORDS ACCESS 📚",
                    (f"Student ID Format on Record: {student_id_on_record}\n\n"
                     "IMPORTANT NOTICE:\n"
                     "Live grade retrieval via this bot is NOT YET ACTIVE. "
                     "This system does not display your specific grades or GPA.\n\n"
                     "For official transcripts and to check your grades, please:\n"
                     f"📧 Email: {KNOWLEDGE['contacts']['email']}\n"
                     f"📞 Phone: {KNOWLEDGE['contacts']['phone']}\n"
                     "Or visit the Registrar Office at ACT Main Campus, Ground Floor.")
                )
            )
        return

    # ... [existing code for course fees, certificates, etc.] ...

# ▼▼▼ Add your new handlers HERE ▼▼▼ (BEFORE OpenAI section) ▼▼▼

# Location Inquiry Handler
    if any(keyword in user_message for keyword in ["location", "address", "where is act", "directions"]):
        loc = KNOWLEDGE['location']
        response = format_message(
            "ACT LOCATION 📍",
            f"🏛️ Main Campus: {loc['main']}\n"
            f"🗺️ Directions: {loc['directions']}\n\n"
            f"📞 Need help finding us? Call: {KNOWLEDGE['contacts']['office_phone']}"
        )
        await update.message.reply_text(response)
        return

    # Enhanced Contact Information Handler
    if any(keyword in user_message for keyword in ["contact", "phone", "call", "number", "reach"]):
        contacts = KNOWLEDGE['contacts']
        response = format_message(
            "CONTACT ACT 📞",
            f"📱 General Inquiries: {contacts['phone']}\n"
            f"📞 Office Direct Line: {contacts['office_phone']}\n"
            f"📧 Email: {contacts['email']}\n"
            f"🌐 Website: {contacts['website']}"
        )
        await update.message.reply_text(response)
        return

    # ============== OPENAI FALLBACK ==============
    client = OpenAI(api_key=OPENAI_API_KEY, timeout=30)
    # ... rest of OpenAI code ...
    
    knowledge_str = "\n".join(
    f"{k}: {', '.join(v.keys()) if isinstance(v, dict) else str(v)[:100]}..."
    for k,v in KNOWLEDGE.items()
)
    system_content = (
        f"You are {AI_CONFIG['name']}, an AI assistant for the American College of Technology (ACT), created by {AI_CONFIG['builder']}.\n"
        f"Your purpose is: {AI_CONFIG['purpose']}\n"
        f"You must strictly follow these rules: {'; '.join(AI_CONFIG['restrictions'])}\n\n"
        "Refer to the following information about ACT. Do not make up information outside of this knowledge base.\n"
        "If information is not available, say so and guide the user to contact the relevant office.\n"
        "CURRENT KNOWLEDGE:\n"
        f"{knowledge_str}"
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_content}, # Pass clean system_content
                {"role": "user", "content": update.message.text} # Use original user message text
            ],
            max_tokens=250 # Adjusted token limit, still a guideline
        )

        bot_reply = response.choices[0].message.content
        # Optional: if you need to strictly enforce character limit AFTER getting response
        # if len(bot_reply) > 300:
        # bot_reply = bot_reply[:297] + "..."
        
        await update.message.reply_text(
            format_message("ACT RESPONSE 📌", bot_reply)
        )

    except Exception as e:
        logger.error(f"OpenAI API Error: {str(e)}")
        await update.message.reply_text(
            format_message(
                "SYSTEM ERROR ⚠️",
                f"I've encountered a technical difficulty.\nPlease try again later or "
                f"contact support: {KNOWLEDGE['contacts']['phone']}"
            )
        )

 
async def update_knowledge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_ID:
        await update.message.reply_text("❌ Admin system disabled")
        return
    if str(update.effective_user.id) != ADMIN_ID.strip():
        await update.message.reply_text("❌ Administrator authorization required")
        return

    command_parts = update.message.text.split(' ', 1)
    if len(command_parts) < 2:
        await update.message.reply_text(
            format_message(
                "UPDATE FAILED ❌",
                "No data provided for update.\n\n"
                "Valid format example:\n"
                "/update_knowledge {\"courses\": {\"new_course\": {\"price\": 10000}}}"
            )
        )
        return

    try:
        new_data_json = command_parts[1]
        new_data = json.loads(new_data_json)
        
        global KNOWLEDGE
        KNOWLEDGE = deep_merge(KNOWLEDGE, new_data)
        
        await update.message.reply_text(
            format_message(
                "KNOWLEDGE UPDATED ✅",
                "New information successfully loaded into the knowledge base!\n\n"
                f"Updated sections: {', '.join(new_data.keys())}"
            )
        )
        logger.info(f"Knowledge base updated by admin {update.effective_user.id}. New keys: {', '.join(new_data.keys())}")

    except json.JSONDecodeError as e:
        await update.message.reply_text(
            format_message(
                "UPDATE FAILED ❌",
                f"Invalid JSON format: {str(e)}\n\n"
                "Ensure your data is correctly formatted JSON.\nExample:\n"
                "/update_knowledge {\"contacts\": {\"new_phone\": \"0912345678\"}}"
            )
        )
    except Exception as e:
        await update.message.reply_text(
            format_message(
                "UPDATE FAILED ❌",
                f"An error occurred: {str(e)}\n\n"
                "Valid format example:\n"
                "/update_knowledge {\"courses\": {\"computer_science\": {\"price\": 20000}}}"
            )
        )

# Webhook handlers and main function remain largely the same
async def webhook_handler(request):
    try:
        # Verify secret token first
        if request.headers.get('X-Telegram-Bot-Api-Secret-Token') != WEBHOOK_SECRET:
            return web.Response(status=403)
        
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return web.Response()
    except Exception as e:  # Now properly aligned
        logger.error(f"Webhook processing failed: {str(e)}")
        return web.Response(status=500)

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
    
    # Initialize application
    await application.initialize()
    await application.start()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("update_knowledge", update_knowledge))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Setup web server
    app = web.Application()
    app.router.add_post('/webhook', webhook_handler)
    app.router.add_get('/health', health_check)

    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host='0.0.0.0', port=port)
    await site.start()
    logger.info(f"🚀 Web server started on port {port}")

    # Webhook configuration
    render_app_url = os.getenv("RENDER_EXTERNAL_URL", "https://ACTAIBOT.onrender.com")
    webhook_url = f"{render_app_url}/webhook"
    
    try:  # Properly aligned with 4-space indentation
        await application.bot.set_webhook(
            url=webhook_url,
            secret_token=WEBHOOK_SECRET,
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        logger.info(f"✅ Webhook successfully set to: {webhook_url}")
        logger.info(f"🛡️ Using secret token: {WEBHOOK_SECRET[:3]}...{WEBHOOK_SECRET[-3:]}")
    except Exception as e:
        logger.error(f"❌ Failed to set webhook: {str(e)}")
        raise

    logger.info("🎓 ACT-AI Assistant is ACTIVE and listening for updates...")
    
    # Keep application alive
    try:
        await asyncio.Event().wait()
    finally:
        logger.info("Shutting down web server and application...")
        await runner.cleanup()
        if application.running:
            await application.stop()
        await application.shutdown()
        logger.info("Shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n🔵 Service shutdown initiated by KeyboardInterrupt.")
    except Exception as e:
        logger.error(f"💥 An unexpected error occurred in main: {e}")
