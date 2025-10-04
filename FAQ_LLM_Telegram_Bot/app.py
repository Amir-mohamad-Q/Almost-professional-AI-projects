import argparse
import sys

import emoji
from loguru import logger

from src.bot import BOT_USERNAME, bot
from src.config import ADMINS_USERNAME, APPROVED_CHATS
from src.constants import (
    HIGH_VOLTAGE_EMOJI,
    HIGH_VOLTAGE_EMOJIS,
    LLM_MODEL,
    PILE_OF_POO_EMOJI,
    REPLY_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    THINKING_EMOJI,
    WAITING_MESSAGE,
    WELCOME_MESSAGE,
)
from src.llm import call_llm
from src.telegram_utils import (
    get_message_content,
    is_bot_mentioned,
    send_telegram_message,
)


def configure_logger(verbose):
    log_level = "DEBUG" if verbose else "INFO"
    logger.remove()  # Remove the default handler
    logger.add(sys.stderr, level=log_level)
    logger.add("logs/bot.log", rotation="100 MB", level="DEBUG")
    logger.info(f"Log level set to {log_level} for console and DEBUG for file")


def is_message_from_admins(message):
    if hasattr(message, "from_user") and getattr(message.from_user, "username", None):
        username = (message.from_user.username or "").lower()
    else:
        username = (getattr(getattr(message, "user", None), "username", "") or "").lower()
    return bool(username) and username in ADMINS_USERNAME


def is_message_in_approved_chats(message):
    chat_username = (getattr(message.chat, "username", "") or "").lower()
    return bool(chat_username) and chat_username in APPROVED_CHATS


def is_message_reply_to_message(message):
    reply_to_message = getattr(message, "reply_to_message", None)
    if not reply_to_message:
        return False
    replied_user = getattr(reply_to_message, "from_user", None)
    replied_username = (getattr(replied_user, "username", "") or "").lower()
    return bool(replied_username) and replied_username == BOT_USERNAME.lower()


def should_process_message(message):
    is_admin = is_message_from_admins(message)
    mention_or_reply = is_bot_mentioned(message, BOT_USERNAME) or is_message_reply_to_message(message)
    conditions = [is_admin, mention_or_reply]

    logger.debug(f"Conditions: {conditions}")
    return all(conditions)


def should_process_reaction(message):
    conditions = [is_message_from_admins(message)]

    logger.debug(f"Conditions: {conditions}")
    return all(conditions)



@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    """Send welcome message for /start and /help commands."""
    send_telegram_message(
        bot,
        message.chat.id,
        WELCOME_MESSAGE,
        reply_to_message_id=message.message_id,
    )


@bot.message_handler(func=lambda message: True)
@bot.edited_message_handler(func=lambda message: True)
def handle_message(message):
    """Handle incoming messages."""
    # db_handler.store_message(message.json)
    if should_process_message(message):
        process_message(message)


@bot.message_handler(content_types=["sticker"])
def handle_sticker(message):
    """Trigger actions based on sticker emoji when admins reply with a sticker."""
    try:
        if not (is_message_from_admins(message) and is_message_reply_to_message(message)):
            return

        if not getattr(message, "sticker", None):
            return

        sticker_emoji = getattr(message.sticker, "emoji", None)
        if not sticker_emoji:
            return

        reaction = emoji.demojize(sticker_emoji)
        logger.debug(f"Sticker reaction: {reaction}")

        if reaction in HIGH_VOLTAGE_EMOJIS:
            message_text = get_message_content(message.chat.id, message.reply_to_message.message_id)
            waiting_message = send_telegram_message(
                bot,
                message.chat.id,
                WAITING_MESSAGE,
                reply_to_message_id=message.message_id
            )
            response = call_llm(message_text, LLM_MODEL, SYSTEM_PROMPT)

            send_llm_response(waiting_message, response)
    except Exception as e:
        logger.exception(f"Error handling sticker: {e}")


@bot.message_reaction_handler(func=lambda message: message.new_reaction)
def handle_reaction(message):
    """Handle reactions to messages."""
    if should_process_reaction(message):
        process_reaction(message)


def process_message(message):
    """Process messages where the bot is mentioned."""
    reply_to_message = getattr(message, "reply_to_message", None)
    if reply_to_message:
        target_message_id = reply_to_message.message_id
    else:
        target_message_id = message.message_id
    message_text = get_message_content(message.chat.id, target_message_id)
    waiting_message = send_telegram_message(
        bot,
        message.chat.id,
        WAITING_MESSAGE,
        reply_to_message_id=message.message_id,
    )

    reply_guideline = message.text.replace(f"@{BOT_USERNAME}", "")
    response = call_llm(
        message_text,
        LLM_MODEL,
        REPLY_SYSTEM_PROMPT.format(reply_guideline=reply_guideline),
    )

    send_llm_response(waiting_message, response)


def process_reaction(message):
    """Process reactions to messages."""
    if not hasattr(message.new_reaction[-1], "emoji"):
        return

    reaction = emoji.demojize(message.new_reaction[-1].emoji)
    logger.debug(f"Reaction: {reaction}")

    if reaction in HIGH_VOLTAGE_EMOJIS:
        message_text = get_message_content(message.chat.id, message.message_id)
        waiting_message = send_telegram_message(
            bot,
            message.chat.id,
            WAITING_MESSAGE,
            reply_to_message_id=message.message_id,
        )
        response = call_llm(message_text, LLM_MODEL, SYSTEM_PROMPT)

        send_llm_response(waiting_message, response)
    elif reaction in [PILE_OF_POO_EMOJI]:
        bot.delete_message(message.chat.id, message.message_id)


def send_llm_response(message, response):
    """Send response, handling long messages with a 'Show More' button."""
    send_telegram_message(
        bot, message.chat.id, response, edit_message_id=message.message_id
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Telegram Bot")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    configure_logger(args.verbose)

    try:
        logger.info("Starting the bot...")
        bot.infinity_polling(
            allowed_updates=[
                "message",
                "message_reaction",
                "callback_query",
                "edited_message",
            ],
        )
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
