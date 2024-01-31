import telegram


async def send_message(token: str, message: str, image_url: str):

    bot = telegram.Bot(token)

    chat_ids = []

    updates = (await bot.get_updates())

    for update in updates:
        chat_ids.append(update.message.from_user.id)

    for chat_id in chat_ids:
        await bot.send_photo(chat_id, image_url)
        await bot.send_message(text=message, chat_id=chat_id)
