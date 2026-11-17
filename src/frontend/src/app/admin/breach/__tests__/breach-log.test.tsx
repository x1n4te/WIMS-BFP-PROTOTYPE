/**
 * /admin/breach — manual "Log a Breach" form (turnover Phase 4).
 *
 * Module 10 no longer depends on the HITL confirm-threat flow: a SYSTEM_ADMIN records a breach
 * through POST /api/admin/breach and it appears in the register with the 72h NPC deadline.
 */
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useAuth } from '@/context/AuthContext';
import BreachNotificationsPage from '../page';

const NOW = new Date().toISOString();
const DEADLINE = new Date(Date.now() + 72 * 3600_000).toISOString();

const existing = {
  breach_id: 1,
  threat_log_id: 42,
  detected_at: NOW,
  npc_deadline_at: DEADLINE,
  status: 'DETECTED' as const,
  affected_systems: null,
  data_scope: null,
  notes: null,
  reported_by: null,
  npc_submitted_at: null,
  created_at: NOW,
  updated_at: NOW,
};

const created = {
  ...existing,
  breach_id: 7,
  threat_log_id: 99,
  affected_systems: 'Field laptop',
  data_scope: 'AFOR exports',
};

vi.mock('next/navigation', () => ({
  usePathname: () => '/admin/breach',
  useRouter: () => ({ replace: vi.fn() }),
}));

vi.mock('next/link', () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => <a href={href}>{children}</a>,
}));

const { createBreach, fetchBreachesOfflineAware, fetchAdminConfigOfflineAware } = vi.hoisted(() => ({
  createBreach: vi.fn(),
  fetchBreachesOfflineAware: vi.fn(),
  fetchAdminConfigOfflineAware: vi.fn(),
}));

vi.mock('@/lib/api/breach', () => ({ createBreach, updateBreach: vi.fn(), fetchBreaches: vi.fn() }));
vi.mock('@/lib/api/legacy', () => ({ updateAdminConfig: vi.fn() }));
vi.mock('@/lib/api/offlineAdmin', () => ({ fetchBreachesOfflineAware, fetchAdminConfigOfflineAware }));
vi.mock('@/context/AuthContext', () => ({ useAuth: vi.fn() }));

let online = true;
vi.mock('@/lib/useNetworkStatus', () => ({
  useNetworkStatus: () => ({ isOnline: online, isChecking: false, isReconnecting: false, state: online ? 'online' : 'offline' }),
}));

function asRole(role: string) {
  vi.mocked(useAuth).mockReturnValue({ user: { role } as never, loading: false, logout: vi.fn() } as never);
}

describe('Breach page — log a breach manually', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    online = true;
    asRole('SYSTEM_ADMIN');
    fetchBreachesOfflineAware.mockResolvedValue({ response: [existing], fromCache: false });
    fetchAdminConfigOfflineAware.mockResolvedValue({ response: [], fromCache: false });
  });

  it('opens the form, posts the breach and shows it in the register', async () => {
    createBreach.mockResolvedValue(created);
    const user = userEvent.setup();
    render(<BreachNotificationsPage />);

    await user.click(await screen.findByTestId('log-breach-button'));
    const form = screen.getByTestId('log-breach-form');
    await user.type(within(form).getByLabelText(/what happened/i), 'Staff laptop with exported AFOR data lost');
    await user.selectOptions(within(form).getByLabelText(/severity/i), 'CRITICAL');
    await user.type(within(form).getByLabelText(/affected systems/i), 'Field laptop');
    await user.type(within(form).getByLabelText(/data scope/i), 'AFOR exports');
    await user.click(within(form).getByRole('button', { name: /log breach/i }));

    await waitFor(() =>
      expect(createBreach).toHaveBeenCalledWith({
        summary: 'Staff laptop with exported AFOR data lost',
        severity: 'CRITICAL',
        affected_systems: 'Field laptop',
        data_scope: 'AFOR exports',
      }),
    );
    expect(await screen.findByTestId('success-banner')).toHaveTextContent('Breach #7 logged');
    expect(screen.queryByTestId('log-breach-form')).not.toBeInTheDocument();
    expect(screen.getByText('#7')).toBeInTheDocument();
    expect(screen.getByText('#1')).toBeInTheDocument();
  });

  it('sends detected_at as an ISO timestamp when provided', async () => {
    createBreach.mockResolvedValue(created);
    const user = userEvent.setup();
    render(<BreachNotificationsPage />);
    await user.click(await screen.findByTestId('log-breach-button'));
    const form = screen.getByTestId('log-breach-form');
    await user.type(within(form).getByLabelText(/what happened/i), 'Misdirected email with contact list');
    await user.type(within(form).getByLabelText(/detected at/i), '2026-06-10T08:30');
    await user.click(within(form).getByRole('button', { name: /log breach/i }));

    await waitFor(() => expect(createBreach).toHaveBeenCalled());
    const payload = createBreach.mock.calls[0][0];
    expect(payload.severity).toBe('HIGH');
    expect(new Date(payload.detected_at).toString()).not.toBe('Invalid Date');
    expect(payload.detected_at).toMatch(/Z$/);
  });

  it('keeps the form open and shows the error when the request fails', async () => {
    createBreach.mockRejectedValue(new Error('detected_at cannot be in the future'));
    const user = userEvent.setup();
    render(<BreachNotificationsPage />);
    await user.click(await screen.findByTestId('log-breach-button'));
    const form = screen.getByTestId('log-breach-form');
    await user.type(within(form).getByLabelText(/what happened/i), 'Portal data exposure');
    await user.click(within(form).getByRole('button', { name: /log breach/i }));

    expect(await screen.findByTestId('log-breach-error')).toHaveTextContent('detected_at cannot be in the future');
    expect(screen.getByTestId('log-breach-form')).toBeInTheDocument();
  });

  it('rejects a too-short description without calling the API', async () => {
    const user = userEvent.setup();
    render(<BreachNotificationsPage />);
    await user.click(await screen.findByTestId('log-breach-button'));
    const form = screen.getByTestId('log-breach-form');
    await user.type(within(form).getByLabelText(/what happened/i), 'ab');
    await user.click(within(form).getByRole('button', { name: /log breach/i }));
    expect(await screen.findByTestId('log-breach-error')).toBeInTheDocument();
    expect(createBreach).not.toHaveBeenCalled();
  });

  it('disables the button offline and hides it from non-admins', async () => {
    online = false;
    const { unmount } = render(<BreachNotificationsPage />);
    expect(await screen.findByTestId('log-breach-button')).toBeDisabled();
    unmount();

    online = true;
    asRole('NATIONAL_VALIDATOR');
    render(<BreachNotificationsPage />);
    expect(await screen.findByText(/restricted to system administrators/i)).toBeInTheDocument();
    expect(screen.queryByTestId('log-breach-button')).not.toBeInTheDocument();
  });
});
