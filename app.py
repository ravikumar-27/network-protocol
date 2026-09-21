"""
Dual-Panel Activity & Protocol Visualizer - Flask Application Server
Author: Antigravity Agent & Student Pair
Course: Computer Networks - Application Layer
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
    STREAM_PRESETS
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "application-layer-visualizer-secret"

@app.route("/")
def index():
    """Renders the dual-panel web dashboard."""
    return render_template("index.html", presets=STREAM_PRESETS)

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "Dual-Panel Activity & Protocol Visualizer",
        "protocols_supported": ["DNS", "HTTP/1.1", "SMTP (RFC 5321)", "HLS Streaming"]
    })

@app.route("/api/browse", methods=["POST"])
def browse():
    """
    Browsing activity endpoint:
    Performs DNS resolution (A record) followed by HTTP GET request + response.
    """
    data = request.get_json() or {}
    raw_url = data.get("url", "example.com").strip()
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

    # Step 1 & 2: DNS Resolution
    dns_result = resolve_dns(domain, "A")
    primary_ip = dns_result["primary_ip"]

    # Step 3 & 4: HTTP Request & Response
    http_result = execute_http_request(url, primary_ip)

    # Combine steps and re-number sequentially
    combined_steps = []
    for step in dns_result["steps"]:
        combined_steps.append(step)
        
    for idx, step in enumerate(http_result["steps"], start=len(combined_steps) + 1):
        step["step_number"] = idx
        step["timestamp_offset_ms"] += dns_result["lookup_time_ms"]
        combined_steps.append(step)

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
        "steps": combined_steps,
        "total_steps": len(combined_steps)
    })

@app.route("/api/mail/send", methods=["POST"])
def send_mail():
    """
    Mail activity endpoint:
    Triggers DNS MX lookup followed by complete RFC 5321 SMTP conversation:
    EHLO, MAIL FROM, RCPT TO, DATA, QUIT.
    """
    data = request.get_json() or {}
    from_email = data.get("from", "student@university.edu")
    to_email = data.get("to", "professor@university.edu")
    subject = data.get("subject", "Application Layer Project Demo")
    body = data.get("body", "Hello Professor,\nThis is a live demonstration of the RFC 5321 SMTP protocol state machine.")

    result = simulate_smtp_transaction(from_email, to_email, subject, body)

    return jsonify({
        "status": "success",
        "activity": "mail",
        "from": result["from"],
        "to": result["to"],
        "subject": result["subject"],
        "server_host": result["server_host"],
        "queue_id": result["queue_id"],
        "steps": result["steps"],
        "total_steps": result["total_steps"]
    })

@app.route("/api/stream/presets", methods=["GET"])
def stream_presets():
    """Returns available online video presets and quality options."""
    return jsonify(STREAM_PRESETS)

@app.route("/api/stream/init", methods=["POST"])
def stream_init():
    """
    Streaming activity start endpoint:
    Triggers DNS CDN resolution, master playlist fetch, quality playlist fetch,
    and initial chunk download.
    """
    data = request.get_json() or {}
    video_id = data.get("video_id", "bbb")
    quality = data.get("quality", "720p")

    result = generate_streaming_init_steps(video_id, quality)

    return jsonify({
        "status": "success",
        "activity": "streaming",
        "video": result["video"],
        "quality": result["quality"],
        "steps": result["steps"],
        "total_steps": result["total_steps"]
    })

@app.route("/api/stream/segment", methods=["POST"])
def stream_segment():
    """
    Fetches next video transport stream (.ts) segment request/response pair
    dynamically as video plays or quality shifts.
    """
    data = request.get_json() or {}
    video_id = data.get("video_id", "bbb")
    quality = data.get("quality", "720p")
    segment_num = int(data.get("segment_num", 1))
    start_step_num = int(data.get("start_step_num", 9))

    pair = generate_segment_step(video_id, quality, segment_num, start_step_num)

    return jsonify({
        "status": "success",
        "request_step": pair["request_step"],
        "response_step": pair["response_step"]
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    print(f"[*] Starting Dual-Panel Visualizer on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
