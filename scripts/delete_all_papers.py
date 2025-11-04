"""
Delete all papers from Firestore to prepare for re-seeding with uniform model.

This script deletes all papers and relationships from Firestore.
"""

from src.storage.firestore_client import FirestoreClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Delete all papers from Firestore."""
    client = FirestoreClient()

    logger.info("=" * 70)
    logger.info("DELETING ALL PAPERS FROM FIRESTORE")
    logger.info("=" * 70)

    # Get all papers using stream to get all docs (list_papers has a limit)
    papers_stream = client.db.collection('papers').stream()
    papers = list(papers_stream)

    logger.info(f"\nFound {len(papers)} papers to delete")

    if len(papers) == 0:
        logger.info("No papers to delete. Exiting.")
        return

    # List papers before deleting
    logger.info("\nPapers to be deleted:")
    for i, doc in enumerate(papers, 1):
        data = doc.to_dict()
        title = data.get('title', 'Unknown')[:60]
        paper_id = doc.id
        logger.info(f"  {i}. {title}... (ID: {paper_id})")

    # Delete papers
    logger.info(f"\nDeleting {len(papers)} papers...")
    deleted_count = 0
    failed_count = 0

    for doc in papers:
        paper_id = doc.id
        try:
            doc.reference.delete()
            deleted_count += 1
            if deleted_count % 5 == 0:
                logger.info(f"  Deleted {deleted_count}/{len(papers)} papers...")
        except Exception as e:
            logger.error(f"  Failed to delete paper {paper_id}: {e}")
            failed_count += 1

    # Delete all relationships
    logger.info(f"\nDeleting relationships...")
    try:
        relationships = list(client.db.collection('relationships').stream())
        for rel in relationships:
            rel.reference.delete()
        logger.info(f"  Deleted {len(relationships)} relationships")
    except Exception as e:
        logger.error(f"  Failed to delete relationships: {e}")

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("DELETION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"✓ Successfully deleted: {deleted_count} papers")
    if failed_count > 0:
        logger.info(f"✗ Failed to delete: {failed_count} papers")
    logger.info(f"✓ Deleted relationships")
    logger.info("\nFirestore is now ready for fresh seeding with uniform model.")


if __name__ == "__main__":
    main()
