"""
Orchestrator Service

Coordinates multi-agent ADK pipelines. Handles:
- Q&A workflow (retrieval → answer → confidence)
- Paper listing
- Agent orchestration

Cloud Run Service: Always running, handles HTTP requests
"""

import os
import logging
from typing import Dict, Any

from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import pubsub_v1, storage
import json
import tempfile
import uuid

# Import our ADK-based pipelines
from src.pipelines.qa_pipeline import QAPipeline
from src.storage.firestore_client import FirestoreClient
from src.utils.config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global pipeline instances (lazy-loaded)
_qa_pipeline = None
_firestore_client = None
_pubsub_publisher = None
_storage_client = None


def get_qa_pipeline() -> QAPipeline:
    """Lazy-load QA pipeline with ADK agents"""
    global _qa_pipeline
    if _qa_pipeline is None:
        logger.info("[Orchestrator] Initializing QA Pipeline with ADK agents...")
        _qa_pipeline = QAPipeline(enable_confidence=True)
        logger.info("[Orchestrator] QA Pipeline initialized (AnswerAgent + ConfidenceAgent)")
    return _qa_pipeline


def get_firestore_client() -> FirestoreClient:
    """Lazy-load Firestore client"""
    global _firestore_client
    if _firestore_client is None:
        logger.info("[Orchestrator] Initializing Firestore client...")
        _firestore_client = FirestoreClient()
        logger.info("[Orchestrator] Firestore client initialized")
    return _firestore_client


def get_pubsub_publisher():
    """Lazy-load Pub/Sub publisher"""
    global _pubsub_publisher
    if _pubsub_publisher is None:
        logger.info("[Orchestrator] Initializing Pub/Sub publisher...")
        _pubsub_publisher = pubsub_v1.PublisherClient()
        logger.info("[Orchestrator] Pub/Sub publisher initialized")
    return _pubsub_publisher


def get_storage_client():
    """Lazy-load Cloud Storage client"""
    global _storage_client
    if _storage_client is None:
        logger.info("[Orchestrator] Initializing Cloud Storage client...")
        _storage_client = storage.Client(project=config.gcp.project_id)
        logger.info("[Orchestrator] Cloud Storage client initialized")
    return _storage_client


@app.route('/health', methods=['GET'])
def health():
    """Health check for Cloud Run"""
    return jsonify({
        'status': 'healthy',
        'service': 'orchestrator',
        'version': '1.0.0',
        'agents': ['AnswerAgent', 'ConfidenceAgent']
    }), 200


@app.route('/', methods=['GET'])
def index():
    """Service documentation"""
    return jsonify({
        'name': 'Research Intelligence Platform - Orchestrator',
        'version': '1.0.0',
        'description': 'Multi-agent ADK pipeline orchestration',
        'agents': {
            'AnswerAgent': 'Answers questions with citations',
            'ConfidenceAgent': 'Scores answer confidence (0.0-1.0)'
        },
        'endpoints': {
            'qa': 'POST /qa',
            'papers': 'GET /papers',
            'upload': 'POST /upload',
            'health': 'GET /health'
        }
    }), 200


@app.route('/qa', methods=['POST'])
def qa():
    """
    Q&A endpoint using ADK multi-agent pipeline

    Workflow:
    1. Retrieve relevant papers from Firestore
    2. AnswerAgent (ADK LlmAgent) generates answer with citations
    3. ConfidenceAgent (ADK LlmAgent) scores confidence
    4. Return combined result

    Request:
        {
            "question": "What is the Transformer architecture?"
        }

    Response:
        {
            "question": "...",
            "answer": "...",
            "citations": [...],
            "confidence": {
                "score": 0.95,
                "evidence_strength": 1.0,
                "consistency": 0.9,
                "coverage": 0.95,
                "source_quality": 0.95,
                "reasoning": "..."
            },
            "retrieved_papers": [...]
        }
    """
    try:
        data = request.json
        if not data or 'question' not in data:
            return jsonify({'error': 'Missing required field: question'}), 400

        question = data.get('question')
        logger.info(f"[Orchestrator] Q&A request: {question}")

        # Run multi-agent pipeline
        qa_pipeline = get_qa_pipeline()
        result = qa_pipeline.ask(question)

        logger.info(f"[Orchestrator] Q&A complete:")
        logger.info(f"  - Answer length: {len(result.get('answer', ''))} chars")
        logger.info(f"  - Citations: {len(result.get('citations', []))}")
        logger.info(f"  - Retrieved papers: {len(result.get('retrieved_papers', []))}")

        if 'confidence' in result:
            logger.info(f"  - Confidence score: {result['confidence'].get('score', 0):.2f}")

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"[Orchestrator] Error in Q&A pipeline: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/papers', methods=['GET'])
def list_papers():
    """
    List all papers in corpus

    Response:
        {
            "papers": [
                {
                    "paper_id": "...",
                    "title": "...",
                    "authors": [...],
                    "key_finding": "...",
                    "ingestion_time": "..."
                },
                ...
            ],
            "count": 4
        }
    """
    try:
        logger.info("[Orchestrator] List papers request")

        firestore_client = get_firestore_client()
        papers = firestore_client.get_all_papers()

        logger.info(f"[Orchestrator] Found {len(papers)} papers")
        return jsonify({
            'papers': papers,
            'count': len(papers)
        }), 200

    except Exception as e:
        logger.error(f"[Orchestrator] Error listing papers: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/upload', methods=['POST'])
def upload_paper():
    """
    Upload a paper PDF and trigger the intake pipeline

    Workflow:
    1. Receive PDF file upload
    2. Store PDF in Cloud Storage bucket
    3. Publish message to arxiv.candidates Pub/Sub topic
    4. Intake pipeline (triggered via Pub/Sub push) processes the paper

    Request:
        Content-Type: multipart/form-data
        Fields:
            - file: PDF file

    Response:
        {
            "status": "success",
            "message": "Paper uploaded and queued for processing",
            "upload_id": "uuid",
            "storage_path": "gs://bucket/path/to/file.pdf"
        }
    """
    try:
        logger.info("[Orchestrator] Upload request received")

        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        # Check if file is PDF
        if not file.filename.endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are supported'}), 400

        # Generate unique ID for this upload
        upload_id = str(uuid.uuid4())
        logger.info(f"[Orchestrator] Processing upload: {upload_id}")

        # Store PDF in Cloud Storage
        storage_client = get_storage_client()
        bucket_name = f"{config.gcp.project_id}-arxiv-uploads"

        try:
            bucket = storage_client.bucket(bucket_name)
            # Create bucket if it doesn't exist
            if not bucket.exists():
                logger.info(f"[Orchestrator] Creating bucket: {bucket_name}")
                bucket = storage_client.create_bucket(bucket_name, location='us-central1')
        except Exception as e:
            logger.warning(f"[Orchestrator] Bucket check/create warning: {str(e)}")
            bucket = storage_client.bucket(bucket_name)

        # Upload file to Cloud Storage
        blob_name = f"uploads/{upload_id}/{file.filename}"
        blob = bucket.blob(blob_name)

        logger.info(f"[Orchestrator] Uploading to Cloud Storage: {blob_name}")
        blob.upload_from_file(file.stream, content_type='application/pdf')
        storage_path = f"gs://{bucket_name}/{blob_name}"
        logger.info(f"[Orchestrator] Upload complete: {storage_path}")

        # Publish message to arxiv.candidates topic
        publisher = get_pubsub_publisher()
        topic_path = publisher.topic_path(config.gcp.project_id, 'arxiv.candidates')

        message_data = {
            'upload_id': upload_id,
            'filename': file.filename,
            'storage_path': storage_path,
            'source': 'manual_upload',
            'timestamp': str(json.dumps({}))  # Placeholder for timestamp
        }

        logger.info(f"[Orchestrator] Publishing to Pub/Sub topic: arxiv.candidates")
        future = publisher.publish(
            topic_path,
            json.dumps(message_data).encode('utf-8')
        )
        message_id = future.result()

        logger.info(f"[Orchestrator] Published message: {message_id}")

        return jsonify({
            'status': 'success',
            'message': 'Paper uploaded and queued for processing',
            'upload_id': upload_id,
            'storage_path': storage_path,
            'pubsub_message_id': message_id
        }), 200

    except Exception as e:
        logger.error(f"[Orchestrator] Error uploading paper: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8081))
    logger.info(f"[Orchestrator] Starting on port {port}")
    logger.info(f"[Orchestrator] Using Google ADK for multi-agent orchestration")
    app.run(host='0.0.0.0', port=port, debug=False)
