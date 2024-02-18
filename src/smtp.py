import logging
import smtplib
import ssl

from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("smtp")


def send_email_starttls(smtp_server, smtp_port, sender_email, password, receiver_email, message):
    logger.debug(f"Sending email via STARTTLS using SMTP server {smtp_server} with user {sender_email}")

    # Create a secure SSL context
    context = ssl.create_default_context()
    server = smtplib.SMTP(smtp_server, smtp_port)

    # Try to log in to server and send email
    try:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)  # Secure the connection
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(from_addr=sender_email, to_addrs=receiver_email, msg=message.as_string())
    except Exception as e:
        logger.error(f"Error occurred while sending email: {e}")
    finally:
        server.quit()


def send_email_ssl(smtp_server, smtp_port, sender_email, password, receiver_email, message):
    logger.debug(f"Sending email via SSL using SMTP server {smtp_server} with user {sender_email}")

    # Create a secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(host=smtp_server, port=smtp_port, context=context) as server:
        server.login(user=sender_email, password=password)
        server.sendmail(from_addr=sender_email, to_addrs=receiver_email, msg=message.as_string())


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


def create_message(sender_email, tracker_entry):

    message = MIMEMultipart("alternative")
    message["Subject"] = tracker_entry.title
    message["From"] = sender_email

    text = f"{tracker_entry.date_string}\nArticle: {tracker_entry.article_url}\nImage: {tracker_entry.image_url}"
    html = f"""
<html>
  <body>
    <p><br>{tracker_entry.date_string}<br>
      You can find the article <a href="{tracker_entry.article_url}">here</a> 
      and the image <a href="{tracker_entry.image_url}">here</a>.
    </p>
    <img src="{tracker_entry.image_url}" alt="img" />
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


def send_email(email_config, receiver_emails, tracker_entry):

    if email_config["security"] != "STARTTLS" and email_config["security"] != "SSL":
        logger.error(f"'{email_config['security']}' invalid for parameter security. Needs to be STARTTLS or SSL.")
        return

    logger.debug("Creating message...")
    msg = create_message(sender_email=email_config["sender_email"], tracker_entry=tracker_entry)
    logger.debug("Finished creating message.")

    if email_config["security"] == "STARTTLS":
        for receiver_email in receiver_emails:
            msg["To"] = receiver_email
            send_email_starttls(
                smtp_server=email_config["server"],
                smtp_port=str(email_config["port"]),
                sender_email=email_config["sender_email"],
                password=email_config["password"],
                receiver_email=receiver_email,
                message=msg
            )

    if email_config["security"] == "SSL":
        for receiver_email in receiver_emails:
            msg["To"] = receiver_email
            send_email_ssl(
                smtp_server=email_config["server"],
                smtp_port=str(email_config["port"]),
                sender_email=email_config["sender_email"],
                password=email_config["password"],
                receiver_email=receiver_email,
                message=msg
            )
