/**
 * MullBar — Flask Frontend (main.js)
 * Exact port of all React components to vanilla JavaScript.
 * Components: LandingHero, FileUpload, LoadingScreen, Dashboard,
 *   SummaryCards, GraphVisualization, ExplainabilityPanel,
 *   FraudRingTable, RiskHeatmap, DownloadButton
 */

// ─── Global State ─────────────────────────────
let appState = 'landing'; // landing | loading | results
let selectedFile = null;
let analysisData = null;
let darkMode = false;
let selectedAccount = null;
let activeTab = 'graph';
let cyInstance = null;

// ─── Loading Stages ───────────────────────────
const STAGES = [
    { label: 'Building Transaction Graph', icon: '🔗' },
    { label: 'Running Cycle Detection', icon: '🔄' },
    { label: 'Analyzing Smurfing Patterns', icon: '🐜' },
    { label: 'Detecting Shell Networks', icon: '🏗️' },
    { label: 'Computing Temporal Features', icon: '⏱️' },
    { label: 'Evaluating Behavioral Metrics', icon: '📊' },
    { label: 'Scoring Risk Factors', icon: '🧮' },
    { label: 'Mapping Fraud Rings', icon: '🧿' },
    { label: 'Generating Explanations', icon: '🧠' },
];

let loadingInterval = null;
let currentLoadingStage = 0;

// ─── Factor Labels ────────────────────────────
const FACTOR_LABELS = {
    cycle: 'Cycle Involvement',
    smurfing: 'Smurfing',
    shell_network: 'Shell Network',
    velocity: 'Transaction Velocity',
    volume_anomaly: 'Volume Anomaly',
    circular_flow: 'Circular Flow',
};

const PATTERN_LABELS = {
    cycle: 'Cycle',
    fan_in: 'Fan-In Smurfing',
    fan_out: 'Fan-Out Smurfing',
    shell_network: 'Shell Network',
};

// ─── Graph Colors (Fixed Dark Palette) ────────
const GRAPH_COLORS = {
    safe: '#982598',
    medium: '#E491C9',
    high: '#F1E9E9',
    bg: '#15173D',
    border: '#2A2D5C',
};

function scoreColor(score) {
    if (score >= 80) return 'var(--color-danger)';
    if (score >= 40) return 'var(--color-warning)';
    return 'var(--color-success)';
}

function graphScoreColor(score) {
    if (score >= 80) return GRAPH_COLORS.high;
    if (score >= 40) return GRAPH_COLORS.medium;
    return GRAPH_COLORS.safe;
}

function formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
}

// ─── App State Management ─────────────────────
function setState(newState) {
    appState = newState;
    document.getElementById('state-landing').classList.toggle('hidden', newState !== 'landing');
    document.getElementById('state-loading').classList.toggle('hidden', newState !== 'loading');
    document.getElementById('state-results').classList.toggle('hidden', newState !== 'results');
    document.getElementById('new-analysis-btn').classList.toggle('hidden', newState !== 'results');
}

function resetApp() {
    selectedFile = null;
    analysisData = null;
    selectedAccount = null;
    activeTab = 'graph';
    if (cyInstance) { cyInstance.destroy(); cyInstance = null; }
    if (loadingInterval) { clearInterval(loadingInterval); loadingInterval = null; }
    currentLoadingStage = 0;
    setState('landing');

    // Reset file upload UI
    document.getElementById('drop-zone-text').classList.remove('hidden');
    document.getElementById('drop-zone-file').classList.add('hidden');
    document.getElementById('analyze-btn').classList.add('hidden');
    document.getElementById('error-banner').classList.add('hidden');
}

// ─── Theme ────────────────────────────────────
function toggleTheme() {
    darkMode = !darkMode;
    document.documentElement.classList.toggle('dark', darkMode);
    document.getElementById('theme-icon').textContent = darkMode ? '☀️' : '🌙';
}

// ─── File Upload ──────────────────────────────
function handleFileSelect(file) {
    if (!file || !file.name.toLowerCase().endsWith('.csv')) return;
    selectedFile = file;
    document.getElementById('drop-zone-text').classList.add('hidden');
    document.getElementById('drop-zone-file').classList.remove('hidden');
    document.getElementById('file-name').textContent = file.name;
    document.getElementById('file-size').textContent = formatSize(file.size);
    document.getElementById('analyze-btn').classList.remove('hidden');
}

function removeFile(e) {
    e.stopPropagation();
    selectedFile = null;
    document.getElementById('drop-zone-text').classList.remove('hidden');
    document.getElementById('drop-zone-file').classList.add('hidden');
    document.getElementById('analyze-btn').classList.add('hidden');
}

function showError(msg) {
    const banner = document.getElementById('error-banner');
    banner.textContent = '⚠️ ' + msg;
    banner.classList.remove('hidden');
}

// ─── Loading Screen ───────────────────────────
function startLoading() {
    setState('loading');
    currentLoadingStage = 0;
    renderLoadingStages();
    loadingInterval = setInterval(() => {
        if (currentLoadingStage < STAGES.length - 1) {
            currentLoadingStage++;
            renderLoadingStages();
        }
    }, 800);
}

function renderLoadingStages() {
    const stage = STAGES[currentLoadingStage];
    document.getElementById('loading-icon').textContent = stage.icon;
    document.getElementById('loading-stage').textContent = stage.label;

    const progress = ((currentLoadingStage + 1) / STAGES.length) * 100;
    document.getElementById('loading-bar').style.width = `${progress}%`;

    const container = document.getElementById('loading-stages');
    container.innerHTML = STAGES.map((s, i) => `
        <div class="flex items-center gap-2 transition-opacity duration-300" style="opacity: ${i <= currentLoadingStage ? 1 : 0.3}">
            <span class="w-4 h-4 sm:w-5 sm:h-5 rounded-full flex items-center justify-center text-xs text-white shrink-0"
                  style="background: ${i < currentLoadingStage ? 'var(--color-accent-green)' : i === currentLoadingStage ? 'var(--color-olive)' : 'var(--color-border)'}">
                ${i < currentLoadingStage ? '✓' : i === currentLoadingStage ? '…' : ''}
            </span>
            <span class="truncate" style="color: ${i <= currentLoadingStage ? 'var(--color-dark)' : 'var(--color-muted)'}">
                ${s.label}
            </span>
        </div>
    `).join('');
}

// ─── API Call ─────────────────────────────────
async function analyzeFile() {
    if (!selectedFile) return;
    document.getElementById('error-banner').classList.add('hidden');
    startLoading();

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData,
        });

        if (loadingInterval) { clearInterval(loadingInterval); loadingInterval = null; }

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Server error response:', errorText);
            showError(`Server Error (${response.status}): ${response.statusText}`);
            setState('landing');
            return;
        }

        let data;
        try {
            data = await response.json();
        } catch (jsonErr) {
            console.error('JSON Parse Error:', jsonErr);
            showError('Server returned an invalid response. Check console for details.');
            setState('landing');
            return;
        }

        if (data.status === 'success') {
            analysisData = data;
            renderDashboard(data);
            setState('results');
        } else {
            showError(data.detail || 'Analysis failed.');
            setState('landing');
        }
    } catch (err) {
        if (loadingInterval) { clearInterval(loadingInterval); loadingInterval = null; }
        console.error('Fetch Error:', err);
        showError(err.message || 'Network error or connection lost.');
        setState('landing');
    }
}

// ═══════════════════════════════════════════════
//  DASHBOARD RENDERING
// ═══════════════════════════════════════════════

function renderDashboard(data) {
    const { results, graph, explanations } = data;
    selectedAccount = null;
    activeTab = 'graph';

    const container = document.getElementById('state-results');
    container.innerHTML = `
        <div class="space-y-4 sm:space-y-6 fade-in w-full">
            <!-- Summary Cards -->
            <div id="summary-cards" class="w-full"></div>

            <!-- Action Bar -->
            <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 w-full">
                <div class="flex gap-1 p-1 rounded-lg overflow-x-auto shrink-0 max-w-full"
                     style="background: var(--color-white); border: 1px solid var(--color-border);">
                    <button class="tab-btn btn-hover px-3 sm:px-4 py-1.5 sm:py-2 rounded-md text-xs sm:text-sm font-medium transition-all duration-200 whitespace-nowrap" data-tab="graph">📊 Graph</button>
                    <button class="tab-btn btn-hover px-3 sm:px-4 py-1.5 sm:py-2 rounded-md text-xs sm:text-sm font-medium transition-all duration-200 whitespace-nowrap" data-tab="rings">🧿 Rings</button>
                    <button class="tab-btn btn-hover px-3 sm:px-4 py-1.5 sm:py-2 rounded-md text-xs sm:text-sm font-medium transition-all duration-200 whitespace-nowrap" data-tab="heatmap">🌡️ Heatmap</button>
                </div>
                <div class="shrink-0">
                    <button id="download-btn"
                        class="btn-hover flex items-center justify-center gap-1.5 sm:gap-2 px-3 sm:px-5 py-2 sm:py-2.5 rounded-lg text-xs sm:text-sm font-semibold text-white w-full sm:w-auto"
                        style="background: var(--color-accent-green);">
                        <svg class="w-3.5 h-3.5 sm:w-4 sm:h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                            <polyline points="7 10 12 15 17 10"/>
                            <line x1="12" y1="15" x2="12" y2="3"/>
                        </svg>
                        <span class="whitespace-nowrap">Download JSON</span>
                    </button>
                </div>
            </div>

            <!-- Main Content: Graph/Tabs full width -->
            <div class="w-full min-w-0 flex flex-col gap-4">
                <div id="tab-graph" class="fade-scale-in h-full"></div>
                <div id="tab-rings" class="fade-scale-in h-full hidden"></div>
                <div id="tab-heatmap" class="fade-scale-in h-full hidden"></div>
            </div>
            <!-- Explainability Panel below -->
            <div class="w-full min-w-0">
                <div id="explainability-panel"></div>
            </div>
        </div>
    `;

    // Render all components
    renderSummaryCards(results.summary);
    renderGraphVisualization(graph);
    renderFraudRingTable(results.fraud_rings);
    renderHeatmap(results.suspicious_accounts);
    renderExplainabilityPanel(explanations, results.suspicious_accounts, null);
    updateTabStyles();

    // Event Listeners
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            activeTab = btn.dataset.tab;
            document.getElementById('tab-graph').classList.toggle('hidden', activeTab !== 'graph');
            document.getElementById('tab-rings').classList.toggle('hidden', activeTab !== 'rings');
            document.getElementById('tab-heatmap').classList.toggle('hidden', activeTab !== 'heatmap');
            updateTabStyles();

            // Re-render graph on tab switch to ensure proper sizing
            if (activeTab === 'graph' && cyInstance) {
                setTimeout(() => cyInstance.resize(), 100);
            }
        });
    });

    document.getElementById('download-btn').addEventListener('click', () => {
        // --- DYNAMIC TRANSFORMATION TO ACCOUNT-CENTRIC FORMAT ---
        const flatData = analysisData.results;
        const summary = flatData.summary;
        const accounts = flatData.suspicious_accounts;
        const rings = flatData.fraud_rings;

        const ringsMap = {};
        rings.forEach(r => { ringsMap[r.ring_id] = r; });

        const resultsList = accounts.map(acc => {
            const ring = ringsMap[acc.ring_id] || {
                ring_id: "N/A", member_accounts: [], pattern_type: "none", risk_score: 0
            };
            return {
                suspicious_account: acc,
                fraud_ring: ring,
                summary: summary
            };
        });

        const exportObj = {
            results: resultsList,
            summary: summary
        };
        // ---------------------------------------------------------

        const json = JSON.stringify(exportObj, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'mullbar_results.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });
}

function updateTabStyles() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        const isActive = btn.dataset.tab === activeTab;
        btn.style.background = isActive ? 'var(--color-deep-brown)' : 'transparent';
        btn.style.color = isActive ? 'var(--color-white)' : 'var(--color-muted)';
    });
}

// ─── Summary Cards ────────────────────────────
function renderSummaryCards(summary) {
    const cards = [
        { label: 'Total Accounts', value: (summary.total_accounts_analyzed || 0).toLocaleString(), icon: '👥', color: 'var(--color-accent-purple)' },
        { label: 'Suspicious Flagged', value: (summary.suspicious_accounts_flagged || 0).toLocaleString(), icon: '🚨', color: 'var(--color-danger)' },
        { label: 'Fraud Rings', value: (summary.fraud_rings_detected || 0).toLocaleString(), icon: '🧿', color: 'var(--color-text-main)' },
        { label: 'Processing Time', value: `${(summary.processing_time_seconds || 0).toFixed(2)}s`, icon: '⚡', color: 'var(--color-accent-pink)' },
    ];

    document.getElementById('summary-cards').innerHTML = `
        <div class="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-3 md:gap-4 w-full">
            ${cards.map((card, i) => `
                <div class="card p-3 sm:p-4 md:p-5 slide-up stagger-${i + 1} flex flex-col justify-between transition-colors duration-300">
                    <div>
                        <div class="flex items-center justify-between mb-2 sm:mb-3">
                            <span class="text-lg sm:text-xl md:text-2xl filter drop-shadow-sm">${card.icon}</span>
                            <span class="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full shrink-0 shadow-sm" style="background: ${card.color};"></span>
                        </div>
                        <p class="text-lg sm:text-xl md:text-2xl font-bold truncate" style="color: ${card.color};">${card.value}</p>
                    </div>
                    <p class="text-xs font-medium mt-0.5 sm:mt-1 truncate opacity-70" style="color: var(--color-text-muted);">${card.label}</p>
                </div>
            `).join('')}
        </div>
    `;
}

// ─── Graph Visualization ──────────────────────
function renderGraphVisualization(graphData) {
    if (!graphData) return;

    document.getElementById('tab-graph').innerHTML = `
        <div class="card overflow-hidden">
            <div class="px-3 sm:px-4 py-2.5 sm:py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2"
                 style="border-bottom: 1px solid var(--color-border);">
                <h3 class="font-semibold text-xs sm:text-sm" style="color: var(--color-text-main);">Transaction Graph</h3>
                <div class="flex flex-wrap items-center gap-2 sm:gap-4 text-xs" style="color: var(--color-text-muted);">
                    <span class="flex items-center gap-1">
                        <span class="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full shrink-0 shadow-[0_0_8px_rgba(241,233,233,0.6)]" style="background: #F1E9E9;"></span> Critical
                    </span>
                    <span class="flex items-center gap-1">
                        <span class="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full shrink-0" style="background: #E491C9;"></span> Medium
                    </span>
                    <span class="flex items-center gap-1">
                        <span class="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full shrink-0" style="background: #982598;"></span> Low
                    </span>
                    <span class="flex items-center gap-1">
                        <span class="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full shrink-0" style="background: #2A2D5C; border: 1px solid #444;"></span> Safe
                    </span>
                </div>
            </div>
            <div class="relative">
                <div id="cy" class="graph-container" style="height: clamp(400px, 60vw, 800px); background: #15173D;"></div>
                <div id="graph-tooltip" class="absolute top-2 left-2 sm:top-3 sm:left-3 card p-2 sm:p-3 text-xs space-y-0.5 sm:space-y-1 fade-in z-10 hidden"
                     style="max-width: 200px; pointer-events: none; background: rgba(21,23,61,0.95); backdrop-filter: blur(8px); border: 1px solid #2A2D5C; color: #F1E9E9;"></div>
            </div>
        </div>
    `;

    initCytoscape(graphData);
}

function initCytoscape(graphData) {
    if (cyInstance) { cyInstance.destroy(); cyInstance = null; }

    const elements = [];

    // Process nodes
    graphData.nodes.forEach(node => {
        const d = node.data;
        elements.push({
            group: 'nodes',
            data: {
                ...d,
                bg: d.suspicious ? graphScoreColor(d.score) : '#2A2D5C',
                size: d.suspicious ? Math.max(30, 20 + d.score * 0.4) : 15,
                labelColor: d.suspicious ? '#F1E9E9' : '#A3A3C2',
            },
        });
    });

    // Process edges
    graphData.edges.forEach(edge => {
        elements.push({ group: 'edges', data: edge.data });
    });

    cyInstance = cytoscape({
        container: document.getElementById('cy'),
        elements,
        style: [
            {
                selector: 'node',
                style: {
                    'background-color': 'data(bg)',
                    'border-width': 0,
                    'label': 'data(label)',
                    'font-size': '10px',
                    'text-valign': 'bottom',
                    'text-margin-y': 6,
                    'color': 'data(labelColor)',
                    'width': 'data(size)',
                    'height': 'data(size)',
                    'text-outline-width': 0,
                    'text-outline-color': '#0B0C1E',
                },
            },
            {
                selector: 'edge',
                style: {
                    'width': 1,
                    'line-color': '#F1E9E9',
                    'target-arrow-color': '#F1E9E9',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'arrow-scale': 0.8,
                    'opacity': 0.6,
                },
            },
            {
                selector: 'node[suspicious]',
                style: {
                    'font-weight': 'bold',
                    'shadow-blur': 10,
                    'shadow-color': 'data(bg)',
                    'shadow-opacity': 0.5,
                },
            },
            {
                selector: ':selected',
                style: {
                    'border-width': 2,
                    'border-color': '#F1E9E9',
                    'shadow-blur': 20,
                    'shadow-opacity': 0.8,
                },
            },
        ],
        layout: (() => {
            const nodeCount = graphData.nodes.length;
            const isLarge = nodeCount > 100;
            return {
                name: 'cose',
                animate: !isLarge,
                animationDuration: isLarge ? 0 : 800,
                nodeRepulsion: () => isLarge ? 40000 : 8000,
                idealEdgeLength: () => isLarge ? 200 : 80,
                gravity: isLarge ? 0.02 : 0.2,
                padding: isLarge ? 60 : 30,
                componentSpacing: isLarge ? 200 : 60,
                numIter: isLarge ? 800 : 1000,
                fit: true,
            };
        })(),
        maxZoom: 5,
        minZoom: 0.2,
        textureOnViewport: graphData.nodes.length > 100,
        hideEdgesOnViewport: graphData.nodes.length > 150,
    });

    // Center graph after layout completes
    cyInstance.on('layoutstop', () => {
        cyInstance.fit(undefined, 40);
        cyInstance.center();
    });

    // Fallback for non-animated layouts
    setTimeout(() => {
        cyInstance.resize();
        cyInstance.fit(undefined, 40);
        cyInstance.center();
    }, 200);

    // Click handler — select suspicious node
    cyInstance.on('tap', 'node', evt => {
        const nodeData = evt.target.data();
        if (nodeData.suspicious) {
            selectedAccount = nodeData.id;
            renderExplainabilityPanel(
                analysisData.explanations,
                analysisData.results.suspicious_accounts,
                selectedAccount
            );
        }
    });

    // Hover handlers
    cyInstance.on('mouseover', 'node', evt => {
        const d = evt.target.data();
        evt.target.style('cursor', 'pointer');
        const tooltip = document.getElementById('graph-tooltip');
        let html = `<p class="font-bold">${d.id}</p>`;
        if (d.suspicious) {
            html += `<p style="color: ${graphScoreColor(d.score)}">Risk Score: ${d.score}/100</p>`;
        }
        html += `<p class="text-gray-300">Sent: $${(d.total_sent || 0).toLocaleString()}</p>`;
        html += `<p class="text-gray-300">Received: $${(d.total_received || 0).toLocaleString()}</p>`;
        html += `<p class="text-gray-300">Transactions: ${d.transaction_count || 0}</p>`;
        if (d.patterns && d.patterns.length > 0) {
            html += `<p class="font-medium" style="color: #E491C9;">${d.patterns.join(', ')}</p>`;
        }
        tooltip.innerHTML = html;
        tooltip.classList.remove('hidden');
    });

    cyInstance.on('mouseout', 'node', () => {
        document.getElementById('graph-tooltip').classList.add('hidden');
    });
}

// ─── Fraud Ring Table ─────────────────────────
function renderFraudRingTable(rings) {
    const container = document.getElementById('tab-rings');

    if (!rings || rings.length === 0) {
        container.innerHTML = `
            <div class="card p-6 sm:p-8 text-center transition-colors duration-300">
                <p class="text-xs sm:text-sm" style="color: var(--color-text-muted);">No fraud rings detected in this dataset.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="card overflow-hidden transition-colors duration-300">
            <div class="px-3 sm:px-4 py-2.5 sm:py-3" style="border-bottom: 1px solid var(--color-border);">
                <h3 class="font-semibold text-xs sm:text-sm" style="color: var(--color-text-main);">
                    🧿 Fraud Rings Detected (${rings.length})
                </h3>
            </div>
            <div class="overflow-x-auto w-full">
                <table class="w-full text-xs sm:text-sm" style="min-width: 400px;">
                    <thead>
                        <tr style="background: var(--color-primary-bg);">
                            <th class="text-left px-3 sm:px-4 py-2 sm:py-3 font-semibold text-xs uppercase tracking-wider" style="color: var(--color-text-muted);">Ring ID</th>
                            <th class="text-left px-3 sm:px-4 py-2 sm:py-3 font-semibold text-xs uppercase tracking-wider" style="color: var(--color-text-muted);">Pattern Type</th>
                            <th class="text-center px-3 sm:px-4 py-2 sm:py-3 font-semibold text-xs uppercase tracking-wider" style="color: var(--color-text-muted);">Members</th>
                            <th class="text-center px-3 sm:px-4 py-2 sm:py-3 font-semibold text-xs uppercase tracking-wider" style="color: var(--color-text-muted);">Risk</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rings.map((ring, i) => `
                            <!-- Main Row -->
                            <tr class="ring-row transition-colors duration-150 hover:bg-black/5 dark:hover:bg-white/5 cursor-pointer"
                                style="${i > 0 ? 'border-top: 1px solid var(--color-border);' : ''}"
                                onclick="toggleRingDetails('details-${ring.ring_id}', this)">
                                <td class="px-3 sm:px-4 py-2 sm:py-3">
                                    <span class="font-mono font-bold text-xs px-1.5 sm:px-2 py-0.5 sm:py-1 rounded border flex items-center gap-1.5 w-fit"
                                          style="background: rgba(152,37,152,0.1); color: var(--color-text-main); border-color: rgba(152,37,152,0.3);">
                                        <svg class="ring-chevron w-2.5 h-2.5 transform transition-transform duration-200" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                                            <polyline points="9 18 15 12 9 6"></polyline>
                                        </svg>
                                        ${ring.ring_id}
                                    </span>
                                </td>
                                <td class="px-3 sm:px-4 py-2 sm:py-3">
                                    <span class="px-2 sm:px-2.5 py-0.5 sm:py-1 rounded-full text-xs font-medium whitespace-nowrap border"
                                          style="background: rgba(228,145,201,0.1); color: var(--color-accent-pink); border-color: rgba(228,145,201,0.3);">
                                        ${PATTERN_LABELS[ring.pattern_type] || ring.pattern_type}
                                    </span>
                                </td>
                                <td class="px-3 sm:px-4 py-2 sm:py-3 text-center font-semibold" style="color: var(--color-text-main);">
                                    ${ring.member_accounts ? ring.member_accounts.length : 0}
                                </td>
                                <td class="px-3 sm:px-4 py-2 sm:py-3 text-center">
                                    <span class="font-bold" style="color: ${scoreColor(ring.risk_score)};">
                                        ${ring.risk_score || 0}
                                    </span>
                                </td>
                            </tr>
                            <!-- Detail Row -->
                            <tr id="details-${ring.ring_id}" class="hidden" style="background: rgba(0,0,0,0.02);">
                                <td colspan="4" class="px-3 sm:px-4 py-3 sm:py-4">
                                    <div class="flex flex-col gap-2 slide-up">
                                        <p class="text-[10px] uppercase tracking-wider font-bold opacity-50" style="color: var(--color-text-muted);">Member Accounts</p>
                                        <p class="text-xs break-all leading-relaxed font-mono" style="color: var(--color-text-main);">
                                            ${(ring.member_accounts || []).join(', ')}
                                        </p>
                                    </div>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

/**
 * Toggle Fraud Ring Detail Row
 */
function toggleRingDetails(id, rowEl) {
    const detailRow = document.getElementById(id);
    const chevron = rowEl.querySelector('.ring-chevron');

    if (detailRow) {
        const isHidden = detailRow.classList.toggle('hidden');
        if (chevron) {
            chevron.style.transform = isHidden ? 'rotate(0deg)' : 'rotate(90deg)';
        }
        // Update row background for better context
        rowEl.style.background = isHidden ? '' : 'rgba(0,0,0,0.04)';
    }
}

// ─── Risk Heatmap ─────────────────────────────
function renderHeatmap(accounts) {
    const container = document.getElementById('tab-heatmap');

    if (!accounts || accounts.length === 0) {
        container.innerHTML = `
            <div class="card p-6 sm:p-8 text-center transition-colors duration-300">
                <p class="text-xs sm:text-sm" style="color: var(--color-text-muted);">No suspicious accounts to visualize.</p>
            </div>
        `;
        return;
    }

    const sorted = [...accounts].sort((a, b) => b.suspicion_score - a.suspicion_score);

    container.innerHTML = `
        <div class="card overflow-hidden transition-colors duration-300">
            <div class="px-3 sm:px-4 py-2.5 sm:py-3" style="border-bottom: 1px solid var(--color-border);">
                <h3 class="font-semibold text-xs sm:text-sm" style="color: var(--color-text-main);">🌡️ Risk Heatmap</h3>
                <p class="text-xs mt-0.5" style="color: var(--color-text-muted);">Accounts sized by risk score.</p>
            </div>
            <div class="p-3 sm:p-4">
                <div class="flex flex-wrap items-center justify-center gap-2 sm:gap-4 md:gap-6 mb-3 sm:mb-4 text-xs transition-colors duration-300" style="color: var(--color-text-muted);">
                    <span class="flex items-center gap-1">
                        <span class="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded shrink-0" style="background: var(--color-danger);"></span> Critical (80+)
                    </span>
                    <span class="flex items-center gap-1">
                        <span class="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded shrink-0" style="background: var(--color-warning);"></span> Medium (40-79)
                    </span>
                    <span class="flex items-center gap-1">
                        <span class="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded shrink-0" style="background: var(--color-success);"></span> Low (&lt;40)
                    </span>
                </div>
                <div class="flex flex-wrap gap-1.5 sm:gap-2 justify-center">
                    ${sorted.map(acc => {
        const size = Math.max(50, 35 + acc.suspicion_score * 0.5);
        let colorVar = 'var(--color-success)';
        if (acc.suspicion_score >= 80) colorVar = 'var(--color-danger)';
        else if (acc.suspicion_score >= 40) colorVar = 'var(--color-warning)';

        return `
                            <div class="rounded-lg flex flex-col items-center justify-center cursor-pointer btn-hover relative overflow-hidden transition-all duration-300"
                                 style="width: ${size}px; height: ${size}px;
                                        background-color: color-mix(in srgb, ${colorVar}, transparent 85%);
                                        border: 1px solid ${colorVar};
                                        ${acc.suspicion_score >= 80 ? `box-shadow: 0 0 10px ${colorVar};` : ''}"
                                 title="${acc.account_id}: ${acc.suspicion_score}/100">
                                <div class="relative z-10 text-center flex flex-col items-center">
                                    <span class="text-xs font-bold block" style="color: ${colorVar};">${acc.suspicion_score}</span>
                                    <span class="text-[9px] font-medium truncate px-0.5 sm:px-1 block"
                                          style="color: var(--color-text-muted); max-width: ${size - 6}px;">${acc.account_id}</span>
                                </div>
                            </div>
                        `;
    }).join('')}
                </div>
            </div>
        </div>
    `;
}

// ─── Explainability Panel ─────────────────────
function renderExplainabilityPanel(explanations, accounts, selected) {
    const panel = document.getElementById('explainability-panel');
    if (!panel) return;

    const explanation = selected ? (explanations || {})[selected] : null;
    const sortedAccounts = [...(accounts || [])].sort((a, b) => b.suspicion_score - a.suspicion_score);

    if (!explanation) {
        // Account List View
        panel.innerHTML = `
            <div class="card p-0 overflow-hidden flex flex-col h-full bg-opacity-90 backdrop-blur-md transition-colors duration-300"
                 style="max-height: 660px;">
                <div class="px-3 sm:px-4 py-2.5 sm:py-3 sticky top-0 z-10 transition-colors duration-300"
                     style="border-bottom: 1px solid var(--color-border); background: var(--color-card-bg);">
                    <h3 class="font-semibold text-xs sm:text-sm" style="color: var(--color-text-main);">
                        🧠 Suspicious Accounts
                    </h3>
                </div>
                <div class="overflow-y-auto flex-1 custom-scrollbar" style="max-height: 600px;">
                    <div class="divide-y" style="border-color: var(--color-border);">
                        ${sortedAccounts.length === 0 ? `
                            <p class="p-4 text-xs sm:text-sm text-center" style="color: var(--color-text-muted);">
                                No suspicious accounts detected.
                            </p>
                        ` : sortedAccounts.slice(0, 30).map(acc => `
                            <button class="account-btn w-full text-left px-3 sm:px-4 py-2.5 sm:py-3 hover:bg-black/5 dark:hover:bg-white/5 transition-colors duration-150 flex items-center justify-between gap-2 border-l-4 border-transparent hover:border-l-[var(--color-accent-pink)]"
                                    data-account-id="${acc.account_id}">
                                <div class="min-w-0">
                                    <p class="text-xs sm:text-sm font-semibold truncate" style="color: var(--color-text-main);">${acc.account_id}</p>
                                    <p class="text-xs truncate" style="color: var(--color-text-muted);">${(acc.detected_patterns || []).slice(0, 2).join(', ')}</p>
                                </div>
                                <div class="text-right shrink-0">
                                    <span class="text-xs sm:text-sm font-bold" style="color: ${scoreColor(acc.suspicion_score)};">${acc.suspicion_score}</span>
                                    <span class="text-xs" style="color: var(--color-text-muted);">/100</span>
                                </div>
                            </button>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        // Add click handlers
        panel.querySelectorAll('.account-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                selectedAccount = btn.dataset.accountId;
                renderExplainabilityPanel(explanations, accounts, selectedAccount);
            });
        });
    } else {
        // Detail Breakdown View
        panel.innerHTML = `
            <div class="card p-0 overflow-hidden flex flex-col h-full bg-opacity-90 backdrop-blur-md transition-colors duration-300"
                 style="max-height: 660px;">
                <div class="px-3 sm:px-4 py-2.5 sm:py-3 sticky top-0 z-10 transition-colors duration-300"
                     style="border-bottom: 1px solid var(--color-border); background: var(--color-card-bg);">
                    <h3 class="font-semibold text-xs sm:text-sm" style="color: var(--color-text-main);">
                        🧠 Risk Breakdown
                    </h3>
                    <button id="back-to-list" class="text-xs underline mt-1 block hover:opacity-80 transition-opacity"
                            style="color: var(--color-accent-pink);">← Back to list</button>
                </div>
                <div class="overflow-y-auto flex-1 custom-scrollbar" style="max-height: 600px;">
                    <div class="p-3 sm:p-4 space-y-4 sm:space-y-5 fade-in">
                        <!-- Score Header -->
                        <div class="text-center p-3 sm:p-4 rounded-xl border"
                             style="background: var(--color-primary-bg); border-color: var(--color-border);">
                            <p class="text-xs font-medium mb-1" style="color: var(--color-text-muted);">Risk Score</p>
                            <p class="text-3xl sm:text-4xl font-extrabold" style="color: ${scoreColor(explanation.suspicion_score)};">
                                ${explanation.suspicion_score}
                                <span class="text-base sm:text-lg font-normal opacity-60">/100</span>
                            </p>
                            <p class="text-xs font-medium mt-1 truncate" style="color: var(--color-text-main);">${selected}</p>
                        </div>

                        <!-- Factor Breakdown Bars -->
                        <div>
                            <h4 class="text-xs font-semibold mb-2 sm:mb-3 uppercase tracking-wider opacity-70"
                                style="color: var(--color-text-muted);">Score Breakdown</h4>
                            <div class="space-y-2 sm:space-y-3">
                                ${(explanation.risk_breakdown || []).map(factor => `
                                    <div>
                                        <div class="flex items-center justify-between mb-1">
                                            <span class="text-xs font-medium truncate mr-2" style="color: var(--color-text-main);">
                                                ${FACTOR_LABELS[factor.factor] || factor.factor}
                                            </span>
                                            <span class="text-xs font-bold shrink-0" style="color: var(--color-text-main);">${factor.score}</span>
                                        </div>
                                        <div class="risk-bar" style="background: var(--color-border);">
                                            <div class="risk-bar-fill"
                                                 style="width: ${factor.score}%; background: var(--color-accent-pink); box-shadow: 0 0 5px rgba(228,145,201,0.3);"></div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>

                        <!-- Detected Patterns -->
                        <div>
                            <h4 class="text-xs font-semibold mb-2 uppercase tracking-wider opacity-70"
                                style="color: var(--color-text-muted);">Detected Patterns</h4>
                            <div class="flex flex-wrap gap-1 sm:gap-1.5">
                                ${(explanation.detected_patterns || []).map(p => `
                                    <span class="px-2 sm:px-2.5 py-0.5 sm:py-1 rounded-full text-xs font-medium border"
                                          style="background: rgba(228,145,201,0.1); color: var(--color-accent-pink); border-color: rgba(228,145,201,0.3);">
                                        ${p}
                                    </span>
                                `).join('')}
                            </div>
                        </div>

                        <!-- Transaction Summary -->
                        <div>
                            <h4 class="text-xs font-semibold mb-2 uppercase tracking-wider opacity-70"
                                style="color: var(--color-text-muted);">Transaction Summary</h4>
                            <div class="grid grid-cols-2 gap-1.5 sm:gap-2 text-xs">
                                ${[
                ['Total Sent', `$${(explanation.transaction_summary?.total_sent || 0).toLocaleString()}`],
                ['Total Received', `$${(explanation.transaction_summary?.total_received || 0).toLocaleString()}`],
                ['Transactions', explanation.transaction_summary?.transaction_count || 0],
                ['Counterparties', explanation.transaction_summary?.unique_counterparties || 0],
            ].map(([label, value]) => `
                                    <div class="p-1.5 sm:p-2 rounded-lg border"
                                         style="background: var(--color-primary-bg); border-color: var(--color-border);">
                                        <p style="color: var(--color-text-muted);">${label}</p>
                                        <p class="font-semibold" style="color: var(--color-text-main);">${value}</p>
                                    </div>
                                `).join('')}
                            </div>
                        </div>

                        <!-- Why Flagged -->
                        <div>
                            <h4 class="text-xs font-semibold mb-2 uppercase tracking-wider opacity-70"
                                style="color: var(--color-text-muted);">Why Flagged</h4>
                            <p class="text-xs leading-relaxed p-2 sm:p-3 rounded-lg border"
                               style="background: rgba(228,145,201,0.05); color: var(--color-text-main); border-color: rgba(228,145,201,0.2);">
                                ${explanation.why_flagged || 'No explanation available.'}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Back button
        document.getElementById('back-to-list').addEventListener('click', () => {
            selectedAccount = null;
            renderExplainabilityPanel(explanations, accounts, null);
        });
    }
}

// ═══════════════════════════════════════════════
//  EVENT LISTENERS (Init on DOMContentLoaded)
// ═══════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    // Theme toggle
    document.getElementById('theme-toggle').addEventListener('click', toggleTheme);

    // Logo / New Analysis → reset
    document.getElementById('logo-btn').addEventListener('click', resetApp);
    document.getElementById('new-analysis-btn').addEventListener('click', resetApp);

    // File Upload — Drop Zone
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');

    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', e => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--color-accent-green)';
        dropZone.style.background = 'var(--color-primary-bg)';
    });
    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = 'var(--color-border)';
        dropZone.style.background = 'var(--color-card-bg)';
    });
    dropZone.addEventListener('drop', e => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--color-border)';
        dropZone.style.background = 'var(--color-card-bg)';
        handleFileSelect(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener('change', e => handleFileSelect(e.target.files[0]));

    // Remove file
    document.getElementById('remove-file-btn').addEventListener('click', removeFile);

    // Analyze button
    document.getElementById('analyze-btn').addEventListener('click', analyzeFile);
});
