/**
 * OIDC UserManager configuration for Keycloak.
 * Used by AuthContext for login redirect and callback handling.
 */
import { UserManager } from 'oidc-client-ts';

if (!process.env.NEXT_PUBLIC_AUTH_API_URL) {
  throw new Error('OIDC Authority URL is undefined');
}

const getBaseUrl = () =>
  typeof window !== 'undefined'
    ? (process.env.NEXT_PUBLIC_BASE_URL ?? process.env.NEXT_PUBLIC_OIDC_REDIRECT_URI?.replace(/\/api\/auth\/callback$/, '') ?? window.location.origin)
    : process.env.NEXT_PUBLIC_BASE_URL ?? process.env.NEXT_PUBLIC_APP_URL ?? 'http://localhost';

const authority = `${process.env.NEXT_PUBLIC_AUTH_API_URL}/realms/bfp`;

export const oidcConfig = {
  authority,
  client_id: process.env.NEXT_PUBLIC_OIDC_CLIENT_ID || 'wims-web',
  redirect_uri: process.env.NEXT_PUBLIC_OIDC_REDIRECT_URI ?? `${getBaseUrl()}/api/auth/callback`,
  response_type: 'code' as const,
  scope: 'openid profile email',
};

export function createUserManager(): UserManager {
  return new UserManager({
    ...oidcConfig,
    post_logout_redirect_uri: getBaseUrl(),
  });
}
