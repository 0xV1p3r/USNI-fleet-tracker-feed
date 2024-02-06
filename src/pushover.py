import requests
import logging

logger = logging.getLogger("pushover")


def send_message(message: str, image_filename: str, user_token: str, app_token: str):
    logger.debug(f"Sending message: '{message}'")

    try:
        requests.post(url="https://api.pushover.net/1/messages.json",
                      data={"token": app_token, "user": user_token, "message": message},
                      files={"attachment": (image_filename, open(f"./images/{image_filename}", "rb"), "image/jpeg")}
                      )
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred while sending a message via Pushover: {str(e)}")
