# Dual-Panel Activity & Transport-Layer Protocol Visualizer
### Computer Networks – Assignment 2 (Extension of Application Layer Dashboard)

An interactive, educational network visualizer built with **Python (Flask)** and **Vanilla HTML5/CSS3/JavaScript**. It bridges the gap between high-level user activities (**Web Browsing**, **Sending Mail**, and **Video Streaming**) and both the **Application Layer** (DNS, HTTP/1.1, SMTP, HLS) and the underlying **Transport Layer** (TCP RFC 793, UDP RFC 768, RTP RFC 3550, and QUIC RFC 9000) in real time.

---

## 🌟 Key Features

### 1. Strict Dual-Panel Architecture
- **Left Panel (Activity Panel)**:
  - **Browsing Mode**: Input URLs, quick domain presets (`example.com`, `wikipedia.org`), responsive browser viewport mockup, and **TCP Mode Toggle** (`Non-Persistent [Close]` vs `Persistent [Keep-Alive]`).
  - **Mail Mode**: Interactive email composer with sender, recipient, subject, and body fields, with animated transmission route lines and MTA status indicator.
  - **Streaming Mode**: Online HTML5 video player (`Big Buck Bunny`, `Tears of Steel`, `Sintel`), quality selector (`1080p`, `720p`, `480p`, `360p`, `Auto`), real-time bitrate display, buffer capacity monitoring, and **Transport Protocol Selector** (`TCP [HLS Chunks]`, `UDP [RTP Live Datagrams]`, `QUIC [HTTP/3]`).
  - **Activity Event Log**: Timestamped, color-coded console tracking network events and protocol transitions across both layers.

- **Right Panel (Protocol Visualization Panel)**:
  - **Live Synchronization**: Every user action on the left panel drives parallel, synchronized animations on the right.
  - **Layer Switcher Tabs**:
    1. **Application Layer View**: DNS A/MX lookups, HTTP GET/200 requests/responses, RFC 5321 SMTP handshake, HLS manifests/playlists.
    2. **Transport Layer View**: TCP 3-way handshake (`SYN`, `SYN-ACK`, `ACK`), byte-level sequence and acknowledgment tracking, PSH+ACK payload transfers, MSS segmentation, flow control (`Win`), congestion control (`cwnd`, `ssthresh`, Slow Start vs Congestion Avoidance), 4-way teardown (`FIN-ACK`, `TIME_WAIT`), UDP datagrams, and QUIC streams.
    3. **Dual View (Side-by-Side)**: Synchronized split columns showing both Application Layer and Transport Layer flows progressing together in lockstep.
  - **TCP State Machine Live Status Bar**:
    - Real-time client state tracking: `CLOSED` ➔ `SYN_SENT` ➔ `ESTABLISHED` ➔ `FIN_WAIT_1` ➔ `FIN_WAIT_2` ➔ `TIME_WAIT` ➔ `CLOSED`.
    - Real-time server state tracking: `LISTEN` ➔ `SYN_RCVD` ➔ `ESTABLISHED` ➔ `CLOSE_WAIT` ➔ `LAST_ACK` ➔ `CLOSED`.
  - **Flow & Congestion Control Telemetry Bar**:
    - Displays `Seq`, `Ack`, `Win` (Receive Window), `cwnd` (Congestion Window), `ssthresh`, `RTT`, and phase (`Slow Start` vs `Congestion Avoidance`).
  - **Interactive Controls**: Play/Pause, Step Forward (Next), Step Backward (Prev), Replay, Speed Adjustment (`0.5x`, `1.0x`, `2.0x`), and keyboard shortcuts (Space, Arrow keys).
  - **Dual View Modes**: Toggle between **Flow View** (Sequence Diagram) and **Packets View** (Wireshark-style 20-byte TCP header dissection and parsed field tables).

---

## 📊 Transport Layer Behavior by Activity

| Activity | Application Layer Protocols | Transport Layer Protocol & Mechanics |
| :--- | :--- | :--- |
| **Web Browsing** | DNS A-Record (UDP 53) + HTTP/1.1 GET/200 | UDP Datagrams (DNS) ➔ TCP 3-Way Handshake (`SYN`, `SYN-ACK`, `ACK`) ➔ Data Segments (`PSH, ACK` with exact Seq/Ack and MSS chunking) ➔ 4-Way Teardown (`FIN-ACK`, `TIME_WAIT`) or Persistent Connection Retention (`Keep-Alive`). |
| **Sending Mail** | DNS MX-Record (UDP 53) + RFC 5321 SMTP | UDP Datagrams (MX) ➔ TCP 3-Way Handshake to port 25 ➔ Conversational multi-turn TCP byte-stream (`220`, `EHLO`, `250`, `MAIL FROM`, `RCPT TO`, `DATA`, `354`, message payload, `250 Queued`, `QUIT`, `221 Bye`) ➔ 4-Way Teardown. |
| **Video Streaming** | HLS Manifests (`.m3u8`) + Media Chunks (`.ts`) | **TCP Mode**: Handshake with CDN edge, manifest transfers, progressive segment downloads with Flow Control (`Win`) and Congestion Control (`cwnd` doubling in Slow Start).<br>**UDP Mode**: RTP live streaming comparison (0-RTT, fire-and-forget datagrams, SSRC, sequence numbers, loss-tolerant).<br>**QUIC Mode**: HTTP/3 over UDP port 443 with 1-RTT TLS 1.3 handshake and multiplexed streams (no Head-of-Line blocking). |

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
The repository includes a comprehensive 9-test suite covering TCP state machines, byte-level sequence/ack numbering, DNS UDP datagrams, SMTP over TCP, streaming modes (TCP/UDP/QUIC), and dual-layer REST APIs:

```bash
python3 -m unittest tests/test_protocol_visualizer.py -v
```

---

## 📁 Project Directory Structure
```
protocol-visualizer/
├── app.py                      # Flask server & Dual-Layer REST APIs
├── requirements.txt            # Python dependencies (Flask, Requests)
├── run.sh                      # One-click startup script
├── protocol_engine/            # Protocol simulation and network engine
│   ├── __init__.py             # Engine package exports
│   ├── dns_engine.py           # RFC 1035 DNS query/response generator
│   ├── http_engine.py          # HTTP/1.1 request/response parser & live fetcher
│   ├── smtp_engine.py          # RFC 5321 SMTP conversation engine
│   ├── streaming_engine.py     # HLS/DASH manifest & chunked segment engine
│   ├── tcp_engine.py           # RFC 793 TCP state machine, Seq/Ack, Congestion control
│   ├── udp_engine.py           # RFC 768 UDP datagrams & RFC 3550 RTP video engine
│   └── quic_engine.py          # RFC 9000 QUIC & HTTP/3 multiplexing engine
├── static/
│   ├── css/
│   │   └── style.css           # Modern dark glassmorphic UI, sequence diagram, dual view
│   └── js/
│       ├── app.js              # Activity tab management, forms, dual-layer dispatch
│       ├── visualizer.js       # Synchronized dual-layer timeline, TCP state machine
│       └── streaming.js        # HTML5 video sync, telemetry, TCP/UDP/QUIC segment pipeline
├── templates/
│   └── index.html              # Responsive dual-panel layout with Layer switcher & TCP bars
├── tests/
│   └── test_protocol_visualizer.py # 9-test unit and integration test suite
├── AI_USAGE_LOG.md             # AI platform, model, prompt iterations, evidence
└── REFLECTION.md               # Comprehensive 1-2 page academic reflection report
```

---

## 📝 Deliverables Checklist
- [x] **Working extended dashboard**: Complete dual-panel implementation supporting Browsing, Mail, and Streaming with synchronized Application and Transport Layer views.
- [x] **AI usage log & artifacts (`AI_USAGE_LOG.md`)**: Complete log documenting Google Antigravity and Gemini 3.8 Flash usage, prompts, and architecture decisions.
- [x] **Automated test suite**: 9 unit and integration tests passing (`python3 -m unittest tests/test_protocol_visualizer.py -v`).
- [x] **Reflection document (`REFLECTION.md`)**: Academic reflection covering AI platform selection, synchronization architecture, TCP sequence/ACK logic corrections, and transport flow comparisons.
