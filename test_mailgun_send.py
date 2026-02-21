"""
Test script to send emails via Mailgun API
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def _get_api_key():
    """Get and validate Mailgun API key."""
    api_key = os.getenv('MAILGUN_API_KEY', '')
    if not api_key:
        print("ERROR: MAILGUN_API_KEY not found in .env file")
        print("Please add: MAILGUN_API_KEY=your-api-key-here")
    return api_key


def _get_email_data():
    """Get email data for Mailgun."""
    return {
        "from": "Mailgun Sandbox <postmaster@sandbox7f309cdf2f4140238ec76af29e4563b8.mailgun.org>",
        "to": "Amey Tripathi <amey_tripathi@outlook.com>",
        "subject": "Hello Amey Tripathi",
        "text": "Congratulations Amey Tripathi, you just sent an email with Mailgun! You are truly awesome!"
    }


def _handle_response(response):
    """Handle Mailgun API response."""
    if response.status_code == 200:
        print("✅ Email sent successfully!")
        print(f"Response: {response.json()}")
        return True
    print(f"❌ Error sending email. Status code: {response.status_code}")
    print(f"Response: {response.text}")
    return False


def send_simple_message():
    """Send an email using Mailgun API"""
    api_key = _get_api_key()
    if not api_key:
        return False
    url = "https://api.mailgun.net/v3/sandbox7f309cdf2f4140238ec76af29e4563b8.mailgun.org/messages"
    try:
        response = requests.post(url, auth=("api", api_key), data=_get_email_data())
        return _handle_response(response)
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        return False


if __name__ == "__main__":
    print("Testing Mailgun email sending...")
    print("-" * 50)
    send_simple_message()
