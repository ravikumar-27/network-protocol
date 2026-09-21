"""
SMTP Protocol Engine
Implements RFC 5321 / RFC 5322 Mail Exchange protocol conversation with complete
command-response sequence: 220 Greeting, EHLO, MAIL FROM, RCPT TO, DATA, QUIT.
"""
import time
import random
import uuid

def simulate_smtp_transaction(from_email: str, to_email: str, subject: str, body: str) -> dict:
    """
    Constructs an authentic RFC 5321 SMTP email delivery session.
    """
    from_email = from_email.strip() or "student@university.edu"
    to_email = to_email.strip() or "professor@university.edu"
    subject = subject.strip() or "Application Layer Assignment Submission"
    body = body.strip() or "Hello, this is a test email demonstrating the SMTP protocol exchange."

    recipient_domain = to_email.split("@")[-1] if "@" in to_email else "university.edu"
    sender_domain = from_email.split("@")[-1] if "@" in from_email else "client.local"
    smtp_server_host = f"mail.{recipient_domain}"
    client_host = "client-workstation.lan"
    server_ip = "198.51.100.25"
    queue_id = f"{random.randint(1000, 9999)}{uuid.uuid4().hex[:6].upper()}"
    rfc_date = time.strftime("%a, %d %b %Y %H:%M:%S +0530", time.localtime())
    message_id = f"<{uuid.uuid4().hex[:12]}@{sender_domain}>"

    steps = []
    current_time = 0

    # Optional DNS MX resolution step before SMTP
    dns_tx = f"0x{random.randint(0x2000, 0x8FFF):04X}"
    steps.append({
        "step_number": 1,
        "protocol": "DNS",
        "direction": "client_to_server",
        "source": "Client Mail Agent (MUA)",
        "destination": "DNS Resolver (8.8.8.8:53)",
        "transport": "UDP",
        "title": "DNS Query (MX)",
        "summary": f"Resolving Mail Exchange (MX) for '{recipient_domain}'",
        "raw_text": f"Standard query {dns_tx} MX {recipient_domain}",
        "fields": {
            "Transaction ID": dns_tx,
            "Query Name": recipient_domain,
            "Record Type": "MX (Mail Exchange)",
            "Class": "IN"
        },
        "details": {"domain": recipient_domain, "type": "MX"},
        "timestamp_offset_ms": current_time
    })
    current_time += 15

    steps.append({
        "step_number": 2,
        "protocol": "DNS",
        "direction": "server_to_client",
        "source": "DNS Resolver (8.8.8.8:53)",
        "destination": "Client Mail Agent (MUA)",
        "transport": "UDP",
        "title": "DNS Response (MX)",
        "summary": f"MX record resolved: {smtp_server_host} (Priority 10) -> {server_ip}",
        "raw_text": f"Standard query response {dns_tx} MX {recipient_domain} -> {smtp_server_host} (pref 10, IP {server_ip})",
        "fields": {
            "Mail Exchange": smtp_server_host,
            "Preference/Priority": "10",
            "Resolved IP": server_ip,
            "TTL": "300s"
        },
        "details": {"server": smtp_server_host, "ip": server_ip, "preference": 10},
        "timestamp_offset_ms": current_time
    })
    current_time += 20

    # Step 3: Server Greeting 220
    steps.append({
        "step_number": 3,
        "protocol": "SMTP",
        "direction": "server_to_client",
        "source": f"Mail Transfer Agent ({smtp_server_host}:25)",
        "destination": "Client Mail Agent (Port 49152)",
        "transport": "TCP",
        "title": "SMTP 220 Service Ready",
        "summary": f"Server banner announcement: {smtp_server_host} ESMTP Postfix ready",
        "raw_text": f"220 {smtp_server_host} ESMTP Postfix (Ubuntu) ready at {rfc_date}",
        "fields": {
            "Reply Code": "220",
            "Status Description": "Service ready",
            "MTA Software": "ESMTP Postfix",
            "Server Hostname": smtp_server_host
        },
        "details": {"code": 220, "message": f"{smtp_server_host} ESMTP Postfix"},
        "timestamp_offset_ms": current_time
    })
    current_time += 25

    # Step 4: Client EHLO
    steps.append({
        "step_number": 4,
        "protocol": "SMTP",
        "direction": "client_to_server",
        "source": "Client Mail Agent (Port 49152)",
        "destination": f"Mail Transfer Agent ({smtp_server_host}:25)",
        "transport": "TCP",
        "title": "SMTP EHLO Command",
        "summary": f"Client greets server with Extended HELO identity ({client_host})",
        "raw_text": f"EHLO {client_host}",
        "fields": {
            "Command": "EHLO",
            "Client Identity": client_host,
            "Protocol": "Extended SMTP (RFC 5321)"
        },
        "details": {"command": "EHLO", "client_host": client_host},
        "timestamp_offset_ms": current_time
    })
    current_time += 20

    # Step 5: Server 250 Multi-line Response with capabilities
    capabilities_text = f"250-{smtp_server_host}\r\n250-PIPELINING\r\n250-SIZE 10485760\r\n250-ETRN\r\n250-ENHANCEDSTATUSCODES\r\n250-8BITMIME\r\n250 DSN"
    steps.append({
        "step_number": 5,
        "protocol": "SMTP",
        "direction": "server_to_client",
        "source": f"Mail Transfer Agent ({smtp_server_host}:25)",
        "destination": "Client Mail Agent (Port 49152)",
        "transport": "TCP",
        "title": "SMTP 250 EHLO Capabilities Response",
        "summary": "Server acknowledges EHLO and advertises supported extensions (PIPELINING, SIZE, 8BITMIME)",
        "raw_text": capabilities_text,
        "fields": {
            "Reply Code": "250",
            "Capabilities": "PIPELINING, SIZE 10MB, ENHANCEDSTATUSCODES, 8BITMIME, DSN",
            "Status": "Requested mail action okay, completed"
        },
        "details": {
            "code": 250,
            "capabilities": ["PIPELINING", "SIZE 10485760", "ETRN", "ENHANCEDSTATUSCODES", "8BITMIME", "DSN"]
        },
        "timestamp_offset_ms": current_time
    })
    current_time += 25

    # Step 6: Client MAIL FROM
    steps.append({
        "step_number": 6,
        "protocol": "SMTP",
        "direction": "client_to_server",
        "source": "Client Mail Agent (Port 49152)",
        "destination": f"Mail Transfer Agent ({smtp_server_host}:25)",
        "transport": "TCP",
        "title": "SMTP MAIL FROM Command",
        "summary": f"Specifying envelope sender address: <{from_email}>",
        "raw_text": f"MAIL FROM:<{from_email}>",
        "fields": {
            "Command": "MAIL FROM",
            "Sender Address": f"<{from_email}>",
            "Envelope Return-Path": from_email
        },
        "details": {"command": "MAIL FROM", "sender": from_email},
        "timestamp_offset_ms": current_time
    })
    current_time += 15

    # Step 7: Server 250 OK for Sender
    steps.append({
        "step_number": 7,
        "protocol": "SMTP",
        "direction": "server_to_client",
        "source": f"Mail Transfer Agent ({smtp_server_host}:25)",
        "destination": "Client Mail Agent (Port 49152)",
        "transport": "TCP",
        "title": "SMTP 250 Sender Accepted",
        "summary": f"Server accepts sender <{from_email}>",
        "raw_text": "250 2.1.0 Ok",
        "fields": {
            "Reply Code": "250",
            "Enhanced Code": "2.1.0 (Sender address valid)",
            "Status": "Sender Ok"
        },
        "details": {"code": 250, "status": "Sender Ok"},
        "timestamp_offset_ms": current_time
    })
    current_time += 20

    # Step 8: Client RCPT TO
    steps.append({
        "step_number": 8,
        "protocol": "SMTP",
        "direction": "client_to_server",
        "source": "Client Mail Agent (Port 49152)",
        "destination": f"Mail Transfer Agent ({smtp_server_host}:25)",
        "transport": "TCP",
        "title": "SMTP RCPT TO Command",
        "summary": f"Specifying envelope recipient address: <{to_email}>",
        "raw_text": f"RCPT TO:<{to_email}>",
        "fields": {
            "Command": "RCPT TO",
            "Recipient Address": f"<{to_email}>",
            "Action": "Request mailbox delivery"
        },
        "details": {"command": "RCPT TO", "recipient": to_email},
        "timestamp_offset_ms": current_time
    })
    current_time += 15

    # Step 9: Server 250 OK for Recipient
    steps.append({
        "step_number": 9,
        "protocol": "SMTP",
        "direction": "server_to_client",
        "source": f"Mail Transfer Agent ({smtp_server_host}:25)",
        "destination": "Client Mail Agent (Port 49152)",
        "transport": "TCP",
        "title": "SMTP 250 Recipient Accepted",
        "summary": f"Server confirms recipient mailbox <{to_email}> exists and is deliverable",
        "raw_text": "250 2.1.5 Ok",
        "fields": {
            "Reply Code": "250",
            "Enhanced Code": "2.1.5 (Recipient address valid)",
            "Status": "Recipient Ok"
        },
        "details": {"code": 250, "status": "Recipient Ok"},
        "timestamp_offset_ms": current_time
    })
    current_time += 20

    # Step 10: Client DATA command
    steps.append({
        "step_number": 10,
        "protocol": "SMTP",
        "direction": "client_to_server",
        "source": "Client Mail Agent (Port 49152)",
        "destination": f"Mail Transfer Agent ({smtp_server_host}:25)",
        "transport": "TCP",
        "title": "SMTP DATA Command",
        "summary": "Initiating transmission of mail headers and message body",
        "raw_text": "DATA",
        "fields": {
            "Command": "DATA",
            "Description": "Start mail input request"
        },
        "details": {"command": "DATA"},
        "timestamp_offset_ms": current_time
    })
    current_time += 15

    # Step 11: Server 354 Intermediate response
    steps.append({
        "step_number": 11,
        "protocol": "SMTP",
        "direction": "server_to_client",
        "source": f"Mail Transfer Agent ({smtp_server_host}:25)",
        "destination": "Client Mail Agent (Port 49152)",
        "transport": "TCP",
        "title": "SMTP 354 Start Mail Input",
        "summary": "Server instructs client to transmit mail content, terminated by single period <CR><LF>.<CR><LF>",
        "raw_text": "354 End data with <CR><LF>.<CR><LF>",
        "fields": {
            "Reply Code": "354",
            "Status": "Start mail input",
            "Delimiter": "<CR><LF>.<CR><LF>"
        },
        "details": {"code": 354, "message": "End data with <CR><LF>.<CR><LF>"},
        "timestamp_offset_ms": current_time
    })
    current_time += 20

    # Step 12: Client sends RFC 5322 formatted message + terminating dot
    email_payload = (
        f"Date: {rfc_date}\r\n"
        f"From: {from_email}\r\n"
        f"To: {to_email}\r\n"
        f"Subject: {subject}\r\n"
        f"Message-ID: {message_id}\r\n"
        f"User-Agent: DualPanelProtocolVisualizer/1.0\r\n"
        f"MIME-Version: 1.0\r\n"
        f"Content-Type: text/plain; charset=utf-8\r\n"
        f"\r\n"
        f"{body}\r\n"
        f"."
    )
    steps.append({
        "step_number": 12,
        "protocol": "SMTP",
        "direction": "client_to_server",
        "source": "Client Mail Agent (Port 49152)",
        "destination": f"Mail Transfer Agent ({smtp_server_host}:25)",
        "transport": "TCP",
        "title": "SMTP Message Content Transmission",
        "summary": f"Sending RFC 5322 email headers, body ({len(body)} chars), and terminating period '.'",
        "raw_text": email_payload,
        "fields": {
            "Subject": subject,
            "Date": rfc_date,
            "Message-ID": message_id,
            "Payload Size": f"{len(email_payload)} bytes",
            "End-of-Data": "<CR><LF>.<CR><LF>"
        },
        "details": {
            "headers": {
                "Date": rfc_date,
                "From": from_email,
                "To": to_email,
                "Subject": subject,
                "Message-ID": message_id
            },
            "body": body,
            "raw": email_payload
        },
        "timestamp_offset_ms": current_time
    })
    current_time += 35

    # Step 13: Server 250 Message Accepted and Queued
    steps.append({
        "step_number": 13,
        "protocol": "SMTP",
        "direction": "server_to_client",
        "source": f"Mail Transfer Agent ({smtp_server_host}:25)",
        "destination": "Client Mail Agent (Port 49152)",
        "transport": "TCP",
        "title": "SMTP 250 Message Queued",
        "summary": f"Message received, validated, and assigned Queue ID: {queue_id}",
        "raw_text": f"250 2.0.0 Ok: queued as {queue_id}",
        "fields": {
            "Reply Code": "250",
            "Enhanced Code": "2.0.0 (Other or undefined status)",
            "Queue ID": queue_id,
            "Status": "Queued for delivery"
        },
        "details": {"code": 250, "queue_id": queue_id},
        "timestamp_offset_ms": current_time
    })
    current_time += 20

    # Step 14: Client QUIT
    steps.append({
        "step_number": 14,
        "protocol": "SMTP",
        "direction": "client_to_server",
        "source": "Client Mail Agent (Port 49152)",
        "destination": f"Mail Transfer Agent ({smtp_server_host}:25)",
        "transport": "TCP",
        "title": "SMTP QUIT Command",
        "summary": "Client issues graceful session termination command",
        "raw_text": "QUIT",
        "fields": {
            "Command": "QUIT",
            "Description": "Close mail transaction channel"
        },
        "details": {"command": "QUIT"},
        "timestamp_offset_ms": current_time
    })
    current_time += 15

    # Step 15: Server 221 Service Closing
    steps.append({
        "step_number": 15,
        "protocol": "SMTP",
        "direction": "server_to_client",
        "source": f"Mail Transfer Agent ({smtp_server_host}:25)",
        "destination": "Client Mail Agent (Port 49152)",
        "transport": "TCP",
        "title": "SMTP 221 Closing Transmission Channel",
        "summary": f"Server acknowledges QUIT and closes TCP connection to {client_host}",
        "raw_text": f"221 2.0.0 Bye {client_host}",
        "fields": {
            "Reply Code": "221",
            "Enhanced Code": "2.0.0",
            "Status": "Service closing transmission channel",
            "Action": "TCP FIN / Close"
        },
        "details": {"code": 221, "status": "Bye"},
        "timestamp_offset_ms": current_time
    })

    return {
        "from": from_email,
        "to": to_email,
        "subject": subject,
        "server_host": smtp_server_host,
        "server_ip": server_ip,
        "queue_id": queue_id,
        "total_steps": len(steps),
        "steps": steps
    }
