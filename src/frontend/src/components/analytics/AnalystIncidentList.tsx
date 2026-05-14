'use client';

import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import Link from 'next/link';
import { ArrowDown, ArrowUp, ArrowUpDown, ExternalLink, X } from 'lucide-react';
import {
  fetchAnalystIncidentList,
  type AnalystIncidentListItem,
  type AnalystIncidentListParams,
  type AnalystListSortField,
  type SortDirection,
} from '@/lib/api';

const PAGE_SIZE = 25;

type Column = {
  key: AnalystListSortField;
  label: string;
  align?: 'left' | 'right';
  render: (incident: AnalystIncidentListItem) => ReactNode;
};

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

const COLUMNS: Column[] = [
  { key: 'notification_dt', label: 'Notification', render: (i) => formatDateTime(i.notification_dt) },
  { key: 'region', label: 'Region', render: (i) => i.region || 'N/A' },
  { key: 'municipality_name', label: 'Municipality', render: (i) => i.municipality_name || 'N/A' },
  { key: 'barangay_name', label: 'Barangay', render: (i) => i.barangay_name || 'N/A' },
  { key: 'general_category', label: 'Category', render: (i) => i.general_category || 'N/A' },
  { key: 'sub_category', label: 'Sub Category', render: (i) => i.sub_category || 'N/A' },
  { key: 'alarm_level', label: 'Alarm', render: (i) => i.alarm_level || 'N/A' },
  { key: 'estimated_damage_php', label: 'Damage', align: 'right', render: (i) => formatMoney(i.estimated_damage_php) },
  { key: 'total_response_time_minutes', label: 'Response', align: 'right', render: (i) => formatMinutes(i.total_response_time_minutes) },
];

function SortIcon({
  column,
  sortBy,
  sortDir,
}: {
  column: AnalystListSortField;
  sortBy: AnalystListSortField;
  sortDir: SortDirection;
}) {
  if (column !== sortBy) return <ArrowUpDown className="h-3.5 w-3.5 text-gray-400" />;
  return sortDir === 'asc'
    ? <ArrowUp className="h-3.5 w-3.5 text-red-700" />
    : <ArrowDown className="h-3.5 w-3.5 text-red-700" />;
}

function SummaryRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="grid grid-cols-3 gap-3 border-b border-gray-100 py-2 text-sm last:border-0">
      <dt className="font-medium text-gray-500">{label}</dt>
      <dd className="col-span-2 text-gray-900">{value || 'N/A'}</dd>
    </div>
  );
}

export function AnalystIncidentList({ filters }: { filters: AnalystIncidentListParams }) {
  const [items, setItems] = useState<AnalystIncidentListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState<AnalystListSortField>('notification_dt');
  const [sortDir, setSortDir] = useState<SortDirection>('desc');
  const [selected, setSelected] = useState<AnalystIncidentListItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const filterKey = useMemo(() => JSON.stringify(filters), [filters]);
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  useEffect(() => {
    setPage(1);
  }, [filterKey]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetchAnalystIncidentList({
          ...filters,
          page,
          page_size: PAGE_SIZE,
          sort_by: sortBy,
          sort_dir: sortDir,
        });
        if (cancelled) return;
        setItems(response.incidents);
        setTotal(response.total);
      } catch (e) {
        if (cancelled) return;
        setItems([]);
        setTotal(0);
        setError(e instanceof Error ? e.message : 'Failed to load incidents.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [filterKey, filters, page, sortBy, sortDir]);

  const toggleSort = (column: AnalystListSortField) => {
    if (column === sortBy) {
      setSortDir((current) => current === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortDir(column === 'notification_dt' ? 'desc' : 'asc');
    }
    setPage(1);
  };

  return (
    <section className="card" aria-labelledby="incident-list-heading">
      <div className="card-header flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 id="incident-list-heading" className="font-bold">Incident List</h2>
          <p className="text-xs font-normal text-gray-500">Verified, non-archived incidents matching the active filters.</p>
        </div>
        <span className="text-xs font-semibold text-gray-500">{total.toLocaleString()} total</span>
      </div>

      <div className="card-body p-0">
        {error && (
          <div className="border-b border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="min-w-[1080px] w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                {COLUMNS.map((column) => (
                  <th
                    key={column.key}
                    className={`border-b border-gray-200 px-3 py-2 text-xs font-semibold uppercase text-gray-600 ${column.align === 'right' ? 'text-right' : 'text-left'}`}
                  >
                    <button
                      type="button"
                      onClick={() => toggleSort(column.key)}
                      className={`inline-flex items-center gap-1 ${column.align === 'right' ? 'justify-end' : 'justify-start'} w-full hover:text-red-700`}
                    >
                      <span>{column.label}</span>
                      <SortIcon column={column.key} sortBy={sortBy} sortDir={sortDir} />
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td colSpan={COLUMNS.length} className="px-4 py-8 text-center text-gray-500">
                    Loading incidents...
                  </td>
                </tr>
              )}
              {!loading && items.length === 0 && (
                <tr>
                  <td colSpan={COLUMNS.length} className="px-4 py-8 text-center text-gray-500">
                    No verified incidents match the active filters.
                  </td>
                </tr>
              )}
              {!loading && items.map((incident) => (
                <tr
                  key={incident.incident_id}
                  onClick={() => setSelected(incident)}
                  className="cursor-pointer border-b border-gray-100 hover:bg-red-50/50"
                >
                  {COLUMNS.map((column) => (
                    <td
                      key={column.key}
                      className={`px-3 py-3 align-top ${column.align === 'right' ? 'text-right' : 'text-left'}`}
                    >
                      {column.render(incident)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex flex-col gap-3 border-t border-gray-200 px-4 py-3 text-sm sm:flex-row sm:items-center sm:justify-between">
          <span className="text-gray-500">
            Page {page} of {pageCount}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              disabled={page <= 1 || loading}
              className="rounded-md border border-gray-200 px-3 py-1.5 font-medium text-gray-700 disabled:opacity-50"
            >
              Previous
            </button>
            <button
              type="button"
              onClick={() => setPage((current) => Math.min(pageCount, current + 1))}
              disabled={page >= pageCount || loading}
              className="rounded-md border border-gray-200 px-3 py-1.5 font-medium text-gray-700 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {selected && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/30" role="dialog" aria-modal="true">
          <div className="flex h-full w-full max-w-[640px] flex-col bg-white shadow-xl">
            <div className="flex items-start justify-between gap-4 border-b border-gray-200 px-5 py-4">
              <div>
                <h3 className="font-mono text-lg font-bold text-gray-900">
                  {selected.reference_number || `Incident #${selected.incident_id}`}
                </h3>
                <p className="mt-1 text-sm text-gray-500">{formatDateTime(selected.notification_dt)}</p>
              </div>
              <button
                type="button"
                onClick={() => setSelected(null)}
                className="rounded-md p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-900"
                aria-label="Close incident summary"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-5 py-4">
              <dl>
                <SummaryRow label="Region" value={selected.region} />
                <SummaryRow label="Province" value={selected.province_name} />
                <SummaryRow label="Municipality" value={selected.municipality_name} />
                <SummaryRow label="Barangay" value={selected.barangay_name} />
                <SummaryRow label="Category" value={selected.general_category} />
                <SummaryRow label="Sub Category" value={selected.sub_category} />
                <SummaryRow label="Alarm Level" value={selected.alarm_level} />
                <SummaryRow label="Damage" value={formatMoney(selected.estimated_damage_php)} />
                <SummaryRow label="Response Time" value={formatMinutes(selected.total_response_time_minutes)} />
                <SummaryRow label="Status" value={selected.verification_status} />
                <SummaryRow label="Created" value={formatDateTime(selected.created_at)} />
              </dl>
            </div>

            <div className="border-t border-gray-200 px-5 py-4">
              <Link
                href={`/dashboard/analyst/incidents/${selected.incident_id}`}
                className="inline-flex w-full items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-semibold text-white"
                style={{ backgroundColor: 'var(--bfp-maroon)' }}
              >
                Open Full Page
                <ExternalLink className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
