import logging
import smtplib
import base64
import ssl

from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("smtp")


def send_email_starttls(smtp_server, smtp_port, sender_email, password, receiver_emails, message):
    logger.debug(f"Sending email via STARTTLS using SMTP server {smtp_server} with user {sender_email}: {message}")

    # Create a secure SSL context
    context = ssl.create_default_context()
    server = smtplib.SMTP(smtp_server, smtp_port)

    # Try to log in to server and send email
    try:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)  # Secure the connection
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(from_addr=sender_email, to_addrs=receiver_emails, msg=message.as_string())
    except Exception as e:
        logger.error(f"Error occurred while sending email: {e}")
    finally:
        server.quit()


def get_base64_encoded_image(file_name):
    logger.debug(f"Getting base64 encoded image from '{file_name}'")
    try:
        with open(f"./images/{file_name}", "rb") as img:
            return base64.b64encode(img.read())
    except OSError as e:
        logger.error(f"Error while encoding '{file_name}': {e}")


def send_email_ssl(smtp_server, smtp_port, sender_email, password, receiver_emails, message):
    logger.debug(f"Sending email via SSL using SMTP server {smtp_server} with user {sender_email}: {message}")

    # Create a secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(host=smtp_server, port=smtp_port, context=context) as server:
        server.login(user=sender_email, password=password)
        server.sendmail(from_addr=sender_email, to_addrs=receiver_emails, msg=message.as_string())


def create_image_attachment(file_name):
    logger.debug(f"Creating image attachment for '{file_name}'")

    try:
        with open(f"./images/{file_name}", "rb") as img:
            # Add file as application/octet-stream
            # Email client can usually download this automatically as attachment
            attachment = MIMEBase("application", "octet-stream")
            attachment.set_payload(img.read())
    except OSError as e:
        logger.error(f"Error while creating image attachment for '{file_name}': {e}")
        return None

    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", f"attachment; filename= {file_name}",)

    return attachment


def create_message(sender_email, receiver_emails, tracker_entry):

    message = MIMEMultipart("alternative")
    message["Subject"] = tracker_entry.title
    message["From"] = sender_email
    message["To"] = receiver_emails
    message["Bcc"] = receiver_emails  # Recommended for mass emails

    text = f"{tracker_entry.date_string}\nArticle: {tracker_entry.article_url}\nImage: {tracker_entry.image_url}"
    html = f"""
<html>
  <body>
    <p>Hi,
      <br>{tracker_entry.date_string}<br>
      You can find the article <a href="{tracker_entry.article_url}">here</a> 
      and the image <a href="{tracker_entry.image_url}">here</a>.
    </p>
    <img src="data:image/png;base64,{get_base64_encoded_image(tracker_entry.image_file_name)}" alt="img" />
  </body>
</html>
"""

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)

    img_filename = tracker_entry.image_file_name
    attachment = create_image_attachment(file_name=img_filename)

    if attachment is None:
        logger.warning(f"Failed to add '{img_filename}' as attachment.")
    else:
        message.attach(attachment)

    return message


def send_email(email_config, tracker_entry):

    if email_config["security"] != "STARTTLS" or email_config["security"] != "SSL":
        logger.error(f"'{email_config['type']}' invalid for parameter type. Needs to be STARTTLS or SSL.")
        return

    msg = create_message(
        sender_email=email_config["sender_email"],
        receiver_emails=email_config["receiver_emails"],
        tracker_entry=tracker_entry
    )

    if email_config["security"] == "STARTTLS":
        send_email_starttls(
            smtp_server=email_config["server"],
            smtp_port=email_config["port"],
            sender_email=email_config["sender_email"],
            password=email_config["password"],
            receiver_emails=email_config["receiver_emails"],
            message=msg
        )

    elif email_config["security"] == "SSL":
        send_email_ssl(
            smtp_server=email_config["server"],
            smtp_port=email_config["port"],
            sender_email=email_config["sender_email"],
            password=email_config["password"],
            receiver_emails=email_config["receiver_emails"],
            message=msg
        )
