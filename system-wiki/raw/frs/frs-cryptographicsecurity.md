Module 6: Cryptographic Security
a. Data-at-Rest Encryption
i.     All sensitive incident data stored in Central Database shall be encrypted (SQLAlchemy TypeDecorator)
ii.      Encryption applied to:
·         Incident narratives
·         Casualty details
·         Property damage estimates
·         File attachments
iii.    Encryption keys managed by dedicated key management service (OpenBao) (OpenBao (Docker))
iv.    Key rotation performed every 90 days (OpenBao Auto-Rotate)
b. Data-in-Transit Encryption
i.      All network communication shall use TLS 1.3 (Nginx / Traefik)
ii.     Enforce HTTPS for all web traffic 
iii.    Disable weak cipher suites (only AES-256-GCM and ChaCha20-Poly1305 allowed) (Nginx Configuration)
iv.    HTTP Strict Transport Security (HSTS) for API endpoints to prevent MITM attacks. (Expect-CT / HSTS)
