/**
 * Napoléon Imperial Web Intelligence Suite
 * Lightweight, 60 FPS Graph Visualizer with Hardware Acceleration & Fast Physics Freezing
 */

class NapoleonGraphRenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.network = null;
        this.rawGraphData = { nodes: [], edges: [] };
        this.currentMode = 'unified'; // unified, crawl, entity
        this.pageIndex = {}; // Maps URL to crawled record

        this.initEventListeners();
    }

    initEventListeners() {
        // Mode switch buttons
        const btnUnified = document.getElementById('btn-graph-unified');
        const btnCrawl = document.getElementById('btn-graph-crawl');
        const btnEntities = document.getElementById('btn-graph-entities');

        if (btnUnified) {
            btnUnified.addEventListener('click', () => {
                this.setActiveModeBtn(btnUnified);
                this.currentMode = 'unified';
                this.render();
            });
        }
        if (btnCrawl) {
            btnCrawl.addEventListener('click', () => {
                this.setActiveModeBtn(btnCrawl);
                this.currentMode = 'crawl';
                this.render();
            });
        }
        if (btnEntities) {
            btnEntities.addEventListener('click', () => {
                this.setActiveModeBtn(btnEntities);
                this.currentMode = 'entity';
                this.render();
            });
        }

        // Search in graph
        const searchInput = document.getElementById('graph-search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchAndFocus(e.target.value.trim().toLowerCase());
            });
        }

        // Fit / center button
        const btnFit = document.getElementById('btn-graph-fit');
        if (btnFit) {
            btnFit.addEventListener('click', () => {
                if (this.network) this.network.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } });
            });
        }

        // Close Inspector
        const btnCloseInspector = document.getElementById('btn-close-inspector');
        if (btnCloseInspector) {
            btnCloseInspector.addEventListener('click', () => {
                document.getElementById('node-inspector')?.classList.remove('open');
            });
        }
    }

    setActiveModeBtn(activeBtn) {
        ['btn-graph-unified', 'btn-graph-crawl', 'btn-graph-entities'].forEach(id => {
            document.getElementById(id)?.classList.remove('active');
        });
        activeBtn.classList.add('active');
    }

    setData(graphData, crawledRecords = []) {
        this.rawGraphData = graphData || { nodes: [], edges: [] };
        this.pageIndex = {};
        if (Array.isArray(crawledRecords)) {
            crawledRecords.forEach(rec => {
                if (rec.url) this.pageIndex[rec.url] = rec;
            });
        }
        this.render();
    }

    render() {
        if (!this.container || typeof vis === 'undefined') return;

        const filtered = this.getFilteredData();
        if (!filtered.nodes.length) {
            this.container.innerHTML = `
                <div class="d-flex align-items-center justify-content-center h-100 text-muted">
                    <div class="text-center">
                        <i class="fa-solid fa-map-location-dot fa-3x mb-3 text-gold opacity-50"></i>
                        <h5>No Cartographic Data Available</h5>
                        <p class="small">Launch a campaign to explore the web topology and decode entities.</p>
                    </div>
                </div>
            `;
            return;
        }

        this.container.innerHTML = '';

        const data = {
            nodes: new vis.DataSet(filtered.nodes),
            edges: new vis.DataSet(filtered.edges)
        };

        // Highly optimized options: instant stabilization + freeze physics to guarantee 60fps
        const options = {
            nodes: {
                font: {
                    color: '#e2e8f0',
                    face: 'Inter, sans-serif',
                    size: 11
                },
                borderWidth: 1.5,
                shadow: true
            },
            edges: {
                smooth: {
                    type: 'continuous',
                    roundness: 0.15
                },
                arrows: {
                    to: { enabled: true, scaleFactor: 0.5 }
                }
            },
            physics: {
                enabled: true,
                barnesHut: {
                    gravitationalConstant: -2200,
                    centralGravity: 0.25,
                    springLength: 85,
                    springConstant: 0.04,
                    damping: 0.12
                },
                stabilization: {
                    enabled: true,
                    iterations: 40, // Fast stabilization: finishes in ~100ms
                    updateInterval: 10
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 100,
                navigationButtons: false,
                keyboard: false,
                hideEdgesOnDrag: true
            }
        };

        this.network = new vis.Network(this.container, data, options);

        // Turn off physics simulation after initial layout is computed to preserve battery & avoid lag!
        this.network.once('stabilizationIterationsDone', () => {
            this.network.setOptions({ physics: { enabled: false } });
        });

        // Click node event -> Open Inspector Drawer
        this.network.on('click', (params) => {
            if (params.nodes && params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const node = filtered.nodes.find(n => n.id === nodeId);
                if (node) {
                    this.showNodeInspector(node);
                }
            }
        });
    }

    getFilteredData() {
        const rawNodes = this.rawGraphData.nodes || [];
        const rawEdges = this.rawGraphData.edges || [];

        let filteredNodes = rawNodes;
        if (this.currentMode === 'crawl') {
            filteredNodes = rawNodes.filter(n => n.type === 'page');
        } else if (this.currentMode === 'entity') {
            filteredNodes = rawNodes.filter(n => n.type === 'entity');
        }

        const validIds = new Set(filteredNodes.map(n => String(n.id)));
        const filteredEdges = rawEdges.filter(e => validIds.has(String(e.from)) && validIds.has(String(e.to)));

        return { nodes: filteredNodes, edges: filteredEdges };
    }

    searchAndFocus(query) {
        if (!this.network || !query) return;
        const filtered = this.getFilteredData();
        const match = filtered.nodes.find(n => 
            (n.label && n.label.toLowerCase().includes(query)) ||
            (n.url && n.url.toLowerCase().includes(query)) ||
            (n.title && n.title.toLowerCase().includes(query))
        );

        if (match) {
            this.network.focus(match.id, {
                scale: 1.2,
                animation: { duration: 600, easingFunction: 'easeInOutQuad' }
            });
            this.network.selectNodes([match.id]);
            this.showNodeInspector(match);
        }
    }

    showNodeInspector(node) {
        const drawer = document.getElementById('node-inspector');
        const content = document.getElementById('inspector-content');
        const titleHeader = document.getElementById('inspector-type');

        if (!drawer || !content) return;

        const isEntity = node.type === 'entity';
        titleHeader.innerText = isEntity ? `DECODED ENTITY (${node.entity_type || 'INTEL'})` : 'TERRITORY DISPATCH';

        let html = '';
        if (isEntity) {
            html = `
                <div class="mb-3">
                    <span class="badge badge-gold mb-2">${node.entity_type || 'ENTITY'}</span>
                    <h5 class="text-white">${node.label}</h5>
                </div>
                <div class="mb-3">
                    <label class="imperial-label">Strategic Connections</label>
                    <div class="text-muted small">Linked to ${node.value || 1} discovered page(s).</div>
                </div>
            `;
        } else {
            const page = this.pageIndex[node.url] || this.pageIndex[node.id] || {};
            const title = page.title || node.title || node.label || 'Untitled Territory';
            const relevance = (node.relevance || page.relevance_score || 0).toFixed(2);
            const summary = page.summary || 'No reconnaissance summary recorded for this coordinate.';
            const emails = page.emails || [];
            const entities = page.entities || [];

            html = `
                <div class="mb-3">
                    <span class="badge ${relevance > 0.6 ? 'bg-success' : 'badge-gold'} mb-2">Relevance: ${relevance}</span>
                    <h6 class="text-white">${title}</h6>
                    <a href="${node.url}" target="_blank" class="small text-gold text-break font-monospace">
                        <i class="fa-solid fa-arrow-up-right-from-square me-1"></i> ${node.url}
                    </a>
                </div>

                <div class="mb-3">
                    <label class="imperial-label">Reconnaissance Summary</label>
                    <p class="text-muted small">${summary}</p>
                </div>

                ${emails.length ? `
                <div class="mb-3">
                    <label class="imperial-label text-danger">Exposed Communications (Emails)</label>
                    <div>${emails.map(e => `<span class="badge bg-danger me-1 mb-1 font-monospace">${e}</span>`).join('')}</div>
                </div>` : ''}

                ${entities.length ? `
                <div class="mb-3">
                    <label class="imperial-label">Extracted Entities</label>
                    <div class="d-flex flex-wrap gap-1">
                        ${entities.slice(0, 10).map(e => `<span class="vintage-tag">${e.text}</span>`).join('')}
                    </div>
                </div>` : ''}
            `;
        }

        content.innerHTML = html;
        drawer.classList.add('open');
    }
}

// Export to window
window.NapoleonGraphRenderer = NapoleonGraphRenderer;
