# Research Intelligence Platform - Demo Mode Guide

## Overview

The demo mode provides a narrative-driven walkthrough of the Research Intelligence Platform, showing both the initial setup experience and ongoing value through time evolution and proactive alerts.

## Files Created

### 1. `src/services/frontend/demo.html`
Complete 3-tab demo interface with:
- **Tab 1: Setup & Configuration** - Folder upload and watch rules selection
- **Tab 2: Knowledge Graph Evolution** - Time slider showing graph evolution over 5 snapshots
- **Tab 3: Proactive Alerts** - Alert inbox with 5 sample notifications

### 2. `src/services/frontend/demo.js`
Demo-specific JavaScript with:
- Tab switching logic
- Fake progress animation (5-step process)
- Time slider with chronological snapshot management
- Alert inbox population
- Integration with shared `app.js` for graph rendering

## Access Points

After deployment, the platform will be accessible at two URLs:

- **Real Mode** (production): `https://<frontend-url>/` or `https://<frontend-url>/index.html`
- **Demo Mode**: `https://<frontend-url>/demo.html`

## Demo Flow

### Tab 1: Setup & Configuration

**Purpose**: Show the onboarding experience at time0

**User Actions**:
1. Click to select a folder (simulates selecting 49 PDFs)
2. Select watch rules from pre-configured templates:
   - 2 Natural Language Claim rules
   - 1 Keyword Matching rule
   - 1 Author Tracking rule
3. Enter email address
4. Click "Start Building Knowledge Graph"

**What Happens**:
- Fake progress animation runs (5 seconds total)
- Shows 5 progress steps:
  1. Extracting text from PDFs
  2. Detecting entities (titles, authors, findings)
  3. Building knowledge graph
  4. Setting up watch rules
  5. Finalizing platform
- Auto-transitions to Tab 2 when complete

### Tab 2: Knowledge Graph Evolution

**Purpose**: Demonstrate how the knowledge graph evolves over time

**Features**:
- Time slider with 5 discrete snapshots:
  - **Snapshot 1**: 30 papers (Jan 15, 2024) - "Initial corpus"
  - **Snapshot 2**: 35 papers (Feb 10, 2024) - "+5 new papers"
  - **Snapshot 3**: 40 papers (Mar 05, 2024) - "+5 new papers"
  - **Snapshot 4**: 45 papers (Apr 01, 2024) - "+5 new papers"
  - **Snapshot 5**: 49 papers (May 01, 2024) - "+4 new papers (current)"

**User Actions**:
1. Drag the time slider to different snapshots
2. Observe how the graph grows with new papers
3. New papers are highlighted with pulsing glow animation
4. Use standard graph controls (filter, fit to screen, freeze)

**Technical Details**:
- Papers are chronologically sorted by `published` date from Firestore
- Each snapshot shows first N papers + their relationships
- New papers (added in current snapshot vs previous) get special visual treatment
- Graph stats update dynamically (paper count, relationship count, new papers)

### Tab 3: Proactive Alerts

**Purpose**: Show the ongoing value of watch rules with real-time alerts

**Features**:
- Alert inbox with 5 sample alerts (3 new, 2 read)
- Each alert shows:
  - Badge (NEW or READ)
  - Timestamp
  - Rule that triggered the match
  - Paper title and authors
  - Match explanation with relevance score
  - Action buttons (View in Graph, Mark as Read)

**Sample Alerts**:
1. **Scaling Laws for Neural Language Models** (92% match)
2. **Training Compute-Optimal Large Language Models** (95% match)
3. **FlashAttention** (88% match)
4. **Reformer: The Efficient Transformer** (100% match)
5. **Emergent Abilities of Large Language Models** (91% match)

## Time Snapshot Implementation

Papers are sorted chronologically and divided into snapshots:

```javascript
const SNAPSHOT_CONFIG = [
    { date: 'January 15, 2024', count: 30, label: 'Initial corpus' },
    { date: 'February 10, 2024', count: 35, label: '+5 new papers' },
    { date: 'March 05, 2024', count: 40, label: '+5 new papers' },
    { date: 'April 01, 2024', count: 45, label: '+5 new papers' },
    { date: 'May 01, 2024', count: 49, label: '+4 new papers (current)' }
];
```

When the slider changes:
1. Papers are filtered to first N papers (based on snapshot)
2. Graph nodes and edges are filtered accordingly
3. New papers (added since previous snapshot) are identified
4. Visual animation highlights new papers with pulsing glow
5. Stats are updated (paper count, relationships, new papers)

## Visual Highlights

### New Paper Animation

New papers in each snapshot are highlighted with a pulsing glow effect:

```css
@keyframes pulseGlow {
    0%, 100% {
        filter: drop-shadow(0 0 8px rgba(255, 165, 0, 0.8));
    }
    50% {
        filter: drop-shadow(0 0 15px rgba(255, 165, 0, 1));
    }
}
```

This animation:
- Preserves the paper's taxonomy color (cs.AI = red, cs.LG = teal, etc.)
- Adds an orange halo to indicate "newness"
- Pulses at 2-second intervals for visual attention

### Demo Mode Badge

A fixed badge in the top-right corner clearly indicates demo mode:

```css
.demo-badge {
    position: fixed;
    top: 20px;
    right: 20px;
    background: #fbbf24;
    color: #78350f;
    ...
}
```

## Code Architecture

### Shared Code (`app.js`)
Already contains 1082 lines of shared functionality:
- Category color mapping
- Relationship color mapping
- Graph rendering with vis-network
- API calls to `/papers`, `/graph`, `/ask`
- Paper detail views
- Q&A interface

### Demo-Specific Code (`demo.js`)
New file with 600+ lines containing:
- Tab switching logic
- Setup page interactions
- Fake progress animation
- Time slider and snapshot management
- Alert inbox population
- Integration hooks to shared code

### No Backend Changes Required
The existing `server.py` uses Python's `SimpleHTTPRequestHandler`, which automatically serves both:
- `/` → `index.html` (real mode)
- `/demo.html` → `demo.html` (demo mode)

## Deployment

No special deployment needed! The demo files will be included in the next frontend deployment:

```bash
cd src/services/frontend
gcloud run deploy frontend \
    --source . \
    --region us-central1 \
    --project research-intel-agents \
    --allow-unauthenticated
```

After deployment:
- **Production**: `https://<frontend-url>/`
- **Demo**: `https://<frontend-url>/demo.html`

## Design Decisions

1. **No Real Computation**: All Tab 1 animations are pure frontend with `setTimeout` - no API calls
2. **Chronological Truth**: Snapshots use real paper dates from Firestore for temporal accuracy
3. **Pres preserved Taxonomy Colors**: New paper animation adds glow without changing category colors
4. **Fake Sample Data**: All alerts in Tab 3 are hardcoded samples for demo consistency
5. **Code Separation**: Demo-specific code isolated in `demo.js` to maintain discipline
6. **Shared Graph Rendering**: Reuses existing `app.js` graph code for maintainability

## Future Enhancements

Potential improvements for the demo:
1. Add more granular snapshots (weekly instead of monthly)
2. Implement real-time alert simulation with fade-in effects
3. Add "View in Graph" functionality to jump from alerts to specific papers
4. Include relationship evolution animation showing edges appearing
5. Add tooltip explaining the demo mode features
6. Create guided tour with callouts/arrows

## Testing Locally

To test the demo locally before deployment:

```bash
cd src/services/frontend
python server.py
```

Then visit:
- `http://localhost:8080/` - Real mode
- `http://localhost:8080/demo.html` - Demo mode
