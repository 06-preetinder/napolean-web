/**
 * Napoléon Imperial Web Intelligence Suite - Client Controller
 */

document.addEventListener('DOMContentLoaded', () => {
    // State
    let eventSource = null;
    let graphRenderer = null;
    let autoScroll = true;
    let soundEnabled = true;
    let audioCtx = null;
    let currentData = null;

    // Elements
    const form = document.getElementById('campaign-form');
    const inputUrl = document.getElementById('target-url');
    const inputIntent = document.getElementById('campaign-intent');
    const sliderDepth = document.getElementById('crawl-depth');
    const labelDepth = document.getElementById('depth-val');
    const selectMethod = document.getElementById('recon-method');
    const checkSecurity = document.getElementById('check-security');
    const checkReport = document.getElementById('check-report');
    const checkGraph = document.getElementById('check-graph');
    
    const cliPreview = document.getElementById('cli-command-preview');
    const btnCopyCmd = document.getElementById('btn-copy-cmd');
    
    const btnLaunch = document.getElementById('btn-launch-campaign');
    const btnStop = document.getElementById('btn-stop-campaign');
    const statusBulb = document.getElementById('status-bulb');
    const statusText = document.getElementById('status-text');
    
    const terminalOutput = document.getElementById('terminal-output');
    const btnTermClear = document.getElementById('btn-terminal-clear');
    const btnTermAutoScroll = document.getElementById('btn-terminal-autoscroll');
    const btnTermCopy = document.getElementById('btn-terminal-copy');

    const soundToggle = document.getElementById('btn-sound-toggle');
    const soundIcon = document.getElementById('sound-icon');

    // Metrics
    const metricPages = document.getElementById('metric-pages');
    const metricLinks = document.getElementById('metric-links');
    const metricDepth = document.getElementById('metric-depth');
    const metricEntities = document.getElementById('metric-entities');
    const metricThreats = document.getElementById('metric-threats');
    const metricSpeed = document.getElementById('metric-speed');

    // Initialize Graph Renderer
    graphRenderer = new NapoleonGraphRenderer('vis-network-container');

    // Clock
    setInterval(() => {
        const now = new Date();
        const clockEl = document.getElementById('imperial-clock');
        if (clockEl) clockEl.innerText = now.toTimeString().split(' ')[0];
    }, 1000);

    // Audio Synth for Military Effects
    function playAudioTone(freq, type = 'sine', duration = 0.15) {
        if (!soundEnabled) return;
        try {
            if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            if (audioCtx.state === 'suspended') audioCtx.resume();
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = type;
            osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
            gain.gain.setValueAtTime(0.04, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + duration);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start();
            osc.stop(audioCtx.currentTime + duration);
        } catch (e) {}
    }

    if (soundToggle) {
        soundToggle.addEventListener('click', () => {
            soundEnabled = !soundEnabled;
            soundIcon.className = soundEnabled ? 'fa-solid fa-volume-high' : 'fa-solid fa-volume-xmark';
            soundToggle.classList.toggle('active', soundEnabled);
        });
    }

    // -------------------------------------------------------------
    // Live CLI Command Preview Generator
    // -------------------------------------------------------------
    function updateCliPreview() {
        const url = inputUrl.value.trim() || 'https://example.com';
        const depth = sliderDepth.value;
        const method = selectMethod.value;
        const intent = inputIntent.value.trim();
        const sec = checkSecurity.checked;
        const rep = checkReport.checked;
        const grp = checkGraph.checked;

        let cmd = `python Napolean.py --url ${url} --depth ${depth} --method ${method}`;
        if (intent) {
            cmd += ` --intent "${intent}"`;
        }
        if (sec) cmd += ` --scan-security`;
        if (rep) cmd += ` --generate-report`;
        if (grp) cmd += ` --generate-graph`;

        cliPreview.innerText = cmd;
    }

    [inputUrl, inputIntent, sliderDepth, selectMethod, checkSecurity, checkReport, checkGraph].forEach(el => {
        el.addEventListener('input', () => {
            if (el === sliderDepth) labelDepth.innerText = sliderDepth.value;
            updateCliPreview();
        });
    });

    if (btnCopyCmd) {
        btnCopyCmd.addEventListener('click', () => {
            navigator.clipboard.writeText(cliPreview.innerText).then(() => {
                const orig = btnCopyCmd.innerHTML;
                btnCopyCmd.innerHTML = '<i class="fa-solid fa-check me-1"></i> Copied!';
                playAudioTone(880, 'sine', 0.1);
                setTimeout(() => btnCopyCmd.innerHTML = orig, 1500);
            });
        });
    }

    // Quick Target Dropdown items
    document.querySelectorAll('.quick-target').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            inputUrl.value = item.getAttribute('data-url');
            updateCliPreview();
        });
    });

    // -------------------------------------------------------------
    // Preset Battle Formations
    // -------------------------------------------------------------
    document.querySelectorAll('.btn-preset').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.btn-preset').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const preset = btn.getAttribute('data-preset');
            if (preset === 'swift') {
                sliderDepth.value = 1;
                selectMethod.value = 'requests';
                checkSecurity.checked = false;
                checkReport.checked = false;
                checkGraph.checked = true;
            } else if (preset === 'conquest') {
                sliderDepth.value = 2;
                selectMethod.value = 'requests';
                checkSecurity.checked = true;
                checkReport.checked = true;
                checkGraph.checked = true;
            } else if (preset === 'siege') {
                sliderDepth.value = 2;
                selectMethod.value = 'requests';
                checkSecurity.checked = true;
                checkReport.checked = false;
                checkGraph.checked = true;
                if (!inputIntent.value) inputIntent.value = 'security vulnerabilities and exposed keys';
            } else if (preset === 'dossier') {
                sliderDepth.value = 3;
                selectMethod.value = 'requests';
                checkSecurity.checked = true;
                checkReport.checked = true;
                checkGraph.checked = true;
            }
            labelDepth.innerText = sliderDepth.value;
            updateCliPreview();
            playAudioTone(520, 'sine', 0.1);
        });
    });

    // -------------------------------------------------------------
    // Terminal Stream & SSE
    // -------------------------------------------------------------
    function appendTerminalLine(text, level = 'info') {
        const line = document.createElement('div');
        line.className = `terminal-line ${level}`;
        line.innerText = text;
        terminalOutput.appendChild(line);

        if (autoScroll) {
            terminalOutput.scrollTop = terminalOutput.scrollHeight;
        }

        // Keep DOM lightweight: max 600 lines
        while (terminalOutput.children.length > 600) {
            terminalOutput.removeChild(terminalOutput.firstChild);
        }

        // Sound cue
        if (level === 'gold') playAudioTone(659, 'triangle', 0.2);
        else if (level === 'danger') playAudioTone(220, 'sawtooth', 0.25);
    }

    function connectSSE() {
        if (eventSource) eventSource.close();

        eventSource = new EventSource('/api/campaign/stream');

        eventSource.onmessage = (e) => {
            try {
                const msg = JSON.parse(e.data);
                if (msg.event === 'init') {
                    if (msg.logs && Array.isArray(msg.logs)) {
                        msg.logs.forEach(l => appendTerminalLine(`[${l.time}] ${l.text}`, l.level));
                    }
                    syncStatus(msg.status);
                } else if (msg.event === 'log') {
                    appendTerminalLine(`[${msg.data.time}] ${msg.data.text}`, msg.data.level);
                } else if (msg.event === 'progress') {
                    const p = msg.data;
                    metricPages.innerText = p.pages_crawled;
                    metricDepth.innerText = `${p.depth} / ${p.max_depth}`;
                    metricSpeed.innerText = p.speed;
                } else if (msg.event === 'complete') {
                    syncStatus(msg.data);
                    fetchCampaignData();
                    fetchArchives();
                    playAudioTone(880, 'sine', 0.4);
                }
            } catch (err) {
                console.error("SSE parse error", err);
            }
        };

        eventSource.onerror = () => {
            // Reconnect automatically handled by browser
        };
    }

    function syncStatus(st) {
        if (!st) return;
        const isRunning = st.status === 'running';

        statusBulb.className = `status-indicator ${isRunning ? 'active' : 'idle'}`;
        statusText.innerText = isRunning ? 'CAMPAIGN IN MOTION' : 'GARRISON IDLE';

        btnLaunch.disabled = isRunning;
        btnStop.disabled = !isRunning;

        if (st.pages_crawled !== undefined) metricPages.innerText = st.pages_crawled;
        if (st.links_discovered !== undefined) metricLinks.innerText = st.links_discovered;
        if (st.depth !== undefined && st.max_depth !== undefined) metricDepth.innerText = `${st.depth} / ${st.max_depth}`;
        if (st.entities_found !== undefined) metricEntities.innerText = st.entities_found;
        if (st.threats_detected !== undefined) {
            metricThreats.innerText = st.threats_detected;
            const badge = document.getElementById('threats-badge');
            if (badge) badge.innerText = st.threats_detected;
        }
        if (st.speed !== undefined) metricSpeed.innerText = st.speed;
    }

    // Terminal Controls
    btnTermClear.addEventListener('click', () => {
        terminalOutput.innerHTML = '<div class="terminal-line text-muted">Terminal cleared by operator.</div>';
    });

    btnTermAutoScroll.addEventListener('click', () => {
        autoScroll = !autoScroll;
        btnTermAutoScroll.innerHTML = `<i class="fa-solid fa-angles-down me-1"></i> Auto-Scroll: ${autoScroll ? 'ON' : 'OFF'}`;
        btnTermAutoScroll.classList.toggle('active', autoScroll);
    });

    btnTermCopy.addEventListener('click', () => {
        const text = Array.from(terminalOutput.children).map(c => c.innerText).join('\n');
        navigator.clipboard.writeText(text).then(() => {
            const orig = btnTermCopy.innerHTML;
            btnTermCopy.innerHTML = '<i class="fa-solid fa-check me-1"></i> Copied!';
            setTimeout(() => btnTermCopy.innerHTML = orig, 1500);
        });
    });

    // -------------------------------------------------------------
    // Campaign Execution
    // -------------------------------------------------------------
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const payload = {
            url: inputUrl.value.trim(),
            intent: inputIntent.value.trim(),
            depth: parseInt(sliderDepth.value),
            method: selectMethod.value,
            scan_security: checkSecurity.checked,
            generate_report: checkReport.checked,
            generate_graph: checkGraph.checked
        };

        if (!payload.url) {
            alert('Please specify target URL coordinates.');
            return;
        }

        try {
            btnLaunch.disabled = true;
            statusText.innerText = 'MOBILIZING TROOPS...';

            const res = await fetch('/api/campaign/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (res.ok) {
                playAudioTone(440, 'triangle', 0.2);
                // Switch to Terminal Tab automatically
                const termTabTrigger = document.querySelector('#terminal-tab');
                if (termTabTrigger) {
                    const tab = new bootstrap.Tab(termTabTrigger);
                    tab.show();
                }
            } else {
                alert(data.error || 'Failed to mobilize campaign.');
                btnLaunch.disabled = false;
            }
        } catch (err) {
            alert('Error communicating with Imperial Command server: ' + err.message);
            btnLaunch.disabled = false;
        }
    });

    btnStop.addEventListener('click', async () => {
        if (confirm('Issue an imperial order of retreat? The campaign will halt.')) {
            try {
                btnStop.disabled = true;
                await fetch('/api/campaign/stop', { method: 'POST' });
            } catch (err) {
                console.error("Stop error", err);
            }
        }
    });

    // -------------------------------------------------------------
    // Data Renderers & Tabs Populator
    // -------------------------------------------------------------
    async function fetchCampaignData() {
        try {
            const res = await fetch('/api/campaign/data');
            if (!res.ok) return;
            const data = await res.json();
            currentData = data;

            // Render Graph
            graphRenderer.setData(data.graph, data.crawled);

            // Render Threats
            renderThreats(data.security);

            // Render Research Dossier
            renderDossier(data.report, data.crawled);

            // Render Conquered Pages Index
            renderTerritories(data.crawled);

        } catch (err) {
            console.error("Failed to load campaign data:", err);
        }
    }

    function renderThreats(sec) {
        const body = document.getElementById('threats-table-body');
        const countBadge = document.getElementById('threat-total-count');
        const techBox = document.getElementById('tech-stack-container');

        const findings = (sec && sec.findings) || [];
        const techs = (sec && sec.summary && sec.summary.technologies) || [];

        if (countBadge) countBadge.innerText = `${findings.length} Detected`;

        // Technologies
        if (techBox) {
            if (techs.length) {
                techBox.innerHTML = techs.map(t => `<span class="vintage-tag"><i class="fa-solid fa-cube me-1"></i>${t}</span>`).join('');
            } else {
                techBox.innerHTML = '<span class="text-muted small">No specific framework signatures detected.</span>';
            }
        }

        // Table
        if (!body) return;
        if (!findings.length) {
            body.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-4 text-muted">
                        <i class="fa-solid fa-shield-check fa-2x mb-2 text-gold opacity-50 d-block"></i>
                        No critical vulnerabilities or exposed secrets flagged in this campaign.
                    </td>
                </tr>
            `;
            return;
        }

        body.innerHTML = findings.map(f => {
            const sev = (f.severity || 'info').toLowerCase();
            const badgeClass = `badge-${sev}`;
            return `
                <tr>
                    <td><span class="badge ${badgeClass} text-uppercase">${sev}</span></td>
                    <td class="font-monospace text-muted small">${f.type || 'RECON'}</td>
                    <td>
                        <strong class="text-white d-block">${f.title || 'Security Finding'}</strong>
                        <div class="small text-muted">${f.description || ''}</div>
                    </td>
                    <td>
                        <a href="${f.url || '#'}" target="_blank" class="small text-gold text-break font-monospace">
                            ${f.url || 'Target'}
                        </a>
                    </td>
                </tr>
            `;
        }).join('');
    }

    function renderDossier(report, crawled) {
        const summaryBox = document.getElementById('dossier-summary-content');
        const topPagesBox = document.getElementById('dossier-top-pages');
        const entitiesCloud = document.getElementById('dossier-entities-cloud');
        const topicsCloud = document.getElementById('dossier-topics-cloud');

        // Summary
        if (summaryBox) {
            if (report && report.summary) {
                const s = report.summary;
                summaryBox.innerHTML = `
                    <div class="row g-3 mb-3">
                        <div class="col-sm-4 text-center border-end border-dark">
                            <h4 class="text-gold mb-0">${s.total_pages_crawled || 0}</h4>
                            <small class="text-muted">Pages Reconnoitered</small>
                        </div>
                        <div class="col-sm-4 text-center border-end border-dark">
                            <h4 class="text-gold mb-0">${s.unique_entities || 0}</h4>
                            <small class="text-muted">Unique Entities</small>
                        </div>
                        <div class="col-sm-4 text-center">
                            <h4 class="text-gold mb-0">${s.average_relevance_score || '0.00'}</h4>
                            <small class="text-muted">Mean AI Relevance</small>
                        </div>
                    </div>
                    <p class="mb-0 text-muted">
                        ${report.key_insights && report.key_insights.length ? report.key_insights.join(' ') : 'Full reconnaissance intelligence successfully processed.'}
                    </p>
                `;
            } else {
                summaryBox.innerHTML = '<p class="text-muted mb-0">Run a campaign with "Research Dossier" enabled to compile intelligence.</p>';
            }
        }

        // Top pages
        if (topPagesBox) {
            const pages = (crawled || []).slice(0, 5);
            if (pages.length) {
                topPagesBox.innerHTML = pages.map((p, idx) => `
                    <div class="list-group-item bg-transparent text-white border-dark py-3">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <strong class="text-gold">#${idx + 1} ${p.title || 'Untitled Territory'}</strong>
                            <span class="badge ${p.relevance_score > 0.6 ? 'bg-success' : 'badge-gold'}">
                                Rel: ${(p.relevance_score || 0).toFixed(2)}
                            </span>
                        </div>
                        <a href="${p.url}" target="_blank" class="small text-muted font-monospace text-break d-block mb-1">
                            ${p.url}
                        </a>
                        <div class="small text-secondary">${(p.summary || '').substring(0, 150)}...</div>
                    </div>
                `).join('');
            } else {
                topPagesBox.innerHTML = '<div class="list-group-item bg-transparent text-muted text-center py-3">No ranked pages available.</div>';
            }
        }

        // Entities cloud
        if (entitiesCloud) {
            const allEntities = new Set();
            (crawled || []).forEach(p => {
                (p.entities || []).forEach(e => allEntities.add(e.text));
            });
            const entityList = Array.from(allEntities).slice(0, 30);

            if (entityList.length) {
                entitiesCloud.innerHTML = entityList.map(e => `<span class="vintage-tag">${e}</span>`).join('');
            } else {
                entitiesCloud.innerHTML = '<span class="text-muted small">No entities extracted yet.</span>';
            }
        }

        // Topics cloud
        if (topicsCloud) {
            const allTopics = new Set();
            (crawled || []).forEach(p => {
                (p.keywords || []).forEach(k => allTopics.add(k));
            });
            const topicList = Array.from(allTopics).slice(0, 25);

            if (topicList.length) {
                topicsCloud.innerHTML = topicList.map(t => `<span class="vintage-tag"><i class="fa-solid fa-hashtag me-1 text-gold opacity-50"></i>${t}</span>`).join('');
            } else {
                topicsCloud.innerHTML = '<span class="text-muted small">No topic keywords indexed yet.</span>';
            }
        }
    }

    function renderTerritories(crawled) {
        const body = document.getElementById('territories-table-body');
        if (!body) return;

        const list = crawled || [];
        if (!list.length) {
            body.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center py-4 text-muted">
                        No pages indexed in the territory log.
                    </td>
                </tr>
            `;
            return;
        }

        body.innerHTML = list.map(p => {
            const rel = (p.relevance_score || 0).toFixed(2);
            const emails = (p.emails || []).join(', ') || '-';
            const entities = (p.entities || []).slice(0, 4).map(e => `<span class="badge badge-gold me-1">${e.text}</span>`).join('') || '-';

            return `
                <tr>
                    <td><strong class="text-white">${p.title || 'Untitled'}</strong></td>
                    <td>
                        <a href="${p.url}" target="_blank" class="small text-gold font-monospace text-break">
                            ${p.url}
                        </a>
                    </td>
                    <td>
                        <div class="d-flex align-items-center gap-2">
                            <span class="small font-monospace">${rel}</span>
                            <div class="progress flex-grow-1" style="height: 5px; background: #152236;">
                                <div class="progress-bar ${rel > 0.6 ? 'bg-success' : 'bg-warning'}" style="width: ${rel * 100}%"></div>
                            </div>
                        </div>
                    </td>
                    <td>${entities}</td>
                    <td class="font-monospace small text-danger">${emails}</td>
                </tr>
            `;
        }).join('');
    }

    // Territories Table Filter
    const filterInput = document.getElementById('territories-filter-input');
    if (filterInput) {
        filterInput.addEventListener('input', (e) => {
            const q = e.target.value.toLowerCase();
            document.querySelectorAll('#territories-table-body tr').forEach(row => {
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(q) ? '' : 'none';
            });
        });
    }

    // -------------------------------------------------------------
    // Archives & History
    // -------------------------------------------------------------
    async function fetchArchives() {
        try {
            const res = await fetch('/api/campaign/archives');
            if (!res.ok) return;
            const archives = await res.json();
            const body = document.getElementById('archives-table-body');
            if (!body) return;

            if (!archives.length) {
                body.innerHTML = `
                    <tr>
                        <td colspan="8" class="text-center py-4 text-muted">
                            No previous campaigns in the annals yet.
                        </td>
                    </tr>
                `;
                return;
            }

            body.innerHTML = archives.map(a => `
                <tr>
                    <td class="font-monospace small text-gold">${a.id}</td>
                    <td><a href="${a.target_url}" target="_blank" class="text-white small font-monospace">${a.target_url}</a></td>
                    <td class="text-muted small">${a.intent || 'General Recon'}</td>
                    <td>
                        <span class="badge ${a.status === 'completed' ? 'bg-success' : 'bg-warning'} text-uppercase">
                            ${a.status}
                        </span>
                    </td>
                    <td class="font-monospace">${a.pages_crawled}</td>
                    <td class="font-monospace text-danger">${a.threats_detected}</td>
                    <td class="text-muted small">${a.date}</td>
                    <td class="text-muted small">${a.duration}s</td>
                </tr>
            `).join('');
        } catch (err) {
            console.error("Archives error", err);
        }
    }

    document.getElementById('btn-refresh-archives')?.addEventListener('click', fetchArchives);

    // -------------------------------------------------------------
    // Exports
    // -------------------------------------------------------------
    function downloadBlob(content, filename, type = 'application/json') {
        const blob = new Blob([content], { type });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }

    document.getElementById('btn-export-security')?.addEventListener('click', () => {
        if (currentData && currentData.security) {
            downloadBlob(JSON.stringify(currentData.security, null, 2), 'napoleon_security_report.json');
        } else {
            alert('No security report available to export.');
        }
    });

    document.getElementById('btn-export-dossier-json')?.addEventListener('click', () => {
        if (currentData && currentData.report) {
            downloadBlob(JSON.stringify(currentData.report, null, 2), 'napoleon_research_report.json');
        } else {
            alert('No dossier available to export.');
        }
    });

    document.getElementById('btn-export-dossier-md')?.addEventListener('click', () => {
        if (!currentData || !currentData.report) {
            alert('No dossier available to export.');
            return;
        }
        const rep = currentData.report;
        let md = `# ⚜️ Napoléon Imperial Intelligence Report\n\n`;
        md += `**Date:** ${new Date().toISOString()}\n`;
        md += `**Target Coordinate:** ${inputUrl.value}\n\n`;
        md += `## Executive Summary\n\n`;
        if (rep.summary) {
            md += `- **Pages Crawled:** ${rep.summary.total_pages_crawled}\n`;
            md += `- **Decoded Entities:** ${rep.summary.total_entities_found}\n`;
            md += `- **Relevance Score:** ${rep.summary.average_relevance_score}\n\n`;
        }
        if (rep.key_insights) {
            md += `### Key Insights\n\n`;
            rep.key_insights.forEach(i => md += `- ${i}\n`);
        }
        downloadBlob(md, 'napoleon_intelligence_brief.md', 'text/markdown');
    });

    // Boot sequence
    updateCliPreview();
    connectSSE();
    fetchCampaignData();
    fetchArchives();
});
