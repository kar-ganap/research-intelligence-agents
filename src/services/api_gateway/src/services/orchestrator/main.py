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

# Import our ADK-based pipelines
from src.pipelines.qa_pipeline import QAPipeline
from src.storage.firestore_client import FirestoreClient

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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8081))
    logger.info(f"[Orchestrator] Starting on port {port}")
    logger.info(f"[Orchestrator] Using Google ADK for multi-agent orchestration")
    app.run(host='0.0.0.0', port=port, debug=False)
