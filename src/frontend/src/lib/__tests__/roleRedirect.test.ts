import { describe, expect, it } from 'vitest';
import { defaultRouteForRole, resolvePostLoginRedirect } from '../roleRedirect';

const ORIGIN = 'http://localhost';

describe('role redirect helpers', () => {
  it('lands every staff role on its own dashboard', () => {
    expect(defaultRouteForRole('SYSTEM_ADMIN')).toBe('/admin/system');
    expect(defaultRouteForRole('REGIONAL_ENCODER')).toBe('/dashboard/regional');
    expect(defaultRouteForRole('NATIONAL_VALIDATOR')).toBe('/dashboard/validator');
    expect(defaultRouteForRole('NATIONAL_ANALYST')).toBe('/dashboard/analyst');
  });

  it('falls back to /dashboard for an unknown or missing role (no civilian/legacy routes)', () => {
    expect(defaultRouteForRole('CIVILIAN_REPORTER')).toBe('/dashboard');
    expect(defaultRouteForRole('ENCODER')).toBe('/dashboard');
    expect(defaultRouteForRole(null)).toBe('/dashboard');
  });

  it('uses the role dashboard when nothing was saved', () => {
    expect(resolvePostLoginRedirect('NATIONAL_ANALYST', null, ORIGIN)).toBe('/dashboard/analyst');
  });

  it('replaces redirects to removed pages and generic paths with the role dashboard', () => {
    for (const saved of ['/home', '/contributor', '/incidents', '/incidents/3', '/report', '/tracking', '/login', '/callback', '/', '/dashboard']) {
      expect(resolvePostLoginRedirect('REGIONAL_ENCODER', `${ORIGIN}${saved}`, ORIGIN)).toBe('/dashboard/regional');
    }
  });

  it('never replays another role area', () => {
    expect(resolvePostLoginRedirect('REGIONAL_ENCODER', `${ORIGIN}/dashboard/validator`, ORIGIN)).toBe('/dashboard/regional');
    expect(resolvePostLoginRedirect('REGIONAL_ENCODER', `${ORIGIN}/admin/system`, ORIGIN)).toBe('/dashboard/regional');
    expect(resolvePostLoginRedirect('NATIONAL_VALIDATOR', `${ORIGIN}/dashboard/regional`, ORIGIN)).toBe('/dashboard/validator');
    expect(resolvePostLoginRedirect('NATIONAL_ANALYST', `${ORIGIN}/admin/audit`, ORIGIN)).toBe('/dashboard/analyst');
    expect(resolvePostLoginRedirect('SYSTEM_ADMIN', `${ORIGIN}/dashboard/analyst`, ORIGIN)).toBe('/admin/system');
  });

  it('keeps a deep link inside the role own area', () => {
    expect(resolvePostLoginRedirect('REGIONAL_ENCODER', `${ORIGIN}/dashboard/regional/incidents/42?x=1#h`, ORIGIN)).toBe('/dashboard/regional/incidents/42?x=1#h');
    expect(resolvePostLoginRedirect('REGIONAL_ENCODER', `${ORIGIN}/afor/create?x=1`, ORIGIN)).toBe('/afor/create?x=1');
    expect(resolvePostLoginRedirect('SYSTEM_ADMIN', `${ORIGIN}/admin/breach`, ORIGIN)).toBe('/admin/breach');
    expect(resolvePostLoginRedirect('SYSTEM_ADMIN', `${ORIGIN}/afor/import`, ORIGIN)).toBe('/afor/import');
    expect(resolvePostLoginRedirect('NATIONAL_VALIDATOR', `${ORIGIN}/profile`, ORIGIN)).toBe('/profile');
  });

  it('ignores cross-origin redirects and malformed URLs', () => {
    expect(resolvePostLoginRedirect('REGIONAL_ENCODER', 'https://evil.example/dashboard/regional', ORIGIN)).toBe('/dashboard/regional');
    expect(resolvePostLoginRedirect('REGIONAL_ENCODER', 'http://[bad', ORIGIN)).toBe('/dashboard/regional');
  });
});
