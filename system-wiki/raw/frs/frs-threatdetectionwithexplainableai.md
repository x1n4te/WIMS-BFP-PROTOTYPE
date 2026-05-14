Module 8: Threat Detection with Explainable AI (XAI)
a. Qwen2.5-3B Integration
i.      The system shall deploy Qwen2.5-3B Small Language Model (SLM) on the VPS via Docker (Llama.cpp bindings).
ii.     SLM shall consume specific Suricata EVE JSON alerts + FastAPI audit logs on-demand to generate human-readable forensic narratives.
iii.    SLM operates in a synchronous on-request mode for the System Administrator, ensuring CPU/GPU resources are only utilized during active analysis.
b. Suricata-Driven Anomaly Detection (Qwen Explainability Layer)
i.        Suricata shall perform deterministic behavioral anomaly detection via custom rules/thresholds, generating EVE JSON alerts for:
o   Impossible Travel: Rapid logins from distant GeoIP locations (GeoIP2 MaxMind + custom Lua distance calc)
o   Bulk Deletion Attempts: >10 deletions/5min (threshold: type limit, track by_src)
o   Off-Hours Access: Admin actions 10PM–6AM (time-based rule suppression whitelist)
o   Privilege Escalation: RBAC violations (endpoint access rules)
o   Suspicious Query Patterns: SQLi/XSS attempts (signature rules)
ii.      Qwen2.5-3B shall generate explainable narratives for Suricata alerts with severity levels:
·         Low: Minor policy violation (e.g., "Failed login from known IP—likely mistyped password")
·         Medium: Suspicious activity (e.g., "Off-hours access by encoderjuan—review required")
·         High: Potential breach (e.g., "Bulk 15 deletions in 3min—possible data poisoning")
·         Critical: Active attack (e.g., "Privilege escalation detected: encoder accessing /api/analytics")
c. Explainable AI (XAI) Reports
i.      For a selected anomaly, the AI shall generate a human-readable explanation using specific System Prompts to interpret the raw log data.
ii.     Each XAI report shall include: (Guidance / Instructor Library)
·         Description of detected anomaly in plain language
·         Evidence (log excerpts, timestamps, user IDs)
·         Risk assessment (likelihood and impact)
·         Recommended action (e.g., “Lock user account”, “Review access logs”, “Investigate further”)
iii.    Reports shall be delivered to the System Monitoring dashboard via standard API requests upon completion of the inference task.
d. Human-in-the-Loop (HITL) Validation
i.      System Administrator shall review all Medium, High, and Critical alerts (React "Tinder for Threats" Card)
ii.     AI-generated alerts shall not trigger automatic blocking actions 
iii.    System Administrator actions: 
·         Confirm Threat: Escalate to incident response, lock affected accounts
·         False Positive: Dismiss alert, optionally add to AI training exclusions (Few-Shot Context Injection)
·         Request More Info: Ask AI to re-analyze with additional context
iv.    System shall log all HITL decisions for audit trail (PostgreSQL JSONB Column)
