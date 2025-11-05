// Configuration loaded from config.js (auto-generated during deployment)
// API_BASE_URL is defined in config.js which loads before this script

// Global network instance for graph
let network = null;
let graphData = null; // Store full graph data for filtering
let selectedFile = null;
let physicsEnabled = false;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadPapers();
    loadGraph();
    loadWatchRules();
    loadAlerts();
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
        html += `<div style="margin-top: 10px;"><p>${formatAnswer(data.answer)}</p>`;

        // Add confidence badge
        if (data.confidence) {
            const score = data.confidence.score;
            let badgeClass = 'confidence-low';
            if (score >= 0.8) badgeClass = 'confidence-high';
            else if (score >= 0.5) badgeClass = 'confidence-medium';

            html += `<span class="confidence-badge ${badgeClass}">Confidence: ${(score * 100).toFixed(0)}%</span>`;
        }
        html += `</div>`;

        answerContent.innerHTML = html;

        // Display citations
        if (data.citations && data.citations.length > 0) {
            let citationsHtml = '<p><strong>Sources:</strong></p>';
            data.citations.forEach(citation => {
                citationsHtml += `<span class="citation">${citation}</span>`;
            });
            citationsBox.innerHTML = citationsHtml;
        }

    } catch (error) {
        console.error('Error asking question:', error);
        answerContent.innerHTML = `<div class="error">Error: ${error.message}. Make sure the API service is running.</div>`;
    } finally {
        askBtn.disabled = false;
        askBtn.innerHTML = 'Ask';
    }
}

/**
 * Load all papers from the corpus
 */
async function loadPapers() {
    const papersList = document.getElementById('papersList');

    try {
        const response = await fetch(`${API_BASE_URL}/api/papers`);

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        const data = await response.json();
        const papers = data.papers || [];

        if (papers.length === 0) {
            papersList.innerHTML = '<p style="color: #5f6368;">No papers in corpus yet.</p>';
            return;
        }

        let html = '';
        papers.forEach(paper => {
            html += `
                <div class="paper-item">
                    <div class="paper-title">${paper.title}</div>
                    <div class="paper-authors">${paper.authors ? paper.authors.join(', ') : 'Unknown authors'}</div>
                </div>
            `;
        });

        papersList.innerHTML = html;

    } catch (error) {
        console.error('Error loading papers:', error);
        papersList.innerHTML = `<div class="error">Error loading papers: ${error.message}</div>`;
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

        // vis.js network options
        const options = {
            nodes: {
                shape: 'box',
                margin: 10,
                widthConstraint: {
                    maximum: 200
                },
                font: {
                    size: 14,
                    color: '#333'
                },
                color: {
                    background: '#e8f0fe',
                    border: '#1a73e8',
                    highlight: {
                        background: '#d4e7ff',
                        border: '#1557b0'
                    }
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
                color: {
                    color: '#5f6368',
                    highlight: '#1a73e8'
                },
                smooth: {
                    type: 'cubicBezier',
                    forceDirection: 'horizontal',
                    roundness: 0.4
                }
            },
            layout: {
                hierarchical: {
                    enabled: true,
                    direction: 'LR',
                    sortMethod: 'directed',
                    levelSeparation: 200,
                    nodeSpacing: 150
                }
            },
            physics: {
                enabled: false
            },
            interaction: {
                hover: true,
                tooltipDelay: 200
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
                    alert(`Paper: ${node.title}\nAuthors: ${node.authors}`);
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
            html += `
                <div class="alert-item ${isNew ? 'alert-new' : ''}">
                    <div style="font-weight: 600; margin-bottom: 5px;">
                        ${alert.paper_title}
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
            rulesList.innerHTML = '<p style="color: #5f6368;">No watch rules yet. Create one to get alerts!</p>';
            return;
        }

        let html = '';
        rules.forEach(rule => {
            html += `
                <div class="rule-item">
                    <div style="font-weight: 600; margin-bottom: 5px;">
                        ${rule.rule_type.charAt(0).toUpperCase() + rule.rule_type.slice(1)} Rule
                    </div>
                    ${rule.keywords ? `
                        <div class="rule-keywords">
                            ${rule.keywords.map(k => `<span class="keyword-tag">${k}</span>`).join('')}
                        </div>
                    ` : ''}
                    ${rule.authors ? `
                        <div style="font-size: 13px; color: #5f6368; margin-top: 5px;">
                            Authors: ${rule.authors.join(', ')}
                        </div>
                    ` : ''}
                    ${rule.claim_description ? `
                        <div style="font-size: 13px; color: #5f6368; margin-top: 5px;">
                            ${rule.claim_description}
                        </div>
                    ` : ''}
                    <div style="font-size: 12px; color: #5f6368; margin-top: 8px;">
                        Email: ${rule.user_email}
                    </div>
                </div>
            `;
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
}
