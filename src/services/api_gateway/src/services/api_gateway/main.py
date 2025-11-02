"""
API Gateway Service

Entry point for all HTTP requests. Handles:
- Request routing to Orchestrator and Graph Service
- Authentication (future)
- Rate limiting (future)
- Request/response logging

Cloud Run Service: Always running, handles HTTP requests
"""

import os
import logging
import requests
from typing import Dict, Any

from flask import Flask, request, jsonify
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Service URLs (from environment or defaults)
ORCHESTRATOR_URL = os.environ.get('ORCHESTRATOR_URL', 'http://localhost:8081')
GRAPH_SERVICE_URL = os.environ.get('GRAPH_SERVICE_URL', 'http://localhost:8082')

# Request timeout
REQUEST_TIMEOUT = 300  # 5 minutes for LLM calls


@app.route('/health', methods=['GET'])
def health():
    """Health check for Cloud Run"""
    return jsonify({
        'status': 'healthy',
        'service': 'api-gateway',
        'version': '1.0.0'
    }), 200


@app.route('/', methods=['GET'])
def index():
    """API documentation"""
    return jsonify({
        'name': 'Research Intelligence Platform - API Gateway',
        'version': '1.0.0',
        'endpoints': {
            'qa': 'POST /api/ask',
            'papers': 'GET /api/papers',
            'graph': 'GET /api/graph',
            'relationships': 'GET /api/relationships',
            'health': 'GET /health'
        },
        'services': {
            'orchestrator': ORCHESTRATOR_URL,
            'graph_service': GRAPH_SERVICE_URL
        }
    }), 200


@app.route('/api/ask', methods=['POST'])
def ask():
    """
    Q&A endpoint - routes to Orchestrator

    Request:
        {
            "question": "What is the Transformer architecture?"
        }

    Response:
        {
            "answer": "...",
            "citations": [...],
            "confidence": {...}
        }
    """
    try:
        data = request.json
        if not data or 'question' not in data:
            return jsonify({'error': 'Missing required field: question'}), 400

        question = data.get('question')
        logger.info(f"[API Gateway] Q&A request: {question}")

        # Forward to Orchestrator
        response = requests.post(
            f"{ORCHESTRATOR_URL}/qa",
            json=data,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        result = response.json()
        logger.info(f"[API Gateway] Q&A response: success")
        return jsonify(result), 200

    except requests.exceptions.RequestException as e:
        logger.error(f"[API Gateway] Error calling Orchestrator: {str(e)}")
        return jsonify({'error': f'Service unavailable: {str(e)}'}), 503
    except Exception as e:
        logger.error(f"[API Gateway] Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/papers', methods=['GET'])
def list_papers():
    """
    List papers endpoint - routes to Orchestrator
    """
    try:
        logger.info("[API Gateway] List papers request")

        # Forward to Orchestrator
        response = requests.get(
            f"{ORCHESTRATOR_URL}/papers",
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        result = response.json()
        logger.info(f"[API Gateway] Papers response: {result.get('count', 0)} papers")
        return jsonify(result), 200

    except requests.exceptions.RequestException as e:
        logger.error(f"[API Gateway] Error calling Orchestrator: {str(e)}")
        return jsonify({'error': f'Service unavailable: {str(e)}'}), 503
    except Exception as e:
        logger.error(f"[API Gateway] Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/graph', methods=['GET'])
def graph():
    """
    Knowledge graph endpoint - routes to Graph Service
    """
    try:
        logger.info("[API Gateway] Graph request")

        # Forward to Graph Service
        response = requests.get(
            f"{GRAPH_SERVICE_URL}/graph",
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        result = response.json()
        logger.info(f"[API Gateway] Graph response: {len(result.get('nodes', []))} nodes")
        return jsonify(result), 200

    except requests.exceptions.RequestException as e:
        logger.error(f"[API Gateway] Error calling Graph Service: {str(e)}")
        return jsonify({'error': f'Service unavailable: {str(e)}'}), 503
    except Exception as e:
        logger.error(f"[API Gateway] Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/relationships', methods=['GET'])
def relationships():
    """
    Relationships endpoint - routes to Graph Service
    """
    try:
        logger.info("[API Gateway] Relationships request")

        # Forward to Graph Service
        response = requests.get(
            f"{GRAPH_SERVICE_URL}/relationships",
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        result = response.json()
        logger.info(f"[API Gateway] Relationships response: {result.get('count', 0)} relationships")
        return jsonify(result), 200

    except requests.exceptions.RequestException as e:
        logger.error(f"[API Gateway] Error calling Graph Service: {str(e)}")
        return jsonify({'error': f'Service unavailable: {str(e)}'}), 503
    except Exception as e:
        logger.error(f"[API Gateway] Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"[API Gateway] Starting on port {port}")
    logger.info(f"[API Gateway] Orchestrator URL: {ORCHESTRATOR_URL}")
    logger.info(f"[API Gateway] Graph Service URL: {GRAPH_SERVICE_URL}")
    app.run(host='0.0.0.0', port=port, debug=False)
