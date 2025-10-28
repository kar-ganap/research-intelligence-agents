# Phase 1.2 Components - Simple Q&A
**Research Intelligence Platform**

Date: 2025-10-28

---

## Objective

Build a simple Q&A system:
**User asks question → System retrieves relevant papers → System answers with citations**

---

## Architecture Overview

```
┌─────────────┐
│   Question  │
└──────┬──────┘
       │
       v
┌─────────────────────┐
│  Retrieval Tool     │ ← Keyword search in Firestore
│  (keyword_search)   │
└──────┬──────────────┘
       │ relevant_papers (list of dicts)
       v
┌─────────────────────┐
│  AnswerAgent        │ ← LLM synthesizes answer
│  (LlmAgent)         │
└──────┬──────────────┘
       │ answer_with_citation
       v
┌─────────────┐
│   Answer    │ "The key finding is X [Paper Title]"
└─────────────┘
```

---

## Components to Build

### 1. Retrieval Tool (src/tools/retrieval.py)

**Purpose**: Find relevant papers from Firestore using keyword matching

**Type**: Python function (not an agent)

**Input**:
- `query: str` - User's question
- `limit: int = 5` - Max papers to return

**Output**:
```python
[
    {
        "paper_id": "abc123",
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", ...],
        "key_finding": "We propose the Transformer...",
        "relevance_score": 0.85
    },
    # ... more papers
]
```

**Algorithm** (Phase 1 - Simple):
```python
def keyword_search(query: str, limit: int = 5) -> List[Dict]:
    """
    Simple keyword-based retrieval.

    1. Extract keywords from query (split on whitespace, remove stopwords)
    2. Query Firestore for papers
    3. Score each paper by keyword overlap in title + key_finding
    4. Return top N papers sorted by score
    """
    # Extract keywords
    keywords = extract_keywords(query)

    # Get all papers from Firestore
    papers = firestore_client.list_papers(limit=100)

    # Score by keyword overlap
    scored_papers = []
    for paper in papers:
        score = calculate_relevance_score(
            keywords=keywords,
            paper_text=f"{paper['title']} {paper['key_finding']}"
        )
        if score > 0:
            paper['relevance_score'] = score
            scored_papers.append(paper)

    # Sort and return top N
    scored_papers.sort(key=lambda p: p['relevance_score'], reverse=True)
    return scored_papers[:limit]
```

**Why not semantic search?**
- Phase 1 goal: Prove concept with simplicity
- Keyword search is fast, deterministic, debuggable
- Phase 2 can add Vertex AI Vector Search

**Implementation complexity**: 🟢 Low (~100 lines)

---

### 2. AnswerAgent (src/agents/qa/answer_agent.py)

**Purpose**: Synthesize answer from retrieved papers with citations

**Type**: LlmAgent (uses Gemini)

**Input**:
- Question (from user)
- Retrieved papers (from retrieval tool)

**Output**:
- Answer with citation in format: `"[Paper Title]"`

**ADK Configuration**:
```python
class AnswerAgent(BaseResearchAgent):
    def _create_agent(self) -> LlmAgent:
        instruction = """
You are an expert research assistant that answers questions based on research papers.

You will be given:
1. A user's question
2. A list of relevant research papers with their key findings

Your task:
- Read the papers' titles and key findings
- Answer the question based ONLY on the information in the papers
- Include a citation after each fact: [Paper Title]
- If multiple papers support a point, cite all: [Paper A], [Paper B]
- If the papers don't contain relevant information, respond: "I don't have enough information in the provided papers to answer this question."

Format:
- Direct, concise answer
- 2-3 sentences maximum
- Citations in square brackets

Example:
"The Transformer architecture uses self-attention mechanisms exclusively [Attention Is All You Need]. This approach outperforms recurrent models on translation tasks [Attention Is All You Need]."
"""

        return LlmAgent(
            name="AnswerAgent",
            model=self.model,
            description="Answers questions based on research papers with citations",
            instruction=instruction
        )

    def answer(self, question: str, papers: List[Dict]) -> str:
        """
        Answer a question using retrieved papers.

        Args:
            question: User's question
            papers: List of paper dicts with title, key_finding, etc.

        Returns:
            Answer with citations
        """
        # Format papers for LLM
        papers_context = self._format_papers(papers)

        prompt = f"""Question: {question}

Research Papers:
{papers_context}

Please answer the question using the papers above."""

        # Use ADK Runner to get answer
        # (Similar pattern to EntityAgent.extract)
        answer = self._run_with_runner(prompt)
        return answer
```

**Key Design Decisions**:
- ✅ **Use LlmAgent** - Need reasoning to synthesize answer
- ✅ **Simple citation format** - Just [Title] for Phase 1
- ✅ **Fail gracefully** - "Don't have enough info" when can't answer
- ✅ **No hallucination** - Explicitly instruct to use ONLY provided papers

**Implementation complexity**: 🟡 Medium (~150 lines)

---

### 3. Q&A Pipeline (src/pipelines/qa_pipeline.py)

**Purpose**: Orchestrate retrieval → answering

**Type**: Simple Python orchestration (same as ingestion pipeline)

**Why not SequentialAgent?**
- Retrieval is a tool (not an agent)
- AnswerAgent is an LLM agent
- Mixed tool + agent = better with simple orchestration
- Explicit control over data flow

**Implementation**:
```python
class QAPipeline:
    """
    Simple Q&A pipeline.

    Flow: Question → Retrieval → Answer
    """

    def __init__(self, project_id: str = None):
        self.answer_agent = AnswerAgent()
        self.firestore_client = FirestoreClient(project_id)

    def ask(self, question: str, limit: int = 5) -> Dict:
        """
        Answer a question with citations.

        Args:
            question: User's question
            limit: Max papers to retrieve

        Returns:
            {
                "success": bool,
                "question": str,
                "answer": str,
                "citations": List[str],  # Paper titles
                "retrieved_papers": List[Dict],
                "steps": {
                    "retrieval": {...},
                    "answering": {...}
                },
                "duration": float
            }
        """
        start_time = time.time()
        result = {
            "success": False,
            "question": question,
            "steps": {}
        }

        try:
            # Step 1: Retrieve relevant papers
            logger.info("Step 1/2: Retrieving relevant papers")
            step_start = time.time()

            papers = keyword_search(
                query=question,
                limit=limit,
                firestore_client=self.firestore_client
            )

            result["steps"]["retrieval"] = {
                "success": True,
                "papers_found": len(papers),
                "duration": time.time() - step_start
            }
            result["retrieved_papers"] = papers

            if not papers:
                result["answer"] = "I couldn't find any relevant papers to answer this question."
                result["citations"] = []
                result["success"] = True
                result["duration"] = time.time() - start_time
                return result

            # Step 2: Generate answer with citations
            logger.info("Step 2/2: Generating answer")
            step_start = time.time()

            answer = self.answer_agent.answer(question, papers)

            result["steps"]["answering"] = {
                "success": True,
                "duration": time.time() - step_start
            }

            # Extract citations from answer
            citations = self._extract_citations(answer)

            result["success"] = True
            result["answer"] = answer
            result["citations"] = citations
            result["duration"] = time.time() - start_time

            logger.info(f"✅ Question answered ({result['duration']:.2f}s)")
            return result

        except Exception as e:
            logger.error(f"Error in Q&A pipeline: {str(e)}")
            result["error"] = str(e)
            result["duration"] = time.time() - start_time
            return result

    def _extract_citations(self, answer: str) -> List[str]:
        """Extract paper titles from [Citation] format."""
        import re
        citations = re.findall(r'\[(.*?)\]', answer)
        return citations
```

**Implementation complexity**: 🟢 Low (~150 lines)

---

## Component Summary

| Component | Type | Lines | Complexity | Dependencies |
|-----------|------|-------|------------|--------------|
| **retrieval.py** | Tool | ~100 | 🟢 Low | Firestore |
| **AnswerAgent** | LlmAgent | ~150 | 🟡 Medium | ADK, Gemini |
| **QAPipeline** | Orchestration | ~150 | 🟢 Low | retrieval, AnswerAgent |

**Total new code**: ~400 lines

---

## Data Flow

### Example: "What is the main contribution of the Transformer paper?"

**Step 1: Retrieval**
```python
# Input
question = "What is the main contribution of the Transformer paper?"

# Retrieval Tool Output
papers = [
    {
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", ...],
        "key_finding": "We propose a new simple network architecture, the Transformer, based solely on attention mechanisms...",
        "relevance_score": 0.95
    },
    # ... other papers
]
```

**Step 2: Answering**
```python
# AnswerAgent Input
question = "What is the main contribution of the Transformer paper?"
papers = [...]  # From retrieval

# AnswerAgent Output
answer = "The main contribution of the Transformer paper is a novel neural network architecture based entirely on self-attention mechanisms, eliminating the need for recurrence and convolutions [Attention Is All You Need]. This architecture achieves superior performance on translation tasks while being more parallelizable [Attention Is All You Need]."
```

**Final Output**
```python
{
    "success": True,
    "question": "What is the main contribution of the Transformer paper?",
    "answer": "The main contribution is...[Attention Is All You Need]...",
    "citations": ["Attention Is All You Need"],
    "retrieved_papers": [...],
    "duration": 2.3
}
```

---

## Test Strategy

### Test Questions (5 diverse questions)

Based on our 3 ingested papers:

1. **Factual extraction** (easy):
   - "Who are the authors of the Attention Is All You Need paper?"
   - Expected: Names from paper, citation

2. **Key finding** (medium):
   - "What is the main contribution of the Transformer architecture?"
   - Expected: Description of self-attention, citation

3. **Comparison** (medium):
   - "How does MobileNetV2 compare to previous MobileNet versions?"
   - Expected: Inverted residuals info, citation

4. **Complex synthesis** (hard):
   - "What are the common themes across papers about neural network architectures?"
   - Expected: Synthesis of multiple papers

5. **Out of scope** (important):
   - "What is the capital of France?"
   - Expected: "I don't have enough information..."

### Success Criteria

| Criterion | Level | Pass Threshold | Measurement |
|-----------|-------|----------------|-------------|
| **Retrieval finds relevant papers** | 1 (Blocker) | ≥3/5 questions | Manual inspection |
| **Answer includes citation** | 1 (Blocker) | ≥4/5 answers (80%) | Regex check for `[...]` |
| **Answer is factually correct** | 2 (Critical) | ≥3/5 answers (60%) | Manual verification |
| **Refuses gracefully** | 2 (Critical) | 1/1 out-of-scope | Check for "don't have enough" |
| **Latency acceptable** | 2 (Critical) | p90 < 10s | Time measurement |

**Go/No-Go**: Must pass all Level 1 criteria + ≥2 Level 2 criteria

---

## Implementation Order

### Step 1: Retrieval Tool (30 min)
- [ ] Create `src/tools/retrieval.py`
- [ ] Implement `keyword_search()` function
- [ ] Test independently on our 3 papers

### Step 2: AnswerAgent (60 min)
- [ ] Create `src/agents/qa/answer_agent.py`
- [ ] Implement with ADK LlmAgent
- [ ] Test with mock retrieved papers

### Step 3: Q&A Pipeline (45 min)
- [ ] Create `src/pipelines/qa_pipeline.py`
- [ ] Integrate retrieval + answer
- [ ] Test on 1 question end-to-end

### Step 4: Full Testing (45 min)
- [ ] Create test script with 5 questions
- [ ] Run full test suite
- [ ] Measure success criteria
- [ ] Record results

**Total estimated time**: 3 hours

---

## Design Decisions

### Why Simple Keyword Search?

**Phase 1 Goal**: Prove the concept works

**Alternatives considered**:
- ❌ Vertex AI Vector Search - Too complex for Phase 1
- ❌ Embedding-based search - Adds latency, API costs
- ✅ **Keyword matching** - Fast, deterministic, debuggable

**Phase 2**: Can upgrade to semantic search if needed

### Why Simple Python Orchestration?

**Same reasoning as Phase 1.1**:
- Retrieval = Tool (not agent)
- AnswerAgent = LLM agent
- Mixed workflow = simple orchestration better
- Explicit data flow easier to debug

### Why Citation Format [Title]?

**Phase 1**: Simple, readable
**Phase 2**: Can add page numbers: `[Title, p. 5]`
**Phase 3**: Can add snippets, confidence scores

---

## Risks & Mitigation

### Risk 1: Keyword search too weak
**Symptom**: Retrieves irrelevant papers
**Mitigation**:
- Test with 3 diverse papers (different domains)
- If <3/5 questions work, add simple TF-IDF scoring
**Fallback**: Just return all 3 papers for every question (brute force)

### Risk 2: LLM hallucinates citations
**Symptom**: Made-up paper titles in answer
**Mitigation**:
- Explicit instruction: "Use ONLY provided papers"
- Post-process: Validate citations against retrieved papers
- Remove invalid citations

### Risk 3: Answer quality low
**Symptom**: Gibberish or off-topic answers
**Mitigation**:
- Improve prompt engineering
- Add few-shot examples to instruction
**Fallback**: Return paper snippets instead of synthesis

### Risk 4: Latency too high
**Symptom**: >10s per question
**Mitigation**:
- Limit retrieved papers to 3 instead of 5
- Use Gemini Flash (fastest model)
- Optimize Firestore queries
**Acceptable**: Phase 1 allows slower performance

---

## File Structure

```
src/
├── tools/
│   └── retrieval.py          ← NEW (keyword search)
├── agents/
│   └── qa/
│       ├── __init__.py       ← NEW
│       └── answer_agent.py   ← NEW (LlmAgent)
├── pipelines/
│   └── qa_pipeline.py        ← NEW (orchestration)
└── storage/
    └── firestore_client.py   ← UPDATE (add query method)

tests/
└── fixtures/
    ├── qa_test_questions.py  ← NEW (5 test questions)
    └── qa_test_results.txt   ← NEW (output)

scripts/
└── test_qa_pipeline.py       ← NEW (test script)
```

---

## Success Looks Like

### Input
```
Question: "Who are the authors of the Transformer paper?"
```

### Output
```
{
    "success": true,
    "answer": "The authors of the Transformer paper are Ashish Vaswani, Noam Shazeer, and Niki Parmar, among others [Attention Is All You Need].",
    "citations": ["Attention Is All You Need"],
    "retrieved_papers": [
        {"title": "Attention Is All You Need", "relevance_score": 0.95}
    ],
    "duration": 2.1
}
```

### Demo
```bash
$ python scripts/test_qa_pipeline.py

Testing Q&A Pipeline
====================

Question 1: Who are the authors of the Transformer paper?
✅ Answer: The authors are Ashish Vaswani, Noam Shazeer... [Attention Is All You Need]
✅ Has citation
✅ Retrieved 1 relevant paper
⏱️  Duration: 2.1s

...

Results: 5/5 questions answered
Success rate: 100%
Citation coverage: 100%
Avg latency: 2.3s

✅ PHASE 1.2 GO DECISION: Criteria MET
```

---

## Next Steps After Phase 1.2

Once Phase 1.2 complete:
- ✅ Phase 1 (Crawl) complete
- 🎯 Move to Phase 2 (Walk) - Knowledge graph, relationships
- 🚀 Or prepare Phase 1 demo for checkpoint

---

## Questions to Consider

1. **How many papers to retrieve?**
   - Recommendation: Start with 3, can increase to 5

2. **Should we cache retrieved papers?**
   - Phase 1: No (keep simple)
   - Phase 2: Yes (add Redis cache)

3. **What if no papers retrieved?**
   - Return: "No relevant papers found in database"

4. **Should AnswerAgent have tools?**
   - Phase 1: No tools needed
   - Phase 2: Could add "search_within_paper" tool

---

## Summary

**3 new components** to build:
1. 🔧 **Retrieval Tool** - Keyword search (simple)
2. 🤖 **AnswerAgent** - LLM synthesis with citations (medium)
3. 🔄 **Q&A Pipeline** - Orchestration (simple)

**~400 lines of code**
**~3 hours estimated**
**High confidence** in feasibility

Ready to start implementing? 🚀
