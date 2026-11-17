/**
 * Tests for Task 3: validator API abstraction — fetchOperationalMap + fetchValidatorAuditLogs.
 *
 * Mocks `../transport` (the module that provides `apiFetch`) so calls to the
 * real fetch never execute. Asserts URL shape matches the inline patterns in
 * the validator pages verbatim.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../transport', () => ({ apiFetch: vi.fn() }));
import { apiFetch } from '../transport';
import {
  type AuditResponse,
  fetchValidatorAuditLogs,
} from '../validator';

describe('validator API functions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchValidatorAuditLogs builds URLSearchParams and calls apiFetch', async () => {
    const mockResponse: AuditResponse = {
      items: [
        {
          history_id: 1,
          incident_id: 42,
          region_id: 13,
          region_display: 'Region 13',
          action_by_user_id: 'u1',
          actor_username: 'jdoe',
          previous_status: 'PENDING',
          new_status: 'APPROVED',
          action_label: 'Approved',
          notes: null,
          action_timestamp: '2025-06-01T00:00:00Z',
        },
      ],
      total: 1,
      limit: 50,
      offset: 0,
    };
    (apiFetch as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse);

    const result = await fetchValidatorAuditLogs({
      dateFrom: '2025-01-01',
      dateTo: '2025-12-31',
      regionId: '13',
      actorUsername: 'jdoe',
      roleFilter: 'NATIONAL_VALIDATOR',
      action: 'APPROVED',
      page: 0,
      pageSize: 50,
    });

    expect(apiFetch).toHaveBeenCalledTimes(1);
    const callUrl = (apiFetch as ReturnType<typeof vi.fn>).mock.calls[0][0] as string;
    expect(callUrl).toContain('/regional/validator/audit-logs?');
    expect(callUrl).toContain('date_from=');
    expect(callUrl).toContain('date_to=');
    expect(callUrl).toContain('region_id=');
    expect(callUrl).toContain('actor_username=');
    expect(callUrl).toContain('role=');
    expect(callUrl).toContain('action=');
    expect(callUrl).toContain('limit=');
    expect(callUrl).toContain('offset=');
    expect(result).toEqual(mockResponse);
  });
});
