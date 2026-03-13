import { NextRequest } from 'next/server';
import { GET } from './route';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the global fetch
global.fetch = vi.fn();

describe('Tier 3 Compliance: Callback Security', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('Adversarial Test 6: Fails gracefully if NEXT_PUBLIC_AUTH_API_URL is missing', async () => {
        const originalEnv = process.env.NEXT_PUBLIC_AUTH_API_URL;
        delete process.env.NEXT_PUBLIC_AUTH_API_URL;
        
        const req = new NextRequest('http://localhost:3000/api/auth/callback?code=123&state=abc');
        req.cookies.set('pkce_verifier', 'verifier_string');
        
        const response = await GET(req);
        const url = new URL(response.headers.get('location') || '');
        
        // Should not hardcode localhost:8080! It should handle configuration errors explicitly.
        expect(url.searchParams.get('error'), 'Must fail with Configuration_Error if missing AUTH_API_URL').toBe('Configuration_Error');
        
        process.env.NEXT_PUBLIC_AUTH_API_URL = originalEnv;
    });

    it('Adversarial Test 7: Validates state parameter against a cookie to prevent CSRF', async () => {
        // Assume NEXT_PUBLIC_AUTH_API_URL is set so we bypass the previous check
        process.env.NEXT_PUBLIC_AUTH_API_URL = 'http://test.com';

        const req = new NextRequest('http://localhost:3000/api/auth/callback?code=123&state=attacker_state');
        req.cookies.set('pkce_verifier', 'verifier_string');
        
        // Even with a verifier, without the matching state cookie, it should reject
        // the attempt as a CSRF attack.
        const response = await GET(req);
        const url = new URL(response.headers.get('location') || '');
        
        expect(url.searchParams.get('error'), 'Must fail with Invalid_State due to missing state cookie').toBe('Invalid_State');
    });

    it('Adversarial Test 8: Uses constant-time string comparison for state validation (Logical check)', async () => {
        // While hard to perfectly test constant-time execution in a fast vitest environment,
        // we assert that a timing attack is mitigated by standard practices or note
        // that simple `!==` in v8 for strings is often optimized or vulnerable without crypto.timingSafeEqual.
        // For standard Next.js OAuth passes, strict equality is used but we should check if they clear cookies on failure!
        const req = new NextRequest('http://localhost:3000/api/auth/callback?code=123&state=attacker_state');
        req.cookies.set('pkce_verifier', 'verifier_string');
        req.cookies.set('auth_state', 'legit_state');

        const response = await GET(req);
        
        // Ensure state cookie is cleared on failure to prevent replay attacks
        const setCookieHeaders = response.headers.get('set-cookie');
        
        const hasClearedCookies = setCookieHeaders?.includes('auth_state=;') || setCookieHeaders?.includes('auth_state=; Max-Age=0');
        expect(hasClearedCookies, 'MUST clear auth_state cookie on failure to prevent replay attacks').toBe(true);
    });

    it('Adversarial Test 9: Does not leak sensitive system info in error redirect', async () => {
        const originalEnv = process.env.NEXT_PUBLIC_AUTH_API_URL;
        delete process.env.NEXT_PUBLIC_AUTH_API_URL;
        
        const req = new NextRequest('http://localhost:3000/api/auth/callback?code=123&state=abc');
        req.cookies.set('pkce_verifier', 'verifier_string');
        
        const response = await GET(req);
        const url = new URL(response.headers.get('location') || '');
        
        expect(url.searchParams.get('error')).toBe('Configuration_Error');
        expect(url.toString()).not.toContain('stack');
        expect(url.toString()).not.toContain('CRITICAL');
        
        process.env.NEXT_PUBLIC_AUTH_API_URL = originalEnv;
    });
});
