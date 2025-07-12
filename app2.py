# this file has all the logic

# Email Automation with AI Summarization and Calendar Events
#
# This script connects to a Gmail account, fetches unread emails,
# summarizes their content using a placeholder for a Large Language Model (LLM),
# extracts deadlines to create an ICS calendar file, and sends a reply
# with the summary and the ICS file.
#
# Author: Gemini
#
#-----------------------------------------------------------------------
#
# REQUIREMENTS:
#
# pip install imapclient ics requests
#
#-----------------------------------------------------------------------
#
# GMAIL SETUP:
#
# 1. Enable IMAP in your Gmail settings:
#    - Go to Gmail -> Settings -> See all settings -> Forwarding and POP/IMAP.
#    - In the "IMAP access" section, select "Enable IMAP".
#
# 2. Create an App Password for your Gmail account:
#    - Go to your Google Account settings: https://myaccount.google.com/
#    - Go to Security.
#    - Under "Signing in to Google," select "2-Step Verification" and follow the steps.
#      (You MUST have 2-Step Verification enabled to use App Passwords).
#    - Go back to the Security page, and select "App passwords".
#    - Under "Select app," choose "Other (Custom name)" and give it a name (e.g., "Python Email Bot").
#    - Google will generate a 16-character password. Use this password in the script, NOT your regular Gmail password.
#
#-----------------------------------------------------------------------

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
import requests # Used for making requests to the LLM API

# --- CONFIGURATION ---
# Enter your Gmail credentials and settings here
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ACCOUNT = "calendarwaala@gmail.com"
APP_PASSWORD = "" # Use the App Password you generated

# --- LLM API Configuration ---
# Replace with your actual LLM API endpoint and key
LLM_API_URL = "YOUR_LLM_API_ENDPOINT"
LLM_API_KEY = "YOUR_LLM_API_KEY"


def check_for_new_emails():
    """
    Connects to the Gmail server and fetches unread emails.
    Returns a list of email messages.
    """
    try:
        # Connect to the server
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        # Login to your account
        mail.login(EMAIL_ACCOUNT, APP_PASSWORD)
        # Select the mailbox you want to check (e.g., 'inbox')
        mail.select("inbox")

        # Search for all unread emails from a specific domain
        search_criteria = '(UNSEEN FROM "@iimtrichy.ac.in")'
        status, messages = mail.search(None, search_criteria)

        if status != "OK":
            print("No new messages found.")
            mail.logout()
            return []

        email_ids = messages[0].split()
        if not email_ids:
            print("No new messages found from the specified domain.")
            mail.logout()
            return []

        print(f"Found {len(email_ids)} new emails.")
        
        fetched_emails = []
        for email_id in email_ids:
            # Fetch the email by ID
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            if status == "OK":
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        fetched_emails.append(msg)
                        # Mark the email as read (seen)
                        mail.store(email_id, '+FLAGS', '\\Seen')

        mail.logout()
        return fetched_emails

    except Exception as e:
        print(f"Error connecting to Gmail: {e}")
        return []


def get_email_content(msg):
    """
    Parses the email message to extract subject, sender, and body.
    """
    subject, encoding = decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding if encoding else "utf-8")

    sender, encoding = decode_header(msg.get("From"))[0]
    if isinstance(sender, bytes):
        sender = sender.decode(encoding if encoding else "utf-8")

    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if "attachment" not in content_disposition:
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode()
                        break
                    except:
                        pass
    else:
        try:
            body = msg.get_payload(decode=True).decode()
        except:
            pass
            
    return subject, sender, body


def summarize_and_extract_deadline_with_llm(email_body):
    """
    Uses a placeholder LLM API to summarize email content and extract a deadline.
    Returns a summary, a boolean indicating if a deadline was found, and the deadline string.
    """
    prompt = f"
    Please perform the following tasks on the email content below:

    1.  Summarize the email in a maximum of 2 concise lines.
    2.  Determine if a deadline is present. Respond with "yes" or "no".
    3.  If a deadline is present, extract it in 'YYYY-MM-DD HH:MM:SS' format. If not, respond with "None".

    Email Content:
    ---
    {email_body}
    ---

    Provide the output in the following format, with each item on a new line:
    Summary: [Your 2-line summary here]
    Deadline_Present: [yes/no]
    Deadline: [YYYY-MM-DD HH:MM:SS or None]
    "

    # This is a mock API call. Replace with your actual implementation.
    # In a real scenario, you would parse the response from the LLM.
    
    # --- MOCK RESPONSE (for testing without a real API) ---
    
    print("\n--- MOCKING LLM RESPONSE ---")
    summary = "This is a mock summary. The project deadline has been set and your feedback is required."
    has_deadline = False
    deadline_str = "None"
    
    if "deadline" in email_body.lower() or "due by" in email_body.lower():
        # Simple regex to find a date for demonstration
        match = re.search(r'\d{4}-\d{2}-\d{2}', email_body)
        if match:
            deadline_str = f"{match.group(0)} 17:00:00" # Assume 5 PM if time not specified
            has_deadline = True
            
    print(f"Extracted Summary: {summary}")
    print(f"Deadline Present: {'yes' if has_deadline else 'no'}")
    print(f"Extracted Deadline: {deadline_str}")
    # --- END MOCK ---

    return summary, has_deadline, deadline_str


def create_ics_file(deadline_str, subject):
    """
    Creates an .ics calendar file for the given deadline.
    """
    try:
        deadline_dt = datetime.datetime.strptime(deadline_str, '%Y-%m-%d %H:%M:%S')
        
        c = Calendar()
        e = Event()
        
        e.name = f"Deadline: {subject}"
        e.begin = deadline_dt
        # Make the event 1 hour long by default
        e.end = deadline_dt + datetime.timedelta(hours=1)
        e.description = f"This event was automatically created based on an email regarding: '{subject}'"
        
        c.events.add(e)
        
        ics_filename = "event.ics"
        with open(ics_filename, 'w') as f:
            f.writelines(c)
            
        return ics_filename
    except Exception as e:
        print(f"Error creating ICS file: {e}")
        return None


def send_reply(sender, subject, summary, deadline_detected, ics_file_path=None):
    """
    Sends an email reply with the summary. Attaches the ICS file if a deadline was detected.
    """
    # Extract just the email address from the sender string
    recipient_email = email.utils.parseaddr(sender)[1]
    
    if not recipient_email:
        print(f"Could not parse recipient email from: {sender}")
        return

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ACCOUNT
    msg['To'] = recipient_email
    msg['Subject'] = f"Re: {subject} (Summary)"

    # Construct email body based on whether a deadline was found
    body = f"Hello,\n\nHere is a summary of your recent email:\n\n---\n{summary}\n---\n\n"
    if deadline_detected:
        body += "I've also attached a calendar event for the deadline mentioned. You can click on it to add it to your calendar.\n\n"
    else:
        body += "No specific deadline was detected in this email.\n\n"
    body += "Best regards,\nYour Email Bot"
    
    msg.attach(MIMEText(body, 'plain'))

    # Attach ICS file only if a deadline was detected and the file was created
    if deadline_detected and ics_file_path:
        try:
            with open(ics_file_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {os.path.basename(ics_file_path)}",
            )
            msg.attach(part)
        except Exception as e:
            print(f"Error attaching file: {e}")

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ACCOUNT, APP_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ACCOUNT, recipient_email, text)
        server.quit()
        print(f"Reply sent to {recipient_email}")
    except Exception as e:
        print(f"Error sending email: {e}")


def main():
    """
    Main function to run the email processing loop.
    """
    print("Starting email automation script...")
    while True:
        emails = check_for_new_emails()
        for msg in emails:
            subject, sender, body = get_email_content(msg)
            print("\n-----------------------------------")
            print(f"Processing email from: {sender}")
            print(f"Subject: {subject}")
            
            if not body:
                print("Email body is empty or could not be parsed. Skipping.")
                continue

            summary, has_deadline, deadline_str = summarize_and_extract_deadline_with_llm(body)
            
            ics_file = None
            if has_deadline:
                ics_file = create_ics_file(deadline_str, subject)
            
            send_reply(sender, subject, summary, has_deadline, ics_file)

            # Clean up the created ICS file
            if ics_file and os.path.exists(ics_file):
                os.remove(ics_file)
        
        # Wait for a specified time before checking for new emails again
        sleep_interval = 60 # in seconds
        print(f"\nWaiting for {sleep_interval} seconds before checking again...")
        time.sleep(sleep_interval)


if __name__ == "__main__":
    # IMPORTANT: Replace placeholder values in the CONFIGURATION section
    if "YOUR_GMAIL_ADDRESS" in EMAIL_ACCOUNT or "YOUR_16_DIGIT_APP_PASSWORD" in APP_PASSWORD:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! PLEASE CONFIGURE YOUR EMAIL_ACCOUNT AND APP_PASSWORD !!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    else:
        main()

