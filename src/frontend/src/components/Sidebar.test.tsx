/**
 * TDD: Sidebar navigation — #363 Rate Limits entry
 *
 * Verifies that the Sidebar:
 * 1. Shows "Rate Limits" nav item for SYSTEM_ADMIN
 * 2. Does NOT show "Rate Limits" for other roles
 * 3. Links to /admin/system/rate-limits
 */
import { render, screen, cleanup } from '@testing-library/react';
import { describe, it, expect, vi, afterEach } from 'vitest';
import { Sidebar } from '@/components/Sidebar';

vi.mock('next/navigation', () => ({
  usePathname: () => '/admin/system/config',
  useRouter: () => ({ push: vi.fn() }),
}));

const { mockUseAuth } = vi.hoisted(() => ({
  mockUseAuth: vi.fn(() => ({
    user: { role: 'SYSTEM_ADMIN' },
    loading: false,
    logout: vi.fn(),
  })),
}));

vi.mock('@/context/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}));

const { mockOfflineWorkCounts } = vi.hoisted(() => ({
  mockOfflineWorkCounts: vi.fn(() => ({
    pendingCount: 0,
    failedCount: 0,
    conflictCount: 0,
    draftCount: 0,
    totalActionableCount: 0,
    loading: false,
  })),
}));

vi.mock('@/lib/useOfflineWorkCounts', () => ({
  useOfflineWorkCounts: () => mockOfflineWorkCounts(),
}));

// Mock next/image
vi.mock('next/image', () => ({
  default: ({ alt, ...props }: { alt: string; [key: string]: unknown }) => {
    // eslint-disable-next-line @next/next/no-img-element
    return <img alt={alt} {...props} />;
  },
}));

describe('Sidebar — Rate Limits entry', () => {
  afterEach(() => {
    cleanup();
  });

  it('shows Rate Limits for SYSTEM_ADMIN', () => {
    mockUseAuth.mockReturnValue({
      user: { role: 'SYSTEM_ADMIN' },
      loading: false,
      logout: vi.fn(),
    });
    render(<Sidebar isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText('Rate Limits')).toBeInTheDocument();
  });

  it('shows Import AFOR (/afor/import) for SYSTEM_ADMIN but not for validators', () => {
    mockUseAuth.mockReturnValue({ user: { role: 'SYSTEM_ADMIN' }, loading: false, logout: vi.fn() });
    const { unmount } = render(<Sidebar isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText('Import AFOR').closest('a')).toHaveAttribute('href', '/afor/import');
    unmount();

    mockUseAuth.mockReturnValue({ user: { role: 'NATIONAL_VALIDATOR' }, loading: false, logout: vi.fn() });
    render(<Sidebar isOpen={true} onClose={vi.fn()} />);
    expect(screen.queryByText('Import AFOR')).not.toBeInTheDocument();
  });

  it('Rate Limits link points to /admin/system/rate-limits', () => {
    mockUseAuth.mockReturnValue({
      user: { role: 'SYSTEM_ADMIN' },
      loading: false,
      logout: vi.fn(),
    });
    render(<Sidebar isOpen={true} onClose={vi.fn()} />);
    const link = screen.getByText('Rate Limits').closest('a');
    expect(link).toHaveAttribute('href', '/admin/system/rate-limits');
  });

  it('does NOT show Rate Limits for REGIONAL_ENCODER', () => {
    mockUseAuth.mockReturnValue({
      user: { role: 'REGIONAL_ENCODER' },
      loading: false,
      logout: vi.fn(),
    });
    render(<Sidebar isOpen={true} onClose={vi.fn()} />);
    expect(screen.queryByText('Rate Limits')).not.toBeInTheDocument();
  });

  it('does NOT show Rate Limits for NATIONAL_VALIDATOR', () => {
    mockUseAuth.mockReturnValue({
      user: { role: 'NATIONAL_VALIDATOR' },
      loading: false,
      logout: vi.fn(),
    });
    render(<Sidebar isOpen={true} onClose={vi.fn()} />);
    expect(screen.queryByText('Rate Limits')).not.toBeInTheDocument();
  });

  it('does NOT show Rate Limits for NATIONAL_ANALYST', () => {
    mockUseAuth.mockReturnValue({
      user: { role: 'NATIONAL_ANALYST' },
      loading: false,
      logout: vi.fn(),
    });
    render(<Sidebar isOpen={true} onClose={vi.fn()} />);
    expect(screen.queryByText('Rate Limits')).not.toBeInTheDocument();
  });

  it('Configuration is still present for SYSTEM_ADMIN', () => {
    mockUseAuth.mockReturnValue({
      user: { role: 'SYSTEM_ADMIN' },
      loading: false,
      logout: vi.fn(),
    });
    render(<Sidebar isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText('Configuration')).toBeInTheDocument();
  });
});

describe('Sidebar — Offline Work badge (Item 10)', () => {
  afterEach(() => {
    cleanup();
  });

  it('shows Offline Work nav item for REGIONAL_ENCODER', () => {
    mockUseAuth.mockReturnValue({
      user: { role: 'REGIONAL_ENCODER', id: 'enc-1' },
      loading: false,
      logout: vi.fn(),
    });
    mockOfflineWorkCounts.mockReturnValue({
      pendingCount: 3,
      failedCount: 1,
      conflictCount: 2,
      draftCount: 0,
      totalActionableCount: 6,
      loading: false,
    });
    render(<Sidebar isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText('Offline Work')).toBeInTheDocument();
    // Badge shows 6 (totalActionableCount)
    expect(screen.getByText('6')).toBeInTheDocument();
  });

  it('Offline Work link points to /dashboard/regional/offline-work', () => {
    mockUseAuth.mockReturnValue({
      user: { role: 'REGIONAL_ENCODER', id: 'enc-2' },
      loading: false,
      logout: vi.fn(),
    });
    mockOfflineWorkCounts.mockReturnValue({
      totalActionableCount: 1,
      loading: false,
    });
    render(<Sidebar isOpen={true} onClose={vi.fn()} />);
    const link = screen.getByText('Offline Work').closest('a');
    expect(link).toHaveAttribute('href', '/dashboard/regional/offline-work');
  });

  it('hides badge when totalActionableCount is zero', () => {
    mockUseAuth.mockReturnValue({
      user: { role: 'REGIONAL_ENCODER', id: 'enc-3' },
      loading: false,
      logout: vi.fn(),
    });
    mockOfflineWorkCounts.mockReturnValue({
      pendingCount: 0,
      failedCount: 0,
      conflictCount: 0,
      draftCount: 0,
      totalActionableCount: 0,
      loading: false,
    });
    render(<Sidebar isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText('Offline Work')).toBeInTheDocument();
    // No badge element with '0'
    expect(screen.queryByText('0')).not.toBeInTheDocument();
  });

  it('does NOT show Offline Work or badge count for SYSTEM_ADMIN role', () => {
    mockUseAuth.mockReturnValue({
      user: { role: 'SYSTEM_ADMIN' },
      loading: false,
      logout: vi.fn(),
    });
    mockOfflineWorkCounts.mockReturnValue({
      pendingCount: 3,
      failedCount: 2,
      conflictCount: 1,
      draftCount: 0,
      totalActionableCount: 6,
      loading: false,
    });
    render(<Sidebar isOpen={true} onClose={vi.fn()} />);
    expect(screen.queryByText('Offline Work')).not.toBeInTheDocument();
    expect(screen.queryByText('6')).not.toBeInTheDocument();
    expect(mockOfflineWorkCounts).toHaveBeenCalled();
  });

  it('does NOT show Offline Work for NATIONAL_VALIDATOR role', () => {
    mockUseAuth.mockReturnValue({
      user: { role: 'NATIONAL_VALIDATOR' },
      loading: false,
      logout: vi.fn(),
    });
    render(<Sidebar isOpen={true} onClose={vi.fn()} />);
    expect(screen.queryByText('Offline Work')).not.toBeInTheDocument();
  });

  it('does NOT show Offline Work for NATIONAL_ANALYST role', () => {
    mockUseAuth.mockReturnValue({
      user: { role: 'NATIONAL_ANALYST' },
      loading: false,
      logout: vi.fn(),
    });
    render(<Sidebar isOpen={true} onClose={vi.fn()} />);
    expect(screen.queryByText('Offline Work')).not.toBeInTheDocument();
  });
});

describe('Sidebar — turnover build navigation', () => {
  afterEach(() => {
    cleanup();
  });

  const REMOVED_LABELS = [
    'Operations',
    'Triage Queue',
    'Operational Map',
    'Perimeter Drawing',
    'Security Monitoring',
    'Telemetry',
    'Civilian Management',
    'Information Management',
    'Contributor',
    'Information',
    'Incidents',
  ];
  const REMOVED_HREF = /^\/(home|incidents|contributor|information|admin\/monitoring|admin\/civilians|admin\/community|admin\/information|dashboard\/validator\/(map|perimeter-draw))/;

  const ROLES = ['SYSTEM_ADMIN', 'REGIONAL_ENCODER', 'NATIONAL_VALIDATOR', 'NATIONAL_ANALYST'] as const;

  it.each(ROLES)('%s sees no entry for a removed page and no link to a removed route', (role) => {
    mockUseAuth.mockReturnValue({ user: { role }, loading: false, logout: vi.fn() });
    mockOfflineWorkCounts.mockReturnValue({
      pendingCount: 0,
      failedCount: 0,
      conflictCount: 0,
      draftCount: 0,
      totalActionableCount: 0,
      loading: false,
    });
    render(<Sidebar isOpen={true} onClose={vi.fn()} />);
    for (const label of REMOVED_LABELS) {
      expect(screen.queryByText(label)).not.toBeInTheDocument();
    }
    const hrefs = screen.getAllByRole('link').map((a) => a.getAttribute('href') ?? '');
    expect(hrefs.length).toBeGreaterThan(1);
    for (const h of hrefs) {
      expect(h).not.toMatch(REMOVED_HREF);
    }
  });

  it('SYSTEM_ADMIN keeps governance, breach, audit, anomalies, config and AFOR import', () => {
    mockUseAuth.mockReturnValue({ user: { role: 'SYSTEM_ADMIN' }, loading: false, logout: vi.fn() });
    render(<Sidebar isOpen={true} onClose={vi.fn()} />);
    for (const label of ['Governance', 'Breach Notifications', 'Import AFOR', 'System Audit', 'Anomaly Detection', 'Configuration']) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it('NATIONAL_VALIDATOR keeps the dashboard and audit trail', () => {
    mockUseAuth.mockReturnValue({ user: { role: 'NATIONAL_VALIDATOR' }, loading: false, logout: vi.fn() });
    render(<Sidebar isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByRole('link', { name: 'Dashboard' })).toHaveAttribute('href', '/dashboard/validator');
    expect(screen.getByText('Audit Trail')).toBeInTheDocument();
  });

  it('REGIONAL_ENCODER keeps manual entry, AFOR import and offline work', () => {
    mockUseAuth.mockReturnValue({ user: { role: 'REGIONAL_ENCODER' }, loading: false, logout: vi.fn() });
    mockOfflineWorkCounts.mockReturnValue({
      pendingCount: 0,
      failedCount: 0,
      conflictCount: 0,
      draftCount: 0,
      totalActionableCount: 0,
      loading: false,
    });
    render(<Sidebar isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText('Manual Entry')).toBeInTheDocument();
    expect(screen.getByText('Import AFOR')).toBeInTheDocument();
    expect(screen.getByText('Offline Work')).toBeInTheDocument();
  });

  it('a leftover CIVILIAN_REPORTER or legacy ENCODER account gets no navigation beyond the profile link', () => {
    for (const role of ['CIVILIAN_REPORTER', 'ENCODER']) {
      mockUseAuth.mockReturnValue({ user: { role }, loading: false, logout: vi.fn() });
      const { unmount } = render(<Sidebar isOpen={true} onClose={vi.fn()} />);
      expect(screen.queryByText('Manual Entry')).not.toBeInTheDocument();
      expect(screen.queryByText('Import Data')).not.toBeInTheDocument();
      expect(screen.queryByText('Incidents')).not.toBeInTheDocument();
      unmount();
    }
  });
});
