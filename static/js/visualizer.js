/**
 * Protocol Visualizer Engine (Assignment 2)
 * Coordinates synchronized Application Layer and Transport Layer timelines,
 * RFC 793 TCP state machine indicators, sequence/ack byte counters,
 * flow & congestion control telemetry, and Wireshark-style packet dissection.
 */

class ProtocolVisualizer {
    constructor() {
        this.appSteps = [];
        this.transportSteps = [];
        this.activeSteps = []; // Pointer to current active array
        this.currentStepIndex = -1;
        this.isPlaying = false;
        this.stepIntervalMs = 1200;
        this.timer = null;
        
        // Modes
        this.layerMode = 'transport'; // 'app', 'transport', 'dual'
        this.viewMode = 'sequence';    // 'sequence' or 'inspector'
        this.actors = {};
        this.protocolTitle = 'DNS ➔ HTTP/1.1 • TCP';

        // DOM Elements - Stage
        this.emptyState = document.getElementById('vizEmptyState');
        this.stepsTimeline = document.getElementById('stepsTimeline');
        this.dualViewStage = document.getElementById('dualViewStage');
        this.dualAppTimeline = document.getElementById('dualAppTimeline');
        this.dualTransportTimeline = document.getElementById('dualTransportTimeline');
        this.dualAppCountBadge = document.getElementById('dualAppCountBadge');
        this.dualTransportCountBadge = document.getElementById('dualTransportCountBadge');
        this.packetInspectorView = document.getElementById('packetInspectorView');
        
        // Toolbar & Counters
        this.stepCounter = document.getElementById('stepCounter');
        this.protocolBadge = document.getElementById('activeProtocolBadge');
        this.progressFill = document.getElementById('vizProgressFill');
        this.btnPlayPause = document.getElementById('btnPlayPause');
        this.playIcon = document.getElementById('playIcon');
        this.pauseIcon = document.getElementById('pauseIcon');
        this.playPauseLabel = document.getElementById('playPauseLabel');
        this.btnNext = document.getElementById('btnNextStep');
        this.btnPrev = document.getElementById('btnPrevStep');
        this.btnReplay = document.getElementById('btnReplay');
        this.speedSelect = document.getElementById('speedSelect');
        this.btnViewSequence = document.getElementById('viewModeSequence');
        this.btnViewInspector = document.getElementById('viewModeInspector');

        // Layer Switcher Buttons
        this.tabLayerApp = document.getElementById('tabLayerApp');
        this.tabLayerTransport = document.getElementById('tabLayerTransport');
        this.tabLayerDual = document.getElementById('tabLayerDual');

        // TCP State Bar & Telemetry
        this.tcpStateBar = document.getElementById('tcpStateBar');
        this.tcpClientStateBadge = document.getElementById('tcpClientStateBadge');
        this.tcpServerStateBadge = document.getElementById('tcpServerStateBadge');
        this.tcpStatusText = document.getElementById('tcpStatusText');
        
        this.congestionBar = document.getElementById('congestionBar');
        this.dispSeq = document.getElementById('dispSeq');
        this.dispAck = document.getElementById('dispAck');
        this.dispWin = document.getElementById('dispWin');
        this.dispCwnd = document.getElementById('dispCwnd');
        this.dispPhase = document.getElementById('dispPhase');
        this.dispRtt = document.getElementById('dispRtt');

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

        // Layer toggles
        this.tabLayerApp.addEventListener('click', () => this.setLayerMode('app'));
        this.tabLayerTransport.addEventListener('click', () => this.setLayerMode('transport'));
        this.tabLayerDual.addEventListener('click', () => this.setLayerMode('dual'));

        // View mode toggles
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

    /**
     * Loads both Application Layer and Transport Layer sequences in parallel.
     */
    loadDualSequences(appSteps, transportSteps, protocolTitle, actors = {}) {
        this.pause();
        this.appSteps = appSteps || [];
        this.transportSteps = transportSteps || [];
        this.protocolTitle = protocolTitle || 'Application & Transport Layer';
        this.actors = actors;
        this.currentStepIndex = -1;

        if (this.protocolBadge) {
            this.protocolBadge.textContent = this.protocolTitle;
        }

        if (actors.clientRole && this.clientActorLabel) this.clientActorLabel.textContent = actors.clientRole;
        if (actors.clientAddr && this.clientAddrLabel) this.clientAddrLabel.textContent = actors.clientAddr;
        if (actors.serverRole && this.serverActorLabel) this.serverActorLabel.textContent = actors.serverRole;
        if (actors.serverAddr && this.serverAddrLabel) this.serverAddrLabel.textContent = actors.serverAddr;

        if (this.emptyState) this.emptyState.classList.add('hidden');
        if (this.stepsTimeline) this.stepsTimeline.innerHTML = '';
        if (this.dualAppTimeline) this.dualAppTimeline.innerHTML = '';
        if (this.dualTransportTimeline) this.dualTransportTimeline.innerHTML = '';

        if (this.dualAppCountBadge) this.dualAppCountBadge.textContent = `${this.appSteps.length} steps`;
        if (this.dualTransportCountBadge) this.dualTransportCountBadge.textContent = `${this.transportSteps.length} steps`;

        // Reset TCP State Badges
        this.resetTcpIndicators();

        // Establish active step list based on current layerMode
        this.updateActiveStepsList();
        this.updateControls();
        this.updateProgress();

        // Autoplay sequence
        this.play();
    }

    /**
     * Backwards-compatible loadSequence helper
     */
    loadSequence(steps, protocolName, actors = {}) {
        this.loadDualSequences(steps, steps, protocolName, actors);
    }

    appendLiveStep(step) {
        if (step.transport === 'TCP' || step.flags) {
            this.transportSteps.push(step);
        } else {
            this.appSteps.push(step);
        }
        this.updateActiveStepsList();
        this.updateControls();
        this.renderStep(step, this.activeSteps.length - 1, this.getTargetContainer());
        this.currentStepIndex = this.activeSteps.length - 1;
        this.highlightActiveCard(this.currentStepIndex);
        this.updateProgress();
        this.updateTcpStateIndicators(step);
    }

    setLayerMode(layer) {
        if (this.layerMode === layer) return;
        this.layerMode = layer;

        // Update Tab styles
        [this.tabLayerApp, this.tabLayerTransport, this.tabLayerDual].forEach(btn => {
            btn.classList.remove('active');
            btn.setAttribute('aria-selected', 'false');
        });

        if (layer === 'app') {
            this.tabLayerApp.classList.add('active');
            this.tabLayerApp.setAttribute('aria-selected', 'true');
        } else if (layer === 'transport') {
            this.tabLayerTransport.classList.add('active');
            this.tabLayerTransport.setAttribute('aria-selected', 'true');
        } else if (layer === 'dual') {
            this.tabLayerDual.classList.add('active');
            this.tabLayerDual.setAttribute('aria-selected', 'true');
        }

        // Toggle Single vs Dual Stage View
        if (layer === 'dual') {
            this.stepsTimeline.classList.add('hidden');
            this.dualViewStage.classList.remove('hidden');
        } else {
            this.stepsTimeline.classList.remove('hidden');
            this.dualViewStage.classList.add('hidden');
        }

        this.updateActiveStepsList();
        this.renderAllSteps();
        this.updateControls();
        this.updateProgress();

        // Re-highlight active step
        if (this.currentStepIndex >= 0 && this.currentStepIndex < this.activeSteps.length) {
            this.highlightActiveCard(this.currentStepIndex);
            this.updateTcpStateIndicators(this.activeSteps[this.currentStepIndex]);
            if (this.viewMode === 'inspector') {
                this.updateInspector(this.activeSteps[this.currentStepIndex]);
            }
        }
    }

    updateActiveStepsList() {
        if (this.layerMode === 'app') {
            this.activeSteps = this.appSteps;
        } else {
            // For both 'transport' and 'dual', primary driver is transportSteps (more granular)
            this.activeSteps = this.transportSteps.length > 0 ? this.transportSteps : this.appSteps;
        }
    }

    getTargetContainer() {
        if (this.layerMode === 'dual') {
            return this.dualTransportTimeline;
        }
        return this.stepsTimeline;
    }

    renderAllSteps() {
        if (this.layerMode === 'dual') {
            this.dualAppTimeline.innerHTML = '';
            this.dualTransportTimeline.innerHTML = '';
            
            // Render App steps into dual left column
            this.appSteps.forEach((s, idx) => {
                if (idx <= this.getCorrespondingAppIndex(this.currentStepIndex)) {
                    this.renderStep(s, idx, this.dualAppTimeline, 'app');
                }
            });
            // Render Transport steps into dual right column
            this.transportSteps.forEach((s, idx) => {
                if (idx <= this.currentStepIndex) {
                    this.renderStep(s, idx, this.dualTransportTimeline, 'transport');
                }
            });
        } else {
            this.stepsTimeline.innerHTML = '';
            this.activeSteps.forEach((s, idx) => {
                if (idx <= this.currentStepIndex) {
                    this.renderStep(s, idx, this.stepsTimeline, this.layerMode);
                }
            });
        }
    }

    getCorrespondingAppIndex(transportIndex) {
        if (transportIndex < 0 || !this.transportSteps[transportIndex]) return -1;
        const currentTrStep = this.transportSteps[transportIndex];
        if (currentTrStep.app_step_ref !== undefined && currentTrStep.app_step_ref !== null) {
            return currentTrStep.app_step_ref - 1;
        }
        // Approximate mapping based on ratio
        if (this.transportSteps.length === 0) return -1;
        return Math.floor((transportIndex / this.transportSteps.length) * this.appSteps.length);
    }

    togglePlayPause() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }

    play() {
        if (this.activeSteps.length === 0) return;
        if (this.currentStepIndex >= this.activeSteps.length - 1) {
            // Restart from beginning if at end
            this.currentStepIndex = -1;
            this.stepsTimeline.innerHTML = '';
            if (this.dualAppTimeline) this.dualAppTimeline.innerHTML = '';
            if (this.dualTransportTimeline) this.dualTransportTimeline.innerHTML = '';
        }

        this.isPlaying = true;
        this.playIcon.classList.add('hidden');
        this.pauseIcon.classList.remove('hidden');
        this.playPauseLabel.textContent = 'Pause';
        
        this.timer = setInterval(() => {
            if (this.currentStepIndex < this.activeSteps.length - 1) {
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
        if (this.dualAppTimeline) this.dualAppTimeline.innerHTML = '';
        if (this.dualTransportTimeline) this.dualTransportTimeline.innerHTML = '';
        this.resetTcpIndicators();
        this.updateProgress();
        this.play();
    }

    nextStep(pauseIfManual = true) {
        if (pauseIfManual) this.pause();
        if (this.currentStepIndex < this.activeSteps.length - 1) {
            this.currentStepIndex++;
            const step = this.activeSteps[this.currentStepIndex];

            if (this.layerMode === 'dual') {
                // Ensure transport card is rendered
                let trCard = document.getElementById(`step-card-transport-${this.currentStepIndex}`);
                if (!trCard) {
                    this.renderStep(step, this.currentStepIndex, this.dualTransportTimeline, 'transport');
                }

                // Render corresponding app step if not present
                const appIdx = this.getCorrespondingAppIndex(this.currentStepIndex);
                if (appIdx >= 0 && appIdx < this.appSteps.length) {
                    let appCard = document.getElementById(`step-card-app-${appIdx}`);
                    if (!appCard) {
                        this.renderStep(this.appSteps[appIdx], appIdx, this.dualAppTimeline, 'app');
                    }
                }
            } else {
                let existingCard = document.getElementById(`step-card-${this.currentStepIndex}`);
                if (!existingCard) {
                    this.renderStep(step, this.currentStepIndex, this.stepsTimeline, this.layerMode);
                }
            }
            
            this.highlightActiveCard(this.currentStepIndex);
            this.updateControls();
            this.updateProgress();
            this.updateTcpStateIndicators(step);
            this.updateInspector(step);
        }
    }

    prevStep() {
        this.pause();
        if (this.currentStepIndex > 0) {
            this.currentStepIndex--;
            const step = this.activeSteps[this.currentStepIndex];
            this.highlightActiveCard(this.currentStepIndex);
            this.updateControls();
            this.updateProgress();
            this.updateTcpStateIndicators(step);
            this.updateInspector(step);
        }
    }

    highlightActiveCard(index) {
        if (this.layerMode === 'dual') {
            const allTrCards = this.dualTransportTimeline.querySelectorAll('.step-card');
            allTrCards.forEach((card, idx) => {
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

            // Highlight corresponding app card
            const appIdx = this.getCorrespondingAppIndex(index);
            const allAppCards = this.dualAppTimeline.querySelectorAll('.step-card');
            allAppCards.forEach((card, idx) => {
                if (idx === appIdx) {
                    card.classList.add('active-step');
                    card.classList.remove('completed-step');
                    card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                } else if (idx < appIdx) {
                    card.classList.remove('active-step');
                    card.classList.add('completed-step');
                } else {
                    card.classList.remove('active-step', 'completed-step');
                }
            });
        } else {
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
    }

    renderStep(step, index, container, mode = 'transport') {
        if (!container) return;
        const card = document.createElement('div');
        card.className = 'step-card active-step';
        card.id = mode === 'dual' ? `step-card-${index}` : `step-card-${mode}-${index}`;

        const isClientToServer = step.direction === 'client_to_server';
        const dirClass = isClientToServer ? 'dir-c2s' : 'dir-s2c';
        const dirLabel = isClientToServer ? 'Client ➔ Server' : 'Server ➔ Client';

        // Tag color and flags badges
        let tagClass = 'tag-http';
        if (step.protocol === 'DNS') tagClass = 'tag-dns';
        if (step.protocol === 'SMTP') tagClass = 'tag-smtp';
        if (step.protocol === 'TCP') tagClass = 'tag-tcp';
        if (step.protocol === 'UDP') tagClass = 'tag-udp';
        if (step.protocol === 'QUIC' || step.protocol === 'HTTP/3') tagClass = 'tag-quic';

        let flagsHtml = '';
        if (step.flags && Array.isArray(step.flags)) {
            flagsHtml = step.flags.map(f => {
                let fClass = 'flag-ack';
                if (f === 'SYN') fClass = 'flag-syn';
                if (f === 'PSH') fClass = 'flag-psh';
                if (f === 'FIN') fClass = 'flag-fin';
                if (f === 'RST') fClass = 'flag-rst';
                if (f === 'UDP') fClass = 'flag-udp';
                if (f === 'RTP') fClass = 'flag-rtp';
                if (f === 'QUIC' || f === 'Initial' || f === '1-RTT') fClass = 'flag-quic';
                return `<span class="flag-tag ${fClass}">[${f}]</span>`;
            }).join('');
        }

        // Highlighted Key Fields Grid
        let fieldsHtml = '';
        if (step.fields) {
            for (const [k, v] of Object.entries(step.fields)) {
                const isHighlight = k.includes('Flags') || k.includes('Seq') || k.includes('Ack') || 
                                    k.includes('Status') || k.includes('Method') || k.includes('Command') || 
                                    k.includes('State') || k.includes('Resolved');
                fieldsHtml += `
                    <div class="field-item">
                        <span class="field-key">${this.escapeHtml(k)}</span>
                        <span class="field-val ${isHighlight ? 'field-val-highlight' : ''}">${this.escapeHtml(String(v))}</span>
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
                        ${flagsHtml}
                        <span class="step-title">${this.escapeHtml(step.title)}</span>
                    </div>
                    <p class="step-summary">${this.escapeHtml(step.summary)}</p>
                </div>
            </div>

            ${fieldsHtml ? `<div class="step-fields-grid">${fieldsHtml}</div>` : ''}

            <div class="step-details-toggle" onclick="this.nextElementSibling.classList.toggle('open');">
                <span>View Wireshark-Style Wire Dissection / Headers</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </div>
            <div class="step-details-content">
                <pre class="raw-code-block">${this.escapeHtml(step.raw_text || '')}</pre>
            </div>
        `;

        container.appendChild(card);
    }

    updateControls() {
        const total = this.activeSteps.length;
        const current = this.currentStepIndex + 1;
        this.stepCounter.textContent = `Step ${Math.max(0, current)} / ${total}`;

        this.btnPrev.disabled = this.currentStepIndex <= 0;
        this.btnNext.disabled = this.currentStepIndex >= total - 1;
    }

    updateProgress() {
        const total = this.activeSteps.length;
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
            this.packetInspectorView.classList.add('hidden');
            if (this.layerMode === 'dual') {
                this.dualViewStage.classList.remove('hidden');
            } else {
                this.stepsTimeline.classList.remove('hidden');
            }
        } else {
            this.btnViewInspector.classList.add('active');
            this.btnViewSequence.classList.remove('active');
            this.stepsTimeline.classList.add('hidden');
            this.dualViewStage.classList.add('hidden');
            this.packetInspectorView.classList.remove('hidden');
            if (this.currentStepIndex >= 0 && this.activeSteps[this.currentStepIndex]) {
                this.updateInspector(this.activeSteps[this.currentStepIndex]);
            }
        }
    }

    updateTcpStateIndicators(step) {
        if (!step) return;

        // Client State
        if (step.client_state) {
            this.tcpClientStateBadge.textContent = step.client_state;
            this.tcpClientStateBadge.className = 'state-badge ' + this.getStateBadgeClass(step.client_state);
        }

        // Server State
        if (step.server_state) {
            this.tcpServerStateBadge.textContent = step.server_state;
            this.tcpServerStateBadge.className = 'state-badge ' + this.getStateBadgeClass(step.server_state);
        }

        // Status text
        if (step.flags && step.flags.includes('SYN')) {
            this.tcpStatusText.textContent = '3-Way Handshake';
            this.tcpStatusText.className = 'state-badge state-badge-syn';
        } else if (step.flags && step.flags.includes('FIN')) {
            this.tcpStatusText.textContent = '4-Way Teardown';
            this.tcpStatusText.className = 'state-badge state-badge-fin';
        } else if (step.client_state === 'ESTABLISHED' || step.server_state === 'ESTABLISHED') {
            this.tcpStatusText.textContent = 'ESTABLISHED (Streaming)';
            this.tcpStatusText.className = 'state-badge state-badge-established';
        } else if (step.protocol === 'UDP' || step.protocol === 'RTP/UDP') {
            this.tcpStatusText.textContent = 'Connectionless Datagram';
            this.tcpStatusText.className = 'state-badge state-badge-time-wait';
        } else if (step.protocol === 'QUIC' || step.protocol === 'HTTP/3') {
            this.tcpStatusText.textContent = 'QUIC 1-RTT Handshake';
            this.tcpStatusText.className = 'state-badge state-badge-established';
        }

        // Telemetry
        if (this.dispSeq) this.dispSeq.textContent = step.seq !== undefined && step.seq !== 0 ? step.seq.toLocaleString() : (step.protocol === 'UDP' ? 'N/A' : '0');
        if (this.dispAck) this.dispAck.textContent = step.ack !== undefined && step.ack !== 0 ? step.ack.toLocaleString() : (step.protocol === 'UDP' ? 'N/A' : '0');
        if (this.dispWin) this.dispWin.textContent = step.win ? `${step.win.toLocaleString()} B` : (step.protocol === 'UDP' ? 'N/A' : '65,535 B');
        if (this.dispCwnd) this.dispCwnd.textContent = step.cwnd ? `${step.cwnd.toLocaleString()} B` : '14,600 B (10 MSS)';
        if (this.dispPhase) {
            let phase = 'Slow Start';
            if (step.cwnd && step.cwnd > 60000) phase = 'Congestion Avoidance';
            if (step.protocol === 'UDP') phase = 'Bitrate-Governed (UDP)';
            this.dispPhase.textContent = phase;
        }
        if (this.dispRtt) this.dispRtt.textContent = '~24 ms';
    }

    getStateBadgeClass(state) {
        if (!state) return 'state-badge-closed';
        const s = state.toUpperCase();
        if (s.includes('CLOSED')) return 'state-badge-closed';
        if (s.includes('LISTEN')) return 'state-badge-listen';
        if (s.includes('SYN')) return 'state-badge-syn';
        if (s.includes('ESTABLISHED')) return 'state-badge-established';
        if (s.includes('FIN') || s.includes('CLOSE_WAIT') || s.includes('LAST_ACK')) return 'state-badge-fin';
        if (s.includes('TIME_WAIT')) return 'state-badge-time-wait';
        return 'state-badge-established';
    }

    resetTcpIndicators() {
        this.tcpClientStateBadge.textContent = 'CLOSED';
        this.tcpClientStateBadge.className = 'state-badge state-badge-closed';
        this.tcpServerStateBadge.textContent = 'LISTEN';
        this.tcpServerStateBadge.className = 'state-badge state-badge-listen';
        this.tcpStatusText.textContent = 'Ready';
        this.tcpStatusText.className = 'state-badge state-badge-established';
        if (this.dispSeq) this.dispSeq.textContent = '-';
        if (this.dispAck) this.dispAck.textContent = '-';
        if (this.dispWin) this.dispWin.textContent = '65,535 B';
        if (this.dispCwnd) this.dispCwnd.textContent = '14,600 B (10 MSS)';
        if (this.dispPhase) this.dispPhase.textContent = 'Slow Start';
    }

    updateInspector(step) {
        if (!step) return;
        const emptyMsg = document.getElementById('inspectorEmpty');
        const content = document.getElementById('inspectorContent');
        if (emptyMsg) emptyMsg.classList.add('hidden');
        if (content) content.classList.remove('hidden');

        document.getElementById('inspProtocolBadge').textContent = step.protocol || 'TCP';
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
                <span class="field-val text-cyan">${this.escapeHtml(step.transport || 'TCP')}</span>
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
