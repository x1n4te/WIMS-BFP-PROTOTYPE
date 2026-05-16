Module 14: Public Anonymous Incident Submission
i.   The system shall provide a zero-trust public endpoint at POST /api/v1/public/report accepting fire incident reports without any authentication token, session cookie, or credential exchange.

ii.   Rate limiting shall be enforced via Redis with a threshold of three (3) requests per source IP address per rolling one-hour window, applied before any database connection acquisition.
  
iii.   Anonymous submissions shall be stored in wims.fire_incidents with encoder_id set to NULL and verification_status set to PENDING_VALIDATION.

iv.   The system shall resolve region_id automatically via a nearest-centroid query against wims.ref_regions geometry, with a fail-safe fallback to the first seeded region.

v.   Exceeding the rate limit shall return HTTP 429 (Too Many Requests) with a Retry-After HTTP header indicating the number of seconds until the window resets.

vi.   No attachment upload capability shall be exposed on the public endpoint; file attachments require an authenticated session and shall use Module 2 functionality.

vii.   No CAPTCHA shall be enforced; rate limiting is the sole abuse prevention mechanism.

viii.   All submitted data shall be subject to Pydantic schema validation before any database write.

ix.   No PII beyond operationally necessary data shall be collected, in compliance with RA 10173 data minimization.

