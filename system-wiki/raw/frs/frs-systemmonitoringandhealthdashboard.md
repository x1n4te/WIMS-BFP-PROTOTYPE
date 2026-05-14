Module 9: System Monitoring and Health Dashboard
a. System Health Metrics
i.        System Monitoring module shall track the following metrics (using Python psutil and Docker API):
o   Container Status: Uptime and health of specific containers (FastAPI, PostgreSQL, Suricata, Qwen-AI).
o   VPS Resource Usage: Real-time CPU and RAM utilization (critical for monitoring AI spikes). 
o   Database Performance: Average query latency in milliseconds. 
o   PWA Sync Health: Success rate of background synchronization events from the PWA client. 
o   Network Traffic: Inbound/outbound bandwidth usage via Nginx.
o   AI On-Demand Latency: Time taken (in seconds) for the SLM to generate a forensic narrative per request. 
ii.     Metrics shall be refreshed every 60 seconds to ensure real-time visibility without over-burdening VPS resources.
iii.    System Administrator can view real-time metrics in dedicated dashboard
b. Log Query and Review
i.        System Administrator can query System Logs using filters: (PostgreSQL JSONB Queries)
o   Date/time range
o   User ID
o   Log severity (INFO, WARN, ERROR, CRITICAL)
o   Event type (authentication, data modification, security alert)
ii.     System shall support full-text search across log entries (PostgreSQL tsvector (Gin Index))
iii.    Query results shall be paginated (50 entries per page) (FastAPI LimitOffsetPagination)
c. Configuration Management
i.      System Administrator can update monitoring thresholds via the interface. 
ii.     Configurable parameters:
·         Alert severity thresholds (e.g., trigger High alert if > 5 failed logins in 10 minutes)
·         Session timeout duration
·         Offline mode maximum storage limit
·         AI Response Timeout: Maximum time allowed for an AI explanation before the request is canceled.