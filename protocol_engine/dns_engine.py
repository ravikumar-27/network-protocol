"""
DNS Protocol Engine
Simulates and executes RFC 1035 DNS queries and responses with full packet field breakdown.
"""
import socket
import random
import time

def resolve_dns(domain: str, record_type: str = "A") -> dict:
    """
    Performs DNS resolution (real with intelligent fallback) and returns
    detailed protocol steps for visualization.
    """
    domain = domain.strip().lower()
    # Strip protocol prefix or paths if passed
    if "://" in domain:
        domain = domain.split("://")[1].split("/")[0].split(":")[0]
    else:
        domain = domain.split("/")[0].split(":")[0]
    
    if not domain:
        domain = "example.com"
        
    tx_id = f"0x{random.randint(0x1000, 0xFFFF):04X}"
    resolved_ips = []
    mx_records = []
    lookup_time_ms = random.randint(12, 45)
    
    # Attempt real socket resolution
    try:
        if record_type == "MX":
            # Standard MX fallback simulation or host lookup
            mx_records = [
                {"preference": 10, "exchange": f"mail.{domain}"},
                {"preference": 20, "exchange": f"alt-mail.{domain}"}
            ]
            # Try resolving the host itself
            try:
                ip = socket.gethostbyname(domain)
                resolved_ips.append(ip)
            except Exception:
                resolved_ips.append("198.51.100.25")
        else:
            # Type A lookup
            addr_info = socket.getaddrinfo(domain, 80, socket.AF_INET, socket.SOCK_STREAM)
            resolved_ips = list(set([item[4][0] for item in addr_info]))
    except Exception:
        # Fallback realistic simulated IPs if offline or intranet
        if domain == "example.com":
            resolved_ips = ["93.184.215.14"]
        elif "google" in domain:
            resolved_ips = ["142.250.190.46", "142.250.190.78"]
        elif "wikipedia" in domain:
            resolved_ips = ["208.80.154.224"]
        else:
            resolved_ips = [f"192.0.2.{random.randint(10, 240)}"]
            
        if record_type == "MX":
            mx_records = [
                {"preference": 10, "exchange": f"mx1.{domain}"},
                {"preference": 20, "exchange": f"mx2.{domain}"}
            ]

    # Build DNS Steps
    steps = []
    
    # 1. Client Query (Client -> Local DNS Resolver)
    query_flags = {
        "hex": "0x0100",
        "qr": 0,          # 0 = Query
        "opcode": "Standard Query (0)",
        "aa": False,      # Authoritative Answer
        "tc": False,      # Truncated
        "rd": True,       # Recursion Desired (1)
        "ra": False,      # Recursion Available
        "rcode": "No error (0)"
    }
    
    query_payload = {
        "header": {
            "transaction_id": tx_id,
            "flags": query_flags,
            "questions": 1,
            "answer_rrs": 0,
            "authority_rrs": 0,
            "additional_rrs": 0
        },
        "queries": [
            {
                "name": domain,
                "type": record_type,
                "type_code": 1 if record_type == "A" else 15,
                "class": "IN (Internet)",
                "class_code": "0x0001"
            }
        ]
    }
    
    steps.append({
        "step_number": 1,
        "protocol": "DNS",
        "direction": "client_to_server",
        "source": "Client (Port 54210)",
        "destination": "Local DNS Resolver (8.8.8.8:53)",
        "transport": "UDP",
        "title": f"DNS Standard Query ({record_type})",
        "summary": f"Resolving domain name '{domain}' via UDP port 53",
        "raw_text": f"Standard query {tx_id} {record_type} {domain}",
        "fields": {
            "Transaction ID": tx_id,
            "Query Name": domain,
            "Record Type": record_type,
            "Recursion Desired": "1 (Yes)",
            "Transport": "UDP Port 53"
        },
        "details": query_payload,
        "timestamp_offset_ms": 0
    })
    
    # 2. DNS Server Response (Local DNS Resolver -> Client)
    response_flags = {
        "hex": "0x8180",
        "qr": 1,          # 1 = Response
        "opcode": "Standard Query (0)",
        "aa": False,
        "tc": False,
        "rd": True,
        "ra": True,       # Recursion Available (1)
        "rcode": "No error (0)"
    }
    
    answers = []
    ttl = random.randint(180, 3600)
    
    if record_type == "MX":
        for mx in mx_records:
            answers.append({
                "name": domain,
                "type": "MX",
                "class": "IN",
                "ttl": ttl,
                "preference": mx["preference"],
                "exchange": mx["exchange"]
            })
    else:
        for ip in resolved_ips:
            answers.append({
                "name": domain,
                "type": "A",
                "class": "IN",
                "ttl": ttl,
                "data_length": 4,
                "address": ip
            })
            
    response_payload = {
        "header": {
            "transaction_id": tx_id,
            "flags": response_flags,
            "questions": 1,
            "answer_rrs": len(answers),
            "authority_rrs": 0,
            "additional_rrs": 0
        },
        "queries": query_payload["queries"],
        "answers": answers
    }
    
    answer_preview = ", ".join(resolved_ips) if record_type == "A" else ", ".join([f"{m['exchange']} (pref={m['preference']})" for m in mx_records])
    
    steps.append({
        "step_number": 2,
        "protocol": "DNS",
        "direction": "server_to_client",
        "source": "Local DNS Resolver (8.8.8.8:53)",
        "destination": "Client (Port 54210)",
        "transport": "UDP",
        "title": f"DNS Standard Query Response ({record_type})",
        "summary": f"Resolved '{domain}' -> {answer_preview} (TTL: {ttl}s)",
        "raw_text": f"Standard query response {tx_id} {record_type} {domain} -> {answer_preview}",
        "fields": {
            "Transaction ID": tx_id,
            "Response Code": "0 (No error)",
            "Answers Count": len(answers),
            "Resolved Value": answer_preview,
            "TTL": f"{ttl} seconds",
            "Recursion Available": "1 (Yes)"
        },
        "details": response_payload,
        "timestamp_offset_ms": lookup_time_ms
    })
    
    return {
        "domain": domain,
        "record_type": record_type,
        "resolved_ips": resolved_ips,
        "primary_ip": resolved_ips[0] if resolved_ips else "93.184.215.14",
        "mx_records": mx_records,
        "steps": steps,
        "lookup_time_ms": lookup_time_ms
    }
