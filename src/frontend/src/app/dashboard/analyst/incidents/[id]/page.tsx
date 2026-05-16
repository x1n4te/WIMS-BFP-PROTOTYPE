'use client';

import { useCallback, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Download, ExternalLink, RefreshCw } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import {
  downloadAnalyticsExport,
  fetchAnalystIncidentDetail,
  queueAnalyticsExport,
  type AnalystIncidentDetailResponse,
} from '@/lib/api';

const ANALYST_ROLES = ['NATIONAL_ANALYST', 'SYSTEM_ADMIN'];
const DETAIL_EXPORT_COLUMNS = [
  'incident_id',
  'notification_dt',
  'region_id',
  'province_name',
  'municipality_name',
  'barangay_name',
  'alarm_level',
  'general_category',
  'sub_category',
  'estimated_damage_php',
  'total_response_time_minutes',
  'fire_origin',
  'extent_of_damage',
  'structures_affected',
  'households_affected',
  'individuals_affected',
  'vehicles_affected',
  'civilian_injured',
  'civilian_deaths',
  'firefighter_injured',
  'firefighter_deaths',
];

function formatDateTime(value: string | null): string {
  if (!value) return 'N/A';
  return new Date(value).toLocaleString();
}

function formatMoney(value: number | null): string {
  if (value == null) return 'N/A';
  return new Intl.NumberFormat('en-PH', {
    style: 'currency',
    currency: 'PHP',
    maximumFractionDigits: 0,
  }).format(value);
}

function formatMinutes(value: number | null): string {
  if (value == null) return 'N/A';
  return `${Number(value).toFixed(1)} min`;
}

function FieldRow({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="grid grid-cols-1 gap-1 border-b border-gray-100 py-3 text-sm last:border-0 md:grid-cols-3 md:gap-4">
      <dt className="font-medium text-gray-500">{label}</dt>
      <dd className="break-words text-gray-900 md:col-span-2">{value == null || value === '' ? 'N/A' : String(value)}</dd>
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="card">
      <div className="card-header">{title}</div>
      <dl className="card-body">{children}</dl>
    </section>
  );
}

export default function AnalystIncidentDetailPage() {
  const router = useRouter();
  const params = useParams();
  const rawId = params?.id as string | undefined;
  const incidentId = rawId != null ? parseInt(rawId, 10) : NaN;
  const { user, loading: authLoading } = useAuth();
  const role = (user as { role?: string })?.role ?? null;
  const canAccess = ANALYST_ROLES.includes(role ?? '');

  const [detail, setDetail] = useState<AnalystIncidentDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exportTask, setExportTask] = useState<{ taskId: string; format: 'csv' | 'pdf' } | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [exportLoading, setExportLoading] = useState<'csv' | 'pdf' | 'download' | null>(null);

  useEffect(() => {
    if (!authLoading && role && !canAccess) {
      router.replace('/dashboard');
    }
  }, [authLoading, canAccess, role, router]);

  const load = useCallback(async () => {
    if (Number.isNaN(incidentId)) {
      setError('Invalid incident id.');
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setDetail(await fetchAnalystIncidentDetail(incidentId));
    } catch (e) {
      setDetail(null);
      setError(e instanceof Error ? e.message : 'Failed to load incident.');
    } finally {
      setLoading(false);
    }
  }, [incidentId]);

  useEffect(() => {
    if (authLoading || !canAccess) return;
    void load();
  }, [authLoading, canAccess, load]);

  const queueExport = async (format: 'csv' | 'pdf') => {
    setExportError(null);
    setExportLoading(format);
    try {
      const response = await queueAnalyticsExport({
        format,
        filters: { incident_id: incidentId },
        columns: DETAIL_EXPORT_COLUMNS,
      });
      setExportTask({ taskId: response.task_id, format });
    } catch (e) {
      setExportError(e instanceof Error ? e.message : 'Failed to queue export.');
    } finally {
      setExportLoading(null);
    }
  };

  const downloadQueuedExport = async () => {
    if (!exportTask) return;
    setExportError(null);
    setExportLoading('download');
    try {
      const blob = await downloadAnalyticsExport(exportTask.taskId);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `incident-${incidentId}.${exportTask.format}`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setExportError(e instanceof Error ? e.message : 'Export is not ready yet.');
    } finally {
      setExportLoading(null);
    }
  };

  if (authLoading || loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-gray-500">
        <RefreshCw className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  if (role && !canAccess) {
    return <div className="text-sm text-gray-500">Redirecting...</div>;
  }

  if (error || !detail) {
    return (
      <div className="space-y-4">
        <Link href="/dashboard/analyst" className="inline-flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900">
          <ArrowLeft className="h-4 w-4" />
          Back to analyst dashboard
        </Link>
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error || 'Incident not found.'}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <Link href="/dashboard/analyst" className="mb-3 inline-flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900">
            <ArrowLeft className="h-4 w-4" />
            Back to analyst dashboard
          </Link>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="font-mono text-2xl font-bold text-gray-900">
              {detail.reference_number || `Incident #${detail.incident_id}`}
            </h1>
            <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-semibold uppercase text-green-700">
              {detail.verification_status}
            </span>
          </div>
          <p className="mt-1 text-sm text-gray-500">
            Verified incident detail for national analytics review.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          {detail.has_wildland_afor && (
            <Link
              href={`/dashboard/analyst/incidents/${detail.incident_id}/wildland`}
              className="inline-flex items-center gap-2 rounded-md border border-orange-200 bg-orange-50 px-3 py-2 text-sm font-semibold text-orange-800 hover:bg-orange-100"
            >
              Wildland Detail
              <ExternalLink className="h-4 w-4" />
            </Link>
          )}
          <button
            type="button"
            onClick={() => void queueExport('pdf')}
            disabled={exportLoading !== null}
            className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
            style={{ backgroundColor: 'var(--bfp-maroon)' }}
          >
            <Download className="h-4 w-4" />
            Export PDF
          </button>
          <button
            type="button"
            onClick={() => void queueExport('csv')}
            disabled={exportLoading !== null}
            className="inline-flex items-center gap-2 rounded-md border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-800 disabled:opacity-60"
          >
            <Download className="h-4 w-4" />
            Export CSV
          </button>
        </div>
      </div>

      {(exportTask || exportError) && (
        <div className={`rounded-md border px-4 py-3 text-sm ${exportError ? 'border-red-200 bg-red-50 text-red-700' : 'border-blue-200 bg-blue-50 text-blue-800'}`}>
          {exportError ? (
            exportError
          ) : (
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <span>Export queued: {exportTask?.taskId}</span>
              <button
                type="button"
                onClick={() => void downloadQueuedExport()}
                disabled={exportLoading !== null}
                className="rounded-md bg-blue-700 px-3 py-1.5 font-semibold text-white disabled:opacity-60"
              >
                Download
              </button>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Section title="Incident Summary">
          <FieldRow label="Notification Date/Time" value={formatDateTime(detail.notification_dt)} />
          <FieldRow label="Region" value={detail.region} />
          <FieldRow label="Province" value={detail.province_name} />
          <FieldRow label="Municipality" value={detail.municipality_name} />
          <FieldRow label="Barangay" value={detail.barangay_name} />
        </Section>

        <Section title="Classification">
          <FieldRow label="General Category" value={detail.general_category} />
          <FieldRow label="Sub Category" value={detail.sub_category} />
          <FieldRow label="Alarm Level" value={detail.alarm_level} />
          <FieldRow label="Casualty Severity" value={detail.casualty_severity} />
        </Section>

        <Section title="Impact And Response">
          <FieldRow label="Estimated Damage" value={formatMoney(detail.estimated_damage_php)} />
          <FieldRow label="Total Response Time" value={formatMinutes(detail.total_response_time_minutes)} />
          <FieldRow label="Analytics Sync Status" value={detail.sync_status} />
        </Section>

        <Section title="Provenance">
          <FieldRow label="Reference Number" value={detail.reference_number} />
          <FieldRow label="Encoder ID" value={detail.encoder_id} />
          <FieldRow label="Encoder Username" value={detail.encoder_username} />
          <FieldRow label="Created At" value={formatDateTime(detail.created_at)} />
          <FieldRow label="Data Hash" value={detail.data_hash} />
        </Section>
      </div>
    </div>
  );
}
