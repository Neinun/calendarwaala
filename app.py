import imaplib
import email
from email.header import decode_header
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from ics import Calendar, Event
import datetime
import re
import os
import time
import requests

import imaplib
import email
from email.header import decode_header
import getpass # To securely ask for the password

# --- Configuration ---
# You can hardcode these, but it's more secure to input them at runtime.
IMAP_SERVER = "imap.gmail.com" # e.g., "imap.gmail.com" for Gmail

def get_email_body(msg):
    """
    Decodes the email body from a message object.
    It prioritizes plain text over HTML.
    """
    body = ""
    # If the email is multipart, walk through each part.
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            # Check for plain text and ignore attachments.
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    # Decode the payload and set it as the body.
                    body = part.get_payload(decode=True).decode()
                    break # Stop after finding the plain text part.
                except:
                    pass
    # If the email is not multipart, get the payload directly.
    else:
        try:
            body = msg.get_payload(decode=True).decode()
        except:
            pass
    return body

def check_for_new_mail():
    """
    Connects to an IMAP server, checks for unread emails from a specific sender,
    and prints their details.
    """
    try:
        # --- User Input ---
        email_address = input("Enter your email address: ")
        # Use getpass to hide password input
        app_password = getpass.getpass("Enter your App Password: ")

        # --- Connect and Login ---
        print(f"\nConnecting to {IMAP_SERVER}...")
        # Connect to the server over SSL
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        # Login to your account
        mail.login(email_address, app_password)
        print("Login successful!")

        # --- Select Mailbox and Search ---
        # Select the inbox (or any other mailbox)
        mail.select("inbox")

        # Search for unread emails from a specific domain.
        # The criteria are combined: UNSEEN and FROM a specific sender.
        search_criteria = '(UNSEEN FROM "@iimtrichy.ac.in")'
        print(f"\nSearching for unread emails from '@iimtrichy.ac.in'...")
        status, message_ids = mail.search(None, search_criteria)

        if status != "OK" or not message_ids[0]:
            print("\nNo new unread messages found from that sender.")
            mail.logout()
            return

        email_id_list = message_ids[0].split()
        print(f"\nFound {len(email_id_list)} new unread email(s) from that sender.")
        print("="*50)


        # --- Fetch and Display Emails ---
        # Iterate through the IDs of the unread messages
        for email_id in email_id_list:
            # Fetch the full email data (RFC822) for the given ID
            status, msg_data = mail.fetch(email_id, "(RFC822)")

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    # Parse the raw email bytes into a message object
                    msg = email.message_from_bytes(response_part[1])

                    # --- Decode Subject ---
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        # If it's in bytes, decode to a string
                        subject = subject.decode(encoding if encoding else "utf-8")

                    # --- Decode Sender ---
                    from_ = msg.get("From")

                    print(f"From: {from_}")
                    print(f"Subject: {subject}")

                    # --- Get Email Body ---
                    body = get_email_body(msg)
                    if body:
                        print("\n--- Body ---\n")
                        print(body.strip())
                    else:
                        print("\n[Could not retrieve plain text body]")

                    print("="*50)

    except imaplib.IMAP4.error as e:
        print(f"\nERROR: Could not connect or log in. Please check your credentials and IMAP server.")
        print(f"IMAP Error: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        # --- Logout ---
        # Ensure logout is called to close the connection
        if 'mail' in locals() and mail.state == 'SELECTED':
            mail.logout()
            print("\nLogged out and connection closed.")


if __name__ == "__main__":
    check_for_new_mail()

