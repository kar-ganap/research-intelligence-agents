# Future Roadmap - Research Intelligence Platform

**Current State:** 85% feature complete for Phase 3. All core functionality deployed and working in production.

This roadmap uses a **Crawl → Walk → Run** approach to prioritize post-hackathon development.

---

## 🐛 CRAWL: Quick Wins & Polish (1-2 Weeks)

**Goal:** Make the platform production-ready and add high-value features with minimal effort.

### C1. MCP Server Integration ⭐ **RECOMMENDED FIRST**
**Effort:** 1-2 days | **Value:** HIGH

Expose platform capabilities via Model Context Protocol (MCP) to enable access from Claude Desktop, Cursor, and other AI tools.

**What You Get:**
- Query research papers directly from Claude Desktop
- Ask research questions while coding in Cursor
- Integrate with other MCP-compatible tools

**Implementation:**
```python
# src/mcp_server/server.py
from mcp import Server, Tool

server = Server("research-intelligence")

@server.tool()
async def search_papers(query: str, max_results: int = 10):
    """Search research papers by keywords or semantic similarity"""
    response = await orchestrator_client.search(query, limit=max_results)
    return response

@server.tool()
async def ask_research_question(question: str):
    """Ask a question about research topics with citations"""
    response = await orchestrator_client.qa(question)
    return response

@server.tool()
async def find_contradictions(claim: str):
    """Find papers that support or contradict a claim"""
    response = await orchestrator_client.find_contradictions(claim)
    return response

@server.tool()
async def get_paper_graph(paper_id: str):
    """Get citation graph and relationships for a paper"""
    response = await graph_service_client.get_subgraph(paper_id)
    return response
```

**Files to Create:**
- `src/mcp_server/server.py`
- `src/mcp_server/Dockerfile`
- `src/mcp_server/cloudbuild.yaml`

**Deployment:** Deploy as Cloud Run service, add to `deploy_all_services.sh`

---

### C2. Frontend Polish
**Effort:** 1 day | **Value:** MEDIUM

Quick UX improvements for better user experience.

**Tasks:**
1. ✅ **DONE:** Acronym handling (GPT, BERT, etc.)
2. ✅ **DONE:** Empty card fix for deleted rules
3. **TODO:** Add loading spinners for long operations
4. **TODO:** Improve error messages (currently generic)
5. **TODO:** Add toast notifications for success/failure
6. **TODO:** Make graph visualization collapsible
7. **TODO:** Add keyboard shortcuts (Enter to submit, Esc to close)
8. **TODO:** "Export to PDF" button for Q&A responses

**Files to Modify:**
- `src/services/frontend/app.js` - Add loading states, error handling
- `src/services/frontend/index.html` - Add toast container

---

### C3. Monitoring & Observability
**Effort:** 2-3 days | **Value:** HIGH

Add comprehensive monitoring to catch issues before users do.

**What to Monitor:**
1. **Cloud Monitoring Dashboards:**
   - Service latency (p50, p95, p99)
   - Error rates by endpoint
   - LLM API costs per day
   - Ingestion pipeline throughput

2. **Alerting Rules:**
   - Alert if any service has >5% error rate
   - Alert if Q&A latency >30 seconds
   - Alert if daily costs >$50
   - Alert if Firestore storage >80% quota

3. **Structured Logging:**
   - Add trace IDs to correlate requests
   - Log LLM prompts/responses for debugging
   - Log request/response sizes

**Implementation:**
```python
# src/utils/monitoring.py
from google.cloud import monitoring_v3, logging

class MonitoringClient:
    def log_request(self, service: str, endpoint: str, latency_ms: int, status: int):
        logger.info("api_request", extra={
            "service": service,
            "endpoint": endpoint,
            "latency_ms": latency_ms,
            "status": status,
            "trace_id": get_trace_id()
        })

    def record_llm_call(self, model: str, prompt_tokens: int,
                       completion_tokens: int, cost: float):
        metric = self.client.metric("llm_usage")
        metric.record(cost, labels={
            "model": model,
            "service": get_current_service()
        })
```

---

### C4. Cost Optimization
**Effort:** 2-3 days | **Value:** MEDIUM | **Expected Savings:** 50-70%

Reduce cloud costs without sacrificing quality.

**Strategies:**
1. **Cache LLM Responses**
   - Cache Q&A responses for duplicate questions (5-minute window)
   - Cache entity extraction for papers
   - Use Redis or Firestore for cache

2. **Use Cheaper Models Where Possible**
   - Entity extraction: Gemini Flash instead of Pro
   - Relationship detection: Flash instead of Pro
   - Final Q&A synthesis: Keep using Pro for quality

3. **Batch Processing**
   - Process multiple papers in single LLM call
   - Batch embedding generation

4. **Request Deduplication**
   - If same question asked within 5 minutes, return cached result

---

### C5. Code Cleanup
**Effort:** 1 hour | **Value:** LOW

Remove empty directories and outdated references.

**Tasks:**
1. Delete `src/jobs/nightly_eval/` (empty, move to Run phase if needed)
2. Delete `src/jobs/weekly_digest/` (empty, move to Walk phase if needed)
3. Update PHASE_3_COMPLETE.md: Change "7 agents" → "6 agents"
4. Remove "weekly digest" from completed features
5. Update FUTURE_WORK.md → Point to this roadmap
6. Mark arXiv ingestion as ✅ IMPLEMENTED in docs

---

## 🚶 WALK: Core Enhancements (1-2 Months)

**Goal:** Significantly improve answer quality and add differentiating features.

### W1. Multi-Agent Deliberation System
**Effort:** 3-5 days | **Value:** HIGH

Implement the "debate system" where multiple agents discuss before answering controversial questions.

**Architecture:**
```python
# src/agents/qa/deliberation_coordinator.py
class DeliberationCoordinator:
    """Coordinates multi-agent deliberation"""

    def __init__(self):
        self.agents = [
            LlmAgent(model="gemini-2.0-flash-exp", name="Agent-Skeptic"),
            LlmAgent(model="gemini-2.0-flash-exp", name="Agent-Optimist"),
            LlmAgent(model="gemini-2.0-flash-exp", name="Agent-Moderator")
        ]

    async def deliberate(self, question: str, evidence: List[Paper]) -> Dict:
        """Run multi-round deliberation

        Round 1: Each agent forms initial opinion
        Round 2: Agents respond to each other
        Round 3: Moderator synthesizes consensus
        """
        opinions = await self._gather_initial_opinions(question, evidence)
        rebuttals = await self._exchange_rebuttals(opinions)
        final_answer = await self._synthesize_consensus(opinions, rebuttals)

        return {
            "answer": final_answer,
            "debate_transcript": [opinions, rebuttals],
            "consensus_strength": self._measure_consensus(rebuttals)
        }
```

**Trade-offs:**
- ⚠️ 3-5x slower than current approach
- ⚠️ 3-5x more expensive (more API calls)
- ✅ Much better for controversial questions
- ✅ Shows reasoning process (transparency)

**Implementation Strategy:**
1. Add `deliberation_mode` flag to Q&A endpoint (default: false)
2. Use only for contradiction detection or when user requests
3. Show agent debate transcript in UI for transparency

**Files to Create:**
- `src/agents/qa/deliberation_agent.py`
- `src/agents/qa/deliberation_coordinator.py`

**Files to Modify:**
- `src/pipelines/qa_pipeline.py` - Add deliberation mode
- `src/services/frontend/app.js` - Add toggle for deliberation

---

### W2. Semantic Paper Search
**Effort:** 5-7 days | **Value:** HIGH

Replace keyword-based retrieval with semantic embeddings for better search.

**Why Now:**
- Current keyword search works but misses conceptual matches
- Users ask questions like "papers about attention mechanisms" (concept, not keyword)
- Paraphrased terminology causes misses

**Implementation:**
```python
# src/tools/embedding_search.py
from vertexai.preview.generative_models import TextEmbeddingModel

class EmbeddingSearchTool:
    def __init__(self):
        self.model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        self.index = VertexAIVectorSearch(
            project="research-intel-agents",
            index_name="papers-embeddings"
        )

    async def search(self, query: str, top_k: int = 10) -> List[Paper]:
        # Generate query embedding
        query_embedding = self.model.get_embeddings([query])[0]

        # Hybrid search: combine semantic + keyword
        semantic_results = await self.index.similarity_search(
            query_embedding, top_k=top_k
        )
        keyword_results = await self.keyword_search(query, top_k=top_k)

        # Merge and re-rank
        return self._merge_results(semantic_results, keyword_results)
```

**Steps:**
1. Generate embeddings for all existing papers (title + abstract + key_finding)
2. Set up Vertex AI Vector Search index
3. Create batch job to embed new papers as they're ingested
4. Implement hybrid search (semantic + keyword)
5. A/B test against current keyword search

**Cost Considerations:**
- Embedding generation: ~$0.00002 per paper (one-time)
- Vector Search: ~$0.70/hour for index serving
- Queries: ~$0.001 per 1000 queries

**Files to Create:**
- `src/tools/embedding_search.py`
- `src/jobs/generate_embeddings/main.py` - Batch job

**Files to Modify:**
- `src/tools/retrieval_tool.py` - Switch to hybrid search

---

### W3. Enhanced Citations with Exact Quotes & Page Numbers
**Effort:** 3-4 days | **Value:** HIGH

Add provenance to every citation: exact quote, page number, section.

**Current State:**
```python
"Transformers use self-attention [Attention Is All You Need]"
```

**Enhanced State:**
```python
{
    "claim": "Transformers use self-attention",
    "evidence": {
        "paper_id": "1706.03762",
        "title": "Attention Is All You Need",
        "quote": "The Transformer architecture uses multi-head self-attention to allow modeling dependencies without regard to their distance in the input or output sequences.",
        "page": 3,
        "section": "3.2 Attention",
        "confidence": 0.95
    }
}
```

**Implementation:**
1. Update PDF parser to preserve page numbers during extraction
2. Modify AnswerAgent to return structured claim-evidence pairs
3. Store citation provenance in answers collection
4. Add UI to show quotes on hover/click

**Value:**
- Audit trail for every claim
- Enables Trust Verification (W6)
- Academic rigor and accountability

**Files to Modify:**
- `src/agents/ingestion/paper_parser.py` - Track page numbers
- `src/agents/qa/answer_agent.py` - Structured citations
- `src/services/frontend/app.js` - Citation UI

---

### W4. Table & Chart Extraction (Multimodal Understanding)
**Effort:** 5-7 days | **Value:** HIGH

Extract quantitative evidence from tables and charts in papers.

**Current Gap:**
- Only text is extracted from PDFs
- Critical experimental results in tables are ignored
- Benchmark comparisons in charts are missed

**Example Missing Data:**
- "GPT-3 achieves 71.8% accuracy on LAMBADA" → Table in paper
- Transformer benchmarks (WMT 2014 BLEU scores) → Table 2
- Ablation study results → Often in tables

**Implementation:**
```python
# src/agents/ingestion/table_extractor.py
import camelot  # For table extraction

class TableExtractor:
    """Extracts tables and charts from research papers"""

    def extract_tables(self, pdf_path: str) -> List[Dict]:
        """Extract all tables from PDF"""
        tables = camelot.read_pdf(pdf_path, pages='all')

        structured_tables = []
        for table in tables:
            structured_tables.append({
                "page": table.page,
                "data": table.df.to_dict(),  # pandas DataFrame
                "caption": self._extract_caption(table),
                "table_type": self._classify_table(table)  # results/ablation/comparison
            })

        return structured_tables

    def extract_charts(self, pdf_path: str) -> List[Dict]:
        """Use Gemini Vision to understand charts"""
        # Extract images from PDF
        # Use Gemini multimodal to interpret charts
        # Return structured data
        pass
```

**Steps:**
1. Add `camelot-py` for table extraction
2. Use Gemini Vision API for chart interpretation
3. Store tables as structured JSON in Firestore
4. Update AnswerAgent to reason over tabular data
5. Link table cells to paper claims in relationship graph

**Files to Create:**
- `src/agents/ingestion/table_extractor.py`
- `src/agents/ingestion/chart_extractor.py`

**Files to Modify:**
- `src/agents/ingestion/paper_parser.py` - Call extractors
- `src/storage/firestore_client.py` - Add `tables` field
- `src/agents/qa/answer_agent.py` - Use table data

---

### W5. Citation Quality & Authority Scoring
**Effort:** 3-4 days | **Value:** MEDIUM

Score citations by quality and weight sources by authority.

**Two Components:**

**A. Citation Quality Scoring**
Rate how well each citation supports its claim (0.0-1.0).

```python
class CitationScorer(LlmAgent):
    """Scores how well a citation supports a claim"""

    def score_citation(self, claim: str, paper: Paper, excerpt: str) -> float:
        """
        Evaluates:
        - Does excerpt directly support claim?
        - Primary or secondary source?
        - How confident is the paper's conclusion?
        """
        prompt = f"""
        Claim: {claim}
        Evidence: {excerpt}
        Paper: {paper.title}

        Rate 0.0-1.0 how well this evidence supports the claim.
        """
        score = await self.model.generate_content(prompt)
        return float(score)
```

**B. Authority-Weighted Reasoning**
Weight papers by venue, citations, recency.

```python
def calculate_source_authority(paper: Dict) -> float:
    """Calculate authority weight (0.0-1.0) for a paper"""
    score = 0.5  # Base score

    # Venue tier
    if paper.get('venue') in ['NeurIPS', 'ICML', 'ICLR', 'Nature', 'Science']:
        score += 0.3
    elif paper.get('is_peer_reviewed'):
        score += 0.2

    # Citation count (diminishing returns)
    citation_count = paper.get('citation_count', 0)
    score += min(0.2, citation_count / 100)

    # Recency (papers >5 years old may be outdated)
    age_years = (datetime.now() - paper['published_date']).days / 365
    if age_years > 5:
        score -= 0.1

    return max(0.1, min(1.0, score))
```

**Use Cases:**
- ConfidenceAgent weights by authority
- UI shows quality badges (⭐⭐⭐⭐⭐)
- Higher-authority papers win contradictions

**Files to Create:**
- `src/agents/qa/citation_scorer.py`
- `src/utils/authority_scoring.py`

**Files to Modify:**
- `src/agents/qa/confidence_agent.py` - Use authority scores
- `src/services/frontend/app.js` - Display quality indicators

---

### W6. Trust Verification Layer
**Effort:** 7-10 days | **Value:** HIGH

Verify that cited claims are actually supported by cited papers.

**What It Does:**
```python
# Example
answer = "Transformer achieves 28.4 BLEU on WMT 2014 [Attention Is All You Need]"

verifier.verify_claim(
    claim="28.4 BLEU on WMT 2014",
    citation="Attention Is All You Need",
    paper_text=full_paper_text
)

# Returns:
{
    'status': 'VERIFIED',  # or PARTIAL, UNVERIFIED, CONTRADICTS
    'evidence': 'On the WMT 2014 English-to-German translation task, our model achieves a BLEU score of 28.4...',
    'page_number': 8,
    'table': 'Table 2',
    'confidence': 0.95
}
```

**Implementation:**
```python
# src/agents/qa/verifier_agent.py
class VerifierAgent(LlmAgent):
    """Verifies claims against cited papers"""

    async def verify_claim(self, claim: str, citation: str,
                          paper_text: str) -> Dict:
        # 1. Extract specific claim (e.g., "28.4 BLEU")
        # 2. Search full paper for this claim
        # 3. Check tables, figures, text
        # 4. Return verification status with evidence

        prompt = f"""
        Find this claim in the paper: {claim}

        Paper text: {paper_text}

        Return:
        - VERIFIED if exact match found
        - PARTIAL if similar but not exact
        - UNVERIFIED if not found
        - CONTRADICTS if paper says something different

        Include exact quote and location.
        """

        result = await self.model.generate_content(prompt)
        return self._parse_verification(result)
```

**Prerequisites:**
- Store full paper text (not just metadata)
- Implement chunking for efficient search
- May need better PDF parsing for tables/figures

**External APIs (Optional):**
- Retraction Watch Database - Check for retracted papers
- PubMed retraction notices
- arXiv version tracking

**Files to Create:**
- `src/agents/qa/verifier_agent.py`
- `src/agents/qa/claim_parser.py`

**Files to Modify:**
- `src/pipelines/qa_pipeline.py` - Add verification step
- `src/services/frontend/app.js` - Show verification badges

---

### W7. Weekly Digest Emails
**Effort:** 3-4 days | **Value:** MEDIUM

Send personalized weekly summaries to users.

**What's Included:**
- Papers matching your watch rules
- New alerts triggered
- Trending topics in your research areas
- Citation count changes for watched papers

**Implementation:**
```python
# src/jobs/weekly_digest/main.py
class WeeklyDigestGenerator:
    """Generates personalized weekly research digests"""

    def generate_digest(self, user_email: str) -> Dict:
        # Get user's watch rules
        rules = self.get_user_rules(user_email)

        # Get papers from last 7 days matching rules
        papers = self.get_matching_papers(rules, days=7)

        # Get alerts triggered
        alerts = self.get_user_alerts(user_email, days=7)

        # Generate summary with LLM
        digest = await self.summarize_weekly_activity(papers, alerts)

        return digest

    def send_email(self, user_email: str, digest: Dict):
        # Use SendGrid (already configured)
        self.sendgrid.send(
            to=user_email,
            subject=f"Research Digest - Week of {date}",
            html=self.render_template(digest)
        )
```

**Deployment:**
- Cloud Scheduler: Trigger every Sunday at 9am
- Cloud Run Job: Generate and send digests

**Files to Create:**
- `src/jobs/weekly_digest/main.py`
- `src/jobs/weekly_digest/cloudbuild.yaml`
- `src/jobs/weekly_digest/email_template.html`

---

### W8. Paper Upload & Processing
**Effort:** 3-4 days | **Value:** MEDIUM

Allow users to upload their own PDFs for ingestion.

**Current State:**
- API endpoint exists (`/api/upload`) but minimally tested
- No progress tracking
- No duplicate detection

**Improvements Needed:**
1. Test and fix upload endpoint
2. Add progress tracking (ingestion takes 2-5 minutes)
3. Duplicate detection (don't re-ingest same paper)
4. Batch upload (multiple PDFs at once)
5. Show processing status in UI with progress bar

**Implementation:**
```python
# src/services/api_gateway/main.py
@app.route('/api/upload/status/<upload_id>', methods=['GET'])
def upload_status(upload_id: str):
    """Check status of PDF upload"""
    status = db.collection('upload_status').document(upload_id).get()
    return jsonify({
        'status': status.get('state'),  # queued, processing, completed, failed
        'progress': status.get('progress'),  # 0-100
        'paper_id': status.get('paper_id'),  # if completed
        'error': status.get('error')  # if failed
    })
```

**Files to Modify:**
- `src/services/api_gateway/main.py` - Improve upload endpoint
- `src/services/orchestrator/main.py` - Add progress tracking
- `src/services/frontend/app.js` - Upload UI with progress

---

## 🏃 RUN: Advanced Features (3-6 Months)

**Goal:** Build sophisticated features that create significant competitive advantages.

### R1. Claim-Level Confidence & Provenance
**Effort:** 7-10 days | **Value:** HIGH

Move from answer-level to claim-level confidence scoring.

**Current State:**
```python
{
    "answer": "Transformers are more efficient than RNNs...",
    "overall_confidence": 0.82
}
```

**Enhanced State:**
```python
{
    "answer": {
        "claims": [
            {
                "claim": "Transformers outperform RNNs on WMT",
                "confidence": 0.95,  # High - directly from paper table
                "evidence_strength": "strong",
                "citations": [{
                    "paper": "Attention Is All You Need",
                    "page": 8,
                    "quote": "Our model achieves...",
                    "table": "Table 2"
                }]
            },
            {
                "claim": "Transformers are more efficient to train",
                "confidence": 0.70,  # Medium - inferred from multiple sources
                "evidence_strength": "moderate",
                "citations": [...]
            }
        ],
        "overall_confidence": 0.82
    }
}
```

**Implementation:**
1. Parse AnswerAgent output into discrete claims
2. Score confidence per claim independently
3. Aggregate for overall answer confidence
4. Display confidence badges per claim in UI

**Value:**
- Users know which parts to trust
- Granular verification possible
- Better transparency

---

### R2. Temporal Intelligence: Supersession Tracking
**Effort:** 5-7 days | **Value:** MEDIUM

Track when newer papers update/supersede older findings.

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

**Use Cases:**
- Prevent citing outdated benchmarks
- Answer "What's the latest result on X?"
- Show "Updated by [Paper X]" tags on older papers

**Implementation:**
1. Update RelationshipAgent to detect supersession
2. Prompt: "Does this paper provide updated results for older work?"
3. Q&A prioritizes non-superseded papers
4. UI shows update chain (Paper A → Paper B → Paper C)

**Files to Modify:**
- `src/agents/ingestion/relationship_agent.py` - Detect supersession
- `src/agents/qa/retrieval_tool.py` - Prioritize current papers
- `src/services/frontend/app.js` - Show update tags

---

### R3. User Research Memory & Personalization
**Effort:** 7-10 days | **Value:** MEDIUM

Track user activity and build personalized research profiles.

**What to Track:**
```python
# user_activity collection
{
    "user_id": "researcher_123",
    "timestamp": "2025-11-06T...",
    "action": "read_paper",  # or asked_question, bookmarked, annotated
    "paper_id": "1706.03762",
    "context": {
        "query": "How do Transformers work?",
        "session_id": "abc123"
    }
}

# user_insights collection
{
    "user_id": "researcher_123",
    "timestamp": "2025-11-06T...",
    "insight": "Transformers use multi-head attention for parallel computation",
    "derived_from": ["paper1", "paper2"],
    "confidence": 0.85,
    "tags": ["transformers", "attention"]
}
```

**Features:**
1. Track read papers and queries per user
2. Capture user annotations/bookmarks
3. Suggest papers based on reading history
4. Build personalized knowledge graph
5. "Continue research" feature to resume context

**Value:**
- Research compounds rather than dissipates
- Personalized recommendations
- Better engagement and retention

---

### R4. Iterative Query Refinement
**Effort:** 3-5 days | **Value:** MEDIUM

Detect ambiguous queries and ask clarifying questions.

**Flow:**
```
User: "Tell me about transformers"

System: "Did you mean:
  1. Transformers in NLP (BERT, GPT)
  2. Electrical transformers in power systems
  3. Transformer networks in computer vision
  4. All of the above"

User: [selects option 1]

System: [searches with refined query]
```

**Implementation:**
```python
class QueryRefinementAgent(LlmAgent):
    """Identifies ambiguous queries and suggests refinements"""

    def analyze_query(self, question: str) -> Dict:
        prompt = f"""
        Is this question ambiguous? {question}

        If yes, suggest 2-4 possible interpretations.
        If no, suggest a refined query.
        """

        result = await self.model.generate_content(prompt)

        return {
            "is_ambiguous": True/False,
            "clarifications": ["option1", "option2"],
            "suggested_refinement": "refined query"
        }
```

**Files to Create:**
- `src/agents/query/refinement_agent.py`

**Files to Modify:**
- `src/pipelines/qa_pipeline.py` - Check ambiguity before retrieval
- `src/services/frontend/app.js` - Clarification UI

---

### R5. Epistemic Status Tracking
**Effort:** 3-5 days | **Value:** LOW

Track consensus, contested, emerging, or deprecated status of claims.

**Status Types:**
```python
epistemic_status = [
    'consensus',    # Widely accepted (e.g., "Transformers use attention")
    'contested',    # Conflicting evidence (e.g., "LLMs are sample-efficient")
    'emerging',     # Recent, not yet validated
    'deprecated'    # Superseded by newer findings
]
```

**How Status is Inferred:**
- Many "supports" relationships → `consensus`
- Mix of "supports" and "contradicts" → `contested`
- Recent papers with few citations → `emerging`
- Has "supersedes" relationship → `deprecated`

**UI:**
- Display status badges (🟢 Consensus, 🟡 Contested, 🔵 Emerging, ⚫ Deprecated)
- Filter by epistemic status
- ConfidenceAgent considers status when scoring

---

### R6. Research Assistant Chat Interface
**Effort:** 7-10 days | **Value:** MEDIUM

Replace Q&A form with conversational multi-turn chat.

**Features:**
- Multi-turn conversations with context
- Follow-up questions
- "Show me more papers about X"
- Conversational commands ("Compare paper A vs B")

**Implementation:**
```python
class ConversationManager:
    """Manages multi-turn research conversations"""

    def __init__(self):
        self.sessions = {}  # session_id -> conversation history

    async def process_message(self, session_id: str, message: str) -> str:
        # Get conversation history
        history = self.sessions.get(session_id, [])

        # Build context from previous turns
        context = self.build_context(history)

        # Process with context
        response = await self.qa_pipeline.answer(message, context=context)

        # Update history
        history.append({"user": message, "assistant": response})
        self.sessions[session_id] = history

        return response
```

**Files to Create:**
- `src/agents/qa/conversation_manager.py`

**Files to Modify:**
- `src/services/frontend/app.js` - Chat UI instead of form

---

### R7. Automated Research Summaries
**Effort:** 7-10 days | **Value:** MEDIUM

Generate comprehensive summaries of research topics.

**Queries:**
- "Summarize all research on transformers in the last 5 years"
- "What's the current state of the art for question answering?"
- "What are the open problems in multimodal learning?"

**Implementation:**
```python
class ResearchSummarizer(LlmAgent):
    """Generates comprehensive research summaries"""

    async def summarize_topic(self, topic: str, time_period: str) -> Dict:
        # 1. Find all relevant papers (semantic search, top 50)
        papers = await self.retrieval_tool.search(topic, top_k=50)

        # 2. Cluster papers by subtopic
        clusters = self.cluster_papers(papers)

        # 3. Summarize each cluster
        cluster_summaries = []
        for cluster in clusters:
            summary = await self.summarize_cluster(cluster)
            cluster_summaries.append(summary)

        # 4. Generate overall summary
        final_summary = await self.synthesize_summaries(cluster_summaries)

        return {
            "topic": topic,
            "summary": final_summary,
            "subtopics": cluster_summaries,
            "paper_count": len(papers),
            "time_period": time_period
        }
```

---

### R8. Advanced Watch Rule Templates
**Effort:** Ongoing, 1-2 hours per template | **Value:** LOW-MEDIUM

Add more sophisticated watch rule templates.

**Currently Implemented:**
- ✅ Breakthrough claim
- ✅ SOTA beat
- ✅ Contradicting claim
- ✅ Author watch
- ✅ Keyword combo

**Future Templates:**
- `dataset_benchmark` - Alert on new benchmark results for specific datasets
- `methodology_adoption` - Papers using specific techniques (e.g., "uses LoRA fine-tuning")
- `reproducibility_check` - Papers that reproduce/challenge existing results
- `cross_domain_application` - Technique from domain A applied to domain B
- `trend_detection` - Multiple papers on emerging topics

**Implementation:**
Add templates to `src/agents/alerting/alert_templates.py`. Each is just a function returning rule configuration.

---

### R9. Nightly Evaluation Suite
**Effort:** 4-6 days | **Value:** LOW (Engineering quality)

Run automated tests every night to catch regressions.

**What to Test:**
1. Q&A pipeline accuracy (golden question set)
2. Retrieval quality (precision@10 for known queries)
3. Entity extraction accuracy (test papers with known metadata)
4. Contradiction detection accuracy (labeled pairs)
5. Service health and latency

**Implementation:**
```python
# src/jobs/nightly_eval/main.py
class NightlyEvaluator:
    """Runs evaluation suite on production system"""

    def run_qa_eval(self) -> Dict:
        # Test 50 golden questions
        golden_set = self.load_golden_questions()
        results = []

        for question, expected_answer in golden_set:
            actual_answer = await self.orchestrator.qa(question)
            score = self.evaluate_answer(expected_answer, actual_answer)
            results.append(score)

        return {
            "average_score": np.mean(results),
            "passing": np.mean(results) > 0.7
        }

    def send_alert_if_failing(self, results: Dict):
        if not results["passing"]:
            self.sendgrid.send_alert(results)
```

**Deployment:**
- Cloud Scheduler: Trigger daily at 3am
- Cloud Run Job: Run tests and send alerts if failing

**Files to Create:**
- `src/jobs/nightly_eval/main.py`
- `src/jobs/nightly_eval/golden_questions.json`
- `src/jobs/nightly_eval/test_cases.json`

---

### R10. Real-Time Collaboration (Future)
**Effort:** 10-15 days | **Value:** LOW

Multi-user collaboration features for research teams.

**Features:**
- Shared Q&A sessions
- Collaborative annotations
- Shared paper collections
- Real-time updates via WebSockets

**Technologies:**
- Firebase Realtime Database
- WebSocket connections

**Note:** Only implement if you get team/enterprise users.

---

## 🔮 DEFERRED: Future Considerations

These are valuable but not priorities for hackathon follow-up.

### D1. CI/CD Pipeline
**Effort:** 3-5 days | **Value:** LOW (for single developer)

Automate deployment with testing and rollback.

**GitHub Actions Workflow:**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Run tests
        run: pytest tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy all services
        run: ./scripts/deploy_all_services.sh

      - name: Run smoke tests
        run: ./scripts/verify_services.sh

      - name: Rollback on failure
        if: failure()
        run: ./scripts/rollback.sh
```

**When to revisit:** When you have a team or frequent deployments

---

### D2. Multi-Environment Setup
**Effort:** 3-4 days | **Value:** LOW (useful for teams)

Separate dev/staging/prod environments.

```bash
# scripts/deploy_to_env.sh
ENV=$1  # dev, staging, prod

if [ "$ENV" = "prod" ]; then
    PROJECT_ID="research-intel-agents-prod"
elif [ "$ENV" = "staging" ]; then
    PROJECT_ID="research-intel-agents-staging"
else
    PROJECT_ID="research-intel-agents-dev"
fi

./scripts/deploy_all_services.sh --project $PROJECT_ID
```

**When to revisit:** When you have multiple developers

---

## Implementation Priority Matrix

```
High Value, Low Effort (DO FIRST - CRAWL):
├─ MCP Server Integration ⭐ (1-2 days)
├─ Frontend Polish (1 day)
├─ Monitoring & Observability (2-3 days)
└─ Cost Optimization (2-3 days)

High Value, High Effort (DO NEXT - WALK):
├─ Multi-Agent Deliberation (3-5 days)
├─ Semantic Paper Search (5-7 days)
├─ Enhanced Citations with Provenance (3-4 days)
├─ Table & Chart Extraction (5-7 days)
└─ Trust Verification Layer (7-10 days)

Medium Value, Medium Effort (WALK/RUN):
├─ Citation Quality & Authority Scoring (3-4 days)
├─ Weekly Digest Emails (3-4 days)
├─ Paper Upload & Processing (3-4 days)
├─ Temporal Intelligence (5-7 days)
└─ User Research Memory (7-10 days)

Low Value or Deferred (DEFER):
├─ CI/CD Pipeline (3-5 days)
├─ Multi-environment setup (3-4 days)
├─ Real-time collaboration (10-15 days)
├─ Nightly eval (4-6 days) - unless quality issues arise
└─ Advanced watch templates (add as needed)
```

---

## Recommended Sequence

### Week 1-2: Quick Wins (CRAWL)
1. MCP Server (2 days) ⭐
2. Frontend Polish (1 day)
3. Monitoring setup (2 days)
4. Cost optimization (2 days)
5. Code cleanup (1 hour)

**Outcome:** Production-ready platform with external integrations

### Month 1: Core Enhancements (WALK Phase 1)
1. Multi-Agent Deliberation (4 days)
2. Enhanced Citations with Provenance (4 days)
3. Citation Quality & Authority Scoring (4 days)
4. Weekly Digest (3 days)

**Outcome:** Significantly better answer quality and trust

### Month 2-3: Advanced Features (WALK Phase 2)
1. Semantic Search (7 days)
2. Table & Chart Extraction (7 days)
3. Trust Verification Layer (10 days)
4. Paper Upload (4 days)

**Outcome:** Complete research intelligence platform

### Month 4+: Sophisticated Capabilities (RUN)
1. Claim-Level Confidence (10 days)
2. Temporal Intelligence (7 days)
3. User Research Memory (10 days)
4. Research Summaries (10 days)

**Outcome:** Competitive moat, unique capabilities

---

## Total Estimated Effort

- **CRAWL:** 1-2 weeks (7-10 days)
- **WALK:** 1.5-2 months (35-50 days)
- **RUN:** 3-5 months (60-90 days)

**Total:** 5-7 months of full-time engineering work

---

## Success Metrics

**CRAWL Phase:**
- MCP server has 10+ active users
- Error rate <1%
- LLM costs reduced by 50%
- Average Q&A latency <5 seconds

**WALK Phase:**
- Answer confidence scores >0.8 for 80% of queries
- Users can verify all citations with quotes
- Weekly digest open rate >40%
- 100+ papers with extracted tables

**RUN Phase:**
- Claim-level confidence tracking for all answers
- User retention >60% month-over-month
- Research summaries generated for 50+ topics
- Personalization increases engagement by 2x

---

## Notes on Deferred Features

### ✅ IMPLEMENTED (previously listed as future work)
- **ArXiv Ingestion** - Daily scheduled ingestion with hybrid approach (categories + watch rules)
- **Watch Rules** - Keyword, author, claim, relationship, template rules all working
- **Alerting** - Email notifications via SendGrid
- **Duplicate Detection** - Backend prevents duplicate rules from being created

### ⚠️ PARTIALLY IMPLEMENTED
- **Key Finding Extraction** - Working but could be better with table data
- **Relationship Detection** - Works with key findings, would improve with full text

### 🚫 DEFERRED TO FUTURE
- **VerifierAgent** - Covered by Trust Verification Layer (W6)
- **SummaryAgent** - Covered by Research Summaries (R7)
- **Weekly Digest** - Moved to Walk phase (W7)
- **Nightly Eval** - Moved to Run phase (R9)
- **CI/CD** - Deferred section (D1)

---

## How to Use This Roadmap

1. **Start with CRAWL** - Get MCP server working first, it's the highest ROI
2. **Measure impact** - Track metrics after each feature
3. **Adjust priorities** - Based on user feedback and usage patterns
4. **Don't skip phases** - CRAWL features enable WALK features enable RUN features
5. **Review quarterly** - Re-prioritize based on new learnings

---

*Last updated: November 6, 2025 - Post-Phase 3 Audit*
*Based on: Comprehensive codebase audit + Original platform planning*
