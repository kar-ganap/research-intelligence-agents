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

# Import service discovery
try:
    from service_discovery import get_orchestrator_url, get_graph_service_url, get_api_gateway_url
    SERVICE_DISCOVERY_ENABLED = True
except ImportError:
    SERVICE_DISCOVERY_ENABLED = False
    logger = logging.getLogger(__name__)
    logger.warning("Service discovery not available, using environment variables")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Service URLs - lazy loaded with service discovery fallback
_orchestrator_url = None
_graph_service_url = None

def get_orchestrator() -> str:
    """Get Orchestrator URL with caching and fallback."""
    global _orchestrator_url
    if _orchestrator_url:
        return _orchestrator_url

    # Try environment variable first
    env_url = os.environ.get('ORCHESTRATOR_URL')
    if env_url:
        _orchestrator_url = env_url
        return _orchestrator_url

    # Try service discovery
    if SERVICE_DISCOVERY_ENABLED:
        try:
            _orchestrator_url = get_orchestrator_url()
            return _orchestrator_url
        except Exception as e:
            logger.error(f"Service discovery failed: {e}")

    # Fallback to localhost
    _orchestrator_url = 'http://localhost:8081'
    return _orchestrator_url

def get_graph_service() -> str:
    """Get Graph Service URL with caching and fallback."""
    global _graph_service_url
    if _graph_service_url:
        return _graph_service_url

    # Try environment variable first
    env_url = os.environ.get('GRAPH_SERVICE_URL')
    if env_url:
        _graph_service_url = env_url
        return _graph_service_url

    # Try service discovery
    if SERVICE_DISCOVERY_ENABLED:
        try:
            _graph_service_url = get_graph_service_url()
            return _graph_service_url
        except Exception as e:
            logger.error(f"Service discovery failed: {e}")

    # Fallback to localhost
    _graph_service_url = 'http://localhost:8082'
    return _graph_service_url

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
            'watch_rules': 'GET /api/watch-rules, POST /api/watch-rules',
            'alerts': 'GET /api/alerts',
            'upload': 'POST /api/upload',
            'health': 'GET /health'
        },
        'services': {
            'orchestrator': get_orchestrator(),
            'graph_service': get_graph_service()
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
            f"{get_orchestrator()}/qa",
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
            f"{get_orchestrator()}/papers",
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
            f"{get_graph_service()}/graph",
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
            f"{get_graph_service()}/relationships",
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


@app.route('/api/watch-rules', methods=['GET', 'POST'])
def watch_rules():
    """
    Watch rules endpoint - direct Firestore access
    """
    try:
        from google.cloud import firestore

        db = firestore.Client()

        if request.method == 'GET':
            logger.info("[API Gateway] List watch rules request")

            # Get all watch rules
            rules_ref = db.collection('watch_rules')
            rules = []

            for doc in rules_ref.stream():
                rule_data = doc.to_dict()
                rule_data['id'] = doc.id
                rules.append(rule_data)

            logger.info(f"[API Gateway] Found {len(rules)} watch rules")
            return jsonify({'rules': rules, 'count': len(rules)}), 200

        elif request.method == 'POST':
            logger.info("[API Gateway] Create watch rule request")

            data = request.json
            if not data:
                return jsonify({'error': 'Missing request body'}), 400

            # Validate required fields
            if 'rule_type' not in data or 'user_email' not in data:
                return jsonify({'error': 'Missing required fields: rule_type, user_email'}), 400

            # Add created_at timestamp
            from datetime import datetime
            data['created_at'] = datetime.utcnow().isoformat() + 'Z'

            # Create the rule
            rule_ref = db.collection('watch_rules').document()
            rule_ref.set(data)

            logger.info(f"[API Gateway] Created watch rule: {rule_ref.id}")
            return jsonify({'rule_id': rule_ref.id, 'success': True}), 201

    except Exception as e:
        logger.error(f"[API Gateway] Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts', methods=['GET'])
def alerts():
    """
    Alerts endpoint - direct Firestore access
    """
    try:
        from google.cloud import firestore

        logger.info("[API Gateway] List alerts request")

        db = firestore.Client()
        alerts_ref = db.collection('alerts')
        alerts_list = []

        for doc in alerts_ref.stream():
            alert_data = doc.to_dict()
            alert_data['id'] = doc.id
            alerts_list.append(alert_data)

        logger.info(f"[API Gateway] Found {len(alerts_list)} alerts")
        return jsonify({'alerts': alerts_list, 'count': len(alerts_list)}), 200

    except Exception as e:
        logger.error(f"[API Gateway] Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/upload', methods=['POST'])
def upload():
    """
    Upload PDF endpoint - routes to Orchestrator
    """
    try:
        logger.info("[API Gateway] PDF upload request")

        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are supported'}), 400

        # Forward to Orchestrator
        files = {'file': (file.filename, file.stream, file.content_type)}
        response = requests.post(
            f"{get_orchestrator()}/upload",
            files=files,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        result = response.json()
        logger.info(f"[API Gateway] Upload response: success")
        return jsonify(result), 200

    except requests.exceptions.RequestException as e:
        logger.error(f"[API Gateway] Error calling Orchestrator: {str(e)}")
        return jsonify({'error': f'Service unavailable: {str(e)}'}), 503
    except Exception as e:
        logger.error(f"[API Gateway] Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"[API Gateway] Starting on port {port}")
    logger.info(f"[API Gateway] Orchestrator URL: {get_orchestrator()}")
    logger.info(f"[API Gateway] Graph Service URL: {get_graph_service()}")
    app.run(host='0.0.0.0', port=port, debug=False)
