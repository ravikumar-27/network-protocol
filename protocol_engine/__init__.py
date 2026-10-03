"""
Protocol Engine package for Dual-Panel Activity & Protocol Visualizer.
Supports both Application Layer (DNS, HTTP/1.1, SMTP, HLS) and
Transport Layer (TCP RFC 793, UDP RFC 768, RTP RFC 3550, QUIC RFC 9000).
"""
from .dns_engine import resolve_dns
from .http_engine import execute_http_request
from .smtp_engine import simulate_smtp_transaction
from .streaming_engine import generate_streaming_init_steps, generate_segment_step, STREAM_PRESETS
from .tcp_engine import (
    TCPConnection,
    generate_browsing_transport_steps,
    generate_mail_transport_steps,
    generate_streaming_transport_steps,
    generate_streaming_segment_transport_steps
)
from .udp_engine import format_udp_header, format_rtp_header
from .quic_engine import format_quic_initial_header

__all__ = [
    "resolve_dns",
    "execute_http_request",
    "simulate_smtp_transaction",
    "generate_streaming_init_steps",
    "generate_segment_step",
    "STREAM_PRESETS",
    "TCPConnection",
    "generate_browsing_transport_steps",
    "generate_mail_transport_steps",
    "generate_streaming_transport_steps",
    "generate_streaming_segment_transport_steps",
    "format_udp_header",
    "format_rtp_header",
    "format_quic_initial_header",
]
