# Pipeline Orchestration Analysis
**SequentialAgent vs. Simple Python Orchestration**

Date: 2025-10-28

---

## The Question

What specific state management features would we forego by using simple Python orchestration instead of ADK's SequentialAgent for our ingestion pipeline?

---

## SequentialAgent State Management Features

### 1. **Shared InvocationContext**

**What it is:**
- All sub-agents receive the same `InvocationContext` object
- Enables automatic state sharing across the agent chain
- Single source of truth for session data

**How it works:**
```python
# SequentialAgent internally does this:
for sub_agent in self.sub_agents:
    result = await sub_agent.run_async(context)  # Same context!
```

### 2. **Four State Namespaces**

| Namespace | Scope | Persistence | Use Case |
|-----------|-------|-------------|----------|
| `state['key']` | Session | With persistent services | User preferences, conversation history |
| `user:key` | All sessions for one user | Persistent (DB/Vertex) | User profile, settings |
| `app:key` | Global (all users) | Persistent (DB/Vertex) | App config, shared data |
| `temp:key` | **Single invocation only** | Never persists | Pipeline intermediates |

### 3. **Automatic State Passing via `output_key`**

**Pattern:**
```python
agent1 = LlmAgent(
    name="Agent1",
    instruction="Generate code",
    output_key="generated_code"  # Writes to state['generated_code']
)

agent2 = LlmAgent(
    name="Agent2",
    instruction="Review this code: {generated_code}",  # Reads from state!
    output_key="review_comments"
)

pipeline = SequentialAgent(
    name="Pipeline",
    sub_agents=[agent1, agent2]
)
```

**Magic:** The `{generated_code}` placeholder automatically gets replaced with the value from `state['generated_code']` - no manual data passing!

### 4. **EventActions for Complex Updates**

**Beyond simple text:**
```python
# In agent callback or tool
context.state['extracted_entities'] = {
    'title': 'Paper Title',
    'authors': ['Author 1', 'Author 2'],
    'key_finding': 'Main result'
}

# Next agent automatically sees this
```

### 5. **State Persistence Across Invocations**

With `DatabaseSessionService` or `VertexAiSessionService`:
```python
# Session 1
state['processed_papers'] = ['paper1', 'paper2']

# Session 2 (same user, different invocation)
# state['processed_papers'] still has ['paper1', 'paper2']
```

### 6. **Tracing and Observability**

ADK automatically tracks:
- Which agent wrote which state key
- When state was modified
- State evolution through the pipeline
- Built-in debugging/logging

---

## Our Current Approach (Simple Python)

### What We're Doing

```python
class IngestionPipeline:
    def ingest_paper(self, pdf_path: str) -> Dict:
        # Step 1: PDF extraction
        pdf_result = read_pdf(pdf_path)
        paper_text = pdf_result['text']

        # Step 2: Entity extraction
        entities = entity_agent.extract(paper_text)

        # Step 3: Indexing
        index_result = indexer_agent.index(entities, pdf_path)

        return index_result
```

**Data passing:** Explicit Python variables

---

## Feature-by-Feature Comparison

### 1. **Automatic State Passing** ❌ Missing

**With SequentialAgent:**
```python
agent1.output_key = "entities"
agent2.instruction = "Store these entities: {entities}"  # Auto-injected!
```

**Our approach:**
```python
entities = agent1.extract(text)
result = agent2.index(entities)  # Manual passing
```

**Impact:**
- ✅ **Not a problem for us** - we only have 3 steps, manual passing is clear
- ✅ **Actually more explicit** - easier to debug
- ❌ **Would matter with 10+ agents** - manual passing becomes error-prone

---

### 2. **Temp State Namespace** ❌ Missing

**With SequentialAgent:**
```python
# Agent 1 writes intermediate data
context.state['temp:pdf_metadata'] = {...}

# Agent 2 reads it
metadata = context.state.get('temp:pdf_metadata')

# After pipeline completes, temp: data auto-deleted
```

**Our approach:**
```python
# No temp: namespace
# All variables are function-local
pdf_result = read_pdf(...)  # Local variable
entities = extract(pdf_result['text'])  # Local variable
```

**Impact:**
- ✅ **Not needed** - we're not persisting sessions between runs
- ✅ **Python scope handles this** - local variables auto-cleanup
- ❌ **Would matter for**: Multi-turn conversations, long-running sessions

---

### 3. **Session Persistence** ❌ Missing

**With SequentialAgent + DatabaseSessionService:**
```python
# Invocation 1
state['processed_papers'] = ['paper1']

# Invocation 2 (hours later, same user)
state['processed_papers']  # Still has ['paper1']
state['processed_papers'].append('paper2')
```

**Our approach:**
```python
# Each invocation is independent
# No memory between runs
pipeline.ingest_paper('paper1.pdf')  # Run 1
pipeline.ingest_paper('paper2.pdf')  # Run 2 - doesn't know about Run 1
```

**Impact:**
- ✅ **Good for Phase 1** - each paper ingestion is independent
- ❌ **Missing feature**: "Don't re-process papers I've already done"
- ⚠️ **Workaround exists**: Query Firestore before processing (we do this in IndexerAgent!)

---

### 4. **User/App-Level State** ❌ Missing

**With SequentialAgent:**
```python
# Store user preferences
context.state['user:preferred_fields'] = ['ML', 'NLP']

# Store app config
context.state['app:processing_quota'] = 100
```

**Our approach:**
```python
# No concept of user state
# No concept of app state
# Everything is per-invocation
```

**Impact:**
- ✅ **Not needed for Phase 1** - batch processing, no users yet
- ❌ **Would need for Phase 2+**: User-specific alerting, personalization
- ⚠️ **Alternative**: Store in Firestore, implement ourselves

---

### 5. **Automatic Tracing/Observability** ❌ Missing

**With SequentialAgent:**
```python
# ADK automatically logs:
# - Agent started: EntityAgent
# - State updated: entities = {...}
# - Agent completed: EntityAgent
# - Agent started: IndexerAgent
# - State read: entities
# - Agent completed: IndexerAgent
```

**Our approach:**
```python
# We add manual logging:
logger.info("Step 1/3: Extracting text")
logger.info("Step 2/3: Extracting entities")
logger.info("Step 3/3: Indexing")
```

**Impact:**
- ✅ **We can add logging ourselves** - not hard
- ❌ **Not standardized** - each developer logs differently
- ❌ **No built-in debugging UI** - ADK has observability tools

---

### 6. **Error Handling & Rollback** ⚠️ Unknown in SequentialAgent

**With SequentialAgent:**
```python
# Documentation doesn't specify error behavior!
# Questions:
# - Does it stop on first error?
# - Does it rollback state changes?
# - Can we retry failed agents?
```

**Our approach:**
```python
try:
    pdf_result = read_pdf(path)
except Exception as e:
    return {"success": False, "error": str(e)}

try:
    entities = entity_agent.extract(text)
except Exception as e:
    return {"success": False, "error": str(e), "step": "extraction"}

# Explicit error handling per step
```

**Impact:**
- ✅ **Our approach is clearer** - explicit error handling
- ✅ **We know exactly what happens** - no magic
- ❌ **SequentialAgent might have smart retry logic** - but docs don't say

---

### 7. **Dynamic Placeholder Injection** ❌ Missing

**With SequentialAgent:**
```python
agent.instruction = """
Review this code: {generated_code}
Check against these standards: {coding_standards}
Previous feedback: {review_comments}
"""
# All placeholders auto-filled from state!
```

**Our approach:**
```python
# Have to manually pass data
instruction = f"""
Review this code: {code}
Check against these standards: {standards}
"""
```

**Impact:**
- ✅ **Works fine for 3 agents** - not many placeholders
- ❌ **Would be painful with many agents** - lots of string formatting
- ❌ **Less declarative** - more imperative code

---

## Specific Impact on Our 3-Agent Pipeline

### Agent 1: PDF Reader (Tool)
**SequentialAgent way:**
```python
# Would be a tool called by an LlmAgent
loader_agent = LlmAgent(
    name="LoaderAgent",
    instruction="Load the PDF from {pdf_path} using read_pdf tool",
    tools=[read_pdf],
    output_key="pdf_text"
)
```

**Our way:**
```python
pdf_result = read_pdf(pdf_path)
paper_text = pdf_result['text']
```

**Difference:**
- ❌ **We lose**: Automatic state storage in `state['pdf_text']`
- ✅ **We gain**: Simpler, direct function call
- ⚠️ **Issue**: PDF reader isn't an agent, it's a tool - awkward fit for SequentialAgent

---

### Agent 2: EntityAgent (LLM Agent)
**SequentialAgent way:**
```python
entity_agent = LlmAgent(
    name="EntityAgent",
    instruction="Extract title, authors, key finding from: {pdf_text}",
    output_key="entities"
)
```

**Our way:**
```python
entities = entity_agent.extract(paper_text)
```

**Difference:**
- ❌ **We lose**: Auto-injection of `{pdf_text}` placeholder
- ❌ **We lose**: Automatic state storage
- ✅ **We gain**: Direct control over extraction logic
- ⚠️ **Current implementation**: EntityAgent uses Runner internally, already ADK-native!

---

### Agent 3: IndexerAgent (Storage Agent)
**SequentialAgent way:**
```python
# Problem: IndexerAgent isn't an LLM agent!
# It's just storage logic
# Would need to wrap it as a tool

indexer_tool = def index_to_firestore(entities: dict) -> str:
    indexer = IndexerAgent()
    result = indexer.index(entities)
    return result['paper_id']

wrapper_agent = LlmAgent(
    name="IndexerAgent",
    instruction="Call index_to_firestore with {entities}",
    tools=[indexer_tool],
    output_key="paper_id"
)
```

**Our way:**
```python
index_result = indexer_agent.index(entities, pdf_path)
```

**Difference:**
- ❌ **We lose**: Automatic state management
- ✅ **We gain**: Direct, simple function call
- ✅ **We avoid**: Awkward LLM wrapper around non-LLM logic

---

## Summary: What We're Missing

| Feature | Impact | Needed for Phase 1? | Workaround Available? |
|---------|--------|---------------------|----------------------|
| **Auto state passing** | Low | ❌ No | ✅ Manual passing is fine |
| **Temp namespace** | Low | ❌ No | ✅ Local variables work |
| **Session persistence** | Low | ❌ No | ✅ Firestore duplicate check |
| **User/app state** | Low | ❌ No | ⚠️ Needed for Phase 2+ |
| **Auto tracing** | Medium | ⚠️ Nice-to-have | ✅ Manual logging works |
| **Placeholder injection** | Low | ❌ No | ✅ String formatting works |
| **Built-in observability** | Medium | ⚠️ Nice-to-have | ⚠️ Build ourselves |

---

## The Core Problem: Architectural Mismatch

### SequentialAgent Expects:
```
LlmAgent → LlmAgent → LlmAgent
   ↓          ↓          ↓
 state     state      state
```

### Our Pipeline Is:
```
Tool (read_pdf) → LlmAgent (entities) → Storage (indexer)
      ↓                  ↓                    ↓
  python var         python var          python var
```

**Issue:** SequentialAgent is designed for **LLM agent chains**, not **mixed tool/agent/storage workflows**.

---

## Recommendation

### Phase 1 (Crawl): ✅ **Use Simple Python Orchestration**

**Why:**
1. **Simpler** - 50 lines vs. 200 lines
2. **More explicit** - clear data flow
3. **Better error handling** - we control it
4. **No architectural mismatch** - tools and storage fit naturally
5. **Faster to debug** - no ADK magic to understand

**What we lose:**
- Auto state management (don't need it - independent ingestions)
- Tracing (can add logging ourselves)
- State persistence (don't need it - batch processing)

### Phase 2 (Walk): 🤔 **Reconsider SequentialAgent**

**When it makes sense:**
1. If we add **multi-agent intelligence** (multiple LLM agents deliberating)
2. If we need **session persistence** (user conversations)
3. If we have **complex state** (10+ pieces of data flowing through)
4. If we want **ADK's built-in observability**

**For ingestion specifically:** Probably still use simple orchestration, but use SequentialAgent for **query pipeline**:

```python
# Query pipeline (good fit for SequentialAgent)
query_pipeline = SequentialAgent(
    sub_agents=[
        retriever_agent,     # LLM: understand query
        search_agent,        # LLM: search papers
        synthesis_agent,     # LLM: synthesize answer
        citation_agent       # LLM: add citations
    ]
)
```

---

## Conclusion

**For our 3-agent ingestion pipeline:**

❌ **Don't use SequentialAgent** because:
- Architectural mismatch (tool + LLM + storage)
- Over-engineering for simple linear flow
- State management features aren't needed
- Simpler code is better code for Phase 1

✅ **Do use SequentialAgent later** for:
- Q&A pipeline (all LLM agents)
- Multi-agent deliberation (Phase 2)
- Complex workflows with branching logic

**The features we're missing aren't needed for Phase 1 success.**

