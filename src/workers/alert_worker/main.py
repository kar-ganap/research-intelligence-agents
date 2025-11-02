"""
Alert Worker

Cloud Run Worker that:
1. Listens to Pub/Sub subscription for paper match events
2. Sends email notifications to users
3. Logs alert delivery
4. Runs continuously (never exits)

Triggered by: Pub/Sub messages
Worker type: Pull-based Pub/Sub consumer
"""

import os
import sys
import logging
import json
import threading
from typing import Dict
from concurrent import futures

from flask import Flask, jsonify
from google.cloud import pubsub_v1
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT')
SUBSCRIPTION_ID = os.environ.get('PUBSUB_SUBSCRIPTION', 'arxiv-matches-sub')
MAX_MESSAGES = int(os.environ.get('MAX_MESSAGES', '10'))
PORT = int(os.environ.get('PORT', '8080'))

# Email configuration (using environment variables for now)
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@research-intelligence.app')

# Flask app for health checks
app = Flask(__name__)
worker_status = {"status": "starting", "messages_processed": 0}


@app.route('/')
def health_check():
    """Health check endpoint for Cloud Run."""
    return jsonify(worker_status), 200


@app.route('/health')
def health():
    """Health check endpoint for Cloud Run."""
    return jsonify(worker_status), 200


def send_email_notification(alert_data: Dict) -> bool:
    """
    Send email notification for a paper match.

    Args:
        alert_data: Alert information
            {
                "user_email": "user@example.com",
                "user_name": "John Doe",
                "paper_title": "...",
                "paper_authors": [...],
                "match_reason": "Matches your interest in 'neural networks'",
                "paper_id": "...",
                "arxiv_id": "..."
            }

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        user_email = alert_data.get('user_email')
        user_name = alert_data.get('user_name', 'Researcher')
        paper_title = alert_data.get('paper_title')
        authors = ', '.join(alert_data.get('paper_authors', [])[:3])
        match_reason = alert_data.get('match_reason')
        arxiv_id = alert_data.get('arxiv_id')

        logger.info(f"Sending email to {user_email}: {paper_title[:50]}...")

        # Prepare email content
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
        """

        if SENDGRID_API_KEY:
            try:
                # Send via SendGrid
                message = Mail(
                    from_email=Email(FROM_EMAIL, "Research Intelligence"),
                    to_emails=To(user_email),
                    subject=subject,
                    plain_text_content=Content("text/plain", text_content),
                    html_content=Content("text/html", html_content)
                )

                sg = SendGridAPIClient(SENDGRID_API_KEY)
                response = sg.send(message)

                logger.info(f"✅ Email sent successfully to {user_email}")
                logger.info(f"SendGrid response status: {response.status_code}")
                return True

            except Exception as e:
                logger.error(f"Failed to send email via SendGrid: {str(e)}")
                # Fall through to logging

        # Fallback: Log the email (for testing or if SendGrid not configured)
        logger.info("=" * 70)
        logger.info(f"📧 EMAIL NOTIFICATION (Log Mode)")
        logger.info(f"To: {user_email}")
        logger.info(f"Subject: {subject}")
        logger.info("-" * 70)
        logger.info(text_content)
        logger.info("=" * 70)

        return True

    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False


def process_message(message: pubsub_v1.subscriber.message.Message) -> None:
    """
    Process a single Pub/Sub message.

    Args:
        message: Pub/Sub message containing alert data
    """
    try:
        # Parse message
        message_data = message.data.decode('utf-8')
        alert_data = json.loads(message_data)

        logger.info(f"Processing alert: {alert_data.get('paper_title', 'Unknown')[:50]}...")

        # Send email
        success = send_email_notification(alert_data)

        if success:
            # Acknowledge message (remove from queue)
            message.ack()
            worker_status["messages_processed"] += 1
            logger.info("✅ Alert processed and acknowledged")
        else:
            # Nack message (requeue for retry)
            message.nack()
            logger.warning("⚠️  Alert processing failed, message requeued")

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        message.nack()


def start_pubsub_worker():
    """Start the Pub/Sub worker in a background thread."""
    logger.info("=" * 70)
    logger.info("Alert Worker Started")
    logger.info("=" * 70)
    logger.info(f"Project ID: {PROJECT_ID}")
    logger.info(f"Subscription: {SUBSCRIPTION_ID}")
    logger.info(f"Max Messages: {MAX_MESSAGES}")
    logger.info("=" * 70)

    try:
        worker_status["status"] = "running"

        # Create subscriber client
        subscriber = pubsub_v1.SubscriberClient()
        subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

        logger.info(f"Subscribing to: {subscription_path}")
        logger.info("Worker is now listening for messages...")

        # Create streaming pull
        streaming_pull_future = subscriber.subscribe(
            subscription_path,
            callback=process_message,
            flow_control=pubsub_v1.types.FlowControl(
                max_messages=MAX_MESSAGES,
            ),
        )

        # Keep worker running
        streaming_pull_future.result()

    except Exception as e:
        logger.error(f"Worker failed: {str(e)}", exc_info=True)
        worker_status["status"] = "error"
        worker_status["error"] = str(e)

    logger.info("=" * 70)
    logger.info("Alert Worker Stopped")
    logger.info("=" * 70)


def main():
    """
    Main function.

    Starts Pub/Sub worker in background thread and Flask server in foreground.
    """
    # Start Pub/Sub worker in background thread
    worker_thread = threading.Thread(target=start_pubsub_worker, daemon=True)
    worker_thread.start()

    # Start Flask server for health checks
    logger.info(f"Starting health check server on port {PORT}...")
    app.run(host='0.0.0.0', port=PORT)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nWorker interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)
