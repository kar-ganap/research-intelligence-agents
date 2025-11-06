#!/usr/bin/env python3
"""
Script to clean up duplicate watch rules in Firestore.
Keeps the oldest rule and deletes newer duplicates.
"""

import sys
import os
from google.cloud import firestore
from collections import defaultdict

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def main():
    db = firestore.Client()
    rules_ref = db.collection('watch_rules')

    print("Fetching all watch rules...")
    all_rules = []
    for doc in rules_ref.stream():
        rule_data = doc.to_dict()
        rule_data['doc_id'] = doc.id
        all_rules.append(rule_data)

    print(f"Found {len(all_rules)} total rules")

    # Group rules by user_email and rule_type, then by content
    duplicates_found = 0
    rules_to_delete = []

    # Group by user and type first
    grouped = defaultdict(list)
    for rule in all_rules:
        key = (rule.get('user_email'), rule.get('rule_type'))
        grouped[key].append(rule)

    # Within each group, find duplicates based on content
    for (user_email, rule_type), rules_group in grouped.items():
        if rule_type == 'keyword':
            # Group by sorted keywords
            keyword_groups = defaultdict(list)
            for rule in rules_group:
                if 'keywords' in rule:
                    keywords_key = tuple(sorted(rule['keywords']))
                    keyword_groups[keywords_key].append(rule)

            # Find duplicates
            for keywords_key, duplicates in keyword_groups.items():
                if len(duplicates) > 1:
                    # Sort by created_at to keep the oldest
                    duplicates.sort(key=lambda x: x.get('created_at', ''))
                    print(f"\nFound {len(duplicates)} duplicate keyword rules for {user_email}")
                    print(f"  Keywords: {list(keywords_key)}")
                    print(f"  Keeping: {duplicates[0]['doc_id']} (created: {duplicates[0].get('created_at', 'unknown')})")
                    for dup in duplicates[1:]:
                        print(f"  Deleting: {dup['doc_id']} (created: {dup.get('created_at', 'unknown')})")
                        rules_to_delete.append(dup['doc_id'])
                        duplicates_found += 1

        elif rule_type == 'author':
            # Group by sorted authors
            author_groups = defaultdict(list)
            for rule in rules_group:
                if 'authors' in rule:
                    authors_key = tuple(sorted(rule['authors']))
                    author_groups[authors_key].append(rule)

            # Find duplicates
            for authors_key, duplicates in author_groups.items():
                if len(duplicates) > 1:
                    duplicates.sort(key=lambda x: x.get('created_at', ''))
                    print(f"\nFound {len(duplicates)} duplicate author rules for {user_email}")
                    print(f"  Authors: {list(authors_key)}")
                    print(f"  Keeping: {duplicates[0]['doc_id']} (created: {duplicates[0].get('created_at', 'unknown')})")
                    for dup in duplicates[1:]:
                        print(f"  Deleting: {dup['doc_id']} (created: {dup.get('created_at', 'unknown')})")
                        rules_to_delete.append(dup['doc_id'])
                        duplicates_found += 1

        elif rule_type == 'claim':
            # Group by claim_description
            claim_groups = defaultdict(list)
            for rule in rules_group:
                if 'claim_description' in rule:
                    claim_groups[rule['claim_description']].append(rule)

            # Find duplicates
            for claim_desc, duplicates in claim_groups.items():
                if len(duplicates) > 1:
                    duplicates.sort(key=lambda x: x.get('created_at', ''))
                    print(f"\nFound {len(duplicates)} duplicate claim rules for {user_email}")
                    print(f"  Claim: {claim_desc[:50]}...")
                    print(f"  Keeping: {duplicates[0]['doc_id']} (created: {duplicates[0].get('created_at', 'unknown')})")
                    for dup in duplicates[1:]:
                        print(f"  Deleting: {dup['doc_id']} (created: {dup.get('created_at', 'unknown')})")
                        rules_to_delete.append(dup['doc_id'])
                        duplicates_found += 1

        elif rule_type == 'relationship':
            # Group by relationship_type and target_paper_id
            relationship_groups = defaultdict(list)
            for rule in rules_group:
                if 'relationship_type' in rule and 'target_paper_id' in rule:
                    rel_key = (rule['relationship_type'], rule['target_paper_id'])
                    relationship_groups[rel_key].append(rule)

            # Find duplicates
            for (rel_type, target_id), duplicates in relationship_groups.items():
                if len(duplicates) > 1:
                    duplicates.sort(key=lambda x: x.get('created_at', ''))
                    print(f"\nFound {len(duplicates)} duplicate relationship rules for {user_email}")
                    print(f"  Relationship: {rel_type}, Target: {target_id}")
                    print(f"  Keeping: {duplicates[0]['doc_id']} (created: {duplicates[0].get('created_at', 'unknown')})")
                    for dup in duplicates[1:]:
                        print(f"  Deleting: {dup['doc_id']} (created: {dup.get('created_at', 'unknown')})")
                        rules_to_delete.append(dup['doc_id'])
                        duplicates_found += 1

        elif rule_type == 'template':
            # Group by template_name and template_params
            template_groups = defaultdict(list)
            for rule in rules_group:
                if 'template_name' in rule and 'template_params' in rule:
                    # Convert template_params dict to sorted tuple for grouping
                    params_key = tuple(sorted(rule['template_params'].items()))
                    template_key = (rule['template_name'], params_key)
                    template_groups[template_key].append(rule)

            # Find duplicates
            for (template_name, params_key), duplicates in template_groups.items():
                if len(duplicates) > 1:
                    duplicates.sort(key=lambda x: x.get('created_at', ''))
                    params_dict = dict(params_key)
                    print(f"\nFound {len(duplicates)} duplicate template rules for {user_email}")
                    print(f"  Template: {template_name}, Params: {params_dict}")
                    print(f"  Keeping: {duplicates[0]['doc_id']} (created: {duplicates[0].get('created_at', 'unknown')})")
                    for dup in duplicates[1:]:
                        print(f"  Deleting: {dup['doc_id']} (created: {dup.get('created_at', 'unknown')})")
                        rules_to_delete.append(dup['doc_id'])
                        duplicates_found += 1

    if duplicates_found == 0:
        print("\nNo duplicates found!")
        return

    print(f"\n{'='*60}")
    print(f"Summary: Found {duplicates_found} duplicate rules to delete")
    print(f"{'='*60}")

    # Ask for confirmation (or auto-confirm with --yes flag)
    import sys
    if '--yes' in sys.argv or '-y' in sys.argv:
        print("\nAuto-confirming deletion (--yes flag)")
    else:
        response = input("\nDo you want to delete these duplicates? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted. No rules were deleted.")
            return

    # Delete duplicates
    print("\nDeleting duplicates...")
    batch = db.batch()
    for doc_id in rules_to_delete:
        doc_ref = rules_ref.document(doc_id)
        batch.delete(doc_ref)

    batch.commit()
    print(f"✓ Successfully deleted {len(rules_to_delete)} duplicate rules")
    print(f"Remaining rules: {len(all_rules) - len(rules_to_delete)}")

if __name__ == '__main__':
    main()
