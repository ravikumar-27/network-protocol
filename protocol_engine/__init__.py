"""
Protocol Engine package for Dual-Panel Activity & Protocol Visualizer.
"""
from .dns_engine import resolve_dns
from .http_engine import execute_http_request
from .smtp_engine import simulate_smtp_transaction
from .streaming_engine import generate_streaming_init_steps, generate_segment_step, STREAM_PRESETS

__all__ = [
    "resolve_dns",
    "execute_http_request",
    "simulate_smtp_transaction",
    "generate_streaming_init_steps",
    "generate_segment_step",
    "STREAM_PRESETS",
]
