# Tier 3 Compliance Tasks: Login Component

## 1. Auth Guard Consistency: Keycloak Migration
- **Context**: Code imports `@/lib/supabaseClient` and directly invokes `supabase.auth.signInWithPassword`. This violates the Constitution's mandate of Keycloak (OIDC/JWT) as the supreme authentication authority.
- **Audit FAILURES**:
  1. **PKCE Missing**: The UI accepts credentials directly and POSTs to `/auth/login` (ROPC flow). There is ZERO PKCE code verifier/challenge generation or Keycloak redirect logic present.
  2. **Security Hardening Untestable**: Cookies cannot be verified as HttpOnly/SameSite=Strict/Secure purely from client `fetch()` requests. The corresponding backend route (e.g. Next.js API route or FastAPI) was not included in the review scope.
  3. **Violation of DRY/SOLID**: `/auth/login` and `/api/auth/session` are hardcoded relative API strings rather than explicitly cast, runtime-validated environment variables.
- **Micro-tasks** (UPDATED):
  1. [x] Strip all Supabase imports and local supabase context. *(Passed, but zombie session shapes remain).*
  2. [x] Implement an explicit Authorization Code Flow with PKCE, generating the `code_verifier` client-side and redirecting to the quantified Keycloak authorize endpoint.
  3. [x] Enforce that the resulting Access and Refresh tokens are stored strictly as HttpOnly, SameSite=Strict secure cookies, fundamentally inaccessible to client-side JavaScript. *(Submit server-side code for review).*
  4. [x] Extrapolate `/auth/login` and `/api/auth/session` into strictly typed `process.env.NEXT_PUBLIC_AUTH_API_URL` values.
- [TDD CHECKPOINT] **[STATUS: PASSED - GREEN STATE]**

## 2. UI Quantification: Extract Arbitrary "Vibes"
- **Context**: The markup is littered with unquantified, hardcoded layout/styling properties (`min-h-[calc(100vh-8rem)]`, `bg-red-900`, `from-yellow-400 via-orange-500 to-red-500`, `w-[150px]`). This is non-deterministic design.
- **Micro-tasks**:
  1. Relocate all literal color hexes and dimensions to a formalized `theme.json` or unified CSS variable map.
  2. Refactor classNames to use semantic tokens (e.g., `bg-theme-brand-dark`, `min-h-auth-layout`).
  3. Eradicate inline assumptions about absolute sizing where responsive container queries would suffice.
- [TDD CHECKPOINT]

## 3. Rate Limiting: Client & Server Throttling
- **Context**: `handleLogin` has zero throttling. A user can click "Login" 50 times a second, flooding the gateway.
- **Micro-tasks**:
  1. Implement a Redis-backed sliding window rate limiter on the FastAPI auth endpoint. Bounds: Maximum 5 failed authentication attempts per 15-minute window per client_ip.
  2. Implement client-side UI debouncing (1000ms lock) and explicitly trap the resulting HTTP 429 from the server, parsing the Retry-After header to lock the form.
  3. Parse the `Retry-After` header when caught, completely disabling the form until the quantified time elapses, alerting the user to the precise cooldown timer.
- [TDD CHECKPOINT]

## 4. Failure State Identification: Gateway & Provider Outages
- **Context**: What happens if the VPS falls over? The UI hangs or relies on a generic `authError.message`. There is no bounded latency.
- **Micro-tasks**:
  1. Implement a rigid network timeout on the auth request (e.g., `AbortController` set to 5000ms).
  2. Explicitly catch `HTTP 503 Service Unavailable`, `HTTP 504 Gateway Timeout`, and Timeout Exceptions.
  3. Map these specific network states to quantified UI error strings independent of the remote payload (e.g. "Identity Provider Unreachable (HTTP 503)").
- [TDD CHECKPOINT]

## 5. Security Telemetry: Interpretability Logging
- **Context**: When authentication fails, the application quietly updates `setError` on the client. It completely starves the XAI interpretability layer of security events.
- **Micro-tasks**:
  1. Eradicate all client-side security logging. The React UI must not attempt to POST to a telemetry endpoint.
  2. Ensure the backend FastAPI auth route intercepts every failed Keycloak challenge and directly performs a database insert into wims.security_audit_log containing the client_ip, user_agent, and failure_reason.
  3. Guarantee that connection timeouts vs. invalid credentials are computationally distinct in the telemetry pipeline.
- [TDD CHECKPOINT]
