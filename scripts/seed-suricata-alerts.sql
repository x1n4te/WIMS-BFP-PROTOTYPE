-- Seed Suricata alerts for system_admin hub.
-- Populates telemetry and AI-aided security analysis views.

INSERT INTO wims.security_threat_logs (
    timestamp, 
    source_ip, 
    destination_ip, 
    suricata_sid, 
    severity_level, 
    raw_payload, 
    xai_narrative, 
    xai_confidence
)
VALUES
(
    NOW() - INTERVAL '15 minutes',
    '192.168.1.100',
    '10.0.0.5',
    2021001,
    'CRITICAL',
    '{"timestamp":"2026-03-25T07:42:00.123456+0800","flow_id":123456789,"event_type":"alert","src_ip":"192.168.1.100","src_port":443,"dest_ip":"10.0.0.5","dest_port":80,"proto":"TCP","alert":{"action":"blocked","gid":1,"signature_id":2021001,"rev":1,"signature":"ET EXPLOIT Possible CVE-2021-44228 Log4j RCE","category":"Attempted Information Leak","severity":1}}',
    'Detected a potential Log4shell (CVE-2021-44228) exploit attempt targeting the internal application server (10.0.0.5) from a suspicious source (192.168.1.100). The payload contains JNDI lookup patterns commonly used for remote code execution.',
    0.98
),
(
    NOW() - INTERVAL '2 hours',
    '45.76.12.34',
    '10.0.0.2',
    2402000,
    'HIGH',
    '{"timestamp":"2026-03-25T05:57:00.654321+0800","flow_id":987654321,"event_type":"alert","src_ip":"45.76.12.34","src_port":54321,"dest_ip":"10.0.0.2","dest_port":22,"proto":"TCP","alert":{"action":"allowed","gid":1,"signature_id":2402000,"rev":3,"signature":"ET SCAN Potential SSH Brute Force","category":"Attempted Information Leak","severity":2}}',
    'Likely SSH brute force attack. Multiple failed login attempts detected from a known malicious IP range in the last 2 minutes. Recommend blocking the source IP at the firewall level.',
    0.85
),
(
    NOW() - INTERVAL '5 hours',
    '10.0.0.15',
    '185.199.110.153',
    2018959,
    'MEDIUM',
    '{"timestamp":"2026-03-25T02:57:00.111222+0800","flow_id":456789123,"event_type":"alert","src_ip":"10.0.0.15","src_port":3389,"dest_ip":"185.199.110.153","dest_port":80,"proto":"TCP","alert":{"action":"allowed","gid":1,"signature_id":2018959,"rev":2,"signature":"ET POLICY Suspicious outbound DNS query","category":"Potentially Corporate Policy Violation","severity":3}}',
    'Unusual outbound traffic detected from a workstation (10.0.0.15) to a known DGA (Domain Generation Algorithm) domain. This pattern is often associated with malware beaconing or data exfiltration.',
    0.72
),
(
    NOW() - INTERVAL '1 day',
    '172.16.0.45',
    '10.0.0.5',
    2100498,
    'LOW',
    '{"timestamp":"2026-03-24T07:57:00.333444+0800","flow_id":321654987,"event_type":"alert","src_ip":"172.16.0.45","src_port":60000,"dest_ip":"10.0.0.5","dest_port":443,"proto":"TCP","alert":{"action":"allowed","gid":1,"signature_id":2100498,"rev":1,"signature":"ET SCAN Nmap Scripting Engine User-Agent Detected (NSE)","category":"Attempted Information Leak","severity":4}}',
    NULL,
    NULL
),
(
    NOW() - INTERVAL '2 days',
    '10.0.0.7',
    '8.8.8.8',
    2012345,
    'MEDIUM',
    '{"timestamp":"2026-03-23T07:57:00.999888+0800","flow_id":159753486,"event_type":"alert","src_ip":"10.0.0.7","src_port":53,"dest_ip":"8.8.8.8","dest_port":53,"proto":"UDP","alert":{"action":"allowed","gid":1,"signature_id":2012345,"rev":5,"signature":"ET TROJAN DNS Query to a known C&C server","category":"A Network Trojan was detected","severity":2}}',
    NULL,
    NULL
);
