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

### 3. Trust Verification (Phase 2.4)
**Priority:** Medium
**Effort:** Medium (1-2 days)
**Blocked by:** Full paper text storage (#2)
**Status:** Deferred from Phase 2

**Context:**
- Phase 2.4 was planned but skipped in favor of moving to Phase 3
- ConfidenceAgent (Phase 2.3) provides overall answer quality assessment
- Trust Verification would add claim-level verification against source papers

**What Trust Verification Does:**
Verify that cited claims are actually supported by the cited papers.

**Example:**
- Answer says: "Transformer achieves 28.4 BLEU on WMT 2014 [Attention Is All You Need]"
- VerifierAgent would:
  1. Extract claim: "28.4 BLEU on WMT 2014"
  2. Read cited paper: "Attention Is All You Need"
  3. Search for this specific claim in the paper
  4. Return verification status:
     - ✅ VERIFIED: Found exact match with page number and quote
     - ⚠️ PARTIAL: Found similar but not exact claim
     - ❌ UNVERIFIED: Could not find this claim
     - 🚫 CONTRADICTS: Paper says something different

**Value Proposition:**
- **Hallucination detection**: Catch when AI makes up claims
- **Citation accuracy**: Ensure citations are correctly attributed
- **Academic rigor**: Provide audit trail with exact quotes and page numbers
- **Trust building**: Show users proof of claims, not just confidence scores

**Difference from ConfidenceAgent:**
| Feature | ConfidenceAgent (Built) | VerifierAgent (Future) |
|---------|----------------------|----------------------|
| What it checks | "Do we have good evidence?" | "Is the citation accurate?" |
| Evaluates | Overall answer quality | Individual claim verification |
| Can detect | Weak evidence, contradictions | Misattributed claims, hallucinations |
| Granularity | Answer-level | Claim-level |

**Implementation Plan:**
1. **VerifierAgent** (`src/agents/qa/verifier_agent.py`):
   ```python
   class VerifierAgent(BaseResearchAgent):
       def verify_claim(self, claim: str, citation: str, paper_text: str) -> Dict:
           """
           Verify claim against cited paper.

           Returns:
               {
                   'status': 'VERIFIED' | 'PARTIAL' | 'UNVERIFIED' | 'CONTRADICTS',
                   'evidence': str,  # Exact quote if found
                   'page_number': int,
                   'confidence': float
               }
           """
   ```

2. **Claim Extraction**: Parse answer to extract individual claims with citations
3. **Evidence Tracing**: For each claim, read full paper and search for supporting text
4. **Output Enhancement**: Add verification data to Q&A pipeline results
5. **UI Display**: Show verification status alongside answers

**Prerequisites:**
- Full paper text storage (#2) - needed to search papers for claims
- Chunking strategy for efficient claim search
- May need OCR or better PDF parsing for tables/figures

**Why Deferred:**
1. ConfidenceAgent already provides strong trust signals
2. Requires full text storage (not yet implemented)
3. Computationally expensive (read full papers for every claim)
4. Better ROI to focus on Phase 3 (UI, deployment) first
5. Can add later when implementing semantic search + full text storage

**Related:**
- See conversation: "tell me more about trust verification?"
- Decision: Skip 2.4, move to Phase 3, add verification later with full text storage

---

### 4. Advanced Watch Rule Templates
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

## Phase 4+ Evidence-First Enhancements

*Inspired by "Reimagining Knowledge Systems in Equity Research — Evidence-First AI" white paper*

### 9. Table & Chart Extraction (Multi-Modal Understanding)
**Priority:** High
**Effort:** Medium (2-3 days)
**Inspiration:** White paper Section II: "Tables, charts, and text are interdependent signals"
**Previous Work:** See `docs/planning/MULTIMODAL_CONTENT_STRATEGY.md` - deferred from Phase 2

**Current Gap:**
- Paper ingestion only extracts text from PDFs
- Critical evidence in tables (experimental results, benchmarks, performance metrics) is ignored
- Academic papers encode key findings in figures/tables
- **Note**: We attempted table extraction earlier with `pdfplumber` but deferred to revisit later

**Example of Missing Data:**
- "GPT-3 achieves 71.8% accuracy on LAMBADA" → Table in paper
- Transformer benchmarks (WMT 2014 BLEU scores) → Table 2
- Ablation study results → Often in tables

**Implementation:**
1. Add table extraction libraries: `camelot-py` (for tables) or `table-transformer`
2. Store extracted tables in Firestore as structured JSON
3. Link table cells to paper claims in relationship graph
4. Enhance AnswerAgent to reason over tabular data
5. Visual extraction with multimodal models (Gemini vision API for charts)

**Files to Modify:**
- `src/agents/ingestion/paper_parser.py` - Add table extraction
- `src/storage/firestore_client.py` - Add `tables` field to schema
- `src/agents/qa/answer_agent.py` - Reason over structured data

**Value:**
- Complete knowledge graph with quantitative evidence
- Answer questions like "Which model performs best on X benchmark?"
- More accurate relationship detection

---

### 10. Enhanced Citations with Exact Quotes & Page Numbers
**Priority:** Medium
**Effort:** Small (1 day)
**Inspiration:** White paper Section II: "Every assertion must trace to a primary source, preserving quote, context, and location"

**Current State:**
- AnswerAgent returns citations as `[Paper Title]`
- No preservation of exact quotes or page numbers
- Cannot verify claim-to-source mapping

**Enhancement:**
```python
# Current citation format
"Transformers use self-attention [Attention Is All You Need]"

# Enhanced citation format
{
    "claim": "Transformers use self-attention",
    "evidence": {
        "paper_id": "1706.03762",
        "title": "Attention Is All You Need",
        "quote": "The Transformer architecture uses multi-head self-attention...",
        "page": 3,
        "section": "3.2 Attention",
        "context": "Preceding/following sentences for verification"
    },
    "confidence": 0.95
}
```

**Implementation:**
1. Update `AnswerAgent` to preserve exact quotes from source papers
2. Add page number tracking during PDF ingestion
3. Structure answers as claim-evidence pairs (not free-form text)
4. Store citation provenance in answers collection

**Value:**
- Audit trail for every claim
- Enables future Trust Verification (Phase 2.4)
- Addresses white paper's "accountability friction"

---

### 11. Claim-Level Confidence Scoring
**Priority:** Medium
**Effort:** Medium (2 days)
**Inspiration:** White paper concept: "Unit of meaning is the sourced fact" (not the sentence)

**Current State:**
- ConfidenceAgent scores entire answer (answer-level)
- Cannot identify which specific claims are weak vs strong

**Enhancement:**
Score confidence per claim, not per answer.

**Example:**
```python
{
    "answer": {
        "claims": [
            {
                "claim": "Transformers outperform RNNs on WMT",
                "confidence": 0.95,  # High - directly from paper table
                "evidence_strength": "strong",
                "citations": ["Attention Is All You Need p.8 Table 2"]
            },
            {
                "claim": "Transformers are more efficient to train",
                "confidence": 0.70,  # Medium - inferred from multiple sources
                "evidence_strength": "moderate",
                "citations": ["Paper A", "Paper B"]
            }
        ],
        "overall_confidence": 0.82  # Weighted average
    }
}
```

**Implementation:**
1. Parse AnswerAgent output into discrete claims
2. For each claim, run confidence scoring independently
3. Aggregate claim-level scores for overall answer confidence
4. Display confidence badges per claim in UI

**Value:**
- Users know which parts of answer to trust
- Aligns with white paper's "provenance reasoning" philosophy
- Enables granular verification

---

### 12. Authority-Weighted Reasoning (Source Quality Scoring)
**Priority:** Medium
**Effort:** Medium (1-2 days)
**Inspiration:** White paper Section III.4: "10-K filings → Transcripts → Analyst reports → News"

**Current State:**
- All papers treated with equal authority
- arXiv preprint has same weight as peer-reviewed JMLR paper

**Enhancement:**
Implement source authority hierarchy for academic research:

```python
def calculate_source_authority(paper: Dict) -> float:
    """Calculate authority weight (0.0-1.0) for a paper."""
    score = 0.5  # Base score

    # Venue tier (top conferences/journals boost authority)
    if paper.get('venue') in ['NeurIPS', 'ICML', 'ICLR', 'Nature', 'Science']:
        score += 0.3
    elif paper.get('is_peer_reviewed'):
        score += 0.2

    # Citation count (diminishing returns)
    citation_count = paper.get('citation_count', 0)
    score += min(0.2, citation_count / 100)

    # Recency penalty (papers >5 years old may be outdated)
    age_years = (datetime.now() - paper['published_date']).days / 365
    if age_years > 5:
        score -= 0.1

    return max(0.1, min(1.0, score))  # Clamp to [0.1, 1.0]
```

**Use Cases:**
1. **ConfidenceAgent**: Weight `source_quality` by authority scores
2. **Relationship Detection**: Higher-authority papers win contradictions
3. **Answer Ranking**: Prioritize citations from top-tier venues

**Implementation:**
1. Add `authority_score` field to papers collection
2. Calculate during ingestion (EntityAgent extracts venue info)
3. Use in ConfidenceAgent's `source_quality` calculation
4. Display authority indicators in UI (e.g., "peer-reviewed", "highly cited")

**Value:**
- Aligns with white paper's authority hierarchy principle
- Improves answer quality by trusting better sources
- Helps users assess credibility

---

### 13. Temporal Intelligence: Tracking Supersession
**Priority:** Low
**Effort:** Small-Medium (1-2 days)
**Inspiration:** White paper Section III.3: "What is current, historical, or superseded"

**Current State:**
- Papers have `published_date` but no version tracking
- No mechanism to mark claims as "updated" or "superseded"
- Cannot answer "What's the latest benchmark on X?"

**Enhancement:**
Add `supersedes` relationship type to track when newer papers update older findings.

**New Relationship Type:**
```python
relationship_types = ['supports', 'contradicts', 'extends', 'supersedes', 'none']
```

**Example:**
```json
{
    "source_paper_id": "gpt4-2023",
    "target_paper_id": "gpt3-2020",
    "relationship_type": "supersedes",
    "confidence": 0.90,
    "description": "GPT-4 updates GPT-3 with multimodal capabilities and improved reasoning"
}
```

**Implementation:**
1. Update `RelationshipAgent` to detect supersession
2. Prompt: "Does this paper provide updated results/methodology for an older work?"
3. In Q&A, prioritize non-superseded papers
4. UI: Show "Updated by [Paper X]" tags on older papers

**Value:**
- Prevents citing outdated benchmarks
- Helps users find the most current research
- Implements white paper's temporal intelligence primitive

---

### 14. User Interaction Tracking (Research Memory)
**Priority:** Medium
**Effort:** Medium (2-3 days)
**Inspiration:** White paper Section III.1: "Remembers everything a firm has read, concluded, and superseded"

**Current Gap:**
- System doesn't track what users have read or queried
- No "derived insights" layer capturing user conclusions
- Research context resets every session

**Enhancement:**
Build persistent user research memory:

**New Firestore Collections:**
```python
# user_activity collection
{
    "user_id": "researcher_123",
    "timestamp": "2025-11-04T...",
    "action": "read_paper",  # or "asked_question", "bookmarked", "annotated"
    "paper_id": "1706.03762",
    "context": {
        "query": "How do Transformers work?",
        "session_id": "abc123"
    }
}

# user_insights collection
{
    "user_id": "researcher_123",
    "timestamp": "2025-11-04T...",
    "insight": "Transformers use multi-head attention for parallel computation",
    "derived_from": ["paper1", "paper2"],  # Source papers
    "confidence": 0.85,
    "tags": ["transformers", "attention", "architecture"]
}
```

**Features:**
1. Track read papers and queries per user
2. Capture user annotations/bookmarks
3. Suggest papers based on reading history
4. Build personalized knowledge graph per researcher
5. "Continue research" feature to resume context

**Value:**
- Addresses white paper's "insight decay" problem
- Research compounds rather than dissipates
- Personalized recommendations

---

### 15. Epistemic Status Tracking
**Priority:** Low
**Effort:** Small (1 day)
**Inspiration:** Academic research reality: multiple valid interpretations coexist

**Current Gap:**
- Binary truth assumption (claim is either supported or not)
- Doesn't track contested/emerging claims

**Enhancement:**
Track epistemic status of claims in knowledge graph:

```python
epistemic_status = [
    'consensus',      # Widely accepted (e.g., "Transformers use attention")
    'contested',      # Conflicting evidence (e.g., "LLMs are sample-efficient")
    'emerging',       # Recent, not yet validated
    'deprecated'      # Superseded by newer findings
]
```

**Implementation:**
1. Add `epistemic_status` field to relationships
2. Infer status from relationship patterns:
   - Many "supports" → `consensus`
   - Mix of "supports" and "contradicts" → `contested`
   - Recent papers with few citations → `emerging`
   - Paper with "supersedes" relationship → `deprecated`
3. Display status badges in UI
4. ConfidenceAgent considers status when scoring

**Value:**
- More nuanced than authority hierarchy
- Helps users navigate controversial topics
- Reflects reality of academic discourse

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
