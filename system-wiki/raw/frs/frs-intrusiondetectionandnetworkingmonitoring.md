Module 7: Intrusion Detection and Network Monitoring
a. Network Traffic Mirroring
i.      Internal Docker Network Traffic shall be monitored by the IDS (Intrusion Detection System) via a virtualized bridge interface (Suricata AF_PACKET).
ii.     IDS shall monitor all inbound and outbound traffic routed through the Nginx Reverse Proxy on the VPS.
iii.    Mirrored traffic includes: (Suricata App-Layer Parsers)
·         HTTP/HTTPS requests
·         Database queries
·         File uploads/downloads
·         Authentication attempts
b. IDS Configuration
i.       System shall use Suricata as the network-based IDS engine, deployed as a containerized service (Suricata (Dockerized))
ii.      Suricata shall be configured with: (Suricata-Update Tool)
·         OWASP Top 10 vulnerability signatures
·         Custom BFP-specific rules (e.g., detect bulk incident deletion attempts)
·         Emerging Threats ruleset (updated weekly)
iii.    IDS shall generate Unstructured Logs for detected security events (EVE JSON Format)
iv.    Unstructured logs shall be sent to System Logs data store
c. Log Collection and Forwarding
i.       IDS shall provide raw security logs to the Qwen2.5-3B AI module upon System Administrator request (Filebeat / Volume Sharing)
ii.      Logs forwarded via “Feeds Unstructured Logs” data flow (Redis (Message Broker))
iii.    Log forwarding occurs in real-time (latency < 5 seconds) (FastAPI Background Worker)
