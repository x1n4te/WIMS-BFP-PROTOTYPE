'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { fetchRegionalIncident, type RegionalIncidentDetailResponse } from '@/lib/api';

function formatFieldValue(v: unknown): string {
  if (v === null || v === undefined) return '—';
  if (typeof v === 'object') return JSON.stringify(v, null, 2);
  return String(v);
}

function DetailBlock({
  title,
  sectionId,
  data,
}: {
  title: string;
  sectionId: string;
  data: Record<string, unknown>;
}) {
  const keys = Object.keys(data).sort();
  return (
    <section className="card" aria-labelledby={sectionId}>
      <div className="card-header">
        <h2 id={sectionId} className="font-bold">
          {title}
        </h2>
      </div>
      <div className="card-body space-y-2">
        {keys.length === 0 ? (
          <p className="text-sm text-gray-500">No rows returned for this block.</p>
        ) : (
          keys.map((k) => (
            <div
              key={k}
              className="grid grid-cols-1 gap-1 border-b border-gray-100 pb-3 text-sm last:border-0 md:grid-cols-3 md:gap-4"
            >
              <div className="font-medium text-gray-600">{k}</div>
              <div className="whitespace-pre-wrap break-words text-gray-900 md:col-span-2">
                {formatFieldValue(data[k])}
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

export default function RegionalIncidentDetailPage() {
  const router = useRouter();
  const params = useParams();
  const rawId = params?.id as string | undefined;
  const incidentId = rawId != null ? parseInt(rawId, 10) : NaN;

  const { user, loading: authLoading } = useAuth();
  const role = (user as { role?: string })?.role ?? null;

  const [detail, setDetail] = useState<RegionalIncidentDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && role !== 'REGIONAL_ENCODER') {
      router.replace('/dashboard');
    }
  }, [authLoading, role, router]);

  const load = useCallback(async () => {
    if (Number.isNaN(incidentId)) {
      setError('Invalid incident id.');
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRegionalIncident(incidentId);
      setDetail(data);
    } catch (e) {
      setDetail(null);
      setError(e instanceof Error ? e.message : 'Failed to load incident.');
    } finally {
      setLoading(false);
    }
  }, [incidentId]);

  useEffect(() => {
    if (authLoading || role !== 'REGIONAL_ENCODER') return;
    load();
  }, [authLoading, role, load]);

  if (authLoading || role !== 'REGIONAL_ENCODER') {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-gray-500">
        Loading…
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <Link
          href="/dashboard/regional"
          className="inline-flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden />
          Back to regional dashboard
        </Link>
      </div>

      {loading && (
        <div className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-8 text-center text-gray-600">
          Loading incident…
        </div>
      )}

      {!loading && error && (
        <div
          className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
          role="alert"
        >
          {error}
        </div>
      )}

      {!loading && !error && detail && (
        <>
          <div>
            <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
              Region incident #{detail.incident_id}
            </h1>
            <p className="mt-1 text-sm" style={{ color: 'var(--text-secondary)' }}>
              Verification:{' '}
              <span className="font-medium">{detail.verification_status}</span>
              {' · '}
              Region {detail.region_id}
              {detail.created_at && (
                <>
                  {' · '}
                  Created {new Date(detail.created_at).toLocaleString()}
                </>
              )}
            </p>
          </div>

          <DetailBlock
            sectionId="regional-incident-nonsensitive"
            title="Non-sensitive details (as returned)"
            data={detail.nonsensitive}
          />
          <DetailBlock
            sectionId="regional-incident-sensitive"
            title="Sensitive details (as returned)"
            data={detail.sensitive}
          />
        </>
      )}
    </div>
  );
}
