import { NextRequest, NextResponse } from 'next/server';
import crypto from 'crypto';

export async function GET(req: NextRequest) {
    const origin = req.nextUrl?.origin ?? process.env.NEXT_PUBLIC_BASE_URL ?? process.env.NEXT_PUBLIC_APP_URL ?? 'http://localhost';
    const appUrl = origin;

    let redirectUrl = new URL('/login?error=Internal_Server_Error', appUrl);
    let successRes: NextResponse | null = null;

    try {
        const url = new URL(req.url);
        const code = url.searchParams.get('code');
        const state = url.searchParams.get('state') || '';

        // Check strict env variable config
        if (!process.env.NEXT_PUBLIC_AUTH_API_URL) {
            console.error('CRITICAL: NEXT_PUBLIC_AUTH_API_URL is missing');
            redirectUrl = new URL('/login?error=Configuration_Error', appUrl);
            return NextResponse.redirect(redirectUrl); // Early return for missing env
        }

        // Extract verifier and auth_state from the session
        const code_verifier = req.cookies.get('pkce_verifier')?.value || '';
        const cookie_auth_state = req.cookies.get('auth_state')?.value || '';

        // CSRF state validation (Constant Time Comparison)
        if (!state || !cookie_auth_state || state.length !== cookie_auth_state.length) {
            redirectUrl = new URL('/login?error=Invalid_State', appUrl);
            throw new Error('CSRF Validation failed (Length mismatch or missing)');
        }

        const stateBuffer = Buffer.from(state);
        const cookieStateBuffer = Buffer.from(cookie_auth_state);

        if (!crypto.timingSafeEqual(stateBuffer, cookieStateBuffer)) {
            redirectUrl = new URL('/login?error=Invalid_State', appUrl);
            throw new Error('CSRF Validation failed (timingSafeEqual)');
        }

        if (!code || !code_verifier) {
            redirectUrl = new URL('/login?error=Missing_Code_or_Verifier', appUrl);
            throw new Error('Missing OAuth Code or PKCE Verifier');
        }

        const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
        const tokenEndpoint = `${authApiUrl}/protocol/openid-connect/token`;
        const clientId = process.env.NEXT_PUBLIC_OIDC_CLIENT_ID || 'wims-web';
        const redirectUri = `${origin}/api/auth/callback`;

        const params = new URLSearchParams();
        params.append('grant_type', 'authorization_code');
        params.append('client_id', clientId);
        params.append('code', code);
        params.append('code_verifier', code_verifier);
        params.append('redirect_uri', redirectUri);

        const response = await fetch(tokenEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: params.toString(),
        });

        if (!response.ok) {
            console.error('Token Exchange Failed');
            redirectUrl = new URL('/login?error=Token_Exchange_Failed', appUrl);
            throw new Error('Token Exchange Failed');
        }

        const data = await response.json();
        
        // Successfully got tokens, setup success redirect
        successRes = NextResponse.redirect(new URL('/dashboard', appUrl));
        
        // Issue tokens as HttpOnly; SameSite=Lax for OAuth redirect compatibility; Path=/
        successRes.cookies.set('access_token', data.access_token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'lax',
            path: '/',
        });

        if (data.refresh_token) {
            successRes.cookies.set('refresh_token', data.refresh_token, {
                httpOnly: true,
                secure: process.env.NODE_ENV === 'production',
                sameSite: 'lax',
                path: '/',
            });
        }
    } catch (err) {
        console.error('Callback Route Error Controlled');
    } finally {
        const res = successRes || NextResponse.redirect(redirectUrl);

        // ALWAYS clear the session cookies (ATOMIC CLEANUP)
        res.cookies.set('pkce_verifier', '', { maxAge: 0, path: '/' });
        res.cookies.set('auth_state', '', { maxAge: 0, path: '/' });

        return res;
    }
}
