"""
Intake Pipeline Service

Cloud Run Service that receives Pub/Sub push messages and processes papers.
Wraps the intake pipeline job logic in an HTTP endpoint.

Triggered by: Pub/Sub push subscription (arxiv-candidates-sub)
"""

import os
import logging
import json
import tempfile
import requests
from pathlib import Path
from typing import Dict, Optional
from base64 import b64decode

from flask import Flask, request, jsonify
from flask_cors import CORS

from src.pipelines.ingestion_pipeline import IngestionPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global pipeline instance (lazy-loaded)
_ingestion_pipeline = None

# Configuration
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT')


def get_ingestion_pipeline() -> IngestionPipeline:
    """Lazy-load ingestion pipeline"""
    global _ingestion_pipeline
    if _ingestion_pipeline is None:
        logger.info("[Intake Pipeline] Initializing ingestion pipeline...")
        _ingestion_pipeline = IngestionPipeline(
            project_id=PROJECT_ID,
            enable_relationships=True,
            enable_alerting=True
        )
        logger.info("[Intake Pipeline] Ingestion pipeline initialized")
    return _ingestion_pipeline


def download_pdf(pdf_url: str, output_dir: Path) -> Optional[Path]:
    """
    Download PDF from arXiv or Cloud Storage.

    Args:
        pdf_url: URL to PDF (http/https or gs://)
        output_dir: Directory to save PDF

    Returns:
        Path to downloaded PDF, or None if failed
    """
    try:
        logger.info(f"Downloading PDF: {pdf_url}")

        if pdf_url.startswith('gs://'):
            # Cloud Storage path
            from google.cloud import storage
            storage_client = storage.Client(project=PROJECT_ID)

            # Parse gs://bucket/path
            parts = pdf_url.replace('gs://', '').split('/', 1)
            bucket_name = parts[0]
            blob_name = parts[1]

            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            # Extract filename
            filename = blob_name.split('/')[-1]
            pdf_path = output_dir / filename

            blob.download_to_filename(str(pdf_path))
            logger.info(f"Downloaded from Cloud Storage to: {pdf_path}")
            return pdf_path
        else:
            # HTTP/HTTPS URL
            response = requests.get(pdf_url, timeout=60)
            response.raise_for_status()

            # Extract filename from URL or generate one
            arxiv_id = pdf_url.split('/')[-1].replace('.pdf', '')
            pdf_path = output_dir / f"{arxiv_id}.pdf"

            with open(pdf_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"Downloaded PDF to: {pdf_path}")
            return pdf_path

    except Exception as e:
        logger.error(f"Error downloading PDF {pdf_url}: {str(e)}")
        return None


def process_paper(paper_data: Dict) -> Dict:
    """
    Process a single paper through ingestion pipeline.

    Args:
        paper_data: Paper metadata (must include pdf_url or storage_path)

    Returns:
        Result dictionary with status and details
    """
    arxiv_id = paper_data.get('arxiv_id', paper_data.get('upload_id', 'unknown'))
    title = paper_data.get('title', paper_data.get('filename', 'Unknown'))

    logger.info(f"Processing paper: {title}")
    logger.info(f"  ID: {arxiv_id}")

    try:
        # Get PDF URL (support both arxiv_watcher and manual upload formats)
        pdf_url = paper_data.get('pdf_url') or paper_data.get('storage_path')

        if not pdf_url:
            return {
                'status': 'error',
                'error': 'No pdf_url or storage_path provided'
            }

        # Create temporary directory for PDF
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Download PDF
            pdf_path = download_pdf(pdf_url, temp_path)
            if not pdf_path:
                return {
                    'status': 'error',
                    'error': f'Failed to download PDF from {pdf_url}'
                }

            # Run ingestion pipeline
            logger.info(f"Running ingestion pipeline for {arxiv_id}...")
            ingestion_pipeline = get_ingestion_pipeline()

            # Pass through metadata fields for Firestore
            metadata = {}
            if 'categories' in paper_data:
                metadata['categories'] = paper_data['categories']
            if 'primary_category' in paper_data:
                metadata['primary_category'] = paper_data['primary_category']
            if 'published' in paper_data:
                metadata['published'] = paper_data['published']
            if 'updated' in paper_data:
                metadata['updated'] = paper_data['updated']

            result = ingestion_pipeline.ingest_paper(
                pdf_path=str(pdf_path),
                arxiv_id=arxiv_id,
                metadata=metadata
            )

            if result.get('success'):
                logger.info(f"✅ Successfully ingested: {title}")
                logger.info(f"  Paper ID: {result['paper_id']}")
                logger.info(f"  Relationships detected: {result.get('relationships_detected', 0)}")
                logger.info(f"  Alerts triggered: {result.get('alerts_triggered', 0)}")
            else:
                logger.error(f"❌ Failed to ingest: {title}")
                logger.error(f"  Error: {result.get('error', 'Unknown')}")

            return result

    except Exception as e:
        logger.error(f"Error processing paper {arxiv_id}: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


@app.route('/health', methods=['GET'])
def health():
    """Health check for Cloud Run"""
    return jsonify({
        'status': 'healthy',
        'service': 'intake-pipeline',
        'version': '1.0.0'
    }), 200


@app.route('/', methods=['POST'])
def handle_pubsub_push():
    """
    Handle Pub/Sub push message from arxiv.candidates topic.

    Pub/Sub sends messages in this format:
    {
        "message": {
            "data": "<base64-encoded-json>",
            "messageId": "...",
            "publishTime": "..."
        },
        "subscription": "..."
    }
    """
    try:
        envelope = request.get_json()

        if not envelope:
            logger.warning("No Pub/Sub message received")
            return jsonify({'error': 'No Pub/Sub message'}), 400

        # Extract Pub/Sub message
        pubsub_message = envelope.get('message')
        if not pubsub_message:
            logger.warning("Invalid Pub/Sub message format")
            return jsonify({'error': 'Invalid Pub/Sub message'}), 400

        # Decode message data
        message_data = b64decode(pubsub_message['data']).decode('utf-8')
        paper_data = json.loads(message_data)

        message_id = pubsub_message.get('messageId', 'unknown')
        logger.info(f"[Intake Pipeline] Received Pub/Sub message: {message_id}")
        logger.info(f"[Intake Pipeline] Paper: {paper_data.get('title', paper_data.get('filename', 'Unknown'))[:50]}...")

        # Process the paper
        result = process_paper(paper_data)

        # Return success (Pub/Sub requires 2xx response to acknowledge)
        return jsonify({
            'status': 'processed',
            'message_id': message_id,
            'result': result
        }), 200

    except Exception as e:
        logger.error(f"[Intake Pipeline] Error handling Pub/Sub message: {str(e)}", exc_info=True)
        # Return error (Pub/Sub will retry)
        return jsonify({'error': str(e)}), 500


@app.route('/process', methods=['POST'])
def process_direct():
    """
    Direct processing endpoint (for testing/manual invocation).

    Request:
        {
            "paper_data": {
                "arxiv_id": "...",
                "title": "...",
                "pdf_url": "..." or "storage_path": "gs://..."
            }
        }
    """
    try:
        data = request.get_json()

        if not data or 'paper_data' not in data:
            return jsonify({'error': 'Missing paper_data'}), 400

        paper_data = data['paper_data']
        result = process_paper(paper_data)

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"[Intake Pipeline] Error in direct processing: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8082))
    logger.info(f"[Intake Pipeline] Starting on port {port}")
    logger.info(f"[Intake Pipeline] Project ID: {PROJECT_ID}")
    app.run(host='0.0.0.0', port=port, debug=False)
