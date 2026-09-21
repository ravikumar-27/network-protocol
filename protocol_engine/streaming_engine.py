"""
Streaming Protocol Engine
Simulates HLS/DASH HTTP Live Streaming protocols, including CDN DNS resolution,
master manifest/playlist parsing, multi-bitrate variant stream selection,
and byte-range / chunked transport stream (.ts) segment requests.
"""
import random
import time

STREAM_PRESETS = {
    "bbb": {
        "id": "bbb",
        "title": "Big Buck Bunny (Blender Animation)",
        "cdn_host": "cdn.videostream.net",
        "cdn_ip": "104.21.64.18",
        "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        "duration": "9:56",
        "qualities": {
            "1080p": {"bitrate": "5200 kbps", "resolution": "1920x1080", "chunk_size": "1.3 MB"},
            "720p":  {"bitrate": "2800 kbps", "resolution": "1280x720",  "chunk_size": "700 KB"},
            "480p":  {"bitrate": "1200 kbps", "resolution": "854x480",   "chunk_size": "300 KB"},
            "360p":  {"bitrate": "600 kbps",  "resolution": "640x360",   "chunk_size": "150 KB"}
        }
    },
    "tos": {
        "id": "tos",
        "title": "Tears of Steel (Sci-Fi Short Film)",
        "cdn_host": "edge.media-delivery.org",
        "cdn_ip": "151.101.65.140",
        "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4",
        "duration": "12:14",
        "qualities": {
            "1080p": {"bitrate": "5500 kbps", "resolution": "1920x1080", "chunk_size": "1.4 MB"},
            "720p":  {"bitrate": "3000 kbps", "resolution": "1280x720",  "chunk_size": "750 KB"},
            "480p":  {"bitrate": "1400 kbps", "resolution": "854x480",   "chunk_size": "350 KB"},
            "360p":  {"bitrate": "700 kbps",  "resolution": "640x360",   "chunk_size": "175 KB"}
        }
    },
    "sintel": {
        "id": "sintel",
        "title": "Sintel (Fantasy CGI Animation)",
        "cdn_host": "fastly.stream-origin.io",
        "cdn_ip": "199.232.69.194",
        "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4",
        "duration": "14:48",
        "qualities": {
            "1080p": {"bitrate": "5000 kbps", "resolution": "1920x1080", "chunk_size": "1.25 MB"},
            "720p":  {"bitrate": "2500 kbps", "resolution": "1280x720",  "chunk_size": "625 KB"},
            "480p":  {"bitrate": "1100 kbps", "resolution": "854x480",   "chunk_size": "275 KB"},
            "360p":  {"bitrate": "550 kbps",  "resolution": "640x360",   "chunk_size": "140 KB"}
        }
    }
}

def generate_streaming_init_steps(video_id: str = "bbb", initial_quality: str = "720p") -> dict:
    """
    Generates the complete startup protocol exchange:
    1. DNS Query for Video CDN Edge
    2. DNS Response with CDN Edge IP
    3. HTTP GET for Master Manifest (master.m3u8)
    4. HTTP 200 Response with Multi-Variant Bitrate Playlist
    5. HTTP GET for Media Quality Playlist (index.m3u8)
    6. HTTP 200 Response with Segment Chunks
    7. HTTP GET for First Video Segment (segment_000.ts)
    8. HTTP 200 / 206 Partial Content Response with Video Data
    """
    video_meta = STREAM_PRESETS.get(video_id, STREAM_PRESETS["bbb"])
    cdn_host = video_meta["cdn_host"]
    cdn_ip = video_meta["cdn_ip"]
    selected_qual = initial_quality if initial_quality in video_meta["qualities"] else "720p"
    qual_info = video_meta["qualities"][selected_qual]

    steps = []
    current_time = 0
    tx_id = f"0x{random.randint(0x3000, 0xAFFF):04X}"

    # Step 1: DNS Query for CDN host
    steps.append({
        "step_number": 1,
        "protocol": "DNS",
        "direction": "client_to_server",
        "source": "Video Player / Browser (Port 51240)",
        "destination": "Local DNS Resolver (8.8.8.8:53)",
        "transport": "UDP",
        "title": "DNS Standard Query (A)",
        "summary": f"Resolving CDN Edge domain '{cdn_host}'",
        "raw_text": f"Standard query {tx_id} A {cdn_host}",
        "fields": {
            "Transaction ID": tx_id,
            "Query Name": cdn_host,
            "Record Type": "A (Host Address)",
            "Class": "IN"
        },
        "details": {"domain": cdn_host, "type": "A"},
        "timestamp_offset_ms": current_time
    })
    current_time += 14

    # Step 2: DNS Response
    steps.append({
        "step_number": 2,
        "protocol": "DNS",
        "direction": "server_to_client",
        "source": "Local DNS Resolver (8.8.8.8:53)",
        "destination": "Video Player / Browser (Port 51240)",
        "transport": "UDP",
        "title": "DNS Standard Query Response",
        "summary": f"Resolved '{cdn_host}' -> Edge IP {cdn_ip} (TTL 120s)",
        "raw_text": f"Standard query response {tx_id} A {cdn_host} -> {cdn_ip}",
        "fields": {
            "Transaction ID": tx_id,
            "Resolved IP": cdn_ip,
            "Edge Node": "Geo-located Anycast CDN Node",
            "TTL": "120s"
        },
        "details": {"domain": cdn_host, "ip": cdn_ip, "ttl": 120},
        "timestamp_offset_ms": current_time
    })
    current_time += 18

    # Step 3: HTTP GET Master Playlist (master.m3u8)
    master_uri = f"/streams/{video_id}/master.m3u8"
    master_req_raw = (
        f"GET {master_uri} HTTP/1.1\r\n"
        f"Host: {cdn_host}\r\n"
        f"User-Agent: VideoPlayer/2.4 (HTML5 MediaSource)\r\n"
        f"Accept: application/vnd.apple.mpegurl, application/x-mpegURL, */*\r\n"
        f"Connection: keep-alive\r\n\r\n"
    )
    steps.append({
        "step_number": 3,
        "protocol": "HTTP",
        "direction": "client_to_server",
        "source": "Video Player Client (Port 51242)",
        "destination": f"CDN Edge Server ({cdn_ip}:443)",
        "transport": "TCP",
        "title": "HTTP GET Master Manifest (.m3u8)",
        "summary": f"Requesting HLS Master Playlist '{master_uri}'",
        "raw_text": master_req_raw,
        "fields": {
            "Method": "GET",
            "Path": master_uri,
            "Host": cdn_host,
            "Content-Type": "application/vnd.apple.mpegurl",
            "Connection": "keep-alive"
        },
        "details": {"method": "GET", "uri": master_uri, "headers": {"Host": cdn_host}},
        "timestamp_offset_ms": current_time
    })
    current_time += 22

    # Step 4: HTTP 200 Master Manifest Response
    master_body = (
        "#EXTM3U\r\n"
        "#EXT-X-VERSION:4\r\n"
        "#EXT-X-INDEPENDENT-SEGMENTS\r\n"
        "#EXT-X-STREAM-INF:BANDWIDTH=5200000,RESOLUTION=1920x1080,FRAME-RATE=60.000,CODECS=\"avc1.64002a,mp4a.40.2\"\r\n"
        "1080p/playlist.m3u8\r\n"
        "#EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1280x720,FRAME-RATE=30.000,CODECS=\"avc1.4d401f,mp4a.40.2\"\r\n"
        "720p/playlist.m3u8\r\n"
        "#EXT-X-STREAM-INF:BANDWIDTH=1200000,RESOLUTION=854x480,FRAME-RATE=30.000,CODECS=\"avc1.4d401e,mp4a.40.2\"\r\n"
        "480p/playlist.m3u8\r\n"
        "#EXT-X-STREAM-INF:BANDWIDTH=600000,RESOLUTION=640x360,FRAME-RATE=30.000,CODECS=\"avc1.42c01e,mp4a.40.2\"\r\n"
        "360p/playlist.m3u8"
    )
    master_resp_raw = (
        f"HTTP/1.1 200 OK\r\n"
        f"Date: {time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())}\r\n"
        f"Server: CloudCDN/5.4\r\n"
        f"Content-Type: application/vnd.apple.mpegurl\r\n"
        f"Content-Length: {len(master_body)}\r\n"
        f"Access-Control-Allow-Origin: *\r\n"
        f"Cache-Control: max-age=300\r\n\r\n"
        f"{master_body}"
    )
    steps.append({
        "step_number": 4,
        "protocol": "HTTP",
        "direction": "server_to_client",
        "source": f"CDN Edge Server ({cdn_ip}:443)",
        "destination": "Video Player Client (Port 51242)",
        "transport": "TCP",
        "title": "HTTP 200 OK (Master Playlist Content)",
        "summary": "Received Master Manifest defining adaptive bitrate tiers (1080p, 720p, 480p, 360p)",
        "raw_text": master_resp_raw,
        "fields": {
            "Status Line": "HTTP/1.1 200 OK",
            "Content-Type": "application/vnd.apple.mpegurl",
            "Available Variants": "1080p, 720p, 480p, 360p",
            "Cache-Control": "max-age=300"
        },
        "details": {"status": 200, "manifest_type": "Master Playlist", "body": master_body},
        "timestamp_offset_ms": current_time
    })
    current_time += 25

    # Step 5: HTTP GET Media Playlist for selected quality
    media_uri = f"/streams/{video_id}/{selected_qual}/playlist.m3u8"
    media_req_raw = (
        f"GET {media_uri} HTTP/1.1\r\n"
        f"Host: {cdn_host}\r\n"
        f"User-Agent: VideoPlayer/2.4 (HTML5 MediaSource)\r\n"
        f"Accept: application/vnd.apple.mpegurl\r\n"
        f"Connection: keep-alive\r\n\r\n"
    )
    steps.append({
        "step_number": 5,
        "protocol": "HTTP",
        "direction": "client_to_server",
        "source": "Video Player Client (Port 51242)",
        "destination": f"CDN Edge Server ({cdn_ip}:443)",
        "transport": "TCP",
        "title": f"HTTP GET {selected_qual} Media Playlist",
        "summary": f"Selected {selected_qual} ({qual_info['bitrate']}) based on player bandwidth estimation",
        "raw_text": media_req_raw,
        "fields": {
            "Method": "GET",
            "Path": media_uri,
            "Quality Tier": selected_qual,
            "Target Bitrate": qual_info["bitrate"],
            "Resolution": qual_info["resolution"]
        },
        "details": {"method": "GET", "uri": media_uri, "quality": selected_qual},
        "timestamp_offset_ms": current_time
    })
    current_time += 20

    # Step 6: HTTP 200 Media Playlist Response with Segment List
    media_body = (
        "#EXTM3U\r\n"
        "#EXT-X-VERSION:4\r\n"
        "#EXT-X-TARGETDURATION:2\r\n"
        "#EXT-X-MEDIA-SEQUENCE:0\r\n"
        "#EXTINF:2.000000,\r\n"
        "segment_000.ts\r\n"
        "#EXTINF:2.000000,\r\n"
        "segment_001.ts\r\n"
        "#EXTINF:2.000000,\r\n"
        "segment_002.ts\r\n"
        "#EXTINF:2.000000,\r\n"
        "segment_003.ts"
    )
    media_resp_raw = (
        f"HTTP/1.1 200 OK\r\n"
        f"Date: {time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())}\r\n"
        f"Server: CloudCDN/5.4\r\n"
        f"Content-Type: application/vnd.apple.mpegurl\r\n"
        f"Content-Length: {len(media_body)}\r\n\r\n"
        f"{media_body}"
    )
    steps.append({
        "step_number": 6,
        "protocol": "HTTP",
        "direction": "server_to_client",
        "source": f"CDN Edge Server ({cdn_ip}:443)",
        "destination": "Video Player Client (Port 51242)",
        "transport": "TCP",
        "title": f"HTTP 200 OK ({selected_qual} Media Playlist)",
        "summary": "Received segment schedule (Target Segment Duration: 2.0 seconds)",
        "raw_text": media_resp_raw,
        "fields": {
            "Status Line": "HTTP/1.1 200 OK",
            "Target Duration": "2.0s per segment",
            "Segment Media": "MPEG-2 Transport Stream (.ts)",
            "Media Sequence": "0"
        },
        "details": {"status": 200, "manifest_type": "Media Playlist", "body": media_body},
        "timestamp_offset_ms": current_time
    })
    current_time += 22

    # Step 7: HTTP GET for First Segment (segment_000.ts)
    seg0_uri = f"/streams/{video_id}/{selected_qual}/segment_000.ts"
    seg0_req_raw = (
        f"GET {seg0_uri} HTTP/1.1\r\n"
        f"Host: {cdn_host}\r\n"
        f"User-Agent: VideoPlayer/2.4 (HTML5 MediaSource)\r\n"
        f"Accept: video/mp2t, */*\r\n"
        f"Range: bytes=0-1048575\r\n"
        f"Connection: keep-alive\r\n\r\n"
    )
    steps.append({
        "step_number": 7,
        "protocol": "HTTP",
        "direction": "client_to_server",
        "source": "Video Player Client (Port 51242)",
        "destination": f"CDN Edge Server ({cdn_ip}:443)",
        "transport": "TCP",
        "title": "HTTP GET Video Segment 0 (Initialization)",
        "summary": f"Requesting initial 2s video chunk (Range: bytes=0-1048575)",
        "raw_text": seg0_req_raw,
        "fields": {
            "Method": "GET",
            "URI": seg0_uri,
            "Range": "bytes=0-1048575 (1 MB)",
            "Accept": "video/mp2t",
            "Buffer State": "Empty -> Filling initial buffer"
        },
        "details": {"method": "GET", "uri": seg0_uri, "range": "bytes=0-1048575"},
        "timestamp_offset_ms": current_time
    })
    current_time += 45

    # Step 8: HTTP 206 Partial Content (Segment Data)
    seg0_resp_raw = (
        f"HTTP/1.1 206 Partial Content\r\n"
        f"Date: {time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())}\r\n"
        f"Server: CloudCDN/5.4\r\n"
        f"Content-Type: video/mp2t\r\n"
        f"Content-Range: bytes 0-1048575/8388608\r\n"
        f"Content-Length: 1048576\r\n"
        f"ETag: \"seg-000-720p-8f2a\"\r\n"
        f"Cache-Control: public, max-age=86400\r\n\r\n"
        f"[Binary MPEG-2 Transport Stream Data: 1,048,576 bytes]"
    )
    steps.append({
        "step_number": 8,
        "protocol": "HTTP",
        "direction": "server_to_client",
        "source": f"CDN Edge Server ({cdn_ip}:443)",
        "destination": "Video Player Client (Port 51242)",
        "transport": "TCP",
        "title": "HTTP 206 Partial Content (Segment 0 Delivered)",
        "summary": "Received 1,048,576 bytes of video stream; buffer hydrated, playback begins!",
        "raw_text": seg0_resp_raw,
        "fields": {
            "Status Line": "HTTP/1.1 206 Partial Content",
            "Content-Range": "bytes 0-1048575/8388608",
            "Content-Length": "1048576 bytes",
            "Content-Type": "video/mp2t",
            "Playback Action": "Decoded via SourceBuffer & Rendered to <video>"
        },
        "details": {"status": 206, "bytes": 1048576, "type": "video/mp2t"},
        "timestamp_offset_ms": current_time
    })

    return {
        "video": video_meta,
        "quality": selected_qual,
        "steps": steps,
        "total_steps": len(steps)
    }

def generate_segment_step(video_id: str, quality: str, segment_num: int, start_step_num: int = 9) -> dict:
    """
    Generates a pair of live segment request/response steps as video plays or buffers.
    """
    video_meta = STREAM_PRESETS.get(video_id, STREAM_PRESETS["bbb"])
    cdn_host = video_meta["cdn_host"]
    cdn_ip = video_meta["cdn_ip"]
    qual_info = video_meta["qualities"].get(quality, video_meta["qualities"]["720p"])

    seg_name = f"segment_{segment_num:03d}.ts"
    seg_uri = f"/streams/{video_id}/{quality}/{seg_name}"
    byte_start = segment_num * 1048576
    byte_end = byte_start + 1048575

    req_step = {
        "step_number": start_step_num,
        "protocol": "HTTP",
        "direction": "client_to_server",
        "source": "Video Player Client (Port 51242)",
        "destination": f"CDN Edge Server ({cdn_ip}:443)",
        "transport": "TCP",
        "title": f"HTTP GET Segment #{segment_num} ({quality})",
        "summary": f"Requesting next 2s playback segment ({seg_name})",
        "raw_text": f"GET {seg_uri} HTTP/1.1\r\nHost: {cdn_host}\r\nRange: bytes={byte_start}-{byte_end}\r\nAccept: video/mp2t\r\n\r\n",
        "fields": {
            "Method": "GET",
            "Segment": seg_name,
            "Quality Tier": f"{quality} ({qual_info['bitrate']})",
            "Byte Range": f"bytes={byte_start}-{byte_end}",
            "Playback Offset": f"{segment_num * 2.0}s - {(segment_num + 1) * 2.0}s"
        },
        "details": {"segment": seg_name, "quality": quality, "range": f"{byte_start}-{byte_end}"},
        "timestamp_offset_ms": 0
    }

    resp_step = {
        "step_number": start_step_num + 1,
        "protocol": "HTTP",
        "direction": "server_to_client",
        "source": f"CDN Edge Server ({cdn_ip}:443)",
        "destination": "Video Player Client (Port 51242)",
        "transport": "TCP",
        "title": f"HTTP 206 Partial Content (Segment #{segment_num})",
        "summary": f"Received {qual_info['chunk_size']} chunk. Buffer forward capacity: {random.randint(6, 14)}s",
        "raw_text": f"HTTP/1.1 206 Partial Content\r\nContent-Type: video/mp2t\r\nContent-Range: bytes {byte_start}-{byte_end}/8388608\r\nContent-Length: 1048576\r\n\r\n[Binary Video Segment Data]",
        "fields": {
            "Status Line": "HTTP/1.1 206 Partial Content",
            "Segment Downloaded": seg_name,
            "Chunk Size": qual_info["chunk_size"],
            "Bitrate": qual_info["bitrate"],
            "Buffer Health": "Healthy (>8s ahead of playhead)"
        },
        "details": {"status": 206, "segment": seg_name, "chunk_size": qual_info["chunk_size"]},
        "timestamp_offset_ms": random.randint(30, 75)
    }

    return {
        "request_step": req_step,
        "response_step": resp_step
    }
