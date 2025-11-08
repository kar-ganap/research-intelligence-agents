# Phase 2 (Walk) - Implementation Plan

**Status**: Planning
**Goal**: Add intelligence, trust mechanisms, and proactive features
**Motto**: "Make it smart and trustworthy"

---

## Overview

Building on Phase 1's foundation (PDF ingestion + Q&A with citations), Phase 2 adds:

1. **Knowledge Graph** - Detect relationships between papers
2. **Proactive Alerting** - Watch rules that notify users of new relevant papers
3. **Multi-Agent Intelligence** - Parallel evidence gathering with confidence scoring
4. **Trust Verification** - Citation verification and source evidence

---

## Phase 2.1: Knowledge Graph Foundation

**Objective**: Detect relationships between papers
**Time Budget**: 4 hours
**Priority**: Medium (Level 2)

### Components to Build

#### 1. RelationshipAgent
- **File**: `src/agents/ingestion/relationship_agent.py`
- **Purpose**: Compare papers and detect relationships
- **Relationship Types**:
  - `supports`: Similar findings, corroborating evidence
  - `contradicts`: Conflicting findings
  - `extends`: Builds upon previous work
  - `cites`: Direct citation reference

#### 2. Graph Operations Tool
- **File**: `src/tools/graph_operations.py`
- **Functions**:
  - `detect_relationship(paper_a, paper_b)` - Compare two papers
  - `get_existing_papers()` - Fetch corpus for comparison
  - `calculate_relationship_confidence()` - Score relationship strength

#### 3. Firestore Schema Extension
- **Collection**: `relationships`
- **Schema**:
```python
{
  'relationship_id': str,        # Auto-generated
  'source_paper_id': str,        # Paper A
  'target_paper_id': str,        # Paper B
  'relationship_type': str,      # supports/contradicts/extends/cites
  'confidence': float,           # 0.0-1.0
  'evidence': str,               # Brief explanation
  'detected_at': timestamp,
  'detected_by': str            # 'RelationshipAgent'
}
```

#### 4. Enhanced Ingestion Pipeline
- Modify `IngestionPipeline` to call `RelationshipAgent` after `IndexerAgent`
- Compare new paper against existing corpus
- Store detected relationships

### Success Criteria

| Criterion | Level | Pass Threshold |
|-----------|-------|----------------|
| Can detect "supports" relationship | 1 | Confidence > 0.6 |
| Can detect "contradicts" relationship | 1 | Confidence > 0.6 |
| Relationships stored in Firestore | 1 | ≥1 relationship exists |
| False positive rate | 2 | <30% incorrect |
| Processing time | 2 | <30s per pair |

### Test Cases

```python
TEST_PAIRS = [
    {
        "type": "supports",
        "paper_a_finding": "Transformer achieves 28.4 BLEU on WMT",
        "paper_b_finding": "Transformer achieves state-of-the-art translation",
        "expected": "supports"
    },
    {
        "type": "contradicts",
        "paper_a_finding": "MobileNetV2 outperforms MobileNetV1",
        "paper_b_finding": "MobileNetV1 shows better performance",
        "expected": "contradicts"
    },
    {
        "type": "unrelated",
        "paper_a": "GPT-3 language model",
        "paper_b": "MobileNetV2 architecture",
        "expected": "none"
    }
]
```

### Fallback Strategy

If relationship detection accuracy is poor (<50%):
- Simplify to just "cites" detection (from bibliography parsing)
- Skip semantic relationship detection
- Still have basic graph structure

---

## Phase 2.2: Proactive Alerting

**Objective**: Watch rules + matching + alert delivery
**Time Budget**: 4 hours
**Priority**: High (Level 1)

### Components to Build

#### 1. Watch Rules CRUD
- **File**: `src/storage/firestore_client.py` (extend)
- **Collection**: `watch_rules`
- **Schema**:
```python
{
  'rule_id': str,                # Auto-generated
  'user_id': str,                # Owner of rule
  'name': str,                   # "AI in Robotics"
  'keywords': List[str],         # ['diffusion', 'robotics', 'manipulation']
  'min_relevance_score': float,  # 0.0-1.0, default 0.7
  'notification_channels': List[str],  # ['email', 'firestore']
  'created_at': timestamp,
  'active': bool                 # Enable/disable
}
```

- **Functions**:
  - `create_watch_rule(rule_data)`
  - `get_watch_rules(user_id)`
  - `update_watch_rule(rule_id, updates)`
  - `delete_watch_rule(rule_id)`

#### 2. Matching Logic
- **File**: `src/tools/matching.py`
- **Functions**:
  - `match_paper_to_rules(paper, rules)` - Find matching rules
  - `calculate_match_score(paper, rule)` - Keyword overlap scoring

```python
def calculate_match_score(paper: dict, rule: dict) -> float:
    """
    Simple keyword overlap score

    Score = (matching keywords) / (total keywords)
    Weights: title (2x), key_finding (1x), authors (0.5x)
    """
    paper_text = f"{paper['title']} {paper['title']} {paper['key_finding']}".lower()
    matches = sum(1 for kw in rule['keywords'] if kw.lower() in paper_text)
    return matches / len(rule['keywords']) if rule['keywords'] else 0.0
```

#### 3. Alert Storage
- **Collection**: `alerts`
- **Schema**:
```python
{
  'alert_id': str,               # Auto-generated
  'user_id': str,
  'rule_id': str,                # Which rule triggered
  'paper_id': str,               # Matching paper
  'match_score': float,          # Relevance score
  'status': str,                 # 'pending', 'sent', 'failed'
  'created_at': timestamp,
  'sent_at': timestamp,          # When delivered
  'notification_channels': List[str]
}
```

#### 4. Alert Integration in Ingestion
- Modify `IngestionPipeline` to check watch rules after indexing
- Create alerts for matches
- Store in Firestore

### Success Criteria

| Criterion | Level | Pass Threshold |
|-----------|-------|----------------|
| Can create watch rule | 1 | Rule stored |
| Matching logic works | 1 | Score > 0.7 for relevant match |
| Alert stored in Firestore | 1 | Alert exists |
| End-to-end latency | 2 | <5 minutes from ingestion |

### Email Integration (Optional - Level 2)

If time permits, integrate SendGrid:
- **File**: `src/utils/email_sender.py`
- For MVP, alerts in Firestore are sufficient

### Test Scenario

```python
def test_proactive_alerting():
    # 1. Create watch rule
    rule = {
        'name': 'Transformer Research',
        'keywords': ['transformer', 'attention', 'architecture'],
        'user_id': 'test_user',
        'min_relevance_score': 0.6
    }
    firestore_client.create_watch_rule(rule)

    # 2. Ingest matching paper
    paper_path = 'tests/fixtures/attention_is_all_you_need.pdf'
    result = ingestion_pipeline.ingest_paper(paper_path)

    # 3. Check alerts created
    alerts = firestore_client.get_alerts(user_id='test_user')
    assert len(alerts) >= 1
    assert alerts[0]['match_score'] > 0.6

    return {'success': True}
```

### Fallback Strategy

- Skip email delivery (Level 2)
- Focus on alerts in Firestore (Level 1)
- Can add email later if time permits

---

## Phase 2.3: Multi-Agent Intelligence

**Objective**: Parallel evidence gathering + confidence scoring
**Time Budget**: 4 hours
**Priority**: High (Level 1 for confidence, Level 2 for parallel)

### Components to Build

#### 1. GraphQueryAgent (Optional - Level 2)
- **File**: `src/agents/qa/graph_query_agent.py`
- **Purpose**: Query knowledge graph for related papers
- Uses relationship data from Phase 2.1

#### 2. ContradictionAgent (Optional - Level 2)
- **File**: `src/agents/qa/contradiction_agent.py`
- **Purpose**: Find papers with conflicting findings
- Looks for "contradicts" relationships

#### 3. ConfidenceAgent (Required - Level 1)
- **File**: `src/agents/qa/confidence_agent.py`
- **Purpose**: Score answer confidence based on evidence quality
- **Inputs**: Retrieved papers, contradictions, graph context
- **Output**: Confidence score 0.0-1.0

```python
class ConfidenceAgent(BaseResearchAgent):
    def score_confidence(self,
                        question: str,
                        answer: str,
                        papers: List[Dict],
                        contradictions: List[Dict]) -> float:
        """
        Calculate confidence score

        Factors:
        - Number of supporting papers (more = higher)
        - Citation quality (exact match = higher)
        - Contradictions present (lower confidence)
        - Answer length and specificity

        Returns: 0.0-1.0
        """
        # LLM-based scoring with instruction
        pass
```

#### 4. Enhanced Q&A Pipeline
- **File**: `src/pipelines/qa_pipeline.py` (v2)
- Add confidence scoring to pipeline
- Optionally use parallel agents if time permits

```python
class QAPipeline:
    def ask(self, question: str, limit: int = 5) -> Dict:
        # Step 1: Retrieve papers (existing)
        papers = keyword_search(question, limit)

        # Step 2: Generate answer (existing)
        answer = self.answer_agent.answer(question, papers)

        # Step 3: Calculate confidence (NEW)
        confidence = self.confidence_agent.score_confidence(
            question=question,
            answer=answer,
            papers=papers,
            contradictions=[]  # From ContradictionAgent if built
        )

        return {
            'question': question,
            'answer': answer,
            'citations': self._extract_citations(answer),
            'confidence_score': confidence,  # NEW
            'papers': papers,
            'success': True
        }
```

### Success Criteria

| Criterion | Level | Pass Threshold |
|-----------|-------|----------------|
| ConfidenceAgent returns score 0-1 | 1 | Score in range |
| Confidence correlates with quality | 1 | High score → good answer |
| Answer includes confidence in output | 1 | Has confidence field |
| GraphQueryAgent returns related papers | 2 | ≥1 related paper |
| ContradictionAgent finds contradictions | 2 | Finds known conflict |

### Test Cases

```python
def test_confidence_scoring():
    # High confidence: Question with clear evidence
    q1 = "Who are the authors of the Transformer paper?"
    result1 = qa_pipeline.ask(q1)
    assert result1['confidence_score'] > 0.8  # Should be very confident

    # Medium confidence: Partial evidence
    q2 = "What is the performance of MobileNetV2?"
    result2 = qa_pipeline.ask(q2)
    assert 0.5 < result2['confidence_score'] < 0.8

    # Low confidence: No evidence
    q3 = "What is quantum entanglement?"
    result3 = qa_pipeline.ask(q3)
    assert result3['confidence_score'] < 0.5
    assert "don't have enough information" in result3['answer'].lower()

    return {'tests_passed': 3}
```

### Fallback Strategy

- **Must have**: ConfidenceAgent (Level 1)
- **Nice to have**: GraphQueryAgent, ContradictionAgent (Level 2)
- If time is short, skip parallel agents and focus on confidence scoring

---

## Phase 2.4: Trust Verification (Optional)

**Objective**: Verify citations and add source evidence
**Time Budget**: 3 hours
**Priority**: Low (Level 2-3)

### Decision Point

**Only proceed if**:
- Phase 2.1, 2.2, 2.3 all complete
- At least 6 hours remaining before Phase 3
- Core features working well

### Components

If built:
- **VerifierAgent**: Check citations against source papers
- **Evidence JSON**: Detailed tracing of claims to sources

### Fallback

- Skip this sub-phase
- Rely on confidence scores from Phase 2.3

---

## Phase 2 Success Criteria

### Go/No-Go Decision

```python
def phase_2_complete_decision():
    checks = {
        # Level 1 (Blockers)
        'alerts_working': test_alert_flow(),          # Must pass
        'confidence_working': test_confidence_scores(), # Must pass

        # Level 2 (Important)
        'relationships_detected': count_relationships() >= 1,  # Should pass
        'multi_agent_working': test_parallel_agents(),         # Should pass
    }

    # Must pass Level 1
    if not (checks['alerts_working'] and checks['confidence_working']):
        return False, "Phase 2 BLOCKED - Core features not working"

    # Warnings for Level 2
    if not checks['relationships_detected']:
        print("⚠️  No relationships detected, graph will be sparse")

    print("✅ PHASE 2 COMPLETE - Proceeding to Phase 3")
    return True
```

### Evidence Required

- [ ] At least 1 relationship detected and stored in Firestore
- [ ] Watch rule created and alert triggered end-to-end
- [ ] 3 questions answered with confidence scores
- [ ] Confidence scores make intuitive sense (high for good data, low for gaps)
- [ ] All components tested individually
- [ ] Integration test passes

---

## Implementation Order

### Recommended Sequence

**Day 1** (8 hours):
1. Phase 2.2: Proactive Alerting (4 hours) - **Highest priority**
   - Watch rules CRUD
   - Matching logic
   - Alert storage
   - Integration test

2. Phase 2.3: Confidence Scoring (4 hours) - **High priority**
   - ConfidenceAgent
   - Enhanced Q&A pipeline
   - Test with confidence scores

**Day 2** (4-6 hours):
3. Phase 2.1: Knowledge Graph (4 hours) - **Medium priority**
   - RelationshipAgent
   - Graph operations
   - Test relationship detection

4. Phase 2.4: Trust Verification (0-2 hours) - **Optional**
   - Only if ahead of schedule

### Rationale

- **Proactive Alerting first**: Most visible feature, high hackathon value
- **Confidence scoring second**: Adds intelligence without complex infrastructure
- **Knowledge graph third**: Nice to have, but can skip if time-constrained
- **Verification last**: Lowest priority, skip if needed

---

## Next Steps

1. Review this plan
2. Confirm priorities with user
3. Begin Phase 2.2 implementation
4. Track progress with TodoWrite tool
