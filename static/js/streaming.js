/**
 * Streaming Controller
 * Connects real online HTML5 video playback with protocol telemetry and segment packet transfers.
 */

class StreamingController {
    constructor() {
        this.videoPlayer = document.getElementById('onlineVideoPlayer');
        this.videoSelect = document.getElementById('videoSelect');
        this.qualitySelect = document.getElementById('qualitySelect');
        this.btnInitStream = document.getElementById('btnInitStream');
        
        // Telemetry Displays
        this.cdnEdgeDisplay = document.getElementById('cdnEdgeDisplay');
        this.bitrateDisplay = document.getElementById('bitrateDisplay');
        this.segmentCountDisplay = document.getElementById('segmentCountDisplay');
        this.bufferCapacityDisplay = document.getElementById('bufferCapacityDisplay');
        this.bufferFill = document.getElementById('bufferFill');
        this.qualityOverlay = document.getElementById('videoQualityOverlay');

        this.currentVideoId = 'bbb';
        this.currentQuality = '720p';
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

        window.logActivity(`Initiating video stream: ${this.videoSelect.options[this.videoSelect.selectedIndex].text} at ${this.currentQuality}`, 'protocol');

        try {
            const resp = await fetch('/api/stream/init', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    video_id: this.currentVideoId,
                    quality: this.currentQuality
                })
            });
            const data = await resp.json();

            if (data.status === 'success') {
                const video = data.video;
                const qualInfo = video.qualities[this.currentQuality];

                // Update Telemetry
                this.cdnEdgeDisplay.textContent = video.cdn_host;
                this.bitrateDisplay.textContent = qualInfo.bitrate;
                this.qualityOverlay.textContent = `${this.currentQuality} • ${qualInfo.bitrate}`;
                this.segmentCountDisplay.textContent = `1 chunk (Init)`;

                // Update HTML5 Video source
                if (video.video_url) {
                    this.videoPlayer.src = video.video_url;
                    this.videoPlayer.load();
                    this.videoPlayer.play().catch(() => {
                        // Autoplay might be muted or blocked by browser policy
                        console.log('Autoplay deferred until user interaction');
                    });
                }

                window.logActivity(`DNS resolved: ${video.cdn_host} ➔ ${video.cdn_ip}`, 'success');
                window.logActivity(`HLS Master Manifest loaded. Available bitrates: 1080p, 720p, 480p, 360p`, 'protocol');
                window.logActivity(`Initial buffer chunk (segment_000.ts) received via HTTP 206 Partial Content.`, 'success');

                // Feed protocol steps to Right Panel visualizer
                window.protocolVisualizer.loadSequence(
                    data.steps,
                    'DNS ➔ HTTP HLS (Manifest + Segments)',
                    {
                        clientRole: 'HTML5 Video Player',
                        clientAddr: 'Port: 51240',
                        serverRole: `CDN Edge (${video.cdn_host})`,
                        serverAddr: `${video.cdn_ip}:443`
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
        window.logActivity(`Adaptive Bitrate Switch: Switching stream quality to ${newQuality.toUpperCase()}...`, 'protocol');

        try {
            const nextStepNum = (window.protocolVisualizer.steps.length || 8) + 1;
            const resp = await fetch('/api/stream/segment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    video_id: this.currentVideoId,
                    quality: selectedTier,
                    segment_num: this.nextSegmentNum++,
                    start_step_num: nextStepNum
                })
            });
            const data = await resp.json();

            if (data.status === 'success') {
                this.currentQuality = selectedTier;
                this.segmentCount++;
                this.segmentCountDisplay.textContent = `${this.segmentCount + 1} chunks`;
                this.bitrateDisplay.textContent = data.response_step.fields.Bitrate || '3,000 kbps';
                this.qualityOverlay.textContent = `${this.currentQuality} • ${this.bitrateDisplay.textContent}`;

                window.logActivity(`Switched to ${selectedTier}. Fetched ${data.request_step.fields.Segment} (${data.response_step.fields['Chunk Size']})`, 'success');

                // Append request & response to live visualizer
                window.protocolVisualizer.appendLiveStep(data.request_step);
                setTimeout(() => {
                    window.protocolVisualizer.appendLiveStep(data.response_step);
                }, 300);
            }
        } catch (err) {
            console.error('Error switching stream quality:', err);
        }
    }

    onTimeUpdate() {
        if (!this.isStreamingActive) return;

        const currentTime = this.videoPlayer.currentTime;
        this.updateBufferMetrics();

        // Every 3 seconds of forward playback, simulate requesting the next video segment chunk
        if (currentTime - this.lastSegmentPlaybackTime >= 3.5) {
            this.lastSegmentPlaybackTime = currentTime;
            this.fetchNextSegment();
        }
    }

    async fetchNextSegment() {
        const segNum = this.nextSegmentNum++;
        const nextStepNum = (window.protocolVisualizer.steps.length || 8) + 1;

        try {
            const resp = await fetch('/api/stream/segment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    video_id: this.currentVideoId,
                    quality: this.currentQuality,
                    segment_num: segNum,
                    start_step_num: nextStepNum
                })
            });
            const data = await resp.json();

            if (data.status === 'success') {
                this.segmentCount++;
                this.segmentCountDisplay.textContent = `${this.segmentCount + 1} chunks`;
                
                window.logActivity(`[HLS] HTTP GET ${data.request_step.fields.Segment} ➔ HTTP 206 Partial Content (${data.response_step.fields['Chunk Size']})`, 'protocol');

                // Append dynamically to visualizer
                window.protocolVisualizer.appendLiveStep(data.request_step);
                setTimeout(() => {
                    window.protocolVisualizer.appendLiveStep(data.response_step);
                }, 250);
            }
        } catch (err) {
            console.error('Error fetching stream segment:', err);
        }
    }

    updateBufferMetrics() {
        const player = this.videoPlayer;
        if (!player || !player.buffered.length) return;

        try {
            const currentTime = player.currentTime;
            let forwardBuffer = 0;
            for (let i = 0; i < player.buffered.length; i++) {
                if (player.buffered.start(i) <= currentTime && player.buffered.end(i) >= currentTime) {
                    forwardBuffer = player.buffered.end(i) - currentTime;
                    break;
                }
            }
            this.bufferCapacityDisplay.textContent = `${forwardBuffer.toFixed(1)}s`;

            // Buffer fill percentage against 30s target
            const pct = Math.min(100, Math.round((forwardBuffer / 20) * 100));
            this.bufferFill.style.width = `${pct}%`;
        } catch (e) {
            // Buffer query exception safeguard
        }
    }
}

// Instantiate streaming controller globally
window.streamingController = new StreamingController();
