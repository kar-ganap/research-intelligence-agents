#!/usr/bin/env python3
"""
Test script to send a sample email via SendGrid.
"""

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Configuration
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
FROM_EMAIL = "gkartik.extraneous@gmail.com"  # Verified sender in SendGrid

if not SENDGRID_API_KEY:
    print("❌ Error: SENDGRID_API_KEY environment variable not set")
    print("Please run: export SENDGRID_API_KEY='your-api-key'")
    exit(1)

# Sample alert data
alert_data = {
    "user_email": input("Enter your email address to receive test: ").strip(),
    "user_name": "Researcher",
    "paper_title": "Attention Is All You Need: Transformers for Natural Language Processing",
    "paper_authors": ["Vaswani, A.", "Shazeer, N.", "Parmar, N.", "Uszkoreit, J."],
    "match_reason": "Matches your interest in 'transformers' and 'neural networks'",
    "arxiv_id": "1706.03762"
}

user_email = alert_data['user_email']
user_name = alert_data['user_name']
paper_title = alert_data['paper_title']
authors = ', '.join(alert_data['paper_authors'][:3])
match_reason = alert_data['match_reason']
arxiv_id = alert_data['arxiv_id']

subject = "New paper matches your research interests"

html_content = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">New Research Paper Alert</h2>
    <p>Hi {user_name},</p>
    <p>A new paper has been published that matches your research interests:</p>

    <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #1f2937;">{paper_title}</h3>
        <p><strong>Authors:</strong> {authors}</p>
        <p><strong>arXiv ID:</strong> {arxiv_id}</p>
        <p><strong>Why this matches:</strong> {match_reason}</p>
    </div>

    <p>
        <a href="https://arxiv.org/abs/{arxiv_id}"
           style="background-color: #2563eb; color: white; padding: 10px 20px;
                  text-decoration: none; border-radius: 5px; display: inline-block;">
            View Paper on arXiv
        </a>
    </p>

    <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
    <p style="color: #6b7280; font-size: 12px;">
        You're receiving this because you subscribed to research alerts.
        To unsubscribe, please contact support.
    </p>
    <p style="color: #6b7280; font-size: 12px;">
        <strong>NOTE:</strong> This is a test email from Research Intelligence Platform.
    </p>
</body>
</html>
"""

text_content = f"""
Hi {user_name},

A new paper has been published that matches your research interests:

Title: {paper_title}
Authors: {authors}
arXiv ID: {arxiv_id}

Why this matches: {match_reason}

View on arXiv: https://arxiv.org/abs/{arxiv_id}

---
You're receiving this because you subscribed to research alerts.

NOTE: This is a test email from Research Intelligence Platform.
"""

print(f"\nSending test email to: {user_email}")
print(f"Subject: {subject}")
print("\n" + "="*70)

try:
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=user_email,
        subject=subject,
        html_content=html_content
    )

    sg = SendGridAPIClient(SENDGRID_API_KEY)
    response = sg.send(message)

    print(f"✅ Email sent successfully!")
    print(f"SendGrid response status: {response.status_code}")
    print(f"Response body: {response.body}")
    print(f"\nCheck your inbox at: {user_email}")
    print("="*70)

except Exception as e:
    print(f"❌ Failed to send email: {e}")
    print("="*70)
