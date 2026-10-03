/**
 * Streaming Controller (Assignment 2)
 * Connects real online HTML5 video playback with protocol telemetry and segment packet transfers.
 * Supports comparison between TCP (HLS Chunks), UDP (RTP Datagrams), and QUIC (HTTP/3).
 */

class StreamingController {
    constructor() {
        this.videoPlayer = document.getElementById('onlineVideoPlayer');
        this.videoSelect = document.getElementById('videoSelect');
        this.qualitySelect = document.getElementById('qualitySelect');
        this.btnInitStream = document.getElementById('btnInitStream');
        this.transportButtons = document.querySelectorAll('#streamTransportModeChoice .segmented-btn');
        
        // Telemetry Displays
        this.cdnEdgeDisplay = document.getElementById('cdnEdgeDisplay');
        this.bitrateDisplay = document.getElementById('bitrateDisplay');
        this.segmentCountDisplay = document.getElementById('segmentCountDisplay');
        this.bufferCapacityDisplay = document.getElementById('bufferCapacityDisplay');
        this.bufferFill = document.getElementById('bufferFill');
        this.qualityOverlay = document.getElementById('videoQualityOverlay');

        this.currentVideoId = 'bbb';
        this.currentQuality = '720p';
        this.transportMode = 'tcp'; // 'tcp', 'udp', 'quic'
        this.segmentCount = 0;
        this.nextSegmentNum = 1;
        this.lastSegmentPlaybackTime = 0;
        this.isStreamingActive = false;

        this.bindEvents();
    }

    bindEvents() {
        this.btnInitStream.addEventListener('click', () => this.startStreaming());

        this.videoSelect.addEventListener('change', (e) => {
            this.currentVideoId = e.target.value;
            this.startStreaming();
        });

        this.qualitySelect.addEventListener('change', (e) => {
            this.handleQualityChange(e.target.value);
        });

        // Transport Mode Selector Buttons (TCP vs UDP vs QUIC)
        this.transportButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.transportButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.transportMode = btn.dataset.mode;
                window.logActivity(`Video Transport Protocol changed to: ${this.transportMode.toUpperCase()}`, 'protocol');
                if (this.isStreamingActive) {
                    this.startStreaming();
                }
            });
        });

        // Track video playback time to trigger progressive segment requests
        this.videoPlayer.addEventListener('timeupdate', () => this.onTimeUpdate());
        this.videoPlayer.addEventListener('progress', () => this.updateBufferMetrics());
        this.videoPlayer.addEventListener('play', () => {
            window.logActivity('Video playback started on online media player.', 'info');
        });
        this.videoPlayer.addEventListener('pause', () => {
            window.logActivity('Video playback paused by user.', 'warn');
        });
    }

    async startStreaming() {
        this.currentVideoId = this.videoSelect.value;
        this.currentQuality = this.qualitySelect.value === 'auto' ? '720p' : this.qualitySelect.value;
        this.segmentCount = 0;
        this.nextSegmentNum = 1;
        this.lastSegmentPlaybackTime = 0;
        this.isStreamingActive = true;

        const modeLabel = this.transportMode.toUpperCase();
        window.logActivity(`Initiating video stream: ${this.videoSelect.options[this.videoSelect.selectedIndex].text} at ${this.currentQuality} via ${modeLabel}`, 'protocol');

        try {
            const resp = await fetch('/api/stream/init', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    video_id: this.currentVideoId,
                    quality: this.currentQuality,
                    transport_mode: this.transportMode
                })
            });
            const data = await resp.json();

            if (data.status === 'success') {
                const video = data.video;
                const qualInfo = video.qualities[this.currentQuality];

                // Update Telemetry
                this.cdnEdgeDisplay.textContent = video.cdn_host;
                this.bitrateDisplay.textContent = qualInfo.bitrate;
                this.qualityOverlay.textContent = `${this.currentQuality} • ${qualInfo.bitrate} • ${modeLabel}`;
                this.segmentCountDisplay.textContent = `1 chunk (Init)`;

                // Update HTML5 Video source
                if (video.video_url && this.videoPlayer.src !== video.video_url) {
                    this.videoPlayer.src = video.video_url;
                    this.videoPlayer.load();
                    this.videoPlayer.play().catch(() => {
                        console.log('Autoplay deferred until user interaction');
                    });
                }

                window.logActivity(`[DNS] Resolved: ${video.cdn_host} ➔ ${video.cdn_ip} (UDP Port 53)`, 'success');
                if (this.transportMode === 'tcp') {
                    window.logActivity(`[TCP] 3-Way Handshake with CDN edge ${video.cdn_ip}:443`, 'protocol');
                    window.logActivity(`[HLS] Master Manifest & Media Playlist retrieved via HTTP GET over TCP`, 'protocol');
                    window.logActivity(`[TCP] Initial buffer chunk received. cwnd doubled (Slow Start phase)`, 'success');
                } else if (this.transportMode === 'udp') {
                    window.logActivity(`[UDP/RTP] Direct media datagram channel opened (0-RTT, No TCP handshake overhead)`, 'protocol');
                    window.logActivity(`[RTP] Streaming H.264 video datagrams (Payload Type 96, 90kHz timestamp clock)`, 'success');
                } else if (this.transportMode === 'quic') {
                    window.logActivity(`[QUIC] 1-RTT Handshake completed over UDP Port 443 with TLS 1.3 encapsulation`, 'protocol');
                    window.logActivity(`[HTTP/3] Multiplexed independent streams active (Eliminates Head-of-Line blocking)`, 'success');
                }

                // Feed protocol steps to Right Panel visualizer (Dual Sequences)
                window.protocolVisualizer.loadDualSequences(
                    data.app_steps,
                    data.transport_steps,
                    `HLS Streaming ➔ ${video.title.split(' ')[0]} (${modeLabel})`,
                    {
                        clientRole: 'HTML5 Video Player',
                        clientAddr: 'Port: 51240',
                        serverRole: `CDN Edge (${video.cdn_host})`,
                        serverAddr: `${video.cdn_ip}:${this.transportMode === 'udp' ? '5004' : '443'}`
                    }
                );
            }
        } catch (err) {
            console.error('Error starting video stream:', err);
            window.logActivity(`Stream initialization failed: ${err.message}`, 'warn');
        }
    }

    async handleQualityChange(newQuality) {
        if (!this.isStreamingActive) {
            this.currentQuality = newQuality === 'auto' ? '720p' : newQuality;
            return;
        }

        const selectedTier = newQuality === 'auto' ? '720p' : newQuality;
        window.logActivity(`Adaptive Bitrate Switch: Switching stream quality to ${newQuality.toUpperCase()} (${this.transportMode.toUpperCase()})...`, 'protocol');

        try {
            const nextStepNum = (window.protocolVisualizer.activeSteps.length || 8) + 1;
            const resp = await fetch('/api/stream/segment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    video_id: this.currentVideoId,
                    quality: selectedTier,
                    segment_num: this.nextSegmentNum++,
                    start_step_num: nextStepNum,
                    transport_mode: this.transportMode
                })
            });
            const data = await resp.json();

            if (data.status === 'success') {
                this.currentQuality = selectedTier;
                this.segmentCount++;
                this.segmentCountDisplay.textContent = `${this.segmentCount + 1} chunks`;
                this.bitrateDisplay.textContent = data.response_step.fields.Bitrate || '3,000 kbps';
                this.qualityOverlay.textContent = `${this.currentQuality} • ${this.bitrateDisplay.textContent} • ${this.transportMode.toUpperCase()}`;

                window.logActivity(`[ABR] Switched to ${selectedTier}. Fetched ${data.request_step.fields.Segment} (${data.response_step.fields['Chunk Size']})`, 'success');

                // Append request & response to live visualizer
                if (data.transport_steps && data.transport_steps.length > 0) {
                    data.transport_steps.forEach(st => window.protocolVisualizer.appendLiveStep(st));
                } else {
                    window.protocolVisualizer.appendLiveStep(data.request_step);
                    window.protocolVisualizer.appendLiveStep(data.response_step);
                }
            }
        } catch (err) {
            console.error('Error switching stream quality:', err);
        }
    }

    onTimeUpdate() {
        if (!this.isStreamingActive) return;
        const currentTime = this.videoPlayer.currentTime;
        this.updateBufferMetrics();

        // Fetch segment periodically as video plays
        if (currentTime - this.lastSegmentPlaybackTime >= 3.5) {
            this.lastSegmentPlaybackTime = currentTime;
            this.fetchNextSegment();
        }
    }

    async fetchNextSegment() {
        const segNum = this.nextSegmentNum++;
        const nextStepNum = (window.protocolVisualizer.activeSteps.length || 8) + 1;

        try {
            const resp = await fetch('/api/stream/segment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    video_id: this.currentVideoId,
                    quality: this.currentQuality,
                    segment_num: segNum,
                    start_step_num: nextStepNum,
                    transport_mode: this.transportMode
                })
            });
            const data = await resp.json();

            if (data.status === 'success') {
                this.segmentCount++;
                this.segmentCountDisplay.textContent = `${this.segmentCount + 1} chunks`;

                if (this.transportMode === 'tcp') {
                    window.logActivity(`[TCP] Video segment #${segNum} downloaded. ACK received. Receive Window advertised.`, 'info');
                } else if (this.transportMode === 'udp') {
                    window.logActivity(`[UDP/RTP] Video datagram #${segNum} streamed (Loss-tolerant, unacknowledged).`, 'info');
                }

                // Append transport steps
                if (data.transport_steps && data.transport_steps.length > 0) {
                    data.transport_steps.forEach(st => window.protocolVisualizer.appendLiveStep(st));
                } else {
                    window.protocolVisualizer.appendLiveStep(data.request_step);
                    window.protocolVisualizer.appendLiveStep(data.response_step);
                }
            }
        } catch (err) {
            console.error('Error fetching progressive video segment:', err);
        }
    }

    updateBufferMetrics() {
        if (!this.videoPlayer || !this.videoPlayer.buffered.length) return;
        const currentTime = this.videoPlayer.currentTime;
        const duration = this.videoPlayer.duration || 600;
        let forwardBuffer = 0;

        for (let i = 0; i < this.videoPlayer.buffered.length; i++) {
            const start = this.videoPlayer.buffered.start(i);
            const end = this.videoPlayer.buffered.end(i);
            if (currentTime >= start && currentTime <= end) {
                forwardBuffer = end - currentTime;
                break;
            }
        }

        this.bufferCapacityDisplay.textContent = `${forwardBuffer.toFixed(1)}s`;
        const bufferPct = Math.min(100, Math.max(5, (forwardBuffer / 30) * 100));
        if (this.bufferFill) {
            this.bufferFill.style.width = `${bufferPct}%`;
        }
    }
}

// Instantiate streaming controller globally
window.streamingController = new StreamingController();
