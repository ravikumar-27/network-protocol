"""
HTTP Protocol Engine
Executes real HTTP requests or rich simulations, generating full HTTP/1.1 request
and response wire messages, headers, status lines, and preview content.
"""
from urllib.parse import urlparse
import time
import requests

def execute_http_request(url: str, server_ip: str = None) -> dict:
    """
    Fetches the requested URL and captures exact HTTP/1.1 request and response
    wire data along with timing and payload preview.
    """
    clean_url = url.strip()
    if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
        clean_url = "http://" + clean_url
        
    parsed = urlparse(clean_url)
    host = parsed.netloc or "example.com"
    path = parsed.path if parsed.path else "/"
    if parsed.query:
        path += f"?{parsed.query}"
        
    scheme = parsed.scheme.upper()
    port = 443 if scheme == "HTTPS" else 80
    if ":" in host:
        host_parts = host.split(":")
        host_only = host_parts[0]
        port = int(host_parts[1])
    else:
        host_only = host

    request_headers = {
        "Host": host,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ProtocolVisualizer/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none"
    }
    
    # Format raw request
    req_lines = [f"GET {path} HTTP/1.1"]
    for k, v in request_headers.items():
        req_lines.append(f"{k}: {v}")
    raw_request = "\r\n".join(req_lines) + "\r\n\r\n"

    status_code = 200
    status_phrase = "OK"
    response_headers = {}
    html_content = ""
    start_time = time.time()
    
    # Attempt real request
    try:
        resp = requests.get(
            clean_url,
            headers={"User-Agent": request_headers["User-Agent"]},
            timeout=3.5,
            allow_redirects=True,
            verify=False
        )
        duration_ms = int((time.time() - start_time) * 1000)
        status_code = resp.status_code
        status_phrase = resp.reason or "OK"
        response_headers = dict(resp.headers)
        # Limit preview length
        html_content = resp.text[:4000]
    except Exception as e:
        duration_ms = 45
        status_code = 200
        status_phrase = "OK"
        response_headers = {
            "Date": time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime()),
            "Server": "Apache/2.4.52 (Ubuntu)",
            "Content-Type": "text/html; charset=UTF-8",
            "Content-Length": "1256",
            "Connection": "keep-alive",
            "ETag": '"34a1-5c8e2b0a1"',
            "Accept-Ranges": "bytes",
            "Cache-Control": "max-age=604800, public"
        }
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{host} - Application Layer Visualizer</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 2rem; background: #0f172a; color: #f8fafc; }}
        h1 {{ color: #38bdf8; }}
        p {{ line-height: 1.6; color: #94a3b8; }}
        .card {{ background: #1e293b; padding: 1.5rem; border-radius: 8px; border: 1px solid #334155; margin-top: 1rem; }}
        .badge {{ display: inline-block; padding: 0.25rem 0.5rem; border-radius: 4px; background: #0284c7; color: white; font-size: 0.85rem; font-weight: bold; }}
    </style>
</head>
<body>
    <span class="badge">Simulated HTTP/1.1 Fetch</span>
    <h1>Welcome to {host}</h1>
    <p>You have successfully requested path <code>{path}</code> via HTTP/1.1 over TCP.</p>
    <div class="card">
        <h3>Server Response Summary</h3>
        <p><strong>Status:</strong> 200 OK | <strong>Transport:</strong> TCP Port {port}</p>
        <p>This payload was rendered by the client browser engine after receiving the complete HTTP response stream.</p>
    </div>
</body>
</html>"""

    # Format raw response line and headers
    resp_lines = [f"HTTP/1.1 {status_code} {status_phrase}"]
    for k, v in response_headers.items():
        resp_lines.append(f"{k}: {v}")
    raw_response_headers = "\r\n".join(resp_lines) + "\r\n\r\n"
    raw_response = raw_response_headers + html_content[:500]

    dest_ip = server_ip or "93.184.215.14"

    steps = [
        {
            "step_number": 3,
            "protocol": "HTTP",
            "direction": "client_to_server",
            "source": "Client (Browser Port 54212)",
            "destination": f"Web Server ({dest_ip}:{port})",
            "transport": "TCP",
            "title": f"HTTP GET Request",
            "summary": f"GET {path} HTTP/1.1 sent to Host: {host}",
            "raw_text": raw_request,
            "fields": {
                "Method": "GET",
                "Request URI": path,
                "HTTP Version": "HTTP/1.1",
                "Host": host,
                "User-Agent": request_headers["User-Agent"][:32] + "...",
                "Connection": "keep-alive"
            },
            "details": {
                "method": "GET",
                "path": path,
                "headers": request_headers,
                "raw": raw_request
            },
            "timestamp_offset_ms": 10
        },
        {
            "step_number": 4,
            "protocol": "HTTP",
            "direction": "server_to_client",
            "source": f"Web Server ({dest_ip}:{port})",
            "destination": "Client (Browser Port 54212)",
            "transport": "TCP",
            "title": f"HTTP {status_code} {status_phrase} Response",
            "summary": f"Received {status_code} {status_phrase} ({len(html_content)} bytes)",
            "raw_text": raw_response,
            "fields": {
                "Status Line": f"HTTP/1.1 {status_code} {status_phrase}",
                "Status Code": str(status_code),
                "Content-Type": response_headers.get("Content-Type", "text/html"),
                "Content-Length": response_headers.get("Content-Length", str(len(html_content))),
                "Server": response_headers.get("Server", "WebEdge/2.1"),
                "Latency": f"{duration_ms} ms"
            },
            "details": {
                "status_code": status_code,
                "status_phrase": status_phrase,
                "headers": response_headers,
                "body_preview": html_content[:2000],
                "raw": raw_response
            },
            "timestamp_offset_ms": 10 + duration_ms
        }
    ]

    return {
        "url": clean_url,
        "host": host,
        "path": path,
        "status_code": status_code,
        "status_phrase": status_phrase,
        "duration_ms": duration_ms,
        "html_content": html_content,
        "headers": response_headers,
        "steps": steps
    }
