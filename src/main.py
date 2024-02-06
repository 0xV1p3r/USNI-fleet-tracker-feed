from telegram_bot import send_message
from data_processing import fetch
from models import TrackerEntry
import logging.config
import urllib.error
import logging
import datetime
import asyncio
import tomllib
import time

logging.config.fileConfig(fname="logger_config.ini", disable_existing_loggers=False)
logger = logging.getLogger("main")


def handle_update(update: TrackerEntry, configuration):

    configured_handlers = configuration['general']['handlers']

    if "telegram" in configured_handlers:

        logger.debug("Handler 'telegram' triggerd.")
        telegram_token = configuration['telegram']['token']

        asyncio.run(send_message(
            token=telegram_token,
            message=f"{update.title}\n{update.date_string}",
            image_url=update.image_url
            ))


if __name__ == '__main__':

    with open("config.toml", "r") as f:
        config = tomllib.loads(f.read())

    logger.info("Configuration loaded.")

    while True:
        logger.info("Fetching data...")

        try:
            new_entries = fetch()

            if len(new_entries) == 1:
                logger.info("Finished fetching data. 1 new entry.")
            else:
                logger.info(f"Finished fetching data. {len(new_entries)} new entries.")

            if new_entries:
                for entry in new_entries:
                    handle_update(update=entry, configuration=config)

        except urllib.error.HTTPError:
            logger.error(f"Error fetching data. Retrying in {config['general']['refresh_interval']} seconds")

        time.sleep(config['general']['refresh_interval'])
