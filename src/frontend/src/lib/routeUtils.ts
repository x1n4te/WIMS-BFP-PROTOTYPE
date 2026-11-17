/**
 * Route constants and helpers for the unauthenticated surface.
 *
 * Turnover build: the civilian/public portal is gone. Only the sign-in screen, the OIDC callback
 * and the static privacy notice (RA 10173) are reachable without a session. Every other removed
 * public URL is redirected to /login by next.config.ts.
 */

export const PUBLIC_ROUTES = ['/login', '/callback'] as const satisfies readonly string[];

export const PUBLIC_ROUTE_PREFIXES = ['/privacy'] as const satisfies readonly string[];

export function isPublicRoute(pathname: string): boolean {
  return (
    (PUBLIC_ROUTES as readonly string[]).includes(pathname) ||
    (PUBLIC_ROUTE_PREFIXES as readonly string[]).some((prefix) => pathname.startsWith(prefix))
  );
}
