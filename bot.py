import logging
import re
from typing import Any

import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ==================== BOT SETTINGS ====================
# Add your NEW BotFather token in Termux as BOT_TOKEN.
BOT_TOKEN = "9294652223:AAFL5H30VWQcyL LW__-bp-DPP7B2YEGtPcY"

# Your Telegram admin user ID
ADMIN_ID = 8118017475

# ==================== FREE FIRE API SETTINGS ====================
API_URL = "https://priya-ff-like-n5ge.vercel.app/like"
API_KEY = "priyasharma"

# =======================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def is_admin(update: Update) -> bool:
    user = update.effective_user
    return bool(user and user.id == ADMIN_ID)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    if not is_admin(update):
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        return

    await update.message.reply_text(
        "✅ Priya FF Like Bot is online!\n\n"
        "Command:\n"
        "/like UID REGION\n\n"
        "Example:\n"
        "/like 2226825881 IND"
    )


async def like(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    if not is_admin(update):
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ Correct format:\n/like UID REGION\n\n"
            "Example:\n/like 2226825881 IND"
        )
        return

    uid = context.args[0].strip()
    region = context.args[1].strip().upper()

    if not re.fullmatch(r"\d{5,20}", uid):
        await update.message.reply_text("❌ UID must contain 5–20 digits.")
        return

    if not re.fullmatch(r"[A-Z]{2,5}", region):
        await update.message.reply_text("❌ Region must be letters, e.g. IND.")
        return

    status_message = await update.message.reply_text("⏳ Sending like request...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                API_URL,
                params={
                    "uid": uid,
                    "region": region,
                    "key": API_KEY,
                },
            )
            response.raise_for_status()

        try:
            data: Any = response.json()
        except ValueError:
            await status_message.edit_text(
                f"⚠️ API returned an invalid response (HTTP {response.status_code})."
            )
            return

        if not isinstance(data, dict):
            await status_message.edit_text("⚠️ Unexpected API response format.")
            return

        nickname = data.get("PlayerNickname", "Unknown")
        likes_before = data.get("LikesbeforeCommand", "N/A")
        likes_after = data.get("LikesafterCommand", "N/A")
        likes_given = data.get("LikesGivenByAPI", "N/A")
        result_uid = data.get("UID", uid)
        result_region = data.get("Region", region)
        api_status = data.get("status")

        if str(api_status).lower() in ("1", "true", "success", "ok"):
            message = (
                "✅ FREE FIRE LIKES RESULT\n\n"
                f"👤 Player: {nickname}\n"
                f"🆔 UID: {result_uid}\n"
                f"🌍 Region: {result_region}\n\n"
                f"❤️ Likes Before: {likes_before}\n"
                f"❤️ Likes After: {likes_after}\n"
                f"➕ Likes Given: {likes_given}"
            )
        else:
            message = (
                "⚠️ API did not confirm success.\n\n"
                f"👤 Player: {nickname}\n"
                f"🆔 UID: {result_uid}\n"
                f"🌍 Region: {result_region}\n"
                f"📄 API response: {data}"
            )

        await status_message.edit_text(message)

    except httpx.TimeoutException:
        await status_message.edit_text("⌛ API timed out. Please try again.")
    except httpx.HTTPStatusError as exc:
        logger.warning("API returned HTTP %s", exc.response.status_code)
        await status_message.edit_text(
            f"⚠️ API error: HTTP {exc.response.status_code}."
        )
    except httpx.HTTPError:
        logger.exception("Could not connect to API")
        await status_message.edit_text("❌ Could not connect to the API.")
    except Exception:
        logger.exception("Unexpected error in /like")
        await status_message.edit_text("❌ Something went wrong. Check Termux logs.")


def main() -> None:
    if not BOT_TOKEN or BOT_TOKEN == "PUT_YOUR_NEW_BOTFATHER_TOKEN_HERE":
        raise SystemExit(
            "Please put your NEW BotFather token in BOT_TOKEN at the top of bot.py."
        )

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("like", like))

    logger.info("Priya FF Like Bot started.")
    app.run_polling()


if __name__ == "__main__":
    main()
