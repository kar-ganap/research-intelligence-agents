/**
 * Demo-specific JavaScript for Research Intelligence Platform
 *
 * Handles:
 * - Tab switching
 * - Setup page interactions (Tab 1)
 * - Time slider and snapshot management (Tab 2)
 * - Alert inbox population (Tab 3)
 * - Fake progress animations
 */

// ============================================================================
// Global Demo State
// ============================================================================

let currentTab = 0;
let selectedFolderFiles = 0;
let selectedRules = [];
let userEmail = '';
let currentSnapshotIndex = 5; // Start with all 49 papers (last snapshot)
let allPapers = [];
let snapshots = [];
let demoMode = true;

// Time snapshots configuration - dynamically calculated from today
function generateSnapshotDates() {
    const today = new Date();
    const snapshots = [];

    // Work backwards from today: 0, 1, 2, 3, 4, 5 weeks back
    const weeksBack = [5, 4, 3, 2, 1, 0];
    const counts = [25, 30, 35, 40, 45, 49];
    const labels = [
        'Initial corpus',
        '+5 new papers',
        '+5 new papers',
        '+5 new papers',
        '+5 new papers',
        '+4 new papers (current)'
    ];

    weeksBack.forEach((weeks, index) => {
        const date = new Date(today);
        date.setDate(date.getDate() - (weeks * 7));

        const dateString = date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });

        snapshots.push({
            date: dateString,
            count: counts[index],
            label: labels[index]
        });
    });

    return snapshots;
}

const SNAPSHOT_CONFIG = generateSnapshotDates();

// Sample alerts data for Tab 3
// These are based on REAL papers from the database matched to relationship-based watch rules
// The knowledge graph detected these papers extend foundational works the user is tracking
const SAMPLE_ALERTS = [
    {
        new: true,
        timestamp: '3 hours ago',
        rule: 'Extends: Chain-of-Thought Prompting',
        paperTitle: 'Tree of Thoughts: Deliberate Problem Solving with Large Language Models',
        authors: ['Shunyu Yao', 'Dian Yu', 'Jeffrey Zhao'],
        matchReason: 'Knowledge graph detected this paper EXTENDS "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models". Tree of Thoughts builds upon chain-of-thought by enabling LLMs to explore multiple reasoning paths simultaneously and make deliberate decisions through lookahead and backtracking. Achieves 74% success on Game of 24 (vs 4% with standard chain-of-thought).',
        matchScore: 0.92
    },
    {
        new: true,
        timestamp: '8 hours ago',
        rule: 'Extends: Chain-of-Thought Prompting',
        paperTitle: 'ReAct: Synergizing Reasoning and Acting in Language Models',
        authors: ['Shunyu Yao', 'Jeffrey Zhao', 'Dian Yu'],
        matchReason: 'Knowledge graph detected this paper EXTENDS "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models". ReAct extends chain-of-thought prompting by interleaving reasoning traces with task-specific actions, enabling dynamic interaction with external environments (e.g., Wikipedia API). Combines reasoning and acting to solve knowledge-intensive and decision-making tasks.',
        matchScore: 0.90
    },
    {
        new: true,
        timestamp: '1 day ago',
        rule: 'Extends: Language Models are Few-Shot Learners',
        paperTitle: 'GPT-4 Technical Report',
        authors: ['OpenAI'],
        matchReason: 'Knowledge graph detected this paper EXTENDS "Language Models are Few-Shot Learners" (GPT-3). GPT-4 advances the few-shot learning paradigm introduced by GPT-3 by adding multimodal capabilities (accepting both image and text inputs) and achieving human-level performance on professional academic benchmarks. Demonstrates stronger reasoning, factuality, and steerability compared to GPT-3.',
        matchScore: 0.94
    },
    {
        new: false,
        timestamp: '2 days ago',
        rule: 'Extends: Visual Instruction Tuning',
        paperTitle: 'GPT-4 Technical Report',
        authors: ['OpenAI'],
        matchReason: 'Knowledge graph detected this paper EXTENDS "Visual Instruction Tuning" (LLaVA). While LLaVA pioneered connecting vision encoders with LLMs through instruction-following data, GPT-4 takes multimodal instruction-following to production scale with human-level vision-language performance. Both papers advance the frontier of multimodal instruction tuning.',
        matchScore: 0.88
    },
    {
        new: false,
        timestamp: '3 days ago',
        rule: 'Extends: Chain-of-Thought Prompting',
        paperTitle: 'Reflexion: Language Agents with Verbal Reinforcement Learning',
        authors: ['Noah Shinn', 'Federico Cassano', 'Edward Berman'],
        matchReason: 'Knowledge graph detected this paper EXTENDS "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models". Reflexion builds upon chain-of-thought by adding self-reflection - agents reflect on task feedback, store reflection traces in episodic memory, and improve decision-making over time through verbal reinforcement learning.',
        matchScore: 0.89
    },
    {
        new: false,
        timestamp: '4 days ago',
        rule: 'Author: Shunyu Yao',
        paperTitle: 'ReAct: Synergizing Reasoning and Acting in Language Models',
        authors: ['Shunyu Yao', 'Jeffrey Zhao', 'Dian Yu'],
        matchReason: 'New paper by tracked author Shunyu Yao. Introduces ReAct, a framework that combines reasoning and acting for language models. This is the researcher\'s follow-up work after Tree of Thoughts, continuing to advance prompting strategies for complex reasoning tasks.',
        matchScore: 1.00
    }
];

// ============================================================================
// Tab Navigation
// ============================================================================

function switchTab(tabIndex) {
    // Update tab buttons
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach((btn, index) => {
        if (index === tabIndex) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Update tab content
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach((content, index) => {
        if (index === tabIndex) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });

    currentTab = tabIndex;

    // Initialize tab-specific content
    if (tabIndex === 1) {
        // Tab 2: Load graph with current snapshot
        initializeGraphTab();
    } else if (tabIndex === 2) {
        // Tab 3: Populate alerts
        populateAlerts();
    }
}

// ============================================================================
// Tab 1: Setup Page
// ============================================================================

function simulateFileSelect() {
    const uploadZone = document.getElementById('folderUploadZone');
    const uploadIcon = document.getElementById('uploadIcon');
    const uploadText = document.getElementById('uploadText');
    const uploadSubtext = document.getElementById('uploadSubtext');
    const selectedFolder = document.getElementById('selectedFolder');
    const startButton = document.getElementById('startButton');

    // Simulate folder selection
    uploadZone.classList.add('has-files');
    uploadIcon.textContent = '✓';
    uploadText.textContent = 'Folder selected with 25 PDF files';
    uploadSubtext.textContent = 'Initial research corpus ready for processing';
    selectedFolder.style.display = 'block';

    selectedFolderFiles = 25;

    // Enable start button if email is entered
    checkStartButtonState();
}

function toggleRuleTemplate(element) {
    const checkbox = element.querySelector('.rule-checkbox');
    const isChecked = checkbox.checked;

    checkbox.checked = !isChecked;

    if (!isChecked) {
        element.classList.add('selected');
        selectedRules.push(element);
    } else {
        element.classList.remove('selected');
        const index = selectedRules.indexOf(element);
        if (index > -1) {
            selectedRules.splice(index, 1);
        }
    }

    checkStartButtonState();
}

function checkStartButtonState() {
    const emailInput = document.getElementById('userEmail');
    const startButton = document.getElementById('startButton');

    userEmail = emailInput.value.trim();

    // Enable button if folder selected, at least one rule selected, and email entered
    if (selectedFolderFiles > 0 && selectedRules.length > 0 && userEmail.length > 0) {
        startButton.disabled = false;
    } else {
        startButton.disabled = true;
    }
}

// Listen to email input
document.addEventListener('DOMContentLoaded', function() {
    const emailInput = document.getElementById('userEmail');
    if (emailInput) {
        emailInput.addEventListener('input', checkStartButtonState);
    }

    // Eagerly load papers and create snapshots on page load
    // This ensures data is ready when user switches to Tab 2
    loadPapersAndCreateSnapshots();
});

function startBuilding() {
    const progressContainer = document.getElementById('progressContainer');
    const startButton = document.getElementById('startButton');

    // Disable setup controls
    startButton.disabled = true;
    startButton.textContent = 'Building...';

    // Show progress container
    progressContainer.classList.add('active');

    // Run fake progress animation
    animateProgress();
}

function animateProgress() {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const steps = ['step1', 'step2', 'step3', 'step4', 'step5'];

    let progress = 0;
    let currentStep = 0;

    const interval = setInterval(() => {
        progress += 1;

        // Update progress bar
        progressFill.style.width = `${progress}%`;

        // Update progress text
        if (progress < 20) {
            progressText.textContent = 'Extracting text from PDFs...';
            updateStepStatus(steps, 0, 'active');
        } else if (progress < 40) {
            progressText.textContent = 'Detecting entities (titles, authors, findings)...';
            updateStepStatus(steps, 0, 'completed');
            updateStepStatus(steps, 1, 'active');
        } else if (progress < 60) {
            progressText.textContent = 'Building knowledge graph...';
            updateStepStatus(steps, 1, 'completed');
            updateStepStatus(steps, 2, 'active');
        } else if (progress < 80) {
            progressText.textContent = 'Setting up watch rules...';
            updateStepStatus(steps, 2, 'completed');
            updateStepStatus(steps, 3, 'active');
        } else if (progress < 100) {
            progressText.textContent = 'Finalizing your platform...';
            updateStepStatus(steps, 3, 'completed');
            updateStepStatus(steps, 4, 'active');
        } else {
            clearInterval(interval);
            progressText.textContent = '✅ Your Research Intelligence Platform is ready!';
            updateStepStatus(steps, 4, 'completed');

            // Auto-switch to Tab 2 after 2 seconds
            setTimeout(() => {
                switchTab(1);
            }, 2000);
        }
    }, 50); // 5 seconds total (100 steps * 50ms)
}

function updateStepStatus(steps, stepIndex, status) {
    const stepElement = document.getElementById(steps[stepIndex]);
    if (!stepElement) return;

    stepElement.classList.remove('active', 'completed');

    if (status === 'active') {
        stepElement.classList.add('active');
        stepElement.querySelector('span').textContent = '⚡';
    } else if (status === 'completed') {
        stepElement.classList.add('completed');
        stepElement.querySelector('span').textContent = '✅';
    }
}

// ============================================================================
// Tab 2: Knowledge Graph with Time Slider
// ============================================================================

function initializeGraphTab() {
    // Only load papers once (guard against multiple initializations)
    if (snapshots.length === 0) {
        loadPapersAndCreateSnapshots();
    } else {
        // Snapshots already loaded, just update the current view
        updateTimeSnapshot();
    }
}

async function loadPapersAndCreateSnapshots() {
    console.log('[DEMO] loadPapersAndCreateSnapshots() called');
    console.log('[DEMO] API_BASE_URL:', API_BASE_URL);
    console.log('[DEMO] SNAPSHOT_CONFIG length:', SNAPSHOT_CONFIG.length);

    try {
        // Fetch all papers from API
        console.log('[DEMO] Fetching papers from:', `${API_BASE_URL}/api/papers`);
        const response = await fetch(`${API_BASE_URL}/api/papers`);
        console.log('[DEMO] Response status:', response.status, response.ok);

        if (!response.ok) {
            throw new Error(`Failed to load papers: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        console.log('[DEMO] Received data:', data);

        const papers = data.papers || [];
        console.log('[DEMO] Received', papers.length, 'papers from API');

        // Sort papers chronologically by published date
        allPapers = papers.sort((a, b) => {
            const dateA = new Date(a.published || '2024-01-01');
            const dateB = new Date(b.published || '2024-01-01');
            return dateA - dateB;
        });

        // Create snapshots
        snapshots = SNAPSHOT_CONFIG.map(config => {
            return {
                ...config,
                papers: allPapers.slice(0, config.count)
            };
        });

        // Initialize with the current snapshot (index 5 = 49 papers)
        console.log('[DEMO] Loaded', allPapers.length, 'papers, created', snapshots.length, 'snapshots');
        updateTimeSnapshot();

    } catch (error) {
        console.error('[DEMO] Error loading papers:', error);
        console.error('[DEMO] Error stack:', error.stack);
        // Fallback: load graph normally
        loadGraph();
    }
}

function updateTimeSnapshot() {
    console.log('[DEMO] updateTimeSnapshot() called');
    const slider = document.getElementById('timeSlider');
    const dateLabel = document.getElementById('currentDate');
    const statPapers = document.getElementById('statPapers');
    const statNewPapers = document.getElementById('statNewPapers');

    currentSnapshotIndex = parseInt(slider.value);
    console.log('[DEMO] Slider value:', slider.value, 'Index:', currentSnapshotIndex);

    const snapshot = snapshots[currentSnapshotIndex];

    if (!snapshot) {
        // Fallback if snapshots not loaded yet
        console.log('[DEMO] No snapshot found, falling back to loadGraph()');
        loadGraph();
        return;
    }

    console.log('[DEMO] Rendering snapshot:', currentSnapshotIndex, 'with', snapshot.count, 'papers, date:', snapshot.date);

    // Update UI labels
    dateLabel.textContent = snapshot.date;
    statPapers.textContent = snapshot.count;

    // Calculate new papers
    let newPapersCount = 0;
    if (currentSnapshotIndex > 0) {
        const previousSnapshot = snapshots[currentSnapshotIndex - 1];
        newPapersCount = snapshot.count - previousSnapshot.count;
    }
    statNewPapers.textContent = newPapersCount;

    // Render graph with snapshot papers
    renderGraphSnapshot(snapshot);
}

async function renderGraphSnapshot(snapshot) {
    // Get papers for this snapshot
    const papers = snapshot.papers;

    // Determine which papers are "new" (added in this snapshot)
    let previousCount = 0;
    if (currentSnapshotIndex > 0) {
        previousCount = snapshots[currentSnapshotIndex - 1].count;
    }

    const newPaperIds = papers.slice(previousCount).map(p => p.paper_id);

    // Fetch graph data from API
    try {
        const response = await fetch(`${API_BASE_URL}/api/graph`);
        if (!response.ok) {
            throw new Error('Failed to load graph');
        }

        const graphData = await response.json();

        // Filter nodes and edges for current snapshot
        const paperIds = new Set(papers.map(p => p.paper_id));

        let filteredNodes = graphData.nodes.filter(node => paperIds.has(node.id));
        let filteredEdges = graphData.edges.filter(edge =>
            paperIds.has(edge.from) && paperIds.has(edge.to)
        );

        // Apply category-based colors to nodes (same as app.js loadGraph)
        filteredNodes = filteredNodes.map(node => {
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

        // Apply relationship-based colors to edges (same as app.js loadGraph)
        filteredEdges = filteredEdges.map(edge => {
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

        // Papers mentioned in watch rules (from Tab 1)
        const watchRulePaperTitles = [
            'Chain-of-Thought Prompting Elicits Reasoning in Large Language Models',
            'Language Models are Few-Shot Learners',
            'Visual Instruction Tuning'
        ];

        // Find watch rule paper IDs by matching titles
        const watchRulePaperIds = allPapers
            .filter(p => watchRulePaperTitles.some(title =>
                p.title && p.title.toLowerCase().includes(title.toLowerCase().substring(0, 20))
            ))
            .map(p => p.paper_id);

        // Mark new papers with orange border and shadow
        // Mark watch rule papers with purple border and shadow
        filteredNodes.forEach(node => {
            if (newPaperIds.includes(node.id)) {
                // Override border color to orange for new papers
                node.color.border = '#FFA500';
                node.borderWidth = 4;
                node.borderWidthSelected = 6;
                node.shadow = {
                    enabled: true,
                    color: 'rgba(255, 165, 0, 0.8)',
                    size: 15,
                    x: 0,
                    y: 0
                };
                node.isNew = true;
            } else if (watchRulePaperIds.includes(node.id)) {
                // Purple/blue border for watch rule papers
                node.color.border = '#9C27B0';  // Purple
                node.borderWidth = 4;
                node.borderWidthSelected = 6;
                node.shadow = {
                    enabled: true,
                    color: 'rgba(156, 39, 176, 0.6)',
                    size: 12,
                    x: 0,
                    y: 0
                };
                node.isWatchRule = true;
            }
        });

        // Update relationship count
        document.getElementById('statRelationships').textContent = filteredEdges.length;

        // Render the graph
        renderGraphWithData({ nodes: filteredNodes, edges: filteredEdges }, newPaperIds);

    } catch (error) {
        console.error('Error rendering snapshot:', error);
    }
}

function renderGraphWithData(snapshotGraphData, newPaperIds = []) {
    const container = document.getElementById('graph');

    const nodes = new vis.DataSet(snapshotGraphData.nodes);
    const edges = new vis.DataSet(snapshotGraphData.edges);

    const data = { nodes, edges };

    // Store the graph data globally so filterGraph() from app.js can access it
    window.graphData = {
        nodes: snapshotGraphData.nodes,
        edges: snapshotGraphData.edges
    };

    const options = {
        nodes: {
            shape: 'box',
            margin: 10,
            widthConstraint: {
                maximum: 200
            }
        },
        edges: {
            width: 2,
            arrows: {
                to: {
                    enabled: true,
                    scaleFactor: 0.5
                }
            },
            smooth: {
                type: 'continuous',
                roundness: 0.5
            }
        },
        physics: {
            barnesHut: {
                gravitationalConstant: -8000,
                centralGravity: 0.3,
                springLength: 150,
                springConstant: 0.04,
                damping: 0.95
            },
            stabilization: {
                iterations: 200
            }
        },
        interaction: {
            hover: true,
            tooltipDelay: 200,
            navigationButtons: false,
            keyboard: true
        }
    };

    // Create or update network
    if (window.network) {
        window.network.setData(data);
        network = window.network; // Also set app.js's global network variable
    } else {
        window.network = new vis.Network(container, data, options);
        network = window.network; // Also set app.js's global network variable

        // Add click handler
        window.network.on('click', function(params) {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                showPaperDetails(nodeId);
            }
        });
    }

    // Add pulsing animation to new papers
    if (newPaperIds.length > 0) {
        animateNewPapers(newPaperIds);
    }
}

function animateNewPapers(newPaperIds) {
    // Add CSS animation class to new nodes
    // This is a simple approach - for more complex animations, you'd manipulate the nodes directly

    // Create a style element for the pulsing glow if it doesn't exist
    if (!document.getElementById('newPaperStyles')) {
        const style = document.createElement('style');
        style.id = 'newPaperStyles';
        style.textContent = `
            @keyframes newPaperPulse {
                0%, 100% {
                    box-shadow: 0 0 10px 4px rgba(255, 165, 0, 0.6);
                }
                50% {
                    box-shadow: 0 0 20px 8px rgba(255, 165, 0, 0.9);
                }
            }
        `;
        document.head.appendChild(style);
    }

    // Note: vis-network doesn't directly support CSS animations on nodes
    // The pulsing effect is simulated through the borderWidth property
    // For a true pulsing glow, you'd need to use a canvas-based approach or custom rendering
}

// ============================================================================
// Tab 3: Alerts Inbox
// ============================================================================

function populateAlerts() {
    const alertsList = document.getElementById('alertsList');
    const alertsCount = document.getElementById('alertsCount');

    // Count new alerts
    const newAlertsCount = SAMPLE_ALERTS.filter(alert => alert.new).length;
    alertsCount.textContent = `${newAlertsCount} new alert${newAlertsCount !== 1 ? 's' : ''}`;

    // Clear existing alerts
    alertsList.innerHTML = '';

    // Populate alerts
    SAMPLE_ALERTS.forEach((alert, index) => {
        const alertCard = createAlertCard(alert, index);
        alertsList.appendChild(alertCard);
    });
}

function createAlertCard(alert, index) {
    const card = document.createElement('div');
    card.className = `alert-card ${alert.new ? 'new' : ''}`;

    card.innerHTML = `
        <div class="alert-header">
            <span class="alert-badge ${alert.new ? 'new' : 'read'}">${alert.new ? 'NEW' : 'READ'}</span>
            <span class="alert-timestamp">${alert.timestamp}</span>
        </div>
        <div class="alert-rule">${alert.rule}</div>
        <div class="alert-paper-title">${alert.paperTitle}</div>
        <div class="alert-paper-authors">${alert.authors.join(', ')}</div>
        <div class="alert-match-reason">
            <strong>Why this matched:</strong> ${alert.matchReason}
            <span class="alert-match-score">${Math.round(alert.matchScore * 100)}% match</span>
        </div>
        <div class="alert-actions">
            <button class="btn-alert" onclick="viewPaperInGraph('${alert.paperTitle}')">View in Graph</button>
            <button class="btn-alert" onclick="markAsRead(${index})">Mark as Read</button>
        </div>
    `;

    return card;
}

function markAsRead(index) {
    SAMPLE_ALERTS[index].new = false;
    populateAlerts();
}

function viewPaperInGraph(paperTitle) {
    // Switch to Tab 2 and highlight the paper
    switchTab(1);

    // Find paper and focus on it in the graph
    // This would require extending the graph rendering logic
    console.log(`Switching to graph view for: ${paperTitle}`);
}

// ============================================================================
// Shared Graph Functions (Compatible with app.js)
// ============================================================================

// Note: filterGraph() is defined in app.js and works with the graphData variable
// We don't need to override it - it will work with the graph data we set via network.setData()

// Override resetGraphView to work with demo's snapshot system
function resetGraphView() {
    if (window.network) {
        window.network.fit();
        const filterSelect = document.getElementById('relationshipFilter');
        if (filterSelect) {
            filterSelect.value = 'all';
        }
        // Re-render current snapshot to reset any filters
        if (snapshots.length > 0) {
            updateTimeSnapshot();
        }
    }
}

// togglePhysics is already defined in app.js and should work as-is
// But we'll keep a reference here for clarity
if (typeof togglePhysics === 'undefined') {
    function togglePhysics() {
        if (!window.network) return;

        const btn = document.getElementById('togglePhysicsBtn');
        const currentPhysics = window.network.physics.physicsEnabled;

        window.network.setOptions({
            physics: { enabled: !currentPhysics }
        });

        if (btn) {
            btn.textContent = !currentPhysics ? '❄️ Freeze Graph' : '▶️ Unfreeze Graph';
        }
    }
}

// ============================================================================
// Initialize Demo
// ============================================================================

console.log('Demo mode initialized');
console.log('Snapshots:', SNAPSHOT_CONFIG);
console.log('Sample alerts:', SAMPLE_ALERTS.length);
