from telegram_bot import wake_bot, send_message
from data_processing import fetch
from models import TrackerEntry
import datetime
import asyncio
import tomllib
import time


def now():
    return f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"


def handle_update(update: TrackerEntry, configuration):

    configured_handlers = configuration['general']['handlers']

    if "telegram" in configured_handlers:

        print(f"{now()} Handler 'telegram' triggered")
        telegram_token = configuration['telegram']['token']

        print(f"{now()} Refreshing chat list...")
        asyncio.run(wake_bot(token=telegram_token))
        print(f"{now()} Finished refreshing chat list")

        print(f"{now()} Sending messages...")
        asyncio.run(send_message(
            token=telegram_token,
            message=f"{update.title}\n{update.date_string}",
            image_url=update.image_url
            ))
        print(f"{now()} Finished sending messages")


if __name__ == '__main__':

    with open("config.toml", "r") as f:
        config = tomllib.loads(f.read())

    print(f"{now()} Config loaded")

    while True:
        print(f"{now()} Fetching data...")
        new_entries = fetch()
        print(f"{now()} Finished fetching data. {len(new_entries)} new entries")

        if new_entries:
            for entry in new_entries:
                handle_update(update=entry, configuration=config)

        time.sleep(config['general']['interval'])
