import type { AnalystIncidentListParams } from '@/lib/api';

export type AnalystWorkflowSlug =
  | 'comparative'
  | 'heatmap'
  | 'trends'
  | 'response-time'
  | 'top-n'
  | 'incident-explorer';

export interface AnalystWorkflowTransferPayload {
  filters: AnalystIncidentListParams;
  selectedIncidentIds?: number[];
  createdAt: string;
}

const TRANSFER_PREFIX = 'analyst-workflow-transfer:';

function createTransferId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export function createAnalystWorkflowTransferUrl(
  workflow: AnalystWorkflowSlug,
  payload: Omit<AnalystWorkflowTransferPayload, 'createdAt'>,
): string {
  if (typeof window === 'undefined') {
    return `/dashboard/analyst/${workflow}`;
  }
  const transferId = createTransferId();
  const storedPayload: AnalystWorkflowTransferPayload = {
    ...payload,
    createdAt: new Date().toISOString(),
  };
  window.sessionStorage.setItem(`${TRANSFER_PREFIX}${transferId}`, JSON.stringify(storedPayload));
  return `/dashboard/analyst/${workflow}?transfer=${encodeURIComponent(transferId)}`;
}

export function readAnalystWorkflowTransfer(
  transferId: string | null,
): AnalystWorkflowTransferPayload | null {
  if (!transferId || typeof window === 'undefined') return null;
  const raw = window.sessionStorage.getItem(`${TRANSFER_PREFIX}${transferId}`);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<AnalystWorkflowTransferPayload>;
    return {
      filters: parsed.filters ?? {},
      selectedIncidentIds: Array.isArray(parsed.selectedIncidentIds)
        ? parsed.selectedIncidentIds.filter((id): id is number => typeof id === 'number')
        : [],
      createdAt: typeof parsed.createdAt === 'string' ? parsed.createdAt : new Date().toISOString(),
    };
  } catch {
    return null;
  }
}
