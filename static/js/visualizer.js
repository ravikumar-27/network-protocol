/**
 * Protocol Visualizer Engine
 * Coordinates live step-by-step animations, packet cards, directional arrows,
 * speed settings, and packet inspection.
 */

class ProtocolVisualizer {
    constructor() {
        this.steps = [];
        this.currentStepIndex = -1;
        this.isPlaying = false;
        this.stepIntervalMs = 1200;
        this.timer = null;
        this.viewMode = 'sequence'; // 'sequence' or 'inspector'

        // DOM Elements
        this.emptyState = document.getElementById('vizEmptyState');
        this.stepsTimeline = document.getElementById('stepsTimeline');
        this.stepCounter = document.getElementById('stepCounter');
        this.protocolBadge = document.getElementById('activeProtocolBadge');
        this.progressFill = document.getElementById('vizProgressFill');
        
        // Control buttons
        this.btnPlayPause = document.getElementById('btnPlayPause');
        this.playIcon = document.getElementById('playIcon');
        this.pauseIcon = document.getElementById('pauseIcon');
        this.playPauseLabel = document.getElementById('playPauseLabel');
        this.btnNext = document.getElementById('btnNextStep');
        this.btnPrev = document.getElementById('btnPrevStep');
        this.btnReplay = document.getElementById('btnReplay');
        this.speedSelect = document.getElementById('speedSelect');
        
        // View toggles
        this.btnViewSequence = document.getElementById('viewModeSequence');
        this.btnViewInspector = document.getElementById('viewModeInspector');
        this.packetInspectorView = document.getElementById('packetInspectorView');
        
        // Actor labels
        this.clientActorLabel = document.getElementById('clientActorLabel');
        this.clientAddrLabel = document.getElementById('clientAddrLabel');
        this.serverActorLabel = document.getElementById('serverActorLabel');
        this.serverAddrLabel = document.getElementById('serverAddrLabel');

        this.bindEvents();
    }

    bindEvents() {
        this.btnPlayPause.addEventListener('click', () => this.togglePlayPause());
        this.btnNext.addEventListener('click', () => this.nextStep());
        this.btnPrev.addEventListener('click', () => this.prevStep());
        this.btnReplay.addEventListener('click', () => this.replay());

        this.speedSelect.addEventListener('change', (e) => {
            this.stepIntervalMs = parseInt(e.target.value, 10);
            if (this.isPlaying) {
                this.pause();
                this.play();
            }
        });

        this.btnViewSequence.addEventListener('click', () => this.setViewMode('sequence'));
        this.btnViewInspector.addEventListener('click', () => this.setViewMode('inspector'));

        // Keyboard navigation
        window.addEventListener('keydown', (e) => {
            if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) return;
            if (e.code === 'Space') {
                e.preventDefault();
                this.togglePlayPause();
            } else if (e.code === 'ArrowRight') {
                e.preventDefault();
                this.nextStep();
            } else if (e.code === 'ArrowLeft') {
                e.preventDefault();
                this.prevStep();
            }
        });
    }

    loadSequence(steps, protocolName, actors = {}) {
        this.pause();
        this.steps = steps || [];
        this.currentStepIndex = -1;
        
        if (protocolName) {
            this.protocolBadge.textContent = protocolName;
        }

        if (actors.clientRole) this.clientActorLabel.textContent = actors.clientRole;
        if (actors.clientAddr) this.clientAddrLabel.textContent = actors.clientAddr;
        if (actors.serverRole) this.serverActorLabel.textContent = actors.serverRole;
        if (actors.serverAddr) this.serverAddrLabel.textContent = actors.serverAddr;

        this.emptyState.classList.add('hidden');
        this.stepsTimeline.innerHTML = '';
        this.updateControls();
        this.updateProgress();

        // Automatically start playing the animation
        this.play();
    }

    appendLiveStep(step) {
        this.steps.push(step);
        this.updateControls();
        
        // Render step immediately
        this.renderStep(step, this.steps.length - 1);
        this.currentStepIndex = this.steps.length - 1;
        this.highlightActiveCard(this.currentStepIndex);
        this.updateProgress();
    }

    togglePlayPause() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }

    play() {
        if (this.steps.length === 0) return;
        if (this.currentStepIndex >= this.steps.length - 1) {
            // Restart from beginning if at end
            this.currentStepIndex = -1;
            this.stepsTimeline.innerHTML = '';
        }

        this.isPlaying = true;
        this.playIcon.classList.add('hidden');
        this.pauseIcon.classList.remove('hidden');
        this.playPauseLabel.textContent = 'Pause';
        
        this.timer = setInterval(() => {
            if (this.currentStepIndex < this.steps.length - 1) {
                this.nextStep(false);
            } else {
                this.pause();
            }
        }, this.stepIntervalMs);

        // Immediate first step if starting at -1
        if (this.currentStepIndex === -1) {
            this.nextStep(false);
        }
    }

    pause() {
        this.isPlaying = false;
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
        this.playIcon.classList.remove('hidden');
        this.pauseIcon.classList.add('hidden');
        this.playPauseLabel.textContent = 'Play';
    }

    replay() {
        this.pause();
        this.currentStepIndex = -1;
        this.stepsTimeline.innerHTML = '';
        this.updateProgress();
        this.play();
    }

    nextStep(pauseIfManual = true) {
        if (pauseIfManual) this.pause();
        if (this.currentStepIndex < this.steps.length - 1) {
            this.currentStepIndex++;
            const step = this.steps[this.currentStepIndex];
            
            // Check if card is already rendered
            let existingCard = document.getElementById(`step-card-${this.currentStepIndex}`);
            if (!existingCard) {
                this.renderStep(step, this.currentStepIndex);
            }
            
            this.highlightActiveCard(this.currentStepIndex);
            this.updateControls();
            this.updateProgress();
            this.updateInspector(step);
        }
    }

    prevStep() {
        this.pause();
        if (this.currentStepIndex > 0) {
            this.currentStepIndex--;
            this.highlightActiveCard(this.currentStepIndex);
            this.updateControls();
            this.updateProgress();
            this.updateInspector(this.steps[this.currentStepIndex]);
        }
    }

    highlightActiveCard(index) {
        const allCards = this.stepsTimeline.querySelectorAll('.step-card');
        allCards.forEach((card, idx) => {
            if (idx === index) {
                card.classList.add('active-step');
                card.classList.remove('completed-step');
                card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            } else if (idx < index) {
                card.classList.remove('active-step');
                card.classList.add('completed-step');
            } else {
                card.classList.remove('active-step', 'completed-step');
            }
        });
    }

    renderStep(step, index) {
        const card = document.createElement('div');
        card.className = 'step-card active-step';
        card.id = `step-card-${index}`;

        const isClientToServer = step.direction === 'client_to_server';
        const dirClass = isClientToServer ? 'dir-c2s' : 'dir-s2c';
        const dirLabel = isClientToServer ? 'Client ➔ Server' : 'Server ➔ Client';

        // Tag color
        let tagClass = 'tag-http';
        if (step.protocol === 'DNS') tagClass = 'tag-dns';
        if (step.protocol === 'SMTP') tagClass = 'tag-smtp';

        // Highlighted Fields Grid
        let fieldsHtml = '';
        if (step.fields) {
            for (const [k, v] of Object.entries(step.fields)) {
                fieldsHtml += `
                    <div class="field-item">
                        <span class="field-key">${this.escapeHtml(k)}</span>
                        <span class="field-val ${k.includes('Status') || k.includes('Method') || k.includes('Command') || k.includes('Resolved') ? 'field-val-highlight' : ''}">${this.escapeHtml(String(v))}</span>
                    </div>
                `;
            }
        }

        card.innerHTML = `
            <div class="step-arrow-bar ${dirClass}">
                <span class="direction-badge ${dirClass}">
                    <span>${dirLabel}</span>
                </span>
                <div class="arrow-line">
                    <div class="arrow-head"></div>
                </div>
                <span class="step-timing">+${step.timestamp_offset_ms || 0}ms &bull; ${this.escapeHtml(step.transport || 'TCP')}</span>
            </div>

            <div class="step-header">
                <div class="step-title-wrap">
                    <div class="step-badge-row">
                        <span class="step-num-badge">Step #${step.step_number || (index + 1)}</span>
                        <span class="proto-tag ${tagClass}">${this.escapeHtml(step.protocol)}</span>
                        <span class="step-title">${this.escapeHtml(step.title)}</span>
                    </div>
                    <p class="step-summary">${this.escapeHtml(step.summary)}</p>
                </div>
            </div>

            ${fieldsHtml ? `<div class="step-fields-grid">${fieldsHtml}</div>` : ''}

            <div class="step-details-toggle" onclick="this.nextElementSibling.classList.toggle('open');">
                <span>View Raw Wire Message / CRLF Headers</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </div>
            <div class="step-details-content">
                <pre class="raw-code-block">${this.escapeHtml(step.raw_text || '')}</pre>
            </div>
        `;

        this.stepsTimeline.appendChild(card);
    }

    updateControls() {
        const total = this.steps.length;
        const current = this.currentStepIndex + 1;
        this.stepCounter.textContent = `Step ${Math.max(0, current)} / ${total}`;

        this.btnPrev.disabled = this.currentStepIndex <= 0;
        this.btnNext.disabled = this.currentStepIndex >= total - 1;
    }

    updateProgress() {
        const total = this.steps.length;
        if (total === 0) {
            this.progressFill.style.width = '0%';
            return;
        }
        const pct = Math.min(100, Math.round(((this.currentStepIndex + 1) / total) * 100));
        this.progressFill.style.width = `${pct}%`;
    }

    setViewMode(mode) {
        this.viewMode = mode;
        if (mode === 'sequence') {
            this.btnViewSequence.classList.add('active');
            this.btnViewInspector.classList.remove('active');
            this.stepsTimeline.classList.remove('hidden');
            this.packetInspectorView.classList.add('hidden');
        } else {
            this.btnViewInspector.classList.add('active');
            this.btnViewSequence.classList.remove('active');
            this.stepsTimeline.classList.add('hidden');
            this.packetInspectorView.classList.remove('hidden');
            if (this.currentStepIndex >= 0 && this.steps[this.currentStepIndex]) {
                this.updateInspector(this.steps[this.currentStepIndex]);
            }
        }
    }

    updateInspector(step) {
        if (!step) return;
        const emptyMsg = document.getElementById('inspectorEmpty');
        const content = document.getElementById('inspectorContent');
        if (emptyMsg) emptyMsg.classList.add('hidden');
        if (content) content.classList.remove('hidden');

        document.getElementById('inspProtocolBadge').textContent = step.protocol;
        document.getElementById('inspTitle').textContent = step.title;
        document.getElementById('inspTime').textContent = `+${step.timestamp_offset_ms || 0}ms`;

        // Meta Grid
        const metaGrid = document.getElementById('inspMetaGrid');
        metaGrid.innerHTML = `
            <div class="field-item">
                <span class="field-key">Source</span>
                <span class="field-val">${this.escapeHtml(step.source || 'Client')}</span>
            </div>
            <div class="field-item">
                <span class="field-key">Destination</span>
                <span class="field-val">${this.escapeHtml(step.destination || 'Server')}</span>
            </div>
            <div class="field-item">
                <span class="field-key">Transport Layer</span>
                <span class="field-val">${this.escapeHtml(step.transport || 'TCP')}</span>
            </div>
            <div class="field-item">
                <span class="field-key">Direction</span>
                <span class="field-val text-cyan">${step.direction === 'client_to_server' ? 'Client ➔ Server' : 'Server ➔ Client'}</span>
            </div>
        `;

        // Fields Table
        const fieldsWrap = document.getElementById('inspFieldsTable');
        let tableRows = '';
        if (step.fields) {
            for (const [k, v] of Object.entries(step.fields)) {
                tableRows += `
                    <tr>
                        <td style="color: var(--cyan); font-weight: 600;">${this.escapeHtml(k)}</td>
                        <td>${this.escapeHtml(String(v))}</td>
                    </tr>
                `;
            }
        }
        fieldsWrap.innerHTML = `
            <table class="fields-table">
                <thead><tr><th>Field Name</th><th>Parsed Value</th></tr></thead>
                <tbody>${tableRows}</tbody>
            </table>
        `;

        // Raw Wire
        document.getElementById('inspRawWire').textContent = step.raw_text || '';
    }

    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, (m) => map[m]);
    }
}

// Instantiate visualizer globally
window.protocolVisualizer = new ProtocolVisualizer();
