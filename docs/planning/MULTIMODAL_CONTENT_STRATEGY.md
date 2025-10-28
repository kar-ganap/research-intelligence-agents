# Multimodal Content Strategy
**Research Intelligence Platform**

Last Updated: 2025-10-28

---

## Problem Statement

Research papers contain rich multimodal content beyond plain text:
- **Tables**: Experimental results, comparisons, datasets
- **Figures**: Architecture diagrams, plots, visualizations
- **Equations**: Mathematical formulations
- **Videos**: Supplementary materials (common in biology/medicine)
- **Code**: Algorithms, implementations

**Current limitation**: Our Phase 1 implementation only extracts plain text, losing critical information.

---

## Current State (Phase 1 - Crawl)

### What We Extract
```python
# src/tools/pdf_reader.py uses PyMuPDF
text = page.get_text()  # Plain text only
```

✅ **Captures**: Body text, abstracts, references
❌ **Loses**: Table structure, images, equations (as images), videos

### Impact Example: "Attention Is All You Need" Paper

**Table 1** (Performance Results):
```
Original: Beautiful structured table with columns
Extracted: "Table 1: Maximum path lengths, per-layer complexity...
            Layer Type Complexity per Layer Sequential..."

→ Structure lost, hard to parse programmatically
```

**Figure 1** (Transformer Architecture):
```
Original: Detailed architecture diagram
Extracted: [Nothing - completely skipped]

→ Critical visual information lost
```

---

## Strategy by Phase

### Phase 1 (Crawl) - Current ✅
**Decision**: **Accept text-only limitation**

**Rationale**:
- Get basic pipeline working first
- Text extraction is reliable and fast
- Most key findings ARE in text (abstract, intro, conclusion)
- Tables/figures are secondary for initial proof-of-concept

**Acceptable Loss**:
- ~30% of paper information (tables, figures)
- Researchers can still find relevant papers
- Just won't have perfect extraction

**Trade-off**: Speed > Completeness

---

### Phase 2 (Walk) - Recommended Enhancements 🎯

#### 2.1: Table Extraction

**Library**: `pdfplumber` or `camelot-py`

```python
# Enhanced PDF reader with table support
import pdfplumber

def read_pdf_with_tables(file_path: str) -> dict:
    """Extract text AND structured tables"""
    with pdfplumber.open(file_path) as pdf:
        text = ""
        tables = []

        for page in pdf.pages:
            text += page.extract_text()

            # Extract tables as structured data
            page_tables = page.extract_tables()
            for table in page_tables:
                tables.append({
                    "page": page.page_number,
                    "data": table,  # 2D array
                    "markdown": _table_to_markdown(table)
                })

    return {"text": text, "tables": tables}
```

**Why tables matter**:
- Experimental results (accuracy, F1, BLEU scores)
- Dataset comparisons
- Ablation studies
- Performance benchmarks

**Use case**: "Find papers where method X outperforms baseline by >5%"
→ Requires parsing tables, not just text

---

#### 2.2: Image/Figure Extraction

**Library**: `PyMuPDF` (can extract images) + `Gemini Vision API`

```python
import fitz  # PyMuPDF

def extract_figures(pdf_path: str) -> List[Dict]:
    """Extract figures and use Gemini Vision to describe them"""
    doc = fitz.open(pdf_path)
    figures = []

    for page_num, page in enumerate(doc):
        # Extract images
        image_list = page.get_images()

        for img_index, img in enumerate(image_list):
            # Get image bytes
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            # Use Gemini Vision to describe
            description = gemini_vision_api.describe_image(image_bytes)

            figures.append({
                "page": page_num + 1,
                "index": img_index,
                "description": description,
                "type": "figure",  # vs. "equation", "diagram"
                "storage_path": f"gs://papers/{paper_id}/fig_{page_num}_{img_index}.png"
            })

    return figures
```

**Why figures matter**:
- Architecture diagrams (deep learning papers)
- Result plots (shows trends, not just final numbers)
- Qualitative examples (image generation, NLP outputs)

**Use case**: "Show me papers with transformer architectures"
→ Can search figure descriptions, not just text mentions

---

#### 2.3: Mathematical Equations

**Two approaches**:

**Option A**: Extract as images + OCR with Gemini Vision
```python
# Extract equation images and convert to LaTeX
equation_latex = gemini_vision_api.image_to_latex(equation_image)
```

**Option B**: Use specialized equation parser
```python
from pix2tex import Pix2Tex  # LaTeX OCR

model = Pix2Tex()
latex = model(equation_image)
```

**Why equations matter**:
- Core methodology understanding
- Reproducibility
- Comparison of approaches

**Storage**:
```python
{
    "equations": [
        {
            "page": 3,
            "latex": "\\mathcal{L} = \\sum_{i=1}^{N} -\\log P(y_i|x_i)",
            "description": "Loss function definition",
            "type": "loss_function"
        }
    ]
}
```

---

#### 2.4: Supplementary Videos (Life Sciences)

**Challenge**: Videos are NOT in PDFs - they're on journal websites

**Strategy**:
1. Extract DOI/URL from paper
2. Parse journal website for supplementary materials
3. Download video files
4. Use Gemini video understanding (if available) or frame sampling

```python
def extract_supplementary_materials(paper_metadata: dict) -> List[str]:
    """Scrape journal website for supplementary materials"""
    doi = paper_metadata.get("doi")

    # Map DOI to journal website
    if "nature.com" in doi:
        return scrape_nature_supplementary(doi)
    elif "science.org" in doi:
        return scrape_science_supplementary(doi)
    # etc.

    return []

def analyze_video(video_path: str) -> dict:
    """Extract key frames and generate description"""
    # Sample frames at intervals
    frames = extract_key_frames(video_path, interval=5)

    # Use Gemini Vision on frames
    descriptions = [gemini_vision_api.describe_image(frame) for frame in frames]

    return {
        "type": "video",
        "duration": get_duration(video_path),
        "key_frames": len(frames),
        "summary": " ".join(descriptions)
    }
```

---

### Phase 3 (Run) - Advanced Features 🚀

#### 3.1: Code Extraction

Many papers include pseudocode or link to GitHub repos.

```python
def extract_code_snippets(paper_text: str, paper_metadata: dict) -> List[dict]:
    """Extract code from paper and linked repos"""

    # 1. Find GitHub URLs in text/references
    github_urls = re.findall(r'https://github\.com/[\w-]+/[\w-]+', paper_text)

    # 2. Clone repos and index code
    code_snippets = []
    for url in github_urls:
        repo_code = clone_and_index(url)
        code_snippets.append({
            "source": url,
            "language": detect_language(repo_code),
            "files": list_files(repo_code)
        })

    return code_snippets
```

#### 3.2: Interactive Data Tables

Store tables in BigQuery for querying:

```sql
-- Find papers where accuracy > 90%
SELECT paper_id, table_name, accuracy_value
FROM papers.tables
WHERE metric_name = 'accuracy'
  AND value > 0.90
ORDER BY value DESC
```

---

## Recommended Implementation Timeline

### Now (Phase 1) ✅
- [x] Text extraction only
- [x] Accept limitation
- [x] Focus on end-to-end pipeline

### Week 2 (Phase 2) 🎯
- [ ] Add table extraction with `pdfplumber`
- [ ] Store tables as structured JSON in Firestore
- [ ] Update EntityAgent to extract "key tables"

### Week 3 (Phase 2 continued)
- [ ] Add figure extraction with PyMuPDF
- [ ] Use Gemini Vision API to describe figures
- [ ] Store figure descriptions in Firestore

### Week 4 (Phase 3)
- [ ] Add equation extraction
- [ ] Add supplementary material scraping
- [ ] Build multimodal search

---

## Data Model Evolution

### Phase 1 (Current)
```javascript
// Firestore: papers/{paper_id}
{
  title: string,
  authors: array,
  key_finding: string,
  // text implicit in full_text field
}
```

### Phase 2 (With Tables/Figures)
```javascript
// Firestore: papers/{paper_id}
{
  title: string,
  authors: array,
  key_finding: string,

  // NEW: Structured content
  tables: [
    {
      page: 5,
      caption: "Performance comparison",
      data: [[...], [...]],  // 2D array
      markdown: "| Model | Acc | F1 |\n|---|---|---|"
    }
  ],

  figures: [
    {
      page: 3,
      caption: "Transformer architecture",
      description: "Neural network diagram showing encoder-decoder...",
      storage_path: "gs://papers/abc123/fig_3_0.png"
    }
  ]
}
```

### Phase 3 (Multimodal Search)
```javascript
{
  // ... existing fields ...

  equations: [
    {page: 4, latex: "...", description: "Loss function"}
  ],

  code_repos: [
    {url: "github.com/...", language: "Python", stars: 1234}
  ],

  videos: [
    {
      url: "nature.com/supplementary/...",
      duration: 120,
      key_frames: ["gs://...frame1.png", ...],
      summary: "Microscopy video showing..."
    }
  ]
}
```

---

## Cost-Benefit Analysis

### Text Only (Current)
- **Cost**: $0 per paper (PyMuPDF is free)
- **Latency**: ~2s per paper
- **Coverage**: ~70% of paper content
- **Quality**: Good for finding papers, poor for deep analysis

### + Tables (Phase 2.1)
- **Cost**: $0 per paper (pdfplumber is free)
- **Latency**: +1s per paper
- **Coverage**: ~85% of paper content
- **Quality**: Can answer quantitative questions

### + Figures (Phase 2.2)
- **Cost**: ~$0.01 per paper (Gemini Vision: ~5 images × $0.002)
- **Latency**: +5s per paper
- **Coverage**: ~95% of paper content
- **Quality**: Can understand methodologies visually

### + Videos (Phase 3)
- **Cost**: ~$0.10 per paper (video analysis, frame sampling)
- **Latency**: +30s per paper
- **Coverage**: ~98% of paper content
- **Quality**: Full multimedia understanding

---

## Decision Framework

### Should we add feature X?

1. **Is it blocking Phase 1 Go/No-Go?**
   - Tables: ❌ No (can find papers with text only)
   - Figures: ❌ No (key findings are in text)
   → Defer to Phase 2

2. **Does it differentiate us in hackathon?**
   - Text only: Standard
   - + Tables: Good differentiation
   - + Figures: Strong differentiation
   - + Videos: Unique (but high risk)
   → Prioritize tables + figures in Phase 2

3. **What's the implementation risk?**
   - Tables: Low (pdfplumber is mature)
   - Figures: Medium (Gemini Vision API might have rate limits)
   - Videos: High (scraping, parsing, complex)
   → Start with tables (low risk), add figures if time permits

---

## Recommendation for This Week

### ✅ Phase 1 (Days 0-1): Proceed with text-only
**Why**: Proves the concept, gets working pipeline

### 🎯 Phase 2 (Days 2-3): Add tables
**Why**:
- Low risk, high value
- Experimental results are in tables
- Differentiates our solution
- Still achievable in hackathon timeframe

### ⏸️ Phase 3 (Day 4): Figures only if ahead of schedule
**Why**:
- Nice-to-have, not must-have
- Can demo without it
- Higher complexity

### ❌ Don't attempt: Videos
**Why**: Too complex for hackathon timeframe

---

## For Life Sciences Researchers Specifically

If targeting life sciences (biology, medicine):
- **Videos are valuable** (microscopy, procedure demonstrations)
- **But**: Implement as Phase 3 "future work"
- **Mention in demo**: "We can extend to analyze supplementary videos using Gemini's video understanding capabilities"
- **Show architecture**: Include video processing block in diagrams (even if not implemented)

This shows **vision** without **risk**.

---

## Summary

| Content Type | Phase 1 | Phase 2 | Phase 3 | Priority |
|--------------|---------|---------|---------|----------|
| **Text** | ✅ | ✅ | ✅ | Must-have |
| **Tables** | ❌ | ✅ | ✅ | Should-have |
| **Figures** | ❌ | 🎯 | ✅ | Nice-to-have |
| **Equations** | ❌ | ❌ | ✅ | Nice-to-have |
| **Videos** | ❌ | ❌ | 🎯 | Future work |
| **Code** | ❌ | ❌ | 🎯 | Future work |

**Current decision**: ✅ **Continue with text-only for Phase 1**

**Next decision point**: After Phase 1 Go/No-Go, evaluate if we have time to add table extraction

---

## Action Items

- [x] Document multimodal strategy
- [ ] Monitor Phase 1 velocity
- [ ] If ahead of schedule: Add table extraction in Phase 2
- [ ] If on schedule: Mention tables/figures as "future work" in demo
- [ ] Create architecture diagram showing multimodal pipeline (even if not implemented)

