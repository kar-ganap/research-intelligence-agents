# Knowledge Graph Design

**Status**: Phase 2.1 (MVP) - Papers as nodes, semantic relationships
**Last Updated**: 2025-10-28

---

## Phase 2.1 MVP Design

### Nodes
- **Type**: Papers only
- **Source**: Existing `papers` collection in Firestore
- **Properties**: title, authors, key_finding, arxiv_id, paper_id

### Edges
- **Storage**: New `relationships` collection in Firestore
- **Types**:
  - `supports`: Similar findings, corroborating evidence
  - `contradicts`: Conflicting findings
  - `extends`: Builds upon previous work

### Edge Creation Rules

```python
# An edge exists if:
# 1. LLM detects semantic relationship
# 2. Confidence meets threshold:
#    - supports: >= 0.7
#    - contradicts: >= 0.8 (more conservative)
#    - extends: >= 0.7
# 3. Evidence is provided by LLM
```

### Directionality
- `supports`: Bidirectional (if A supports B, B supports A)
- `contradicts`: Bidirectional (symmetric relationship)
- `extends`: Directional (A extends B's work)

### Schema

**Relationships Collection**:
```python
{
  'relationship_id': str,           # Auto-generated
  'source_paper_id': str,           # From paper
  'target_paper_id': str,           # To paper
  'relationship_type': str,         # 'supports' | 'contradicts' | 'extends'
  'confidence': float,              # 0.0-1.0
  'evidence': str,                  # LLM explanation (1-2 sentences)
  'detected_by': str,               # 'RelationshipAgent'
  'detected_at': timestamp
}
```

### Detection Process

When ingesting a new paper:
1. Fetch all existing papers from Firestore
2. Compare new paper against each existing paper using RelationshipAgent
3. For each comparison where confidence >= threshold:
   - Create relationship document in Firestore
   - Log the relationship

**Complexity**: O(N) comparisons for N existing papers

---

## Future Extensions (Phase 3+)

### Extension 1: Citation-Based Edges

**Motivation**: Objective, verifiable relationships from bibliography

**Implementation**:
- Parse PDF references section
- Extract cited paper identifiers (arXiv IDs, DOIs)
- Create `cites` edges with confidence 1.0

**Challenges**:
- Bibliography parsing is error-prone
- Need to match citations to papers in our corpus
- Different citation formats (BibTeX, IEEE, etc.)

**Priority**: Phase 3 (nice to have)

---

### Extension 2: Concept/Topic Nodes

**Motivation**: Enable topic-based exploration, abstract from individual papers

**Design**:
```python
# Two node types:
nodes = {
  'papers': [...],      # Individual papers
  'concepts': [...]     # Research concepts/topics
}

# Three edge types:
edges = {
  'paper_to_concept': [...],    # Paper discusses concept
  'concept_to_concept': [...],  # Concept relates to concept
  'paper_to_paper': [...]       # Existing semantic relationships
}
```

**Concept Node Schema**:
```python
{
  'concept_id': str,
  'name': str,                  # "Attention Mechanisms"
  'description': str,           # Brief description
  'related_keywords': List[str],
  'paper_count': int           # How many papers discuss this
}
```

**Extraction Process**:
- LLM extracts key concepts from each paper
- Cluster similar concepts (embedding-based)
- Create concept nodes for frequently-occurring topics

**Challenges**:
- Concept extraction accuracy
- Concept deduplication/merging
- Maintaining concept consistency

**Priority**: Phase 3 (if time permits)

---

### Extension 3: Topic Similarity Edges

**Motivation**: "Show me related papers" without strong semantic relationship

**Implementation**:
- Compute embeddings for each paper (title + abstract + key_finding)
- Calculate cosine similarity between all pairs
- Create `related_to` edges where similarity > 0.6

**Edge Schema**:
```python
{
  'relationship_type': 'related_to',
  'similarity_score': float,     # Cosine similarity
  'detected_by': 'EmbeddingModel'
}
```

**Pros**:
- Fast to compute (batch embeddings)
- Objective metric
- Enables exploration

**Cons**:
- Can create many edges (O(N²) pairs)
- May be noisy
- Need to set good threshold

**Priority**: Phase 3 (optimization)

---

### Extension 4: Temporal Edges

**Motivation**: Track how research evolves over time

**Edge Type**: `precedes`
- Paper A published before Paper B
- Both papers on same topic
- Enables timeline visualization

**Use Case**:
- "Show me the evolution of Transformer research"
- Temporal graph visualization

**Priority**: Phase 3 (visualization feature)

---

### Extension 5: Author/Institution Nodes

**Motivation**: Track collaborations, influential researchers

**Design**:
```python
# Three node types:
nodes = {
  'papers': [...],
  'authors': [...],
  'institutions': [...]
}

# New edge types:
edges = {
  'authored_by': [...],        # Paper → Author
  'affiliated_with': [...],    # Author → Institution
  'collaborated_with': [...]   # Author → Author (co-authorship)
}
```

**Use Cases**:
- "What has this author published?"
- "Show collaboration networks"
- "Which institutions work on this topic?"

**Priority**: Phase 3+ (advanced feature)

---

### Extension 6: Evidence Strength Weighting

**Motivation**: Not all relationships are equally strong

**Enhancement to Existing Edges**:
```python
{
  # Existing fields...
  'evidence_strength': str,  # 'weak' | 'moderate' | 'strong'
  'evidence_count': int,     # How many pieces of evidence
  'citations_count': int     # How many times this relationship is cited
}
```

**Heuristics**:
- Strong: Confidence > 0.9, multiple papers support it
- Moderate: Confidence 0.7-0.9
- Weak: Confidence 0.6-0.7 (might filter these out)

**Priority**: Phase 3 (refinement)

---

### Extension 7: Dynamic Graph Updates

**Motivation**: Relationships may change as corpus grows

**Features**:
- Re-evaluate relationships periodically
- Update confidence scores based on new evidence
- Archive outdated relationships

**Challenges**:
- Computational cost (re-running comparisons)
- Version control for graph state
- Avoiding thrashing

**Priority**: Phase 3+ (advanced)

---

## Design Principles

### For MVP (Phase 2.1)
1. **Simplicity**: Papers as nodes, semantic edges only
2. **Validation**: Test on small corpus, verify accuracy
3. **Iterative**: Build, measure, learn

### For Extensions
1. **Add value incrementally**: Each extension should solve a real user need
2. **Measure impact**: Does it improve answer quality? User experience?
3. **Manage complexity**: Don't add features that make system fragile

---

## Decision Log

### 2025-10-28: Phase 2.1 Design
- **Decision**: Papers-only nodes, semantic relationships
- **Rationale**: Simplest to implement and validate, clear provenance
- **Deferred**: Citation parsing, concept nodes, topic similarity
- **Next review**: After Phase 2.1 testing
