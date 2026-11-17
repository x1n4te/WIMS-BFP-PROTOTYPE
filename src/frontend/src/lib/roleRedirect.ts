const DEFAULT_STAFF_ROUTES: Record<string, string> = {
  SYSTEM_ADMIN: '/admin/system',
  REGIONAL_ENCODER: '/dashboard/regional',
  NATIONAL_VALIDATOR: '/dashboard/validator',
  NATIONAL_ANALYST: '/dashboard/analyst',
};

/** Path prefixes each role may be sent back to after login (besides its own dashboard). */
const ROLE_ALLOWED_PREFIXES: Record<string, readonly string[]> = {
  SYSTEM_ADMIN: ['/admin', '/afor', '/profile', '/privacy'],
  REGIONAL_ENCODER: ['/dashboard/regional', '/afor', '/profile', '/privacy'],
  NATIONAL_VALIDATOR: ['/dashboard/validator', '/profile', '/privacy'],
  NATIONAL_ANALYST: ['/dashboard/analyst', '/profile', '/privacy'],
};

const GENERIC_LOGIN_PATHS = new Set(['/', '/login', '/callback', '/dashboard']);

/** Every staff role lands on its own dashboard; an unknown role falls back to /dashboard. */
export function defaultRouteForRole(role?: string | null): string {
  return role ? DEFAULT_STAFF_ROUTES[role] ?? '/dashboard' : '/dashboard';
}

function pathAllowedForRole(role: string, pathname: string): boolean {
  return (ROLE_ALLOWED_PREFIXES[role] ?? []).some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

export function resolvePostLoginRedirect(
  role: string | null | undefined,
  savedRedirect: string | null,
  origin: string,
): string {
  const defaultRoute = defaultRouteForRole(role);
  if (!savedRedirect || !role) return defaultRoute;

  try {
    const target = new URL(savedRedirect, origin);
    if (target.origin !== origin) return defaultRoute;
    if (GENERIC_LOGIN_PATHS.has(target.pathname)) return defaultRoute;
    // A saved URL that belongs to another role's area (e.g. a validator URL replayed for an
    // encoder login) or to a removed page must never be replayed: use the role's own dashboard.
    if (!pathAllowedForRole(role, target.pathname)) return defaultRoute;
    return `${target.pathname}${target.search}${target.hash}`;
  } catch {
    return defaultRoute;
  }
}
