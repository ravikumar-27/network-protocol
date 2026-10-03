"""
Dual-Panel Activity & Protocol Visualizer - Flask Application Server
Course: Computer Networks – Application & Transport Layer
Features:
- Dual-Panel Architecture with synchronized Application Layer & Transport Layer views
- Application Layer: DNS (RFC 1035), HTTP/1.1 (RFC 9110), SMTP (RFC 5321), HLS Video
- Transport Layer: TCP 3-Way Handshake, Sequence/Ack Progression, Flow & Congestion Control,
  4-Way Teardown (RFC 793), UDP Datagrams (RFC 768), RTP (RFC 3550), and QUIC (RFC 9000).
"""
import os
import sys
from flask import Flask, render_template, request, jsonify

# Ensure local modules are accessible
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from protocol_engine import (
    resolve_dns,
    execute_http_request,
    simulate_smtp_transaction,
    generate_streaming_init_steps,
    generate_segment_step,
    STREAM_PRESETS,
    generate_browsing_transport_steps,
    generate_mail_transport_steps,
    generate_streaming_transport_steps,
    generate_streaming_segment_transport_steps
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "transport-layer-visualizer-secret"

@app.route("/")
def index():
    """Renders the dual-panel web dashboard."""
    return render_template("index.html", presets=STREAM_PRESETS)

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "Dual-Panel Activity & Protocol Visualizer (Assignment 2)",
        "layers_supported": ["Application Layer", "Transport Layer"],
        "protocols_supported": {
            "application": ["DNS (RFC 1035)", "HTTP/1.1 (RFC 9110)", "SMTP (RFC 5321)", "HLS Streaming"],
            "transport": ["TCP (RFC 793)", "UDP (RFC 768)", "RTP (RFC 3550)", "QUIC (RFC 9000)"]
        }
    })

@app.route("/api/browse", methods=["POST"])
def browse():
    """
    Browsing activity endpoint:
    - Application Layer: DNS A-record lookup + HTTP GET request/response.
    - Transport Layer: UDP DNS datagrams + TCP 3-way handshake + PSH-ACK data + Teardown.
    """
    data = request.get_json() or {}
    raw_url = data.get("url", "example.com").strip()
    persistent = bool(data.get("persistent", False))
    if not raw_url:
        raw_url = "example.com"

    # Normalize url
    if not raw_url.startswith("http://") and not raw_url.startswith("https://"):
        url = "http://" + raw_url
    else:
        url = raw_url

    # Extract hostname
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc.split(":")[0] or "example.com"

    # 1. DNS Resolution (App Layer)
    dns_result = resolve_dns(domain, "A")
    primary_ip = dns_result["primary_ip"]

    # 2. HTTP Request & Response (App Layer)
    http_result = execute_http_request(url, primary_ip)

    # Combine App Layer steps sequentially
    app_steps = []
    for step in dns_result["steps"]:
        app_steps.append(step)
        
    for idx, step in enumerate(http_result["steps"], start=len(app_steps) + 1):
        step["step_number"] = idx
        step["timestamp_offset_ms"] += dns_result["lookup_time_ms"]
        app_steps.append(step)

    # 3. Transport Layer Steps (TCP + UDP)
    transport_steps = generate_browsing_transport_steps(
        dns_steps=dns_result["steps"],
        http_steps=http_result["steps"],
        domain=domain,
        server_ip=primary_ip,
        persistent=persistent
    )

    return jsonify({
        "status": "success",
        "activity": "browsing",
        "url": url,
        "domain": domain,
        "resolved_ip": primary_ip,
        "status_code": http_result["status_code"],
        "status_phrase": http_result["status_phrase"],
        "duration_ms": dns_result["lookup_time_ms"] + http_result["duration_ms"],
        "html_content": http_result["html_content"],
        "persistent": persistent,
        # Backward-compatible steps field (Application layer)
        "steps": app_steps,
        "app_steps": app_steps,
        "transport_steps": transport_steps,
        "total_app_steps": len(app_steps),
        "total_transport_steps": len(transport_steps)
    })

@app.route("/api/mail/send", methods=["POST"])
def send_mail():
    """
    Mail activity endpoint:
    - Application Layer: DNS MX lookup + complete RFC 5321 SMTP conversation.
    - Transport Layer: UDP DNS lookup + TCP 3-way handshake + conversational PSH-ACK byte stream + Teardown.
    """
    data = request.get_json() or {}
    from_email = data.get("from", "student@university.edu")
    to_email = data.get("to", "professor@university.edu")
    subject = data.get("subject", "Application & Transport Layer Visualizer")
    body = data.get("body", "Hello Professor,\nThis is a live demonstration of SMTP RFC 5321 and underlying TCP byte-stream transport.")

    smtp_result = simulate_smtp_transaction(from_email, to_email, subject, body)
    app_steps = smtp_result["steps"]

    # Transport Layer steps
    transport_steps = generate_mail_transport_steps(
        from_email=from_email,
        to_email=to_email,
        subject=subject,
        body=body,
        smtp_result=smtp_result
    )

    return jsonify({
        "status": "success",
        "activity": "mail",
        "from": smtp_result["from"],
        "to": smtp_result["to"],
        "subject": smtp_result["subject"],
        "server_host": smtp_result["server_host"],
        "queue_id": smtp_result["queue_id"],
        "steps": app_steps,
        "app_steps": app_steps,
        "transport_steps": transport_steps,
        "total_app_steps": len(app_steps),
        "total_transport_steps": len(transport_steps)
    })

@app.route("/api/stream/presets", methods=["GET"])
def stream_presets():
    """Returns available online video presets and quality options."""
    return jsonify(STREAM_PRESETS)

@app.route("/api/stream/init", methods=["POST"])
def stream_init():
    """
    Streaming activity start endpoint:
    - Application Layer: DNS CDN resolution, master playlist, quality playlist, segment 0.
    - Transport Layer: TCP handshake, manifest & chunk data transfers with Flow/Congestion control.
      Optionally supports 'udp' (RTP live stream) or 'quic' (HTTP/3) comparison modes!
    """
    data = request.get_json() or {}
    video_id = data.get("video_id", "bbb")
    quality = data.get("quality", "720p")
    transport_mode = data.get("transport_mode", "tcp").lower()
    if transport_mode not in ["tcp", "udp", "quic"]:
        transport_mode = "tcp"

    app_result = generate_streaming_init_steps(video_id, quality)
    app_steps = app_result["steps"]
    video = app_result["video"]

    # Transport Layer steps
    transport_steps = generate_streaming_transport_steps(
        video=video,
        quality=quality,
        stream_init_result=app_result,
        mode=transport_mode
    )

    return jsonify({
        "status": "success",
        "activity": "streaming",
        "video": video,
        "quality": quality,
        "transport_mode": transport_mode,
        "steps": app_steps,
        "app_steps": app_steps,
        "transport_steps": transport_steps,
        "total_app_steps": len(app_steps),
        "total_transport_steps": len(transport_steps)
    })

@app.route("/api/stream/segment", methods=["POST"])
def stream_segment():
    """
    Fetches next video transport stream (.ts) segment pair dynamically:
    Returns both Application Layer HTTP 206 Partial Content request/response
    and Transport Layer TCP/UDP/QUIC segment packets.
    """
    data = request.get_json() or {}
    video_id = data.get("video_id", "bbb")
    quality = data.get("quality", "720p")
    segment_num = int(data.get("segment_num", 1))
    start_step_num = int(data.get("start_step_num", 9))
    transport_mode = data.get("transport_mode", "tcp").lower()
    if transport_mode not in ["tcp", "udp", "quic"]:
        transport_mode = "tcp"

    pair = generate_segment_step(video_id, quality, segment_num, start_step_num)
    video = STREAM_PRESETS.get(video_id, STREAM_PRESETS["bbb"])

    # Transport segment steps
    transport_steps = generate_streaming_segment_transport_steps(
        video=video,
        quality=quality,
        segment_num=segment_num,
        start_step_num=start_step_num,
        mode=transport_mode
    )

    return jsonify({
        "status": "success",
        "transport_mode": transport_mode,
        "request_step": pair["request_step"],
        "response_step": pair["response_step"],
        "transport_steps": transport_steps
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    print(f"[*] Starting Dual-Panel Visualizer (Assignment 2) on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
