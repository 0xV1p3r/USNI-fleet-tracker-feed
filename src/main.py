from data_processing import fetch
from models import TrackerEntry

import logging.config
import urllib.error
import pushover
import logging
import tomllib
import time
import smtp

logging.config.fileConfig(fname="logger_config.ini", disable_existing_loggers=False)
logger = logging.getLogger("main")


def handle_update(update: TrackerEntry, configuration):

    configured_handlers = configuration['general']['handlers']
    logger.debug(f"Configured handlers: {configured_handlers}")

    logger.info(f"Sending notification using {configured_handlers}")

    if "pushover" in configured_handlers:

        logger.debug("Handler 'pushover' triggered.")
        pushover_app_token = configuration['pushover']['app_token']
        pushover_user_token = configuration['pushover']['user_token']

        pushover.send_message(
            message=f"{update.title}\n{update.date_string}",
            image_filename=update.image_file_name,
            user_token=pushover_user_token,
            app_token=pushover_app_token
        )

    if "smtp" in configured_handlers:

        logger.debug("Handler 'smtp' triggered.")
        smtp.send_email(
            email_config=configuration["smtp"],
            receiver_emails=configuration["smtp"]["receiver_emails"],
            tracker_entry=update
        )


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
