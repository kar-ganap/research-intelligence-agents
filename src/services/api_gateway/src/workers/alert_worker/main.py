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
from typing import Dict
from concurrent import futures

from google.cloud import pubsub_v1

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

# Email configuration (using environment variables for now)
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@research-intelligence.app')


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

        # For MVP: Log instead of actually sending
        # In production, use SendGrid API
        if SENDGRID_API_KEY:
            # TODO: Implement SendGrid email sending
            logger.info("SendGrid integration not implemented yet")
            pass

        # For now, just log the alert
        logger.info("=" * 70)
        logger.info(f"📧 EMAIL NOTIFICATION")
        logger.info(f"To: {user_email}")
        logger.info(f"Subject: New paper matches your research interests")
        logger.info("-" * 70)
        logger.info(f"Hi {user_name},")
        logger.info(f"")
        logger.info(f"A new paper has been published that matches your interests:")
        logger.info(f"")
        logger.info(f"  Title: {paper_title}")
        logger.info(f"  Authors: {authors}")
        logger.info(f"  arXiv ID: {arxiv_id}")
        logger.info(f"")
        logger.info(f"  Why this matches: {match_reason}")
        logger.info(f"")
        logger.info(f"View on arXiv: https://arxiv.org/abs/{arxiv_id}")
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
            logger.info("✅ Alert processed and acknowledged")
        else:
            # Nack message (requeue for retry)
            message.nack()
            logger.warning("⚠️  Alert processing failed, message requeued")

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        message.nack()


def main():
    """
    Main worker loop.

    Continuously pulls messages from Pub/Sub and processes them.
    Runs until interrupted or error occurs.
    """
    logger.info("=" * 70)
    logger.info("Alert Worker Started")
    logger.info("=" * 70)
    logger.info(f"Project ID: {PROJECT_ID}")
    logger.info(f"Subscription: {SUBSCRIPTION_ID}")
    logger.info(f"Max Messages: {MAX_MESSAGES}")
    logger.info("=" * 70)

    try:
        # Create subscriber client
        subscriber = pubsub_v1.SubscriberClient()
        subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

        logger.info(f"Subscribing to: {subscription_path}")
        logger.info("Worker is now listening for messages... (Ctrl+C to stop)")

        # Create streaming pull
        streaming_pull_future = subscriber.subscribe(
            subscription_path,
            callback=process_message,
            flow_control=pubsub_v1.types.FlowControl(
                max_messages=MAX_MESSAGES,
            ),
        )

        # Keep worker running
        try:
            streaming_pull_future.result()
        except KeyboardInterrupt:
            logger.info("Received interrupt, shutting down...")
            streaming_pull_future.cancel()
            streaming_pull_future.result()

    except Exception as e:
        logger.error(f"Worker failed: {str(e)}", exc_info=True)
        return 1

    logger.info("=" * 70)
    logger.info("Alert Worker Stopped")
    logger.info("=" * 70)
    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\nWorker interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)
