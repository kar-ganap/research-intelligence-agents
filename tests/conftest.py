"""
Pytest configuration and fixtures
"""

import pytest
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))


@pytest.fixture
def sample_paper():
    """Sample paper data for testing"""
    return {
        'paper_id': 'test:001',
        'title': 'Test Paper on Machine Learning',
        'authors': ['Smith, J.', 'Doe, A.'],
        'year': 2023,
        'abstract': 'This is a test paper about machine learning.',
        'entities': {
            'methods': ['neural_networks', 'deep_learning'],
            'findings': ['improved_accuracy', 'faster_training'],
            'datasets': ['imagenet', 'cifar10']
        }
    }


@pytest.fixture
def sample_question():
    """Sample question for testing"""
    return "What methods were used in the paper?"


@pytest.fixture
def mock_firestore(monkeypatch):
    """Mock Firestore client for testing"""
    class MockFirestore:
        def collection(self, name):
            return self

        def document(self, id):
            return self

        def get(self):
            return self

        def exists(self):
            return True

        def to_dict(self):
            return {'test': 'data'}

    monkeypatch.setattr('google.cloud.firestore.Client', MockFirestore)
    return MockFirestore()
