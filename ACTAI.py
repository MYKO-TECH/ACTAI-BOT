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
        "phone": "0944150000",
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
    print(f"Message from {update.effective_user.first_name} ({update.effective_user.id}): {user_message}")

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

    # OpenAI fallback
    client = OpenAI(api_key=OPENAI_API_KEY)
    
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
        print(f"OpenAI API Error: {str(e)}")
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
        # Note: KNOWLEDGE.update() is a shallow update.
        # For deep merging of nested dictionaries, a custom function would be needed.
        KNOWLEDGE.update(new_data) 
        def deep_merge(target: dict, source: dict) -> dict:
    """Recursively merge nested dictionaries"""
    for key in source:
        if isinstance(source[key], dict) and isinstance(target.get(key), dict):
            target[key] = deep_merge(target[key], source[key])
        else:
            target[key] = source[key]
    return target

async def update_knowledge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Existing admin checks...
    
    try:
        new_data_json = command_parts[1]
        new_data = json.loads(new_data_json)
        
        global KNOWLEDGE
        KNOWLEDGE = deep_merge(KNOWLEDGE, new_data)  # Replaced shallow update
        
        await update.message.reply_text(
            format_message(
                "KNOWLEDGE UPDATED ✅",
                "New information successfully loaded into the knowledge base!\n\n"
                f"Updated sections: {', '.join(new_data.keys())}"
            )
        )
        print(f"Knowledge base updated by admin {update.effective_user.id}. New keys: {', '.join(new_data.keys())}")

    # Rest of your update_knowledge code...

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
    if request.headers.get('X-Telegram-Bot-Api-Secret-Token') != WEBHOOK_SECRET:
        return web.Response(status=403)
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return web.Response()

async def health_check(request):
    return web.Response(text="OK")

async def main():
    global application # Make application global so webhook_handler can access it
    application = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .updater(None) # For webhook setup
        .build()
    )

    # Initialize application (important for some internal setups)
    await application.initialize()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start)) # Help can point to start or a dedicated help message
    application.add_handler(CommandHandler("update_knowledge", update_knowledge))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot's polling mechanism (not strictly needed if only webhook, but good for dev)
    # await application.start() # Comment out if purely webhook based on Render

    # Setup web server for webhook
    app = web.Application()
    app.router.add_post(f'/{TELEGRAM_TOKEN}', webhook_handler) # Using token in path for some security
    app.router.add_get('/health', health_check)

    port = int(os.environ.get("PORT", 8080)) # Render usually sets PORT env var
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host='0.0.0.0', port=port)
    await site.start()
    print(f"🚀 Web server started on port {port}")

    # Set webhook
    # Ensure your Render service URL is correct. Using a generic placeholder.
    # Example: "https://your-app-name.onrender.com"
    render_app_url = os.getenv("RENDER_EXTERNAL_URL", f"https://ACTAIBOT.onrender.com") # Default if not set
    webhook_url = f"{render_app_url}/{TELEGRAM_TOKEN}"
    
    try:
        await application.bot.set_webhook(
            url=webhook_url,
            allowed_updates=Update.ALL_TYPES # Or specify types like [Update.MESSAGE, Update.CALLBACK_QUERY]
        )
        print(f"✅ Webhook successfully set to: {webhook_url}")
    except Exception as e:
        print(f"❌ Failed to set webhook: {str(e)}")
        # Depending on severity, you might want to raise e or handle differently
        # raise # Uncomment if critical

    print("🎓 ACT-AI Assistant is ACTIVE and listening for updates...")
    
    # Keep the application alive
    try:
        await asyncio.Event().wait() # Keeps the main coroutine running indefinitely
    finally:
        print("Shutting down web server and application...")
        await runner.cleanup()
        if application.running: # Check if application was started with .start()
             await application.stop()
        await application.shutdown()
        print("Shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🔵 Service shutdown initiated by KeyboardInterrupt.")
    except Exception as e:
        print(f"💥 An unexpected error occurred in main: {e}")
