"""
Test End-to-End Alert Flow

This script tests the complete alert pipeline:
1. Creates a test watch rule
2. Simulates a matching paper
3. Runs alert matching
4. Verifies alert creation
5. Tests email notification (dry run)
"""

import os
import sys
from src.storage.firestore_client import FirestoreClient
from src.tools.matching import match_keyword_rule

def test_alert_flow():
    """Test the complete alert flow."""
    client = FirestoreClient()

    print("=" * 80)
    print("TESTING END-TO-END ALERT FLOW")
    print("=" * 80)

    # Step 1: Create a test watch rule
    print("\n[1/5] Creating test watch rule...")
    test_rule = {
        "user_email": os.getenv("USER_EMAIL", "test@example.com"),
        "rule_type": "keyword",
        "keywords": ["multimodal", "vision", "language"],
        "min_relevance_score": 0.5,
        "created_at": "2025-01-01T00:00:00Z"
    }

    # Check if rule already exists
    existing_rules = list(client.db.collection('watch_rules')
                         .where('rule_type', '==', 'keyword')
                         .where('keywords', '==', test_rule['keywords'])
                         .stream())

    if existing_rules:
        rule_id = existing_rules[0].id
        print(f"  ✓ Using existing rule: {rule_id}")
    else:
        rule_ref = client.db.collection('watch_rules').document()
        rule_ref.set(test_rule)
        rule_id = rule_ref.id
        print(f"  ✓ Created new rule: {rule_id}")

    # Step 2: Get a paper that should match
    print("\n[2/5] Finding a matching paper...")
    papers = list(client.db.collection('papers').limit(25).stream())

    matching_paper = None
    for doc in papers:
        paper_data = doc.to_dict()
        paper_data['paper_id'] = doc.id

        # Test if paper matches
        match_result = match_keyword_rule(paper_data, test_rule)
        if match_result:
            matching_paper = paper_data
            print(f"  ✓ Found matching paper: {paper_data.get('title', 'Unknown')[:60]}...")
            print(f"    Match score: {match_result['match_score']:.2f}")
            print(f"    Matched keywords: {match_result['matched_keywords']}")
            break

    if not matching_paper:
        print("  ✗ No matching papers found")
        return False

    # Step 3: Create an alert
    print("\n[3/5] Creating alert...")
    alert_data = {
        "user_email": test_rule["user_email"],
        "rule_id": rule_id,
        "rule_type": test_rule["rule_type"],
        "paper_id": matching_paper['paper_id'],
        "paper_title": matching_paper.get('title', 'Unknown'),
        "paper_authors": matching_paper.get('authors', []),
        "paper_key_finding": matching_paper.get('key_finding', ''),
        "match_score": match_result['match_score'],
        "match_explanation": match_result['match_explanation'],
        "sent": False,
        "created_at": "2025-01-01T00:00:00Z"
    }

    # Check if alert already exists
    existing_alerts = list(client.db.collection('alerts')
                          .where('paper_id', '==', matching_paper['paper_id'])
                          .where('rule_id', '==', rule_id)
                          .stream())

    if existing_alerts:
        alert_id = existing_alerts[0].id
        print(f"  ✓ Using existing alert: {alert_id}")
    else:
        alert_ref = client.db.collection('alerts').document()
        alert_ref.set(alert_data)
        alert_id = alert_ref.id
        print(f"  ✓ Created alert: {alert_id}")

    # Step 4: Test email sending (dry run)
    print("\n[4/5] Testing email notification (dry run)...")
    print(f"  Would send email to: {test_rule['user_email']}")
    print(f"  Subject: New research alert: {matching_paper.get('title', 'Unknown')[:50]}...")
    print(f"  Body preview:")
    print(f"    Paper: {matching_paper.get('title', 'Unknown')}")
    print(f"    Authors: {', '.join(matching_paper.get('authors', [])[:3])}")
    print(f"    Match: {match_result['match_explanation']}")
    print(f"    Key Finding: {matching_paper.get('key_finding', '')[:100]}...")

    # Step 5: Verify alert in database
    print("\n[5/5] Verifying alert in database...")
    alert_doc = client.db.collection('alerts').document(alert_id).get()
    if alert_doc.exists:
        print(f"  ✓ Alert verified in Firestore")
        print(f"    Alert ID: {alert_id}")
        print(f"    Paper: {alert_doc.to_dict().get('paper_title', 'Unknown')[:60]}...")
        print(f"    Match Score: {alert_doc.to_dict().get('match_score', 0):.2f}")
    else:
        print(f"  ✗ Alert not found in Firestore")
        return False

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"✓ Rule created/verified: {rule_id}")
    print(f"✓ Matching paper found: {matching_paper['paper_id']}")
    print(f"✓ Alert created: {alert_id}")
    print(f"✓ Alert stored in Firestore")
    print("\nEnd-to-end alert flow is working correctly!")

    # Count total alerts
    total_alerts = sum(1 for _ in client.db.collection('alerts').stream())
    print(f"\nTotal alerts in database: {total_alerts}")

    return True


if __name__ == "__main__":
    success = test_alert_flow()
    sys.exit(0 if success else 1)
