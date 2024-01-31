import telegram
import json


def load_chat_ids():
    with open("./telegram_chat_ids.json", "r") as f:
        return json.loads(f.read())


def add_chat_ids(new_ids: list):
    existing_ids = load_chat_ids()

    if existing_ids is not None:
        data = existing_ids.extend(new_ids)
    else:
        data = new_ids

    with open("./telegram_chat_ids.json", "w") as f:
        f.write(json.dumps(data))


def refresh_chat_ids(fetched_ids):
    existing_ids = load_chat_ids()
    new_ids = []

    if existing_ids is None:
        for _id in fetched_ids:
            new_ids.append(_id)
    else:
        for _id in fetched_ids:
            if _id in existing_ids:
                continue
            new_ids.append(_id)

    if new_ids:
        add_chat_ids(new_ids)


async def wake_bot(token: str) -> list:

    bot = telegram.Bot(token)

    async with bot:
        updates = (await bot.get_updates())

    chat_ids = []

    for update in updates:
        chat_ids.append(update.message.from_user.id)

    refresh_chat_ids(chat_ids)

    return chat_ids


async def send_message(token: str, message: str, image_url: str):
    bot = telegram.Bot(token)
    chat_ids = load_chat_ids()

    for chat_id in chat_ids:
        await bot.send_photo(chat_id, image_url)
        await bot.send_message(text=message, chat_id=chat_id)
