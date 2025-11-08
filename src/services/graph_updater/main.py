"""
Graph Updater Service

Cloud Run Service that receives Pub/Sub push messages and updates the knowledge graph.
Wraps the graph updater job logic in an HTTP endpoint.

Triggered by: Pub/Sub push subscription (docs-ready-sub) or Cloud Scheduler
"""

import os
import logging
import json
from typing import List, Dict, Tuple
from base64 import b64decode

from flask import Flask, request, jsonify
from flask_cors import CORS

from src.agents.ingestion.relationship_agent import RelationshipAgent
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

# Global instances (lazy-loaded)
_relationship_agent = None
_firestore_client = None

# Configuration
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT')


def get_relationship_agent() -> RelationshipAgent:
    """Lazy-load relationship agent"""
    global _relationship_agent
    if _relationship_agent is None:
        logger.info("[Graph Updater] Initializing RelationshipAgent...")
        _relationship_agent = RelationshipAgent()
        logger.info("[Graph Updater] RelationshipAgent initialized")
    return _relationship_agent


def get_firestore_client() -> FirestoreClient:
    """Lazy-load Firestore client"""
    global _firestore_client
    if _firestore_client is None:
        logger.info("[Graph Updater] Initializing Firestore client...")
        _firestore_client = FirestoreClient(project_id=PROJECT_ID)
        logger.info("[Graph Updater] Firestore client initialized")
    return _firestore_client


def detect_relationship(
    source_paper: Dict,
    target_paper: Dict,
    skip_existing: bool = True
) -> Dict:
    """
    Detect and store relationship between two papers.

    Args:
        source_paper: Source paper data
        target_paper: Target paper data
        skip_existing: Skip if relationship already exists

    Returns:
        Result dictionary
    """
    source_id = source_paper['paper_id']
    target_id = target_paper['paper_id']

    logger.info(f"Analyzing: {source_paper['title'][:40]}... → {target_paper['title'][:40]}...")

    try:
        firestore_client = get_firestore_client()
        relationship_agent = get_relationship_agent()

        # Check if relationship already exists
        if skip_existing:
            existing = firestore_client.get_relationship(source_id, target_id)
            if existing:
                logger.info(f"  ⏭️  Relationship already exists, skipping")
                return {
                    'status': 'skipped',
                    'reason': 'already_exists'
                }

        # Detect relationship using ADK agent
        result = relationship_agent.detect_relationship(
            source_paper=source_paper,
            target_paper=target_paper
        )

        if result.get('relationship_type'):
            # Store relationship
            relationship_data = {
                'source_id': source_id,
                'target_id': target_id,
                'relationship_type': result['relationship_type'],
                'confidence': result.get('confidence', 0.5),
                'evidence': result.get('evidence', ''),
                'created_at': firestore_client._get_timestamp()
            }

            firestore_client.store_relationship(relationship_data)

            logger.info(f"  ✅ Found: {result['relationship_type']} (confidence: {result.get('confidence', 0):.2f})")
            return {
                'status': 'success',
                'relationship_type': result['relationship_type'],
                'confidence': result.get('confidence', 0.5)
            }
        else:
            logger.info(f"  ⚪ No relationship detected")
            return {
                'status': 'no_relationship'
            }

    except Exception as e:
        logger.error(f"  ❌ Error: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


def update_graph_for_paper(paper_id: str) -> Dict:
    """
    Update graph relationships for a specific paper.

    Compares the paper against all other papers in the corpus.

    Args:
        paper_id: ID of the paper to process

    Returns:
        Summary dictionary
    """
    logger.info(f"[Graph Updater] Updating graph for paper: {paper_id}")

    try:
        firestore_client = get_firestore_client()

        # Get the target paper
        papers = firestore_client.get_all_papers()
        target_paper = next((p for p in papers if p['paper_id'] == paper_id), None)

        if not target_paper:
            return {
                'status': 'error',
                'error': f'Paper not found: {paper_id}'
            }

        # Compare against all other papers
        relationships_found = 0
        relationships_skipped = 0
        errors = 0

        for other_paper in papers:
            if other_paper['paper_id'] == paper_id:
                continue

            # Check both directions
            for source, target in [(target_paper, other_paper), (other_paper, target_paper)]:
                result = detect_relationship(source, target, skip_existing=True)

                if result['status'] == 'success':
                    relationships_found += 1
                elif result['status'] == 'skipped':
                    relationships_skipped += 1
                elif result['status'] == 'error':
                    errors += 1

        logger.info(f"[Graph Updater] Complete for {paper_id}")
        logger.info(f"  Relationships found: {relationships_found}")
        logger.info(f"  Skipped (existing): {relationships_skipped}")
        logger.info(f"  Errors: {errors}")

        return {
            'status': 'success',
            'paper_id': paper_id,
            'relationships_found': relationships_found,
            'relationships_skipped': relationships_skipped,
            'errors': errors
        }

    except Exception as e:
        logger.error(f"[Graph Updater] Error updating graph for {paper_id}: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


def update_full_graph() -> Dict:
    """
    Update graph for all papers (full recomputation).

    Used for scheduled full graph updates.

    Returns:
        Summary dictionary
    """
    logger.info("[Graph Updater] Running full graph update")

    try:
        firestore_client = get_firestore_client()

        # Fetch all papers
        papers = firestore_client.get_all_papers()
        logger.info(f"[Graph Updater] Found {len(papers)} papers")

        if len(papers) < 2:
            return {
                'status': 'success',
                'message': 'Not enough papers for relationships'
            }

        # Generate all unique pairs
        relationships_found = 0
        relationships_skipped = 0
        errors = 0
        pairs_processed = 0

        for i in range(len(papers)):
            for j in range(i + 1, len(papers)):
                source = papers[i]
                target = papers[j]

                result = detect_relationship(source, target, skip_existing=True)
                pairs_processed += 1

                if result['status'] == 'success':
                    relationships_found += 1
                elif result['status'] == 'skipped':
                    relationships_skipped += 1
                elif result['status'] == 'error':
                    errors += 1

        logger.info("[Graph Updater] Full graph update complete")
        logger.info(f"  Pairs processed: {pairs_processed}")
        logger.info(f"  Relationships found: {relationships_found}")
        logger.info(f"  Skipped (existing): {relationships_skipped}")
        logger.info(f"  Errors: {errors}")

        return {
            'status': 'success',
            'pairs_processed': pairs_processed,
            'relationships_found': relationships_found,
            'relationships_skipped': relationships_skipped,
            'errors': errors
        }

    except Exception as e:
        logger.error(f"[Graph Updater] Error in full graph update: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


@app.route('/health', methods=['GET'])
def health():
    """Health check for Cloud Run"""
    return jsonify({
        'status': 'healthy',
        'service': 'graph-updater',
        'version': '1.0.0'
    }), 200


@app.route('/', methods=['POST'])
def handle_pubsub_push():
    """
    Handle Pub/Sub push message from docs.ready topic.

    Message contains paper_id of newly ingested paper.

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
        data = json.loads(message_data)

        message_id = pubsub_message.get('messageId', 'unknown')
        paper_id = data.get('paper_id')

        logger.info(f"[Graph Updater] Received Pub/Sub message: {message_id}")
        logger.info(f"[Graph Updater] Paper ID: {paper_id}")

        if not paper_id:
            return jsonify({'error': 'No paper_id in message'}), 400

        # Update graph for this paper
        result = update_graph_for_paper(paper_id)

        # Return success (Pub/Sub requires 2xx response to acknowledge)
        return jsonify({
            'status': 'processed',
            'message_id': message_id,
            'result': result
        }), 200

    except Exception as e:
        logger.error(f"[Graph Updater] Error handling Pub/Sub message: {str(e)}", exc_info=True)
        # Return error (Pub/Sub will retry)
        return jsonify({'error': str(e)}), 500


@app.route('/update', methods=['POST'])
def update_graph():
    """
    Manual graph update endpoint.

    Request:
        {
            "paper_id": "..." (optional, if not provided updates full graph)
        }
    """
    try:
        data = request.get_json() or {}

        paper_id = data.get('paper_id')

        if paper_id:
            result = update_graph_for_paper(paper_id)
        else:
            result = update_full_graph()

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"[Graph Updater] Error in manual update: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/scheduled', methods=['POST', 'GET'])
def scheduled_update():
    """
    Scheduled update endpoint (triggered by Cloud Scheduler).

    Performs full graph update.
    """
    try:
        logger.info("[Graph Updater] Scheduled update triggered")

        result = update_full_graph()

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"[Graph Updater] Error in scheduled update: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8083))
    logger.info(f"[Graph Updater] Starting on port {port}")
    logger.info(f"[Graph Updater] Project ID: {PROJECT_ID}")
    app.run(host='0.0.0.0', port=port, debug=False)
