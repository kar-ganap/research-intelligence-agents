// Configuration loaded from config.js (auto-generated during deployment)
// API_BASE_URL is defined in config.js which loads before this script

// Global network instance for graph
let network = null;
let graphData = null; // Store full graph data for filtering
let selectedFile = null;
let physicsEnabled = true; // Physics enabled by default with force-directed layout

// Category color mapping
const CATEGORY_COLORS = {
    'cs.AI': '#FF6B6B',   // Red
    'cs.LG': '#4ECDC4',   // Teal
    'cs.CL': '#45B7D1',   // Blue
    'cs.CV': '#FFA07A',   // Orange
    'cs.MA': '#98D8C8',   // Mint
    'math.ST': '#F7DC6F', // Yellow
    'stat.ML': '#BB8FCE', // Purple
    'stat.CO': '#85C1E2', // Sky blue
    'default': '#95A5A6'  // Gray
};

// Category display names
const CATEGORY_NAMES = {
    'cs.AI': 'Artificial Intelligence (cs.AI)',
    'cs.LG': 'Machine Learning (cs.LG)',
    'cs.CL': 'Computation and Language (cs.CL)',
    'cs.CV': 'Computer Vision (cs.CV)',
    'cs.MA': 'Multiagent Systems (cs.MA)',
    'math.ST': 'Statistics Theory (math.ST)',
    'stat.ML': 'Machine Learning - Statistics (stat.ML)',
    'stat.CO': 'Computation - Statistics (stat.CO)',
    'default': 'Other'
};

// Relationship type color mapping (distinct from node colors)
const RELATIONSHIP_COLORS = {
    'supports': '#2E7D32',     // Green - corroborating evidence
    'contradicts': '#C62828',  // Red - conflicting findings
    'extends': '#1565C0'       // Blue - builds upon
};

/**
 * Get color for a given arXiv category
 */
function getCategoryColor(category) {
    if (!category) return CATEGORY_COLORS.default;
    // Handle categories like "cs.LG" or just "cs.LG, cs.AI" (take first)
    const primaryCat = category.split(',')[0].trim();
    return CATEGORY_COLORS[primaryCat] || CATEGORY_COLORS.default;
}

/**
 * Get display name for a given arXiv category
 */
function getCategoryDisplayName(category) {
    if (!category) return CATEGORY_NAMES.default;
    const primaryCat = category.split(',')[0].trim();
    return CATEGORY_NAMES[primaryCat] || `${category}`;
}

/**
 * Get color for a given relationship type
 */
function getRelationshipColor(relationshipType) {
    return RELATIONSHIP_COLORS[relationshipType] || '#616161'; // Default gray fallback
}

/**
 * Convert string to title case with special handling for acronyms and common words
 */
function toTitleCase(str) {
    if (!str) return str;

    // Words to keep lowercase (unless first word)
    const minorWords = new Set(['a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'from', 'by', 'of', 'in', 'with', 'via']);

    // Common acronyms to keep uppercase
    const acronyms = new Set(['AI', 'ML', 'NLP', 'CV', 'GPU', 'CPU', 'API', 'BERT', 'GPT', 'LSTM', 'GAN', 'CNN', 'RNN', 'RL']);

    // Check if the entire title is in ALL CAPS (more than 70% uppercase letters)
    const letters = str.replace(/[^a-zA-Z]/g, '');
    const uppercaseCount = (str.match(/[A-Z]/g) || []).length;
    const isAllCaps = letters.length > 0 && (uppercaseCount / letters.length) > 0.7;

    // If entire title is ALL CAPS, lowercase it first to avoid false acronym detection
    const workingStr = isAllCaps ? str.toLowerCase() : str;

    return workingStr.split(' ').map((word, index) => {
        // Keep empty strings as-is
        if (!word) return word;

        // Strip punctuation for comparison but preserve it
        const cleanWord = word.replace(/[^a-zA-Z0-9]/g, '');
        const upperClean = cleanWord.toUpperCase();
        const lowerWord = word.toLowerCase();

        // Check if word (without punctuation) is a known acronym
        if (acronyms.has(upperClean)) {
            // Preserve original punctuation but uppercase the letters
            return word.replace(/[a-zA-Z0-9]/g, c => c.toUpperCase());
        }

        // Detect likely acronyms:
        // - 2-6 characters (without punctuation)
        // - All letters are uppercase OR it's a mixed case like "GPT4" (uppercase letters + numbers)
        // - No consecutive vowels (typical of acronyms)
        if (cleanWord.length >= 2 && cleanWord.length <= 6) {
            const hasConsecutiveVowels = /[aeiou]{2,}/i.test(cleanWord);
            const isAcronymPattern = /^[A-Z]+[0-9]*$/.test(cleanWord);

            if (!hasConsecutiveVowels && isAcronymPattern) {
                // Preserve original punctuation but uppercase the letters/numbers
                return word.replace(/[a-zA-Z0-9]/g, c => c.toUpperCase());
            }
        }

        // Keep minor words lowercase (except if first word)
        if (index > 0 && minorWords.has(lowerWord.replace(/[^a-zA-Z]/g, ''))) {
            return lowerWord;
        }

        // Title case: capitalize first letter
        return lowerWord.charAt(0).toUpperCase() + lowerWord.slice(1);
    }).join(' ');
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadPapers();
    loadGraph();
    loadWatchRules();
    loadAlerts();
    updateStats(); // Update stats for new design
});

/**
 * Set a question in the input field (for example buttons)
 */
function setQuestion(question) {
    document.getElementById('questionInput').value = question;
}

/**
 * Ask a question to the Q&A system
 */
async function askQuestion() {
    const questionInput = document.getElementById('questionInput');
    const answerBox = document.getElementById('answerBox');
    const answerContent = document.getElementById('answerContent');
    const citationsBox = document.getElementById('citationsBox');
    const askBtn = document.getElementById('askBtn');

    const question = questionInput.value.trim();
    if (!question) {
        alert('Please enter a question');
        return;
    }

    // Show loading state
    askBtn.disabled = true;
    askBtn.innerHTML = 'Asking... <span class="loading"></span>';
    answerBox.classList.add('visible');
    answerContent.innerHTML = '<p style="color: #5f6368;">Processing your question with ADK agents...</p>';
    citationsBox.innerHTML = '';

    try {
        const response = await fetch(`${API_BASE_URL}/api/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question })
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        const data = await response.json();

        // Helper function to format answer text (convert markdown-like formatting to HTML)
        function formatAnswer(text) {
            return text
                .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')  // **bold** -> <strong>bold</strong>
                .replace(/\n\n/g, '</p><p>')  // Double newlines -> paragraph breaks
                .replace(/\n/g, '<br>');  // Single newlines -> line breaks
        }

        // Display answer
        let html = `<p><strong>Question:</strong> ${data.question}</p>`;
        html += `<div style="margin-top: 15px;"><strong>Answer:</strong></div>`;
        html += `<div style="margin-top: 10px; background: #f8f9fa; padding: 15px; border-radius: 6px;"><p style="margin: 0;">${formatAnswer(data.answer)}</p></div>`;

        // Add confidence section with details
        if (data.confidence) {
            const score = data.confidence.score;
            let badgeClass = 'confidence-low';
            if (score >= 0.8) badgeClass = 'confidence-high';
            else if (score >= 0.5) badgeClass = 'confidence-medium';

            html += `<div style="margin-top: 15px;">`;
            html += `<p><strong>Confidence Assessment:</strong> <span class="confidence-badge ${badgeClass}">${(score * 100).toFixed(0)}%</span></p>`;

            // Show breakdown if available
            if (data.confidence.breakdown) {
                const b = data.confidence.breakdown;
                html += `<div style="margin-left: 15px; font-size: 13px; color: #5f6368;">`;
                html += `<div>Evidence Strength: ${(b.evidence_strength * 100).toFixed(0)}%</div>`;
                html += `<div>Consistency: ${(b.consistency * 100).toFixed(0)}%</div>`;
                html += `<div>Coverage: ${(b.coverage * 100).toFixed(0)}%</div>`;
                html += `<div>Source Quality: ${(b.source_quality * 100).toFixed(0)}%</div>`;
                html += `</div>`;
            }

            // Show reasoning if available
            if (data.confidence.reasoning) {
                html += `<div style="margin-top: 8px; font-size: 13px; font-style: italic; color: #5f6368;">${data.confidence.reasoning}</div>`;
            }

            // Show warning if present
            if (data.confidence.warning) {
                html += `<div style="margin-top: 8px; padding: 8px; background: #fff3cd; border-radius: 4px; font-size: 13px; color: #856404;">⚠️ ${data.confidence.warning}</div>`;
            }

            html += `</div>`;
        }

        answerContent.innerHTML = html;

        // Display citations and retrieved papers
        let citationsHtml = '';

        if (data.citations && data.citations.length > 0) {
            citationsHtml += '<p style="margin-top: 0;"><strong>Sources:</strong></p>';
            citationsHtml += '<ul style="margin-top: 10px; padding-left: 20px;">';
            data.citations.forEach(citation => {
                citationsHtml += `<li style="margin-bottom: 5px;">${citation}</li>`;
            });
            citationsHtml += '</ul>';
        }

        // Show retrieved papers if available
        if (data.retrieved_papers && data.retrieved_papers.length > 0) {
            citationsHtml += '<p style="margin-top: 15px;"><strong>Retrieved Papers:</strong></p>';
            citationsHtml += '<div style="font-size: 13px;">';
            data.retrieved_papers.forEach((paper, idx) => {
                const paperTitle = toTitleCase(paper.title || paper.paper_id);
                citationsHtml += `<div style="margin: 8px 0; padding: 8px; background: #f8f9fa; border-radius: 4px;">`;
                citationsHtml += `${idx + 1}. ${paperTitle}`;
                if (paper.relevance_score) {
                    citationsHtml += ` <span style="font-size: 11px; color: #5f6368;">(relevance: ${(paper.relevance_score * 100).toFixed(0)}%)</span>`;
                }
                citationsHtml += `</div>`;
            });
            citationsHtml += '</div>';
        }

        citationsBox.innerHTML = citationsHtml;

    } catch (error) {
        console.error('Error asking question:', error);
        answerContent.innerHTML = `<div class="error">Error: ${error.message}. Make sure the API service is running.</div>`;
    } finally {
        askBtn.disabled = false;
        askBtn.innerHTML = 'Ask';
    }
}

/**
 * Load all papers from the corpus (grouped by category with collapsible sections)
 */
// Global papers data and sort state
let allPapersData = [];
let sortOrder = {}; // Track sort order per category

function sortCategoryPapers(categoryId, sortKey) {
    // Toggle sort order
    const currentOrder = sortOrder[categoryId] || 'desc';
    sortOrder[categoryId] = currentOrder === 'desc' ? 'asc' : 'desc';

    // Get category from categoryId
    const category = categoryId.replace(/_/g, '.');

    // Find papers for this category
    const categoryPapers = allPapersData.filter(paper => {
        const paperCategory = paper.primary_category || (paper.categories && paper.categories[0]) || 'Unknown';
        return paperCategory === category;
    });

    // Sort papers
    categoryPapers.sort((a, b) => {
        if (sortKey === 'published') {
            const dateA = a.published ? new Date(a.published) : new Date(0);
            const dateB = b.published ? new Date(b.published) : new Date(0);
            return sortOrder[categoryId] === 'asc' ? dateA - dateB : dateB - dateA;
        }
        return 0;
    });

    // Rebuild table for this category
    const tableBody = document.getElementById(`table-body-${categoryId}`);
    if (!tableBody) return;

    let html = '';
    categoryPapers.forEach(paper => {
        const arxivId = paper.arxiv_id || paper.paper_id;
        const arxivUrl = arxivId ? `https://arxiv.org/abs/${arxivId}` : null;
        const pdfUrl = arxivId ? `https://arxiv.org/pdf/${arxivId}.pdf` : null;
        const displayTitle = toTitleCase(paper.title);

        html += `
            <tr>
                <td style="padding: 12px 8px;">
                    ${arxivUrl ? `<a href="${arxivUrl}" target="_blank" style="color: #1a73e8; text-decoration: none;">${displayTitle}</a>` : displayTitle}
                    ${arxivUrl ? `<a href="${arxivUrl}" target="_blank" style="margin-left: 8px; font-size: 12px; color: #5f6368;" title="View on arXiv">↗</a>` : ''}
                    ${pdfUrl ? `<a href="${pdfUrl}" target="_blank" style="margin-left: 4px; font-size: 12px; color: #5f6368;" title="Download PDF">📥</a>` : ''}
                </td>
                <td style="padding: 12px 8px; color: #5f6368; font-size: 14px;">${paper.authors ? paper.authors.slice(0, 3).join(', ') + (paper.authors.length > 3 ? ', et al.' : '') : 'Unknown authors'}</td>
                <td style="padding: 12px 8px; color: #5f6368; font-size: 14px; white-space: nowrap;">${paper.published ? new Date(paper.published).toLocaleDateString() : 'N/A'}</td>
            </tr>
        `;
    });

    tableBody.innerHTML = html;

    // Update sort arrow
    const sortArrow = document.getElementById(`sort-arrow-${categoryId}`);
    if (sortArrow) {
        sortArrow.textContent = sortOrder[categoryId] === 'asc' ? '▲' : '▼';
    }
}

async function loadPapers() {
    const papersList = document.getElementById('papersList');

    try {
        const response = await fetch(`${API_BASE_URL}/api/papers`);

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        const data = await response.json();
        const papers = data.papers || [];
        allPapersData = papers; // Store globally

        if (papers.length === 0) {
            papersList.innerHTML = '<p style="color: #6b7280;">No papers in corpus yet.</p>';
            return;
        }

        // Check if we're using the new grid layout (index_v2.html)
        // The new layout has papers-grid class on papersList
        const isGridLayout = papersList && papersList.classList.contains('papers-grid');

        if (isGridLayout) {
            // New grid layout for index_v2.html
            renderPapersGrid(papers, papersList);
        } else {
            // Old categorized table layout for index.html
            renderPapersTable(papers, papersList);
        }

    } catch (error) {
        console.error('Error loading papers:', error);
        papersList.innerHTML = `<div class="error">Error loading papers: ${error.message}</div>`;
    }
}

/**
 * Render papers in grid layout (index_v2.html)
 */
function renderPapersGrid(papers, papersList) {
    let html = '';

    // Show most recent papers first
    const sortedPapers = papers.sort((a, b) => {
        const dateA = a.published ? new Date(a.published) : new Date(0);
        const dateB = b.published ? new Date(b.published) : new Date(0);
        return dateB - dateA;
    });

    sortedPapers.forEach(paper => {
        const displayTitle = toTitleCase(paper.title);
        const authors = paper.authors ? paper.authors.slice(0, 2).join(', ') + (paper.authors.length > 2 ? ', et al.' : '') : 'Unknown authors';
        const arxivId = paper.arxiv_id || paper.paper_id;
        const published = paper.published ? new Date(paper.published).toLocaleDateString() : 'N/A';

        html += `
            <div class="paper-card">
                <div class="paper-title">${displayTitle}</div>
                <div class="paper-authors">${authors}</div>
                <div class="paper-meta">
                    <span>📅 ${published}</span>
                    ${arxivId ? `<span><a href="https://arxiv.org/abs/${arxivId}" target="_blank" style="color: #667eea; text-decoration: none;">View arXiv ↗</a></span>` : ''}
                </div>
            </div>
        `;
    });

    papersList.innerHTML = html;
}

/**
 * Render papers in categorized table layout (index.html)
 */
function renderPapersTable(papers, papersList) {
    // Group papers by category
    const papersByCategory = {};
    papers.forEach(paper => {
        const category = paper.primary_category || (paper.categories && paper.categories[0]) || 'Unknown';
        if (!papersByCategory[category]) {
            papersByCategory[category] = [];
        }
        papersByCategory[category].push(paper);
    });

    // Sort each category by published date (newest first by default)
    Object.keys(papersByCategory).forEach(category => {
        const categoryId = category.replace(/\./g, '_');
        sortOrder[categoryId] = 'desc'; // Initialize sort order

        papersByCategory[category].sort((a, b) => {
            const dateA = a.published ? new Date(a.published) : new Date(0);
            const dateB = b.published ? new Date(b.published) : new Date(0);
            return dateB - dateA; // Newest first
        });
    });

    // Build HTML with collapsible sections and tables
    let html = '';
    const sortedCategories = Object.keys(papersByCategory).sort();

    sortedCategories.forEach(category => {
        const categoryPapers = papersByCategory[category];
        const categoryColor = getCategoryColor(category);
        const categoryDisplayName = getCategoryDisplayName(category);
        const categoryId = category.replace(/\./g, '_'); // Safe ID for HTML

        html += `
                <div class="category-section">
                    <div class="category-header" onclick="toggleCategory('${categoryId}')" style="cursor: pointer; background: ${categoryColor}15; padding: 10px; border-radius: 6px; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
                        <div>
                            <span style="display: inline-block; width: 12px; height: 12px; background: ${categoryColor}; border-radius: 50%; margin-right: 8px;"></span>
                            <span style="font-weight: 600; color: #333;">${categoryDisplayName}</span>
                            <span style="margin-left: 8px; font-size: 12px; color: #5f6368;">(${categoryPapers.length} paper${categoryPapers.length !== 1 ? 's' : ''})</span>
                        </div>
                        <span id="toggle-${categoryId}" style="font-size: 18px; color: #5f6368;">▼</span>
                    </div>
                    <div id="papers-${categoryId}" class="category-papers" style="display: block;">
                        <table style="width: 100%; border-collapse: collapse; margin-left: 12px; margin-bottom: 16px;">
                            <thead>
                                <tr style="border-bottom: 2px solid #e0e0e0;">
                                    <th style="text-align: left; padding: 12px 8px; font-weight: 600; color: #5f6368; font-size: 13px;">Title</th>
                                    <th style="text-align: left; padding: 12px 8px; font-weight: 600; color: #5f6368; font-size: 13px; width: 30%;">Authors</th>
                                    <th onclick="sortCategoryPapers('${categoryId}', 'published')" style="text-align: left; padding: 12px 8px; font-weight: 600; color: #5f6368; font-size: 13px; width: 15%; cursor: pointer; user-select: none;" title="Click to sort">
                                        Published Date <span id="sort-arrow-${categoryId}">▼</span>
                                    </th>
                                </tr>
                            </thead>
                            <tbody id="table-body-${categoryId}">
        `;

        categoryPapers.forEach(paper => {
            const arxivId = paper.arxiv_id || paper.paper_id;
            const arxivUrl = arxivId ? `https://arxiv.org/abs/${arxivId}` : null;
            const pdfUrl = arxivId ? `https://arxiv.org/pdf/${arxivId}.pdf` : null;
            const displayTitle = toTitleCase(paper.title);

            html += `
                <tr>
                    <td style="padding: 12px 8px;">
                        ${arxivUrl ? `<a href="${arxivUrl}" target="_blank" style="color: #1a73e8; text-decoration: none;">${displayTitle}</a>` : displayTitle}
                        ${arxivUrl ? `<a href="${arxivUrl}" target="_blank" style="margin-left: 8px; font-size: 12px; color: #5f6368;" title="View on arXiv">↗</a>` : ''}
                        ${pdfUrl ? `<a href="${pdfUrl}" target="_blank" style="margin-left: 4px; font-size: 12px; color: #5f6368;" title="Download PDF">📥</a>` : ''}
                    </td>
                    <td style="padding: 12px 8px; color: #5f6368; font-size: 14px;">${paper.authors ? paper.authors.slice(0, 3).join(', ') + (paper.authors.length > 3 ? ', et al.' : '') : 'Unknown authors'}</td>
                    <td style="padding: 12px 8px; color: #5f6368; font-size: 14px; white-space: nowrap;">${paper.published ? new Date(paper.published).toLocaleDateString() : 'N/A'}</td>
                </tr>
            `;
        });

        html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    });

    papersList.innerHTML = html;
}

/**
 * Toggle category section visibility
 */
function toggleCategory(categoryId) {
    const papersDiv = document.getElementById(`papers-${categoryId}`);
    const toggleIcon = document.getElementById(`toggle-${categoryId}`);

    if (papersDiv.style.display === 'none') {
        papersDiv.style.display = 'block';
        toggleIcon.textContent = '▼';
    } else {
        papersDiv.style.display = 'none';
        toggleIcon.textContent = '▶';
    }
}

/**
 * Load and render knowledge graph
 */
async function loadGraph() {
    const container = document.getElementById('graph');

    try {
        const response = await fetch(`${API_BASE_URL}/api/graph`);

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        const data = await response.json();
        graphData = data; // Store for filtering

        // Apply category-based colors to nodes
        if (data.nodes) {
            data.nodes = data.nodes.map(node => {
                const category = node.primary_category || (node.categories && node.categories[0]);
                const categoryColor = getCategoryColor(category);
                const displayTitle = toTitleCase(node.title);
                const displayLabel = displayTitle.length > 50 ? displayTitle.substring(0, 50) + '...' : displayTitle;

                return {
                    ...node,
                    label: displayLabel,
                    color: {
                        background: categoryColor,
                        border: categoryColor,
                        highlight: {
                            background: categoryColor,
                            border: '#000'
                        }
                    },
                    font: {
                        color: '#fff',
                        size: 14
                    },
                    title: `${displayTitle}<br><b>Category:</b> ${category || 'Unknown'}<br><b>Authors:</b> ${node.authors || 'Unknown'}`
                };
            });
        }

        // Apply relationship-based colors to edges
        if (data.edges) {
            data.edges = data.edges.map(edge => {
                const relationshipColor = getRelationshipColor(edge.label);

                return {
                    ...edge,
                    color: {
                        color: relationshipColor,
                        highlight: relationshipColor,
                        hover: relationshipColor
                    },
                    width: 2
                };
            });
        }

        // vis.js network options
        const options = {
            nodes: {
                shape: 'box',
                margin: 10,
                widthConstraint: {
                    maximum: 200
                }
            },
            edges: {
                arrows: {
                    to: {
                        enabled: true,
                        scaleFactor: 0.5
                    }
                },
                font: {
                    size: 12,
                    align: 'middle'
                },
                smooth: {
                    type: 'continuous'
                }
            },
            layout: {
                improvedLayout: true,
                randomSeed: 42  // Consistent layout across reloads
            },
            physics: {
                enabled: true,
                stabilization: {
                    enabled: true,
                    iterations: 200,
                    updateInterval: 25
                },
                barnesHut: {
                    gravitationalConstant: -8000,
                    centralGravity: 0.3,
                    springLength: 250,
                    springConstant: 0.04,
                    damping: 0.09,
                    avoidOverlap: 0.5
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 200,
                dragNodes: true,
                dragView: true,
                zoomView: true
            }
        };

        // Create network
        network = new vis.Network(container, data, options);

        // Add click handler
        network.on('click', function(params) {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const node = data.nodes.find(n => n.id === nodeId);
                if (node) {
                    // Extract title from the tooltip (which has the full title)
                    const titleMatch = node.title.match(/^(.+?)<br>/);
                    const displayTitle = titleMatch ? titleMatch[1] : toTitleCase(node.label);
                    alert(`Paper: ${displayTitle}\nAuthors: ${node.authors}`);
                }
            }
        });

        console.log(`Knowledge graph loaded: ${data.nodes.length} nodes, ${data.edges.length} edges`);

    } catch (error) {
        console.error('Error loading graph:', error);
        container.innerHTML = `<div class="error">Error loading graph: ${error.message}</div>`;
    }
}

/**
 * Tab switching
 */
function switchTab(tabId) {
    // Remove active from all tabs and buttons
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));

    // Activate selected tab
    const tab = document.getElementById(tabId);
    if (tab) {
        tab.classList.add('active');
        // Find and activate corresponding button
        const buttons = document.querySelectorAll('.tab-button');
        buttons.forEach(btn => {
            if (btn.getAttribute('onclick').includes(tabId)) {
                btn.classList.add('active');
            }
        });
    }
}

/**
 * File upload handling
 */
function handleFileSelect(event) {
    selectedFile = event.target.files[0];
    const status = document.getElementById('uploadStatus');
    const uploadBtn = document.getElementById('uploadBtn');

    if (selectedFile) {
        if (selectedFile.type !== 'application/pdf') {
            status.innerHTML = '<div class="error">Please select a PDF file</div>';
            uploadBtn.disabled = true;
            return;
        }

        status.innerHTML = `<p style="color: #1a73e8;">Selected: ${selectedFile.name}</p>`;
        uploadBtn.disabled = false;
    }
}

async function uploadPaper() {
    if (!selectedFile) {
        alert('Please select a file first');
        return;
    }

    const uploadBtn = document.getElementById('uploadBtn');
    const status = document.getElementById('uploadStatus');

    uploadBtn.disabled = true;
    uploadBtn.innerHTML = 'Uploading... <span class="loading"></span>';
    status.innerHTML = '<p style="color: #5f6368;">Processing PDF with multi-agent pipeline...</p>';

    try {
        const formData = new FormData();
        formData.append('file', selectedFile);

        const response = await fetch(`${API_BASE_URL}/api/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }

        const data = await response.json();
        status.innerHTML = `<div style="color: #155724; background: #d4edda; padding: 10px; border-radius: 6px;">
            ✓ Paper uploaded and processed successfully!<br>
            <small>Paper ID: ${data.paper_id || 'N/A'}</small>
        </div>`;

        // Refresh papers list and graph
        setTimeout(() => {
            loadPapers();
            loadGraph();
        }, 1000);

    } catch (error) {
        console.error('Error uploading paper:', error);
        status.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = 'Upload & Process';
    }
}

/**
 * Load and display alerts
 */
async function loadAlerts() {
    const alertsList = document.getElementById('alertsList');

    try {
        const response = await fetch(`${API_BASE_URL}/api/alerts`);

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        const data = await response.json();
        const alerts = data.alerts || [];

        if (alerts.length === 0) {
            alertsList.innerHTML = '<p style="color: #5f6368;">No alerts yet. Create a watch rule to get notified!</p>';
            return;
        }

        let html = '';
        alerts.forEach(alert => {
            const isNew = !alert.sent;
            const displayTitle = toTitleCase(alert.paper_title);
            html += `
                <div class="alert-item ${isNew ? 'alert-new' : ''}">
                    <div style="font-weight: 600; margin-bottom: 5px;">
                        ${displayTitle}
                        ${isNew ? '<span style="background: #1a73e8; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; margin-left: 5px;">NEW</span>' : ''}
                    </div>
                    <div style="font-size: 13px; color: #5f6368; margin-bottom: 8px;">
                        ${alert.match_explanation || 'Matches your watch rule'}
                    </div>
                    <div style="font-size: 12px; color: #5f6368;">
                        Match Score: ${(alert.match_score * 100).toFixed(0)}%
                    </div>
                </div>
            `;
        });

        alertsList.innerHTML = html;

    } catch (error) {
        console.error('Error loading alerts:', error);
        alertsList.innerHTML = `<div class="error">Error loading alerts: ${error.message}</div>`;
    }
}

/**
 * Load and display watch rules
 */
async function loadWatchRules() {
    const rulesList = document.getElementById('rulesList');

    try {
        const response = await fetch(`${API_BASE_URL}/api/watch-rules`);

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        const data = await response.json();
        const rules = data.rules || [];

        if (rules.length === 0) {
            // Show example rules (without email) when no rules exist
            rulesList.innerHTML = `
                <p style="color: #5f6368; margin-bottom: 20px;">No watch rules yet. Create one to get alerts! Here are some examples:</p>

                <div class="rule-item" style="opacity: 0.7; border: 2px dashed #e0e0e0;">
                    <div style="font-weight: 600; margin-bottom: 8px; color: #1a73e8;">Keyword Rule</div>
                    <div class="rule-keywords">
                        <span class="keyword-tag">attention mechanisms</span>
                        <span class="keyword-tag">transformers</span>
                        <span class="keyword-tag">self-attention</span>
                    </div>
                </div>

                <div class="rule-item" style="opacity: 0.7; border: 2px dashed #e0e0e0;">
                    <div style="font-weight: 600; margin-bottom: 8px; color: #1a73e8;">Author Rule</div>
                    <div style="font-size: 14px; color: #333;">
                        Yoshua Bengio, Geoffrey Hinton, Yann LeCun
                    </div>
                </div>

                <div class="rule-item" style="opacity: 0.7; border: 2px dashed #e0e0e0;">
                    <div style="font-weight: 600; margin-bottom: 8px; color: #1a73e8;">Claim Rule</div>
                    <div style="font-size: 14px; color: #333;">
                        Papers introducing novel neural network architectures achieving state-of-the-art results on benchmark datasets
                    </div>
                </div>
            `;
            return;
        }

        let html = '';
        rules.forEach(rule => {
            // Only create a card if the rule has the required fields
            let ruleContent = '';

            if (rule.rule_type === 'keyword' && rule.keywords && rule.keywords.length > 0) {
                ruleContent = `
                    <div style="font-weight: 600; margin-bottom: 8px; color: #1a73e8;">Keyword Rule</div>
                    <div class="rule-keywords">
                        ${rule.keywords.map(k => `<span class="keyword-tag">${k}</span>`).join('')}
                    </div>
                `;
            } else if (rule.rule_type === 'author' && rule.authors && rule.authors.length > 0) {
                ruleContent = `
                    <div style="font-weight: 600; margin-bottom: 8px; color: #1a73e8;">Author Rule</div>
                    <div style="font-size: 14px; color: #333;">
                        ${rule.authors.join(', ')}
                    </div>
                `;
            } else if (rule.rule_type === 'claim' && rule.claim_description) {
                ruleContent = `
                    <div style="font-weight: 600; margin-bottom: 8px; color: #1a73e8;">Claim Rule</div>
                    <div style="font-size: 14px; color: #333;">
                        ${rule.claim_description}
                    </div>
                `;
            }

            // Only add the rule card if we have content
            if (ruleContent) {
                html += `<div class="rule-item">${ruleContent}</div>`;
            }
        });

        rulesList.innerHTML = html;

    } catch (error) {
        console.error('Error loading watch rules:', error);
        rulesList.innerHTML = `<div class="error">Error loading rules: ${error.message}</div>`;
    }
}

/**
 * Update rule form based on selected type
 */
function updateRuleForm() {
    const ruleType = document.getElementById('ruleType').value;
    const formFields = document.getElementById('ruleFormFields');

    let html = '';
    if (ruleType === 'keyword') {
        html = `
            <div class="form-group">
                <label class="form-label">Keywords (comma-separated)</label>
                <input type="text" id="ruleKeywords" class="form-input" placeholder="e.g., transformer, attention, neural">
            </div>
        `;
    } else if (ruleType === 'author') {
        html = `
            <div class="form-group">
                <label class="form-label">Author Names (comma-separated)</label>
                <input type="text" id="ruleAuthors" class="form-input" placeholder="e.g., Yoshua Bengio, Geoffrey Hinton">
            </div>
        `;
    } else if (ruleType === 'claim') {
        html = `
            <div class="form-group">
                <label class="form-label">Claim Description</label>
                <textarea id="ruleClaim" class="form-input" rows="3" placeholder="e.g., Papers claiming to beat MMLU by more than 2%"></textarea>
            </div>
        `;
    }

    formFields.innerHTML = html;
}

/**
 * Create a new watch rule
 */
async function createWatchRule() {
    const ruleType = document.getElementById('ruleType').value;
    const email = document.getElementById('ruleEmail').value;
    const createBtn = document.getElementById('createRuleBtn');

    if (!email || !email.includes('@')) {
        alert('Please enter a valid email address');
        return;
    }

    let ruleData = {
        rule_type: ruleType,
        user_email: email,
        min_relevance_score: 0.7
    };

    // Add type-specific fields
    if (ruleType === 'keyword') {
        const keywords = document.getElementById('ruleKeywords')?.value;
        if (!keywords) {
            alert('Please enter keywords');
            return;
        }
        ruleData.keywords = keywords.split(',').map(k => k.trim()).filter(k => k);
    } else if (ruleType === 'author') {
        const authors = document.getElementById('ruleAuthors')?.value;
        if (!authors) {
            alert('Please enter author names');
            return;
        }
        ruleData.authors = authors.split(',').map(a => a.trim()).filter(a => a);
    } else if (ruleType === 'claim') {
        const claim = document.getElementById('ruleClaim')?.value;
        if (!claim) {
            alert('Please enter a claim description');
            return;
        }
        ruleData.claim_description = claim;
    }

    createBtn.disabled = true;
    createBtn.innerHTML = 'Creating... <span class="loading"></span>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/watch-rules`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(ruleData)
        });

        if (!response.ok) {
            throw new Error(`Failed to create rule: ${response.statusText}`);
        }

        alert('Watch rule created successfully! You will receive alerts when matching papers are found.');

        // Refresh rules list and switch to list tab
        loadWatchRules();
        switchTab('rules-list-tab');

        // Clear form
        document.getElementById('ruleEmail').value = '';
        updateRuleForm();

    } catch (error) {
        console.error('Error creating watch rule:', error);
        alert(`Error: ${error.message}`);
    } finally {
        createBtn.disabled = false;
        createBtn.innerHTML = 'Create Alert Rule';
    }
}

/**
 * Graph filtering and controls
 */
function filterGraph() {
    if (!graphData || !network) return;

    const filter = document.getElementById('relationshipFilter').value;

    if (filter === 'all') {
        network.setData(graphData);
        return;
    }

    // Filter edges by relationship type
    const filteredEdges = graphData.edges.filter(edge => edge.label === filter);

    // Get nodes that are connected by filtered edges
    const nodeIds = new Set();
    filteredEdges.forEach(edge => {
        nodeIds.add(edge.from);
        nodeIds.add(edge.to);
    });

    const filteredNodes = graphData.nodes.filter(node => nodeIds.has(node.id));

    network.setData({
        nodes: filteredNodes,
        edges: filteredEdges
    });
}

function resetGraphView() {
    if (network) {
        network.fit();
        document.getElementById('relationshipFilter').value = 'all';
        filterGraph();
    }
}

function togglePhysics() {
    if (!network) return;

    physicsEnabled = !physicsEnabled;
    network.setOptions({
        physics: {
            enabled: physicsEnabled
        }
    });

    // Update button text based on state
    const btn = document.getElementById('togglePhysicsBtn');
    if (btn) {
        btn.textContent = physicsEnabled ? '❄️ Freeze Graph' : '🔥 Unfreeze Graph';
    }
}

/**
 * Update stats for new design (header and insights)
 */
async function updateStats() {
    try {
        // Fetch all data
        const [papersRes, graphRes, alertsRes] = await Promise.all([
            fetch(`${API_BASE_URL}/api/papers`),
            fetch(`${API_BASE_URL}/api/graph`),
            fetch(`${API_BASE_URL}/api/alerts`)
        ]);

        const papersData = await papersRes.json();
        const graphData = await graphRes.json();
        const alertsData = await alertsRes.json();

        const paperCount = (papersData.papers || []).length;
        const relationshipCount = (graphData.edges || []).length;
        const alertCount = (alertsData.alerts || []).filter(a => !a.sent).length;

        // Update header stats (if they exist - for index_v2)
        const statPapers = document.getElementById('statPapers');
        const statRelationships = document.getElementById('statRelationships');
        const statAlerts = document.getElementById('statAlerts');

        if (statPapers) statPapers.textContent = paperCount;
        if (statRelationships) statRelationships.textContent = relationshipCount;
        if (statAlerts) statAlerts.textContent = alertCount;

        // Update insights section (if it exists - for index_v2)
        const insightPapers = document.getElementById('insightPapers');
        const insightRelationships = document.getElementById('insightRelationships');

        if (insightPapers) insightPapers.textContent = paperCount;
        if (insightRelationships) insightRelationships.textContent = relationshipCount;

    } catch (error) {
        console.error('Error updating stats:', error);
    }
}
