/**
 * AFOR import page — SYSTEM_ADMIN region selection (turnover Phase 2).
 *
 * Admins have no assigned region: the region comes from a dropdown that is
 * pre-selected from the region printed on the file. A mismatch warns but is allowed.
 * Encoders keep the existing behaviour (no dropdown, assigned region wins).
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AforImportPage from '../page';

const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, replace: vi.fn() }),
  useSearchParams: () => ({ get: () => null }),
}));

const mockUseAuth = vi.fn();
vi.mock('@/context/AuthContext', () => ({ useAuth: () => mockUseAuth() }));

vi.mock('@/lib/useNetworkStatus', () => ({
  useNetworkStatus: () => ({ isOnline: true, isReconnecting: false }),
}));

const { importAforFile, detectAforRegion, commitAforImport } = vi.hoisted(() => ({
  importAforFile: vi.fn(),
  detectAforRegion: vi.fn(),
  commitAforImport: vi.fn(),
}));
vi.mock('@/lib/api', () => ({
  importAforFile,
  detectAforRegion,
  commitAforImport,
  submitIncidentForReview: vi.fn(),
}));

vi.mock('@/lib/offlineStore', () => ({ queueOfflineOp: vi.fn() }));
vi.mock('@/lib/geocode', () => ({ searchGeocode: vi.fn().mockResolvedValue([]) }));
vi.mock('@/lib/connectivity', () => ({ markConnectivityOffline: vi.fn() }));
vi.mock('@/components/MapPicker', () => ({ MapPicker: () => null }));
vi.mock('@/components/DuplicateResolutionModal', () => ({ DuplicateResolutionModal: () => null }));
vi.mock('@/components/SectionDotNav', () => ({ SectionDotNav: () => null }));

function authAs(role: string, assignedRegionId: number | null = null) {
  mockUseAuth.mockReturnValue({
    user: { id: 'u1', role, assignedRegionId },
    loading: false,
    loggingOut: false,
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
    refreshSession: vi.fn(),
  });
}

const PREVIEW = {
  total_rows: 1,
  valid_rows: 1,
  invalid_rows: 0,
  form_kind: 'STRUCTURAL_AFOR' as const,
  requires_location: false,
  region_id: 1,
  file_region_text: 'Region III - Central Luzon',
  region_mismatch: true,
  rows: [
    {
      row_index: 0,
      status: 'VALID',
      errors: [],
      data: { _form_kind: 'STRUCTURAL_AFOR', _city_text: 'Angeles' },
    },
  ],
};

async function pickFile() {
  const user = userEvent.setup();
  const input = document.getElementById('file-upload') as HTMLInputElement;
  const file = new File(['x'], 'afor.xlsx', {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
  await user.upload(input, file);
  return { user, file };
}

describe('AFOR import page — SYSTEM_ADMIN region selection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });
  afterEach(() => sessionStorage.clear());

  it('pre-selects the region detected from the file and imports with it', async () => {
    authAs('SYSTEM_ADMIN');
    detectAforRegion.mockResolvedValue({
      file_region_text: 'Region III - Central Luzon',
      suggested_region_id: 5,
    });
    importAforFile.mockResolvedValue({ ...PREVIEW, region_id: 5, region_mismatch: false });
    render(<AforImportPage />);

    const { user, file } = await pickFile();
    const select = (await screen.findByLabelText(/region for this import/i)) as HTMLSelectElement;
    await waitFor(() => expect(select.value).toBe('5'));
    expect(detectAforRegion).toHaveBeenCalledWith(file);

    await user.click(screen.getByRole('button', { name: /analyze file/i }));
    await waitFor(() => expect(importAforFile).toHaveBeenCalledWith(file, 5));
    // Admins stay on the batch preview/commit path (no redirect to the manual form).
    expect(mockPush).not.toHaveBeenCalledWith('/afor/create?from=import');
  });

  it('blocks analysis until a region is chosen when the file has none', async () => {
    authAs('SYSTEM_ADMIN');
    detectAforRegion.mockResolvedValue({ file_region_text: null, suggested_region_id: null });
    render(<AforImportPage />);

    const { user } = await pickFile();
    const analyze = await screen.findByRole('button', { name: /analyze file/i });
    expect(analyze).toBeDisabled();
    await waitFor(() =>
      expect(screen.getByText(/no region found in the file/i)).toBeInTheDocument(),
    );

    await user.selectOptions(screen.getByLabelText(/region for this import/i), '3');
    expect(analyze).toBeEnabled();
  });

  it('warns on a region mismatch but still allows the commit, sending the chosen region', async () => {
    authAs('SYSTEM_ADMIN');
    detectAforRegion.mockResolvedValue({
      file_region_text: 'Region III - Central Luzon',
      suggested_region_id: 5,
    });
    // Admin overrode the suggestion: chosen region 1, while the file says Region III.
    importAforFile.mockResolvedValue(PREVIEW);
    commitAforImport.mockResolvedValue({
      status: 'ok',
      batch_id: 1,
      incident_ids: [7],
      total_committed: 1,
    });
    render(<AforImportPage />);

    const { user } = await pickFile();
    await user.selectOptions(await screen.findByLabelText(/region for this import/i), '1');
    await user.click(screen.getByRole('button', { name: /analyze file/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /differs from the region on the file/i,
    );

    await user.click(screen.getByRole('button', { name: /commit 1 valid row/i }));
    await waitFor(() =>
      expect(commitAforImport).toHaveBeenCalledWith(
        expect.any(Array),
        'STRUCTURAL_AFOR',
        expect.objectContaining({ regionId: 1 }),
      ),
    );
    expect(await screen.findByText(/saved as draft/i)).toBeInTheDocument();
  });

  it('does not show the region dropdown to encoders and imports without a region', async () => {
    authAs('REGIONAL_ENCODER', 1);
    importAforFile.mockResolvedValue({ ...PREVIEW, valid_rows: 0, invalid_rows: 1, rows: [] });
    render(<AforImportPage />);

    const { user, file } = await pickFile();
    expect(screen.queryByLabelText(/region for this import/i)).not.toBeInTheDocument();
    expect(detectAforRegion).not.toHaveBeenCalled();

    await user.click(screen.getByRole('button', { name: /analyze file/i }));
    await waitFor(() => expect(importAforFile).toHaveBeenCalledWith(file, undefined));
  });
});
