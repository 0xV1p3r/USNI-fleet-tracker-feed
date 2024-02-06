import telegram
import logging

logger = logging.getLogger("telegram")


async def send_message(token: str, message: str, image_url: str):

    logger.debug(f"Sending message: {message}")

    bot = telegram.Bot(token)

    chat_ids = []

    updates = (await bot.get_updates())
    logger.debug(f"Received updates: {updates}")

    for update in updates:
        chat_ids.append(update.message.from_user.id)

    for chat_id in chat_ids:
        await bot.send_photo(chat_id, image_url)
        await bot.send_message(text=message, chat_id=chat_id)
        logger.debug(f"Sent message to chat_id: {chat_id}")
