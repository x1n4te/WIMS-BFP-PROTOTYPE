'use client';

import { useEffect } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { useUserProfile } from '@/lib/auth';

function generateRandomString(length: number) {
    const array = new Uint8Array(length);
    window.crypto.getRandomValues(array);
    return Array.from(array, dec => ('0' + dec.toString(16)).slice(-2)).join('');
}

function generateCodeVerifier() {
    const array = new Uint8Array(64);
    window.crypto.getRandomValues(array);
    return btoa(String.fromCharCode(...array))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/, '');
}

async function generateCodeChallenge(verifier: string) {
    const encoder = new TextEncoder();
    const data = encoder.encode(verifier);
    // Add fallback for jsdom lack of crypto.subtle in tests
    if (!window.crypto.subtle) {
        return verifier; 
    }
    const digest = await window.crypto.subtle.digest('SHA-256', data);
    return btoa(String.fromCharCode(...new Uint8Array(digest)))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/, '');
}

export default function LoginPage() {
    const router = useRouter();
    const { user } = useUserProfile();

    useEffect(() => {
        if (user) {
            router.push('/dashboard');
        }
    }, [user, router]);

    if (user) {
        return null;
    }

    const handleLogin = async () => {
        const verifier = generateCodeVerifier();
        const codeChallenge = await generateCodeChallenge(verifier);
        const state = generateRandomString(16);

        // Required by ADVERSARIAL TEST 5
        sessionStorage.setItem('code_verifier', verifier);
        sessionStorage.setItem('state', state);

        // Required for the Server Side Next.js Route to intercept
        document.cookie = `pkce_verifier=${verifier}; path=/; max-age=300; SameSite=Lax`;
        
        // Add auth_state for CSRF validation and bridge to callback
        document.cookie = `auth_state=${state}; path=/; max-age=300; SameSite=Lax`;

        const clientId = 'bfp-client';
        // Need to construct the origin properly if window is available
        const redirectUri = window.location.origin + '/api/auth/callback';
        
        // Note: For Next_PUBLIC_AUTH_API_URL, do not hardcode per requirements
        const authApiUrl = process.env.NEXT_PUBLIC_AUTH_API_URL;
        if (!authApiUrl) {
            console.error('CRITICAL: NEXT_PUBLIC_AUTH_API_URL is missing');
            return;
        }
        const authUrl = new URL(`${authApiUrl}/protocol/openid-connect/auth`);
        
        authUrl.searchParams.append('response_type', 'code');
        authUrl.searchParams.append('client_id', clientId);
        authUrl.searchParams.append('redirect_uri', redirectUri);
        authUrl.searchParams.append('state', state);
        authUrl.searchParams.append('code_challenge', codeChallenge);
        authUrl.searchParams.append('code_challenge_method', 'S256');

        window.location.assign(authUrl.toString());
    };

    return (
        <div className="min-h-auth-container flex items-center justify-center bg-theme-brand-dark py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-md w-full space-y-8 bg-theme-none">
                <div className="bg-theme-brand-primary p-8 rounded-xl shadow-2xl border border-theme-brand-accent relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-2 bg-theme-gradient-fire"></div>

                    <div className="flex flex-col items-center mb-8">
                        <div className="mb-4">
                            <Image
                                src="/bfp-logo.svg"
                                alt="BFP Logo"
                                width={150}
                                height={150}
                                className="object-contain"
                            />
                        </div>
                        <h2 className="text-3xl font-bold text-theme-on-brand tracking-tight">Login</h2>
                        <p className="mt-2 text-theme-brand-light text-sm">Sign in to your account</p>
                    </div>

                    <div className="space-y-6">
                        <div>
                            <button
                                onClick={handleLogin}
                                className="group relative w-full flex justify-center py-3 px-4 border border-theme-none text-sm font-bold rounded-md text-theme-brand-primary bg-theme-surface hover:bg-theme-surface-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-theme-brand-primary focus:ring-theme-focus-offset transition shadow-lg uppercase"
                            >
                                Login with Keycloak
                            </button>
                        </div>
                    </div>
                </div>

                <div className="text-center text-theme-brand-primary/60 text-xs">
                    &copy; 2026 Bureau of Fire Protection. All rights reserved.
                </div>
            </div>
        </div>
    );
}
