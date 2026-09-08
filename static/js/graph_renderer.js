/**
 * Napoléon Imperial Web Intelligence Suite
 * 18th-Century Field Cartography Graph Renderer (Hardware-Accelerated 60 FPS)
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
                    <div class="text-center p-4">
                        <i class="fa-solid fa-compass-drafting fa-3x mb-3 text-sepia opacity-50"></i>
                        <h4 class="font-heading text-sepia">Carte Vierge</h4>
                        <p class="small font-italic">Ordonnez une reconnaissance pour dresser le réseau des bastions et tracer les voies.</p>
                    </div>
                </div>
            `;
            return;
        }

        this.container.innerHTML = '';

        // Apply vintage cartography styling to nodes & edges
        const styledNodes = filtered.nodes.map(n => {
            const isEntity = n.type === 'entity';
            const isHighRel = (n.relevance || 0) > 0.6;
            
            let colorBg = '#3b4d61'; // Slate Iron Bastion
            let colorBorder = '#253342';
            if (isEntity) {
                colorBg = '#8a171d'; // Crimson Wax Seal
                colorBorder = '#5e0d12';
            } else if (isHighRel) {
                colorBg = '#2e7d32'; // Laurel Green
                colorBorder = '#1b5e20';
            }

            return {
                ...n,
                color: {
                    background: colorBg,
                    border: colorBorder,
                    highlight: { background: '#9d762f', border: '#6e511b' }
                },
                font: {
                    color: '#1f1610', // Deep Sepia Iron Gall Ink
                    face: 'Cormorant Garamond, serif',
                    size: 13,
                    bold: { color: '#000', size: 14 }
                },
                borderWidth: 2,
                shadow: { enabled: true, color: 'rgba(80, 60, 40, 0.25)', size: 4, x: 2, y: 2 }
            };
        });

        const styledEdges = filtered.edges.map(e => ({
            ...e,
            color: {
                color: 'rgba(90, 69, 54, 0.45)', // Hand-drawn Sepia Ink line
                highlight: '#8a171d',
                hover: '#9d762f'
            },
            width: 1.4,
            smooth: { type: 'continuous', roundness: 0.15 },
            arrows: { to: { enabled: true, scaleFactor: 0.55 } }
        }));

        const data = {
            nodes: new vis.DataSet(styledNodes),
            edges: new vis.DataSet(styledEdges)
        };

        // Pre-stabilized physics: freezes after 40 iterations for instant 60 FPS performance
        const options = {
            physics: {
                enabled: true,
                barnesHut: {
                    gravitationalConstant: -2200,
                    centralGravity: 0.25,
                    springLength: 90,
                    springConstant: 0.04,
                    damping: 0.12
                },
                stabilization: {
                    enabled: true,
                    iterations: 40,
                    updateInterval: 10
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 120,
                hideEdgesOnDrag: true
            }
        };

        this.network = new vis.Network(this.container, data, options);

        // Turn off physics once stabilized to ensure zero-lag interactivity
        this.network.once('stabilizationIterationsDone', () => {
            this.network.setOptions({ physics: { enabled: false } });
        });

        // Click node event -> Open Slide-out Scout Drawer
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
                scale: 1.3,
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
        titleHeader.innerText = isEntity ? `ENTITÉ DÉCHIFFRÉE (${node.entity_type || 'INTEL'})` : "MÉMOIRE D'ÉCLAIREUR";

        let html = '';
        if (isEntity) {
            html = `
                <div class="mb-3">
                    <span class="badge badge-critical mb-2 font-heading">${node.entity_type || 'ENTITÉ'}</span>
                    <h4 class="text-ink">${node.label}</h4>
                </div>
                <div class="mb-3">
                    <label class="field-parchment-label">Ramifications Militaires</label>
                    <div class="text-muted small">Rattaché à ${node.value || 1} bastion(s) exploré(s).</div>
                </div>
            `;
        } else {
            const page = this.pageIndex[node.url] || this.pageIndex[node.id] || {};
            const title = page.title || node.title || node.label || 'Bastion sans titre';
            const relevance = (node.relevance || page.relevance_score || 0).toFixed(2);
            const summary = page.summary || "Aucun rapport d'observation rédigé pour ce bastion.";
            const emails = page.emails || [];
            const entities = page.entities || [];

            html = `
                <div class="mb-3">
                    <span class="badge ${relevance > 0.6 ? 'bg-success' : 'badge-gold'} mb-2">Valeur Tactique: ${relevance}</span>
                    <h5 class="text-ink">${title}</h5>
                    <a href="${node.url}" target="_blank" class="small text-danger text-break font-typewriter">
                        <i class="fa-solid fa-arrow-up-right-from-square me-1"></i> ${node.url}
                    </a>
                </div>

                <div class="mb-3">
                    <label class="field-parchment-label">Notes de Reconnaissance</label>
                    <p class="text-muted small font-italic">${summary}</p>
                </div>

                ${emails.length ? `
                <div class="mb-3">
                    <label class="field-parchment-label text-danger">Correspondances Interceptées (Courriels)</label>
                    <div>${emails.map(e => `<span class="badge badge-critical me-1 mb-1 font-typewriter">${e}</span>`).join('')}</div>
                </div>` : ''}

                ${entities.length ? `
                <div class="mb-3">
                    <label class="field-parchment-label">Personnages & Forces Détectés</label>
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
