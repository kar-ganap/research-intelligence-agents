# Future Work & Deferred Improvements

This document tracks features and improvements that have been identified but deferred to future phases.

## Phase 3+ Improvements

### 1. Semantic Search & RAG Enhancement
**Priority:** High
**Effort:** Medium (2-3 days)
**Blocked by:** Growing corpus (>50 papers)

**Context:**
- Current keyword search works well for small corpus (<50 papers)
- Semantic search becomes valuable when:
  - Corpus grows beyond 50-100 papers
  - Users ask conceptual questions ("papers about attention mechanisms")
  - Questions use paraphrased terminology

**Implementation Plan:**
- Use embedding models (e.g., `text-embedding-004`)
- Implement vector storage (Firestore doesn't support vector search natively)
- Options: Vertex AI Vector Search, Pinecone, or PostgreSQL with pgvector
- Hybrid search: Combine keyword + semantic for best results

**Related:**
- See conversation: "Wonder at what point in time would we need semantic search"
- Decision: Defer until corpus size justifies complexity

---

### 2. Store Full Paper Text in Firestore
**Priority:** Medium
**Effort:** Medium (1-2 days)
**Blocked by:** Semantic search implementation (makes sense to do together)

**Current State:**
- Only storing extracted metadata: `title`, `authors`, `key_finding`, `pdf_path`
- Full PDF text is extracted but then discarded
- PDFs remain on local disk

**Pros of storing full text:**
- Complete information availability for answering detailed questions
- Better answer quality (can reference any part of paper)
- Future-proofing for semantic search/RAG
- Can re-extract different summaries without re-ingesting PDFs
- Better relationship detection with full context

**Cons:**
- 100-200x storage increase (~50-100KB per paper vs 500 bytes)
- 10x API costs for Q&A (more tokens to process)
- Requires chunking strategy to avoid overwhelming AnswerAgent
- Need to re-ingest existing papers

**Implementation Plan:**
1. Add `full_text` field to papers collection schema
2. Update `FirestoreClient.store_paper()` to accept full text
3. Update `IngestionPipeline` to preserve and store full text
4. Implement chunking strategy for AnswerAgent
5. Re-ingest existing papers to backfill full text
6. Consider hybrid approach: use `key_finding` for overview, `full_text` for details

**Related:**
- See conversation: "help me understand how we've structured it"
- Decision: Quick win now (better key_finding), full text storage later with semantic search

---

### 3. Advanced Watch Rule Templates
**Priority:** Low
**Effort:** Small (ongoing)

**Currently Implemented (Phase 2.2):**
- 5 basic templates: breakthrough_claim, sota_beat, contradicting_claim, author_watch, keyword_combo

**Future Templates to Add:**
- `dataset_benchmark`: Alert when new benchmark results on specific datasets
- `methodology_adoption`: Papers using specific techniques (e.g., "uses LoRA fine-tuning")
- `reproducibility_check`: Papers that reproduce or challenge existing results
- `cross_domain_application`: Technique from domain A applied to domain B
- `trend_detection`: Multiple papers on emerging topics

**Implementation:**
- Add templates to `src/agents/alerting/alert_templates.py`
- Each template is just a function that returns rule configuration
- Low effort, high user value

---

### 4. Improve Key Finding Extraction Quality
**Priority:** High
**Effort:** Small (30 min)
**Status:** IN PROGRESS (Part of Phase 2.3 Option A)

**Current Issue:**
- EntityAgent extracts "ONE sentence" key findings
- Missing specific metrics (BLEU scores, accuracy numbers, benchmark results)
- Example: Transformer paper key_finding doesn't mention "BLEU 28.4" or "WMT 2014"

**Solution:**
- Update EntityAgent prompt to request 2-4 sentences
- Explicitly ask for: metrics, performance numbers, comparisons to baselines
- Provide examples of good key findings in prompt

**Next Step:**
- Update `src/agents/ingestion/entity_agent.py` instruction
- Re-ingest existing 3 papers to verify improvement
- Continue with Phase 2.3 testing

---

### 5. Relationship Detection Improvements
**Priority:** Medium
**Effort:** Small-Medium (ongoing)

**Current State (Phase 2.1):**
- Detects: supports, contradicts, extends
- Works with key findings only (limited context)

**Future Improvements:**
- Use full text for deeper relationship analysis
- Detect implicit relationships (e.g., uses same dataset, cites common baseline)
- Confidence calibration based on manual review
- Relationship visualization UI

**Related:**
- Depends on #2 (store full text) for better detection

---

### 6. ConfidenceAgent Calibration
**Priority:** Medium
**Effort:** Medium (ongoing)
**Status:** Needs evaluation after more data

**Current State (Phase 2.3):**
- LLM-based confidence scoring
- Weights: evidence_strength (40%), consistency (30%), coverage (20%), source_quality (10%)
- Working correctly on initial tests

**Future Work:**
- Collect ground truth labels for confidence scores
- Calibrate thresholds based on user feedback
- A/B test different weighting schemes
- Add confidence score to UI to guide user trust

**Why deferred:**
- Need more papers and real usage to calibrate properly
- Current implementation is good enough for Phase 2.3 go/no-go

---

### 7. Batch Ingestion & ArXiv Integration
**Priority:** Medium
**Effort:** Small (1 day)

**Current State:**
- Manual PDF ingestion only
- Small corpus (3 papers)

**Future Work:**
- Bulk ArXiv ingestion by category or search query
- Scheduled daily ingestion of new papers
- Integration with other sources (OpenReview, ACL Anthology)
- Deduplication logic

**Related:**
- Will enable testing semantic search at scale
- Currently blocked by: want to validate Phase 2.3 first

---

### 8. Production Deployment & Monitoring
**Priority:** High (before public launch)
**Effort:** Medium (2-3 days)

**Current State:**
- Local development only
- No monitoring, logging, or error tracking

**Future Work:**
- Deploy to Cloud Run or GKE
- Add structured logging (Cloud Logging)
- Error tracking (Cloud Error Reporting)
- Performance monitoring (Cloud Trace)
- Cost monitoring and alerts
- Rate limiting for API calls
- User authentication and multi-tenancy

---

## Decision Log

### Decisions Made During Phase 2.3
1. **Semantic search deferred** - Current keyword search sufficient for small corpus
2. **Full text storage deferred** - Improve key_finding extraction first (quick win)
3. **Option A chosen** - Improve extraction + add papers, rather than architectural changes

---

## How to Use This Document

1. **Review quarterly** - Revisit deferred items and re-prioritize
2. **Update after each phase** - Add new deferred items as they're identified
3. **Link from README** - Ensure visibility for future contributors
4. **Cross-reference** - Link related items together

---

*Last updated: Phase 2.3 implementation*
