/**
 * Main Application Controller (Assignment 2)
 * Handles tab switching, user activity dispatchers, activity logging,
 * and live dual-panel synchronization across Application and Transport layers.
 */

document.addEventListener('DOMContentLoaded', () => {

    // Tab buttons & Views
    const tabBtns = document.querySelectorAll('.tab-btn');
    const views = {
        browsing: document.getElementById('viewBrowsing'),
        mail: document.getElementById('viewMail'),
        streaming: document.getElementById('viewStreaming')
    };

    // Activity Log
    const logStream = document.getElementById('activityLogStream');
    const btnClearLog = document.getElementById('btnClearLog');

    // Browsing Elements
    const browseForm = document.getElementById('browseForm');
    const browseUrlInput = document.getElementById('browseUrlInput');
    const btnVisit = document.getElementById('btnVisit');
    const presetChips = document.querySelectorAll('.preset-chip');
    const mockupAddressBar = document.getElementById('mockupAddressBar');
    const browserStatusBadge = document.getElementById('browserStatusBadge');
    const browserPreviewFrame = document.getElementById('browserPreviewFrame');
    const viewportPlaceholder = document.querySelector('.viewport-placeholder');
    const browseTcpButtons = document.querySelectorAll('#browseTcpModeChoice .segmented-btn');

    // Mail Elements
    const mailForm = document.getElementById('mailForm');
    const btnSendMail = document.getElementById('btnSendMail');
    const mailFromInput = document.getElementById('mailFromInput');
    const mailToInput = document.getElementById('mailToInput');
    const mailSubjectInput = document.getElementById('mailSubjectInput');
    const mailBodyInput = document.getElementById('mailBodyInput');
    const mailStatusBadge = document.getElementById('mailStatusBadge');
    const envelopeQueueId = document.getElementById('envelopeQueueId');
    const mailRouteLine = document.getElementById('mailRouteLine');
    const routeMtaName = document.getElementById('routeMtaName');
    const envelopeDetails = document.getElementById('envelopeDetails');

    // -------------------------------------------------------------
    // Activity Logger
    // -------------------------------------------------------------
    window.logActivity = function(message, type = 'info') {
        const now = new Date();
        const timeStr = now.toTimeString().split(' ')[0];
        
        const entry = document.createElement('div');
        entry.className = `log-entry log-entry-${type}`;
        entry.innerHTML = `
            <span class="log-time">${timeStr}</span>
            <span class="log-msg">${escapeHtml(message)}</span>
        `;
        logStream.appendChild(entry);
        logStream.scrollTop = logStream.scrollHeight;
    };

    btnClearLog.addEventListener('click', () => {
        logStream.innerHTML = '';
        window.logActivity('Activity event log cleared.', 'info');
    });

    // -------------------------------------------------------------
    // Tab Switching
    // -------------------------------------------------------------
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.dataset.mode;
            
            tabBtns.forEach(b => {
                b.classList.remove('active');
                b.setAttribute('aria-selected', 'false');
            });
            btn.classList.add('active');
            btn.setAttribute('aria-selected', 'true');

            Object.values(views).forEach(view => view.classList.remove('active'));
            if (views[mode]) {
                views[mode].classList.add('active');
            }

            window.logActivity(`Switched activity mode to: ${mode.toUpperCase()}`, 'info');

            // Set default protocol badge text
            const badge = document.getElementById('activeProtocolBadge');
            if (mode === 'browsing') {
                if (badge) badge.textContent = 'DNS ➔ HTTP/1.1 • TCP Stream';
            } else if (mode === 'mail') {
                if (badge) badge.textContent = 'DNS MX ➔ SMTP (RFC 5321) • TCP Port 25';
            } else if (mode === 'streaming') {
                if (badge) badge.textContent = 'HLS / RTP ➔ Video Streaming • TCP/UDP';
            }
        });
    });

    // -------------------------------------------------------------
    // 1. Browsing Activity Handler
    // -------------------------------------------------------------
    browseTcpButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            browseTcpButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const isPersistent = btn.dataset.persistent === 'true';
            window.logActivity(`TCP Mode changed to: ${isPersistent ? 'PERSISTENT (Keep-Alive)' : 'NON-PERSISTENT (Teardown)'}`, 'info');
        });
    });

    presetChips.forEach(chip => {
        chip.addEventListener('click', () => {
            browseUrlInput.value = chip.dataset.url;
            executeBrowsing();
        });
    });

    browseForm.addEventListener('submit', (e) => {
        e.preventDefault();
        executeBrowsing();
    });

    async function executeBrowsing() {
        const rawUrl = browseUrlInput.value.trim() || 'example.com';
        const activeTcpBtn = document.querySelector('#browseTcpModeChoice .segmented-btn.active');
        const persistent = activeTcpBtn ? activeTcpBtn.dataset.persistent === 'true' : false;

        btnVisit.disabled = true;
        browserStatusBadge.textContent = 'Resolving DNS & Connecting TCP...';
        browserStatusBadge.className = 'mockup-status-badge';
        mockupAddressBar.textContent = rawUrl.startsWith('http') ? rawUrl : `http://${rawUrl}`;

        window.logActivity(`[BROWSE] Initiating visit to: ${rawUrl} (TCP Mode: ${persistent ? 'Keep-Alive' : 'Close'})`, 'protocol');

        try {
            const resp = await fetch('/api/browse', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: rawUrl, persistent: persistent })
            });
            const data = await resp.json();

            if (data.status === 'success') {
                browserStatusBadge.textContent = `${data.status_code} ${data.status_phrase} (${data.duration_ms}ms)`;
                browserStatusBadge.classList.add('badge-success');

                // Render in browser preview frame
                if (viewportPlaceholder) viewportPlaceholder.classList.add('hidden');
                browserPreviewFrame.classList.remove('hidden');
                browserPreviewFrame.srcdoc = data.html_content;

                window.logActivity(`[DNS] UDP Port 53 resolved '${data.domain}' ➔ ${data.resolved_ip}`, 'success');
                window.logActivity(`[TCP] 3-Way Handshake established on ${data.resolved_ip}:80 (SYN ➔ SYN-ACK ➔ ACK)`, 'protocol');
                window.logActivity(`[HTTP] GET ${data.url} ➔ HTTP ${data.status_code} ${data.status_phrase} (${data.duration_ms}ms total)`, 'success');
                if (!persistent) {
                    window.logActivity(`[TCP] 4-Way Connection Teardown executed (FIN-ACK ➔ ACK ➔ FIN-ACK ➔ ACK)`, 'info');
                } else {
                    window.logActivity(`[TCP] Connection retained in ESTABLISHED state for subsequent HTTP requests (Keep-Alive)`, 'info');
                }

                // Trigger Live Dual-Layer Protocol Visualization on Right Panel
                window.protocolVisualizer.loadDualSequences(
                    data.app_steps,
                    data.transport_steps,
                    `DNS ➔ HTTP/1.1 • TCP (${data.domain})`,
                    {
                        clientRole: 'Web Browser (Client)',
                        clientAddr: 'Port: 54212',
                        serverRole: `Web Server (${data.domain})`,
                        serverAddr: `${data.resolved_ip}:80`
                    }
                );
            } else {
                browserStatusBadge.textContent = 'Request Failed';
                window.logActivity(`[BROWSE] Request error: ${data.message || 'Unknown error'}`, 'warn');
            }
        } catch (err) {
            browserStatusBadge.textContent = 'Network Error';
            window.logActivity(`[BROWSE] Error fetching URL: ${err.message}`, 'warn');
        } finally {
            btnVisit.disabled = false;
        }
    }

    // -------------------------------------------------------------
    // 2. Mail Activity Handler (SMTP)
    // -------------------------------------------------------------
    mailForm.addEventListener('submit', (e) => {
        e.preventDefault();
        executeSendMail();
    });

    async function executeSendMail() {
        const fromEmail = mailFromInput.value.trim();
        const toEmail = mailToInput.value.trim();
        const subject = mailSubjectInput.value.trim();
        const body = mailBodyInput.value.trim();

        btnSendMail.disabled = true;
        mailStatusBadge.textContent = 'Transmitting...';
        envelopeQueueId.textContent = 'Queue ID: Negotiating';
        envelopeDetails.innerHTML = `<span class="badge badge-neutral">Executing DNS MX &amp; TCP Handshake (Port 25)...</span>`;

        // Animate route dot
        const routeDot = mailRouteLine.querySelector('.route-dot');
        if (routeDot) routeDot.style.left = '45%';

        window.logActivity(`[MAIL] Dispatching email from <${fromEmail}> to <${toEmail}>`, 'protocol');

        try {
            const resp = await fetch('/api/mail/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    from: fromEmail,
                    to: toEmail,
                    subject: subject,
                    body: body
                })
            });
            const data = await resp.json();

            if (data.status === 'success') {
                mailStatusBadge.textContent = '250 Delivered';
                mailStatusBadge.classList.add('badge-success');
                envelopeQueueId.textContent = `Queue ID: ${data.queue_id}`;
                routeMtaName.textContent = `MTA (${data.server_host}:25)`;
                envelopeDetails.innerHTML = `<span class="badge badge-success">✓ 250 2.0.0 Ok: queued as ${data.queue_id}</span>`;

                if (routeDot) routeDot.style.left = '90%';

                window.logActivity(`[DNS] UDP MX query resolved mail exchange: ${data.server_host}`, 'success');
                window.logActivity(`[TCP] 3-Way Handshake connected to SMTP server ${data.server_host}:25`, 'protocol');
                window.logActivity(`[SMTP] Complete RFC 5321 conversation: EHLO ➔ MAIL FROM ➔ RCPT TO ➔ DATA ➔ QUIT`, 'protocol');
                window.logActivity(`[TCP] All SMTP commands and replies transported over reliable byte-stream segments`, 'info');
                window.logActivity(`[SMTP] Accepted by MTA with Queue ID: ${data.queue_id}`, 'success');

                // Trigger Live Dual-Layer Protocol Visualization on Right Panel
                window.protocolVisualizer.loadDualSequences(
                    data.app_steps,
                    data.transport_steps,
                    `DNS MX ➔ SMTP RFC 5321 • TCP Stream (Port 25)`,
                    {
                        clientRole: 'Client Mail Agent (MUA)',
                        clientAddr: 'Port: 49152',
                        serverRole: `Mail Transfer Agent (${data.server_host})`,
                        serverAddr: 'Port: 25'
                    }
                );
            } else {
                mailStatusBadge.textContent = 'Failed';
                window.logActivity(`[SMTP] Mail transmission failed.`, 'warn');
            }
        } catch (err) {
            mailStatusBadge.textContent = 'Error';
            window.logActivity(`[SMTP] Network error: ${err.message}`, 'warn');
        } finally {
            btnSendMail.disabled = false;
        }
    }

    // -------------------------------------------------------------
    // Helpers
    // -------------------------------------------------------------
    function escapeHtml(text) {
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

    // Default startup action: Auto-visit example.com on page load for immediate visual engagement
    executeBrowsing();
});
