// Configuration - API Gateway URL
const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8080'
    : 'https://api-gateway-338657477881.us-central1.run.app';

// Global network instance for graph
let network = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadPapers();
    loadGraph();
});

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

        // Display answer
        let html = `<p><strong>Question:</strong> ${data.question}</p>`;
        html += `<p style="margin-top: 15px;"><strong>Answer:</strong> ${data.answer}`;

        // Add confidence badge
        if (data.confidence) {
            const score = data.confidence.score;
            let badgeClass = 'confidence-low';
            if (score >= 0.8) badgeClass = 'confidence-high';
            else if (score >= 0.5) badgeClass = 'confidence-medium';

            html += `<span class="confidence-badge ${badgeClass}">Confidence: ${(score * 100).toFixed(0)}%</span>`;
        }
        html += `</p>`;

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
