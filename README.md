# Dual-Panel Activity & Protocol Visualizer
### Computer Networks – Application Layer Dashboard

A full-stack, dual-panel interactive educational dashboard built with **Python (Flask)** and **Vanilla HTML5/CSS3/JavaScript**. It demonstrates what occurs at the Application and Transport layers in real time when users perform common network activities: **Web Browsing**, **Sending Mail (SMTP)**, and **Adaptive Bitrate Video Streaming (HLS)**.

---

## 🌟 Key Features

### 1. Strict Dual-Panel Architecture
- **Left Panel (Activity Panel)**:
  - **Browsing Mode**: Input URLs, use quick domain presets (`example.com`, `wikipedia.org`), view rendered responses inside a responsive browser mockup, and inspect live activity events.
  - **Mail Mode**: Interactive email composer with sender, recipient, subject, and body fields. Features an animated transmission route line and MTA status indicator.
  - **Streaming Mode**: Full online HTML5 video player playing real online MP4/HLS video streams (`Big Buck Bunny`, `Tears of Steel`, `Sintel`), quality selector (`1080p`, `720p`, `480p`, `360p`, `Auto`), real-time bitrate display, buffer capacity monitoring, and segment counters.
  - **Activity Event Log**: Timestamped, color-coded console tracking network events and protocol transitions.

- **Right Panel (Protocol Visualization Panel)**:
  - **Live Synchronization**: Left panel actions trigger synchronized packet timeline visualizations on the right.
  - **Animated Sequence Diagram**: Clear visual separation of actors (Client vs Server), directional arrows (`Client ➔ Server` in blue/cyan, `Server ➔ Client` in emerald green), and timing offsets.
  - **Exact Protocol Messages**:
    - **Browsing**: DNS A-record query/response on UDP port 53 followed by HTTP/1.1 `GET` request and `200 OK` response with headers and body snippets.
    - **Mail**: DNS MX lookup followed by the complete RFC 5321 SMTP handshake (`220 Greeting`, `EHLO`, `250 Capabilities`, `MAIL FROM`, `250 OK`, `RCPT TO`, `250 OK`, `DATA`, `354 Start Mail Input`, message payload, `250 Queued`, `QUIT`, `221 Bye`).
    - **Streaming**: DNS CDN lookup, master manifest (`master.m3u8`), media playlist (`index.m3u8`), and chunked segment requests (`segment_000.ts`, `Range: bytes=...`, `HTTP 206 Partial Content`).
  - **Interactive Controls**: Play/Pause, Step Forward (Next), Step Backward (Prev), Replay, Speed Adjustment (`0.5x`, `1.0x`, `2.0x`), and keyboard shortcuts (Space, Arrow keys).
  - **Dual Views**: Toggle between **Flow View** (Sequence Diagram) and **Packets View** (Wireshark-style Raw Wire Inspector with CRLF headers and field tables).

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Option 1: One-Click Launch Script
```bash
cd /Users/ravikumar/.gemini/antigravity-ide/scratch/protocol-visualizer
./run.sh
```

### Option 2: Manual Setup
```bash
# 1. Navigate to project root
cd /Users/ravikumar/.gemini/antigravity-ide/scratch/protocol-visualizer

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the Flask server
python app.py
```

Open your browser and navigate to:
```
http://localhost:5005
```

---

## 🧪 Running Automated Tests
The repository includes a comprehensive test suite covering protocol engines, REST APIs, and template delivery:

```bash
./venv/bin/python -m unittest tests/test_protocol_visualizer.py -v
```

---

## 📁 Project Directory Structure
```
protocol-visualizer/
├── app.py                      # Flask application server & REST APIs
├── requirements.txt            # Python dependencies (Flask, Requests)
├── run.sh                      # Shell script for automated setup and launch
├── protocol_engine/            # Protocol simulation and network engine
│   ├── __init__.py
│   ├── dns_engine.py           # RFC 1035 DNS query/response generator
│   ├── http_engine.py          # HTTP/1.1 request/response parser & live fetcher
│   ├── smtp_engine.py          # RFC 5321 SMTP conversation engine
│   └── streaming_engine.py     # HLS/DASH manifest & chunked segment engine
├── static/
│   ├── css/
│   │   └── style.css           # Glassmorphism UI, sequence diagrams, dark mode
│   └── js/
│       ├── app.js              # Activity tab management, forms, event logs
│       ├── visualizer.js       # Sequence animator, state machine, packet inspector
│       └── streaming.js        # HTML5 video sync, segment pipeline, telemetry
├── templates/
│   └── index.html              # Responsive dual-panel layout
├── tests/
│   └── test_protocol_visualizer.py # Unit and integration test suite
├── AI_USAGE_LOG.md             # AI platform, model, prompt iterations, evidence
└── REFLECTION.md               # 1-2 page academic reflection report
```

---

## 📚 Deliverables Included
1. **Source Code**: Fully functional, modular Flask backend and responsive HTML/JS/CSS frontend.
2. **AI Usage Log**: [AI_USAGE_LOG.md](AI_USAGE_LOG.md) detailing Google Antigravity and Gemini 3.8 Flash collaboration.
3. **Reflection Document**: [REFLECTION.md](REFLECTION.md) answering all four criteria outlined in the course specification.
