/**
 * Unit tests for LayoutShell — route-driven shell selection (turnover build).
 *
 * Verifies that:
 * - /login, /callback and /privacy render the unauthenticated shell (no Sidebar/Header).
 * - Anonymous users on any other route are sent to sign-in (login()).
 * - Staff-authenticated routes render Sidebar+Header.
 */
import { render, screen, cleanup, act } from '@testing-library/react';
import { describe, it, expect, vi, afterEach } from 'vitest';
import { LayoutShell } from './LayoutShell';

// ---- Hoisted mocks ----
const { mockUseAuth, mockUsePathname, mockUseNetworkStatus } = vi.hoisted(() => ({
  mockUseAuth: vi.fn((): Record<string, unknown> => ({
    user: null,
    isAuthenticated: false,
    serverValidated: false,
    canQueueOfflineWrites: false,
    loading: false,
    loggingOut: false,
    login: vi.fn(),
    logout: vi.fn(),
    refreshSession: vi.fn(),
  })),
  mockUsePathname: vi.fn(() => '/'),
  mockUseNetworkStatus: vi.fn(() => ({ isOnline: true })),
}));

// ---- Module mocks ----
vi.mock('@/context/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}));

vi.mock('next/navigation', () => ({
  usePathname: () => mockUsePathname(),
}));

vi.mock('@/lib/useNetworkStatus', () => ({
  useNetworkStatus: () => mockUseNetworkStatus(),
}));

vi.mock('@/lib/swRegistration', () => ({
  registerServiceWorker: vi.fn(),
}));

vi.mock('@/lib/offlineStore', () => ({
  maybePruneCaches: vi.fn(() => Promise.resolve()),
}));

vi.mock('@/lib/usePreloadDashboardData', () => ({
  usePreloadDashboardData: vi.fn(),
}));

// Child component markers
vi.mock('@/components/Sidebar', () => ({
  Sidebar: () => <div data-testid="sidebar" />,
}));

vi.mock('@/components/Header', () => ({
  Header: () => <div data-testid="header" />,
}));

vi.mock('@/components/PwaInstallPrompt', () => ({
  PwaInstallPrompt: () => null,
}));

function anonymous(login = vi.fn()) {
  return {
    user: null,
    isAuthenticated: false,
    serverValidated: false,
    canQueueOfflineWrites: false,
    loading: false,
    loggingOut: false,
    login,
    logout: vi.fn(),
    refreshSession: vi.fn(),
  };
}

describe('LayoutShell', () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  describe('Anonymous user', () => {
    it.each(['/login', '/callback', '/privacy'])(
      'renders children without the staff shell on %s',
      (path) => {
        mockUseAuth.mockReturnValue(anonymous());
        mockUsePathname.mockReturnValue(path);
        render(<LayoutShell>content</LayoutShell>);
        expect(screen.getByText('content')).toBeInTheDocument();
        expect(screen.queryByTestId('sidebar')).not.toBeInTheDocument();
        expect(screen.queryByTestId('header')).not.toBeInTheDocument();
      },
    );

    it.each(['/dashboard', '/dashboard/regional', '/admin/system', '/afor/import'])(
      'sends an anonymous visitor on %s to sign-in',
      async (path) => {
        vi.useFakeTimers();
        const login = vi.fn();
        mockUseAuth.mockReturnValue(anonymous(login));
        mockUsePathname.mockReturnValue(path);
        render(<LayoutShell>content</LayoutShell>);
        await act(async () => {
          await vi.advanceTimersByTimeAsync(600);
        });
        expect(login).toHaveBeenCalled();
      },
    );

    it('does not redirect on the public routes', async () => {
      vi.useFakeTimers();
      const login = vi.fn();
      mockUseAuth.mockReturnValue(anonymous(login));
      mockUsePathname.mockReturnValue('/privacy');
      render(<LayoutShell>content</LayoutShell>);
      await act(async () => {
        await vi.advanceTimersByTimeAsync(600);
      });
      expect(login).not.toHaveBeenCalled();
    });
  });

  describe('Staff-authenticated user', () => {
    const staffRoles = ['REGIONAL_ENCODER', 'NATIONAL_VALIDATOR', 'NATIONAL_ANALYST', 'SYSTEM_ADMIN'];

    it.each(staffRoles)('renders Sidebar+Header for role %s', (role) => {
      mockUseAuth.mockReturnValue({
        user: {
          id: 'staff-1',
          preferred_username: 'staff_user',
          role,
          assignedRegionId: role === 'REGIONAL_ENCODER' ? 1 : null,
        },
        isAuthenticated: true,
        serverValidated: true,
        canQueueOfflineWrites: true,
        loading: false,
        loggingOut: false,
        login: vi.fn(),
        logout: vi.fn(),
        refreshSession: vi.fn(),
      });
      mockUsePathname.mockReturnValue('/dashboard');
      render(<LayoutShell>content</LayoutShell>);

      expect(screen.getByTestId('sidebar')).toBeInTheDocument();
      expect(screen.getByTestId('header')).toBeInTheDocument();
    });
  });
});
