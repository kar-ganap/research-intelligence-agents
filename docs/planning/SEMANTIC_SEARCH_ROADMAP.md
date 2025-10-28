# Semantic Search Roadmap
**Research Intelligence Platform**

Date: 2025-10-28

---

## Current State: Phase 1 - Keyword Search Only

**What we have:**
- Simple keyword matching in Firestore
- TF-IDF style scoring (count keyword overlaps)
- Fast, deterministic, debuggable

**Limitations:**
- ❌ Can't understand synonyms ("ML" vs "machine learning")
- ❌ Can't understand semantic meaning ("neural networks" related to "deep learning")
- ❌ Struggles with complex queries ("papers about attention mechanisms")

---

## The Plan: Multi-Phase Semantic Search Evolution

### Phase 1 (Current) - Keyword Only ✅
**Status**: Implementing now
**When**: Days 0-1
**Technology**: Keyword matching + TF-IDF

**Retrieval method:**
```python
def keyword_search(query: str) -> List[Dict]:
    """Simple keyword overlap scoring"""
    keywords = query.lower().split()

    for paper in papers:
        score = sum(1 for kw in keywords
                   if kw in paper['title'].lower()
                   or kw in paper['key_finding'].lower())
        paper['relevance_score'] = score

    return sorted(papers, key=lambda p: p['relevance_score'], reverse=True)
```

**Good for**: Exact matches, simple queries
**Sufficient for**: Phase 1 Go/No-Go (prove the concept)

---

### Phase 2 - Hybrid Search (Keyword + Semantic) 🎯
**Status**: Planned
**When**: Days 2-3
**Technology**: Vertex AI Vector Search + Keyword search

#### What Changes:

**1. Add Embeddings to Data Model**

```python
# Firestore schema update
{
    "paper_id": "abc123",
    "title": "Attention Is All You Need",
    "abstract": "...",
    "key_finding": "...",

    # NEW: Embedding fields
    "embeddings": {
        "title_embedding": [0.123, -0.456, ...],      # 768-dim vector
        "abstract_embedding": [0.789, -0.234, ...],
        "full_text_embedding": [0.345, -0.678, ...]
    }
}
```

**2. Generate Embeddings During Ingestion**

```python
# Update IndexerAgent or create EmbeddingAgent
class EmbeddingAgent:
    def __init__(self):
        # Use Vertex AI Text Embedding API
        self.embedding_model = "text-embedding-004"  # Latest Gemini embedding

    def generate_embeddings(self, paper: Dict) -> Dict:
        """Generate embeddings for paper text"""
        return {
            "title_embedding": self._embed(paper['title']),
            "abstract_embedding": self._embed(paper['abstract']),
            # Optional: chunk and embed full text
        }

    def _embed(self, text: str) -> List[float]:
        """Call Vertex AI embedding API"""
        from vertexai.language_models import TextEmbeddingModel

        model = TextEmbeddingModel.from_pretrained(self.embedding_model)
        embeddings = model.get_embeddings([text])
        return embeddings[0].values  # 768-dimensional vector
```

**3. Setup Vertex AI Vector Search**

```python
# Infrastructure: Create vector search index
from google.cloud import aiplatform

# Create index
index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
    display_name="research_papers_index",
    dimensions=768,  # Gemini embedding dimension
    approximate_neighbors_count=10,
    distance_measure_type="DOT_PRODUCT_DISTANCE"
)

# Deploy index to endpoint
endpoint = index.deploy(
    deployed_index_id="papers_endpoint",
    machine_type="e2-standard-2"
)
```

**4. Implement Hybrid Retrieval**

```python
# src/tools/retrieval.py - Phase 2 version
def hybrid_search(query: str, limit: int = 5, semantic_weight: float = 0.7) -> List[Dict]:
    """
    Hybrid search: Combine semantic and keyword search.

    Args:
        query: User question
        limit: Max papers to return
        semantic_weight: Weight for semantic score (0-1)
                        keyword_weight = 1 - semantic_weight
    """
    # 1. Semantic search via Vertex AI Vector Search
    query_embedding = embedding_model.embed(query)
    semantic_results = vector_search_endpoint.find_neighbors(
        query_embedding,
        num_neighbors=20  # Get more candidates
    )

    # 2. Keyword search in Firestore
    keyword_results = keyword_search(query, limit=20)

    # 3. Combine scores
    paper_scores = {}

    for paper in semantic_results:
        paper_id = paper['id']
        semantic_score = paper['distance']  # 0-1, higher = more similar
        paper_scores[paper_id] = {
            'semantic': semantic_score,
            'keyword': 0,
            'paper': paper
        }

    for paper in keyword_results:
        paper_id = paper['paper_id']
        if paper_id in paper_scores:
            paper_scores[paper_id]['keyword'] = paper['relevance_score']
        else:
            paper_scores[paper_id] = {
                'semantic': 0,
                'keyword': paper['relevance_score'],
                'paper': paper
            }

    # 4. Calculate hybrid score
    for paper_id, scores in paper_scores.items():
        # Normalize scores to 0-1
        sem_norm = scores['semantic']
        kw_norm = scores['keyword'] / max_keyword_score if max_keyword_score > 0 else 0

        # Weighted combination
        hybrid_score = (semantic_weight * sem_norm) +
                      ((1 - semantic_weight) * kw_norm)

        scores['hybrid'] = hybrid_score

    # 5. Sort and return top N
    ranked = sorted(paper_scores.items(),
                   key=lambda x: x[1]['hybrid'],
                   reverse=True)

    return [scores['paper'] for _, scores in ranked[:limit]]
```

#### Benefits of Hybrid Search:

| Query Type | Keyword | Semantic | Hybrid |
|------------|---------|----------|--------|
| "transformer architecture" | Good | Good | **Best** |
| "attention mechanism" | OK | **Best** | **Best** |
| "paper by Vaswani" | **Best** | Poor | **Best** |
| "self-attention vs RNN" | Poor | **Best** | **Best** |

**Cost**: ~$0.001 per embedding (text-embedding-004)
**Latency**: +50-100ms for embedding generation
**When to implement**: After Phase 1 succeeds, if retrieval quality needs improvement

---

### Phase 3 - Advanced Semantic Search 🚀
**Status**: Future enhancement
**When**: Days 4+ or post-hackathon
**Technology**: Advanced techniques

#### Possible Enhancements:

**1. Multi-Vector Retrieval**
```python
# Store multiple embedding types
embeddings = {
    "title": [...],           # Title embedding
    "abstract": [...],        # Abstract embedding
    "key_findings": [...],    # Just the findings
    "methods": [...],         # Just the methods
    "results": [...]          # Just the results
}

# Query-aware retrieval
def smart_search(query: str, query_type: str):
    if query_type == "methods":
        return search_in_embeddings("methods", query)
    elif query_type == "findings":
        return search_in_embeddings("key_findings", query)
    # etc.
```

**2. Re-ranking with Cross-Encoder**
```python
# After initial retrieval, re-rank with more expensive model
def rerank_results(query: str, candidates: List[Dict]) -> List[Dict]:
    """Use cross-encoder for precise relevance scoring"""

    # Vertex AI has built-in reranking
    from vertexai.language_models import RankingModel

    ranking_model = RankingModel.from_pretrained("ranking-gecko@001")

    reranked = ranking_model.rank(
        query=query,
        documents=[c['title'] + " " + c['abstract'] for c in candidates],
        top_n=5
    )

    return reranked
```

**3. Query Understanding**
```python
# Use LLM to expand/refine query before search
def expand_query(user_query: str) -> Dict:
    """
    Use LLM to understand and expand query.

    "papers about transformers" → {
        "main_query": "transformer architecture",
        "synonyms": ["attention mechanism", "self-attention"],
        "related_terms": ["BERT", "GPT", "encoder-decoder"],
        "intent": "find_methodology"
    }
    """
    expansion = llm.generate(f"Expand this search query: {user_query}")
    return parse_expansion(expansion)

def multi_query_search(user_query: str) -> List[Dict]:
    """Search with original query + expansions"""
    expanded = expand_query(user_query)

    # Search with multiple query variants
    results_main = hybrid_search(expanded['main_query'])
    results_synonyms = [hybrid_search(syn) for syn in expanded['synonyms']]

    # Merge and deduplicate
    return merge_results(results_main, results_synonyms)
```

**4. Metadata Filtering**
```python
# Add filters to semantic search
def filtered_search(
    query: str,
    filters: Dict = None
) -> List[Dict]:
    """
    Semantic search with metadata filters.

    filters = {
        "year_range": (2020, 2024),
        "authors": ["Vaswani"],
        "topics": ["NLP", "deep learning"],
        "min_citations": 100
    }
    """
    # Vertex AI supports metadata filtering
    results = vector_search_endpoint.find_neighbors(
        query_embedding,
        filter=build_filter_expression(filters)
    )
    return results
```

---

## Implementation Roadmap

### Phase 1 (Days 0-1) ✅ In Progress
- [x] Keyword search only
- [ ] Test on 5 questions
- [ ] Measure: Can we get ≥60% accuracy?

**Decision Point**: If keyword search gets ≥60% accuracy → Phase 1 complete, move to Phase 2
**If not**: Quick TF-IDF improvement, retry

---

### Phase 2 (Days 2-3) 🎯 Planned

#### Day 2 Morning (2 hours)
- [ ] Add embedding generation to ingestion pipeline
- [ ] Update Firestore schema with embeddings field
- [ ] Re-ingest 3 test papers with embeddings

#### Day 2 Afternoon (3 hours)
- [ ] Setup Vertex AI Vector Search index
- [ ] Deploy index to endpoint
- [ ] Implement semantic_search() function

#### Day 3 Morning (2 hours)
- [ ] Implement hybrid_search() combining keyword + semantic
- [ ] Tune semantic_weight parameter (try 0.5, 0.7, 0.9)
- [ ] Test on same 5 questions

#### Day 3 Afternoon (2 hours)
- [ ] Compare keyword vs hybrid performance
- [ ] Measure improvement in accuracy
- [ ] Update QA pipeline to use hybrid search

**Decision Point**: Does hybrid improve accuracy by ≥10%?
**If yes**: Keep hybrid, proceed to Phase 2.2 (alerting)
**If no**: Revert to keyword, focus on other features

---

### Phase 3 (Post-Hackathon) 🚀

Only implement if:
1. Phase 2 hybrid search works well
2. We have extra time before submission
3. Retrieval is identified as main bottleneck

Priority order:
1. Re-ranking (biggest accuracy boost)
2. Query expansion (better query understanding)
3. Multi-vector retrieval (more granular)
4. Metadata filtering (user feature)

---

## Cost Analysis

### Embedding Generation Costs

**Vertex AI Text Embedding API** (text-embedding-004):
- Cost: ~$0.000025 per 1,000 characters
- Our papers: ~40,000 chars avg = $0.001 per paper

**For 1,000 papers**:
- Embedding cost: $1.00
- Storage (Firestore): ~$0.20/GB (embeddings are ~3KB each)
- Total: **~$1.20 for 1,000 papers**

### Query Costs

**Semantic search** (Vertex AI Vector Search):
- Cost: $0.0001 per query
- 1,000 queries = $0.10

**Hybrid search** (keyword + semantic):
- Firestore read: $0.06 per 100K reads
- Vector search: $0.0001 per query
- Total: **~$0.0002 per query**

### Comparison

| Approach | Setup Cost | Per Query | 1K Queries |
|----------|-----------|-----------|------------|
| Keyword only | $0 | ~$0 | ~$0.60 (Firestore) |
| Semantic only | $1.20 | $0.0001 | $1.30 |
| Hybrid | $1.20 | $0.0002 | $1.40 |

**Conclusion**: Semantic search is cheap! (~$0.20 extra for 1,000 queries)

---

## Performance Comparison

### Expected Metrics

| Metric | Keyword | Hybrid | Improvement |
|--------|---------|--------|-------------|
| **Accuracy** | 60-70% | 75-85% | +15-20% |
| **Synonym handling** | Poor | Good | Major |
| **Complex queries** | Poor | Good | Major |
| **Exact name match** | Excellent | Good | -10% |
| **Latency** | 200ms | 250-300ms | +50-100ms |

### Real Example

**Query**: "papers about attention mechanisms"

**Keyword search** might find:
- ✅ "Attention Is All You Need" (has "attention" in title)
- ❌ Miss "Transformer architecture paper" (no keyword match)

**Semantic search** finds:
- ✅ "Attention Is All You Need"
- ✅ "BERT: Pre-training of Deep Bidirectional Transformers" (semantically related)
- ✅ "GPT-2: Language Models are Unsupervised Multitask Learners" (uses attention)

**Hybrid** combines both:
- ✅ Keyword ensures exact matches not missed
- ✅ Semantic catches related papers
- ✅ Best of both worlds

---

## Recommendation

### For Hackathon Timeline

**Phase 1 (Now)**:
- ✅ Implement keyword search
- ✅ Test thoroughly
- ✅ Prove the concept works

**Phase 2 (If ahead of schedule)**:
- 🎯 Add semantic search if:
  - Keyword search accuracy < 70%
  - We finish Phase 1.2 early
  - We want to differentiate from competitors

**Phase 3 (Mention only)**:
- 📝 Include in architecture diagram
- 📝 Mention in demo: "Can be extended with..."
- ❌ Don't implement (too risky for time)

### Decision Tree

```
Phase 1 complete?
├─ Yes: Keyword accuracy ≥70%?
│  ├─ Yes: → Phase 2.1 (knowledge graph) ✅
│  └─ No:  → Phase 2 semantic (improve retrieval) 🎯
└─ No: Fix keyword search first
```

---

## Summary

**Yes, we have plans for semantic search:**
- **Phase 2**: Hybrid search (keyword + Vertex AI Vector Search)
- **Phase 3**: Advanced techniques (re-ranking, query expansion)

**Current focus**: Phase 1 keyword search
**Next opportunity**: After Phase 1.2 complete, evaluate if needed

**Key insight**: Keyword search may be sufficient for Phase 1 Go/No-Go. Semantic search is an enhancement, not a requirement.

