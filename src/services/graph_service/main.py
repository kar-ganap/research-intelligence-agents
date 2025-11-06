"""
Graph Service

Specialized service for knowledge graph queries. Handles:
- Graph data retrieval (nodes + edges)
- Relationship queries
- Graph analytics (future: centrality, clustering)

Cloud Run Service: Always running, handles HTTP requests
"""

import os
import logging
from typing import Dict, List, Any

from flask import Flask, request, jsonify
from flask_cors import CORS

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

# Global client (lazy-loaded)
_firestore_client = None


def get_firestore_client() -> FirestoreClient:
    """Lazy-load Firestore client"""
    global _firestore_client
    if _firestore_client is None:
        logger.info("[Graph Service] Initializing Firestore client...")
        _firestore_client = FirestoreClient()
        logger.info("[Graph Service] Firestore client initialized")
    return _firestore_client


@app.route('/health', methods=['GET'])
def health():
    """Health check for Cloud Run"""
    return jsonify({
        'status': 'healthy',
        'service': 'graph-service',
        'version': '1.0.0'
    }), 200


@app.route('/', methods=['GET'])
def index():
    """Service documentation"""
    return jsonify({
        'name': 'Research Intelligence Platform - Graph Service',
        'version': '1.0.0',
        'description': 'Knowledge graph queries and analytics',
        'endpoints': {
            'graph': 'GET /graph',
            'relationships': 'GET /relationships',
            'paper_neighbors': 'GET /paper/<paper_id>/neighbors',
            'health': 'GET /health'
        }
    }), 200


@app.route('/graph', methods=['GET'])
def graph():
    """
    Get complete knowledge graph in vis.js format

    Response:
        {
            "nodes": [
                {
                    "id": "paper_123",
                    "label": "Attention Is All You Need",
                    "title": "Full title for hover",
                    "authors": "Vaswani et al."
                },
                ...
            ],
            "edges": [
                {
                    "from": "paper_123",
                    "to": "paper_456",
                    "label": "extends",
                    "title": "extends (confidence: 0.85)",
                    "arrows": "to"
                },
                ...
            ]
        }
    """
    try:
        logger.info("[Graph Service] Graph request")

        firestore_client = get_firestore_client()
        papers = firestore_client.get_all_papers()
        relationships = firestore_client.get_all_relationships()

        # Transform to vis.js format
        nodes = []
        for paper in papers:
            title = paper.get('title', 'Unknown')
            label = title[:50] + '...' if len(title) > 50 else title

            node = {
                'id': paper['paper_id'],
                'label': label,
                'title': title,  # Full title on hover
                'authors': ', '.join(paper.get('authors', [])[:3])
            }

            # Add category fields if available
            if paper.get('primary_category'):
                node['primary_category'] = paper['primary_category']
            if paper.get('categories'):
                node['categories'] = paper['categories']

            nodes.append(node)

        edges = []
        for rel in relationships:
            edges.append({
                'from': rel['source_paper_id'],
                'to': rel['target_paper_id'],
                'label': rel['relationship_type'],
                'title': f"{rel['relationship_type']} (confidence: {rel.get('confidence', 0):.2f})",
                'arrows': 'to',
                'confidence': rel.get('confidence', 0)
            })

        logger.info(f"[Graph Service] Graph: {len(nodes)} nodes, {len(edges)} edges")
        return jsonify({
            'nodes': nodes,
            'edges': edges,
            'stats': {
                'node_count': len(nodes),
                'edge_count': len(edges)
            }
        }), 200

    except Exception as e:
        logger.error(f"[Graph Service] Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/relationships', methods=['GET'])
def relationships():
    """
    List all relationships with details

    Response:
        {
            "relationships": [
                {
                    "source_id": "...",
                    "target_id": "...",
                    "relationship_type": "extends",
                    "confidence": 0.85,
                    "evidence": "...",
                    "created_at": "..."
                },
                ...
            ],
            "count": 5
        }
    """
    try:
        logger.info("[Graph Service] Relationships request")

        firestore_client = get_firestore_client()
        rels = firestore_client.get_all_relationships()

        logger.info(f"[Graph Service] Found {len(rels)} relationships")
        return jsonify({
            'relationships': rels,
            'count': len(rels)
        }), 200

    except Exception as e:
        logger.error(f"[Graph Service] Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/paper/<paper_id>/neighbors', methods=['GET'])
def paper_neighbors(paper_id: str):
    """
    Get all papers related to a specific paper

    Response:
        {
            "paper_id": "...",
            "neighbors": [
                {
                    "paper_id": "...",
                    "title": "...",
                    "relationship_type": "extends",
                    "confidence": 0.85,
                    "direction": "outgoing"  # or "incoming"
                },
                ...
            ],
            "count": 3
        }
    """
    try:
        logger.info(f"[Graph Service] Neighbors request for paper: {paper_id}")

        firestore_client = get_firestore_client()
        relationships = firestore_client.get_all_relationships()
        papers = firestore_client.get_all_papers()

        # Build paper lookup
        paper_lookup = {p['paper_id']: p for p in papers}

        # Find neighbors
        neighbors = []

        for rel in relationships:
            if rel['source_paper_id'] == paper_id:
                # Outgoing relationship
                target_paper = paper_lookup.get(rel['target_paper_id'])
                if target_paper:
                    neighbors.append({
                        'paper_id': rel['target_paper_id'],
                        'title': target_paper['title'],
                        'relationship_type': rel['relationship_type'],
                        'confidence': rel.get('confidence', 0),
                        'direction': 'outgoing'
                    })

            elif rel['target_paper_id'] == paper_id:
                # Incoming relationship
                source_paper = paper_lookup.get(rel['source_paper_id'])
                if source_paper:
                    neighbors.append({
                        'paper_id': rel['source_paper_id'],
                        'title': source_paper['title'],
                        'relationship_type': rel['relationship_type'],
                        'confidence': rel.get('confidence', 0),
                        'direction': 'incoming'
                    })

        logger.info(f"[Graph Service] Found {len(neighbors)} neighbors for {paper_id}")
        return jsonify({
            'paper_id': paper_id,
            'neighbors': neighbors,
            'count': len(neighbors)
        }), 200

    except Exception as e:
        logger.error(f"[Graph Service] Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8082))
    logger.info(f"[Graph Service] Starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
