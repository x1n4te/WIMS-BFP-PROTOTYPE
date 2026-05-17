"use client";

import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  ChevronDown,
  ChevronRight,
  Download,
  Eye,
  EyeOff,
  Lock,
  RefreshCw,
  ShieldAlert,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import {
  downloadAnalyticsExport,
  fetchAnalystIncidentDetail,
  fetchAnalystIncidentSensitive,
  queueAnalyticsExport,
  type AnalystIncidentDetailResponse,
  type AnalystIncidentSensitiveResponse,
} from "@/lib/api";

const ANALYST_ROLES = ["NATIONAL_ANALYST", "SYSTEM_ADMIN"];
const DETAIL_EXPORT_COLUMNS = [
  "incident_id",
  "notification_dt",
  "province_name",
  "municipality_name",
  "alarm_level",
  "general_category",
  "sub_category",
  "estimated_damage_php",
  "total_response_time_minutes",
  "fire_origin",
  "extent_of_damage",
  "structures_affected",
  "households_affected",
  "families_affected",
  "individuals_affected",
  "vehicles_affected",
];

// ─── Formatters ───────────────────────────────────────────────────────────────

function formatDateTime(value: string | null): string {
  if (!value) return "N/A";
  return new Date(value).toLocaleString("en-PH", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function formatMoney(value: number | null): string {
  if (value == null) return "N/A";
  return new Intl.NumberFormat("en-PH", {
    style: "currency",
    currency: "PHP",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatMinutes(value: number | null): string {
  if (value == null) return "N/A";
  return `${Number(value).toFixed(1)} min`;
}

// ─── Sub-components ───────────────────────────────────────────────────────────

interface CollapsibleSectionProps {
  title: string;
  children: ReactNode;
  defaultOpen?: boolean;
  badge?: string;
  locked?: boolean;
}

function CollapsibleSection({
  title,
  children,
  defaultOpen = false,
  badge,
  locked = false,
}: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <button
        type="button"
        onClick={() => !locked && setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-semibold text-gray-800 hover:bg-gray-50 disabled:cursor-not-allowed"
      >
        <span className="flex items-center gap-2">
          {locked && <Lock className="h-4 w-4 text-gray-400" />}
          {title}
          {badge && (
            <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600">
              {badge}
            </span>
          )}
        </span>
        {!locked &&
          (open ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          ))}
      </button>
      {open && !locked && (
        <div className="border-t border-gray-100 px-4 py-4">{children}</div>
      )}
    </div>
  );
}

interface FieldRowProps {
  label: string;
  value: unknown;
}

function FieldRow({ label, value }: FieldRowProps) {
  return (
    <div className="grid grid-cols-1 gap-1 border-b border-gray-100 py-2.5 text-sm last:border-0 md:grid-cols-3 md:gap-4">
      <dt className="font-medium text-gray-500">{label}</dt>
      <dd className="break-words text-gray-900 md:col-span-2">
        {value == null || value === "" ? "N/A" : String(value)}
      </dd>
    </div>
  );
}

interface BlurredRowProps {
  label: string;
  fieldKey: string;
  value: string | null;
  revealed: Set<string>;
  onReveal: (key: string) => void;
}

function BlurredRow({
  label,
  fieldKey,
  value,
  revealed,
  onReveal,
}: BlurredRowProps) {
  const isRevealed = revealed.has(fieldKey);
  return (
    <div className="grid grid-cols-1 gap-1 border-b border-gray-100 py-2.5 text-sm last:border-0 md:grid-cols-3 md:gap-4">
      <dt className="font-medium text-gray-500">{label}</dt>
      <dd className="flex items-center gap-2 md:col-span-2">
        {value == null || value === "" ? (
          <span className="text-gray-400">N/A</span>
        ) : isRevealed ? (
          <span className="text-gray-900">{value}</span>
        ) : (
          <span className="relative flex items-center gap-2">
            <span className="blur-sm contrast-75 select-none">{value}</span>
            <button
              type="button"
              onClick={() => onReveal(fieldKey)}
              className="ml-1 rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
              title="Reveal"
            >
              <Eye className="h-4 w-4" />
            </button>
          </span>
        )}
      </dd>
    </div>
  );
}

interface AlarmTimelineTableProps {
  rows: Array<{ alarm_level: string; time: string; commander: string }>;
  revealed: Set<string>;
  timelineKey: string;
}

function AlarmTimelineTable({
  rows,
  revealed,
  timelineKey,
}: AlarmTimelineTableProps) {
  const isRevealed = revealed.has(timelineKey);
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-xs">
        <thead>
          <tr className="border-b border-gray-200 text-left text-gray-500">
            <th className="pb-2 pr-4 font-medium">Alarm Level</th>
            <th className="pb-2 pr-4 font-medium">Time</th>
            <th className="pb-2 font-medium">Commander</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b border-gray-100 last:border-0">
              <td className="py-1.5 pr-4 text-gray-900">{row.alarm_level}</td>
              <td className="py-1.5 pr-4">
                {isRevealed ? (
                  row.time
                ) : (
                  <span className="blur-sm contrast-75 select-none">
                    {row.time}
                  </span>
                )}
              </td>
              <td className="py-1.5">
                {isRevealed ? (
                  row.commander
                ) : (
                  <span className="blur-sm contrast-75 select-none">
                    {row.commander}
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Wildland Section ─────────────────────────────────────────────────────────

interface WildlandSectionProps {
  detail: AnalystIncidentDetailResponse;
}

function WildlandSection({ detail }: WildlandSectionProps) {
  const isWildland = detail.form_kind === "WILDLAND_AFOR";

  return (
    <CollapsibleSection
      title="Wildland Data"
      locked={!isWildland}
      badge={isWildland ? "AFOR" : undefined}
    >
      {isWildland && detail.wildland ? (
        <div className="space-y-4">
          {Object.entries(detail.wildland).map(([key, val]) => (
            <FieldRow
              key={key}
              label={key
                .replace(/_/g, " ")
                .replace(/\b\w/g, (c) => c.toUpperCase())}
              value={val}
            />
          ))}
          {detail.alarm_statuses && detail.alarm_statuses.length > 0 && (
            <div className="mt-4">
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                Alarm Statuses
              </h4>
              <table className="min-w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-gray-500">
                    <th className="pb-2 pr-4 font-medium">#</th>
                    <th className="pb-2 pr-4 font-medium">Alarm Status</th>
                    <th className="pb-2 pr-4 font-medium">Time Declared</th>
                    <th className="pb-2 font-medium">Ground Commander</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.alarm_statuses.map((row) => (
                    <tr
                      key={row.sort_order}
                      className="border-b border-gray-100 last:border-0"
                    >
                      <td className="py-1.5 pr-4 text-gray-600">
                        {row.sort_order}
                      </td>
                      <td className="py-1.5 pr-4 text-gray-900">
                        {row.alarm_status}
                      </td>
                      <td className="py-1.5 pr-4 text-gray-900">
                        {row.time_declared ?? "N/A"}
                      </td>
                      <td className="py-1.5 text-gray-900">
                        {row.ground_commander ?? "N/A"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {detail.assistance_rows && detail.assistance_rows.length > 0 && (
            <div className="mt-4">
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                Assistance / Mutual Aid
              </h4>
              <table className="min-w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-gray-500">
                    <th className="pb-2 pr-4 font-medium">#</th>
                    <th className="pb-2 pr-4 font-medium">
                      Organization / Unit
                    </th>
                    <th className="pb-2 font-medium">Detail</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.assistance_rows.map((row) => (
                    <tr
                      key={row.sort_order}
                      className="border-b border-gray-100 last:border-0"
                    >
                      <td className="py-1.5 pr-4 text-gray-600">
                        {row.sort_order}
                      </td>
                      <td className="py-1.5 pr-4 text-gray-900">
                        {row.organization_or_unit}
                      </td>
                      <td className="py-1.5 text-gray-900">
                        {row.detail ?? "N/A"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        <p className="text-sm text-gray-500 italic">
          Wildland data not applicable for structural incidents.
        </p>
      )}
    </CollapsibleSection>
  );
}

// ─── Sensitive Data Section ───────────────────────────────────────────────────

interface SensitiveSectionProps {
  incidentId: number;
}

function SensitiveSection({ incidentId }: SensitiveSectionProps) {
  const [sensitiveData, setSensitiveData] =
    useState<AnalystIncidentSensitiveResponse | null>(null);
  const [sensitiveLoading, setSensitiveLoading] = useState(false);
  const [sensitiveError, setSensitiveError] = useState<string | null>(null);
  const [revealed, setRevealed] = useState<Set<string>>(new Set());

  const loadSensitive = useCallback(async () => {
    setSensitiveLoading(true);
    setSensitiveError(null);
    try {
      const data = await fetchAnalystIncidentSensitive(incidentId);
      setSensitiveData(data);
    } catch (e) {
      setSensitiveError(
        e instanceof Error
          ? e.message
          : "Failed to load protected information.",
      );
    } finally {
      setSensitiveLoading(false);
    }
  }, [incidentId]);

  const reveal = useCallback((key: string) => {
    setRevealed((prev) => new Set([...prev, key]));
  }, []);

  if (!sensitiveData && !sensitiveLoading) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50">
        <div className="flex flex-col items-center justify-center px-4 py-6 text-center">
          <ShieldAlert className="mb-2 h-6 w-6 text-amber-600" />
          <p className="mb-3 text-sm font-medium text-amber-800">
            Protected Information
          </p>
          <p className="mb-4 max-w-xs text-xs text-amber-700">
            This section contains sensitive personal and incident data. Access
            is logged.
          </p>
          <button
            type="button"
            onClick={() => void loadSensitive()}
            className="inline-flex items-center gap-2 rounded-md border border-amber-300 bg-white px-4 py-2 text-sm font-semibold text-amber-800 shadow-sm hover:bg-amber-100"
          >
            <Eye className="h-4 w-4" />
            Reveal Protected Information
          </button>
          {sensitiveError && (
            <p className="mt-3 text-xs text-red-600">{sensitiveError}</p>
          )}
        </div>
      </div>
    );
  }

  if (sensitiveLoading) {
    return (
      <div className="flex items-center justify-center rounded-lg border border-amber-200 bg-amber-50 px-4 py-8">
        <RefreshCw className="h-5 w-5 animate-spin text-amber-600" />
        <span className="ml-2 text-sm text-amber-700">
          Loading protected data...
        </span>
      </div>
    );
  }

  if (!sensitiveData) return null;

  const allRevealed = revealed.size > 0;

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50">
      <div className="border-b border-amber-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-amber-600" />
            <span className="text-sm font-semibold text-amber-800">
              Protected Information
            </span>
          </div>
          {allRevealed && (
            <button
              type="button"
              onClick={() => setRevealed(new Set())}
              className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-amber-600 hover:bg-amber-100"
            >
              <EyeOff className="h-3 w-3" />
              Hide All
            </button>
          )}
        </div>
      </div>
      <div className="bg-white">
        <dl className="px-4 py-2">
          <BlurredRow
            label="Caller Name"
            fieldKey="caller_name"
            value={sensitiveData.caller_name}
            revealed={revealed}
            onReveal={reveal}
          />
          <BlurredRow
            label="Caller Number"
            fieldKey="caller_number"
            value={sensitiveData.caller_number}
            revealed={revealed}
            onReveal={reveal}
          />
          <BlurredRow
            label="Owner Name"
            fieldKey="owner_name"
            value={sensitiveData.owner_name}
            revealed={revealed}
            onReveal={reveal}
          />
          <BlurredRow
            label="Establishment Name"
            fieldKey="establishment_name"
            value={sensitiveData.establishment_name}
            revealed={revealed}
            onReveal={reveal}
          />
          <BlurredRow
            label="Occupant Name"
            fieldKey="occupant_name"
            value={sensitiveData.occupant_name}
            revealed={revealed}
            onReveal={reveal}
          />
          <BlurredRow
            label="Fire Origin"
            fieldKey="fire_origin"
            value={sensitiveData.fire_origin}
            revealed={revealed}
            onReveal={reveal}
          />
          <BlurredRow
            label="Extent of Damage"
            fieldKey="extent_of_damage"
            value={sensitiveData.extent_of_damage}
            revealed={revealed}
            onReveal={reveal}
          />
          <BlurredRow
            label="Prepared By Officer"
            fieldKey="prepared_by_officer"
            value={sensitiveData.prepared_by_officer}
            revealed={revealed}
            onReveal={reveal}
          />
          <BlurredRow
            label="Noted By Officer"
            fieldKey="noted_by_officer"
            value={sensitiveData.noted_by_officer}
            revealed={revealed}
            onReveal={reveal}
          />
          <BlurredRow
            label="Disposition"
            fieldKey="disposition"
            value={sensitiveData.disposition}
            revealed={revealed}
            onReveal={reveal}
          />
          <BlurredRow
            label="Narrative Report"
            fieldKey="narrative_report"
            value={sensitiveData.narrative_report}
            revealed={revealed}
            onReveal={reveal}
          />
        </dl>

        {sensitiveData.alarm_timeline &&
          sensitiveData.alarm_timeline.length > 0 && (
            <div className="border-t border-gray-100 px-4 py-3">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs font-medium text-gray-500">
                  Alarm Timeline
                </span>
                <button
                  type="button"
                  onClick={() => reveal("alarm_timeline")}
                  disabled={revealed.has("alarm_timeline")}
                  className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-gray-500 hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Eye className="h-3 w-3" />
                  {revealed.has("alarm_timeline") ? "Revealed" : "Reveal"}
                </button>
              </div>
              <AlarmTimelineTable
                rows={sensitiveData.alarm_timeline}
                revealed={revealed}
                timelineKey="alarm_timeline"
              />
            </div>
          )}
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function AnalystIncidentDetailPage() {
  const router = useRouter();
  const params = useParams();
  const rawId = params?.id as string | undefined;
  const incidentId = rawId != null ? parseInt(rawId, 10) : NaN;
  const { user, loading: authLoading } = useAuth();
  const role = (user as { role?: string })?.role ?? null;
  const canAccess = ANALYST_ROLES.includes(role ?? "");

  const [detail, setDetail] = useState<AnalystIncidentDetailResponse | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exportTask, setExportTask] = useState<{
    taskId: string;
    format: "csv" | "pdf";
  } | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [exportLoading, setExportLoading] = useState<
    "csv" | "pdf" | "download" | null
  >(null);

  useEffect(() => {
    if (!authLoading && role && !canAccess) {
      router.replace("/dashboard");
    }
  }, [authLoading, canAccess, role, router]);

  const load = useCallback(async () => {
    if (Number.isNaN(incidentId)) {
      setError("Invalid incident id.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setDetail(await fetchAnalystIncidentDetail(incidentId));
    } catch (e) {
      setDetail(null);
      setError(e instanceof Error ? e.message : "Failed to load incident.");
    } finally {
      setLoading(false);
    }
  }, [incidentId]);

  useEffect(() => {
    if (authLoading || !canAccess) return;
    void load();
  }, [authLoading, canAccess, load]);

  const queueExport = async (format: "csv" | "pdf") => {
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
      setExportError(
        e instanceof Error ? e.message : "Failed to queue export.",
      );
    } finally {
      setExportLoading(null);
    }
  };

  const downloadQueuedExport = async () => {
    if (!exportTask) return;
    setExportError(null);
    setExportLoading("download");
    try {
      const blob = await downloadAnalyticsExport(exportTask.taskId);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `incident-${incidentId}.${exportTask.format}`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setExportError(
        e instanceof Error ? e.message : "Export is not ready yet.",
      );
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
        <Link
          href="/dashboard/analyst"
          className="inline-flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to analyst dashboard
        </Link>
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error || "Incident not found."}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <Link
            href="/dashboard/analyst"
            className="mb-3 inline-flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900"
          >
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
            <span
              className={`rounded-full px-3 py-1 text-xs font-semibold uppercase ${detail.form_kind === "WILDLAND_AFOR" ? "bg-orange-100 text-orange-700" : "bg-blue-100 text-blue-700"}`}
            >
              {detail.form_kind === "WILDLAND_AFOR" ? "Wildland" : "Structural"}
            </span>
          </div>
          <p className="mt-1 text-sm text-gray-500">
            Verified incident detail for national analytics review.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void queueExport("pdf")}
            disabled={exportLoading !== null}
            className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
            style={{ backgroundColor: "var(--bfp-maroon)" }}
          >
            <Download className="h-4 w-4" />
            Export PDF
          </button>
          <button
            type="button"
            onClick={() => void queueExport("csv")}
            disabled={exportLoading !== null}
            className="inline-flex items-center gap-2 rounded-md border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-800 disabled:opacity-60"
          >
            <Download className="h-4 w-4" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Export status banner */}
      {(exportTask || exportError) && (
        <div
          className={`rounded-md border px-4 py-3 text-sm ${exportError ? "border-red-200 bg-red-50 text-red-700" : "border-blue-200 bg-blue-50 text-blue-800"}`}
        >
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

      {/* Collapsible Sections */}
      <CollapsibleSection title="A. Response Details">
        <dl>
          <FieldRow
            label="Notification Date/Time"
            value={formatDateTime(detail.notification_dt)}
          />
          <FieldRow label="Region" value={detail.region} />
          <FieldRow label="Province" value={detail.province_name} />
          <FieldRow label="Municipality" value={detail.municipality_name} />
          <FieldRow label="Barangay" value={detail.barangay_name} />
          <FieldRow label="Responder Type" value={detail.responder_type} />
          <FieldRow
            label="Fire Station Name"
            value={detail.fire_station_name}
          />
          <FieldRow
            label="Distance from Station (km)"
            value={detail.distance_from_station_km}
          />
          <FieldRow label="Alarm Level" value={detail.alarm_level} />
          <FieldRow
            label="Total Response Time"
            value={formatMinutes(detail.total_response_time_minutes)}
          />
        </dl>
      </CollapsibleSection>

      <CollapsibleSection title="B. Classification">
        <dl>
          <FieldRow label="General Category" value={detail.general_category} />
          <FieldRow label="Sub Category" value={detail.sub_category} />
          <FieldRow label="Fire Origin" value={detail.fire_origin} />
          <FieldRow label="Extent of Damage" value={detail.extent_of_damage} />
          <FieldRow label="Stage of Fire" value={detail.stage_of_fire} />
          <FieldRow
            label="Total Floor Area (sqm)"
            value={detail.extent_total_floor_area_sqm}
          />
          <FieldRow
            label="Total Land Area (hectares)"
            value={detail.extent_total_land_area_hectares}
          />
        </dl>
      </CollapsibleSection>

      <CollapsibleSection title="C. Impact & Casualties">
        <dl>
          <FieldRow
            label="Estimated Damage (PHP)"
            value={formatMoney(detail.estimated_damage_php)}
          />
          <FieldRow
            label="Casualty Severity"
            value={detail.casualty_severity}
          />
          <FieldRow
            label="Structures Affected"
            value={detail.structures_affected}
          />
          <FieldRow
            label="Households Affected"
            value={detail.households_affected}
          />
          <FieldRow
            label="Families Affected"
            value={detail.families_affected}
          />
          <FieldRow
            label="Individuals Affected"
            value={detail.individuals_affected}
          />
          <FieldRow
            label="Vehicles Affected"
            value={detail.vehicles_affected}
          />
          <FieldRow
            label="Water Tankers Used"
            value={detail.water_tankers_used}
          />
          <FieldRow
            label="Breathing Apparatus Used"
            value={detail.breathing_apparatus_used}
          />
          <FieldRow
            label="Total Gas Consumed (L)"
            value={detail.total_gas_consumed_liters}
          />
        </dl>
      </CollapsibleSection>

      <CollapsibleSection title="D. Assets & Resources">
        {detail.resources_deployed &&
        Object.keys(detail.resources_deployed).length > 0 ? (
          <dl>
            {Object.entries(detail.resources_deployed).map(([key, val]) => (
              <FieldRow
                key={key}
                label={key
                  .replace(/_/g, " ")
                  .replace(/\b\w/g, (c) => c.toUpperCase())}
                value={val}
              />
            ))}
          </dl>
        ) : (
          <p className="text-sm text-gray-500">
            No resource deployment data recorded.
          </p>
        )}
      </CollapsibleSection>

      <CollapsibleSection title="E. Fire Alarm Timeline">
        {detail.alarm_timeline && detail.alarm_timeline.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 text-left text-gray-500">
                  <th className="pb-2 pr-4 font-medium">Alarm Level</th>
                  <th className="pb-2 pr-4 font-medium">Time</th>
                  <th className="pb-2 font-medium">Commander</th>
                </tr>
              </thead>
              <tbody>
                {detail.alarm_timeline.map((row, i) => (
                  <tr
                    key={i}
                    className="border-b border-gray-100 last:border-0"
                  >
                    <td className="py-2 pr-4 text-gray-900">
                      {row.alarm_level}
                    </td>
                    <td className="py-2 pr-4 text-gray-900">
                      {formatDateTime(row.time)}
                    </td>
                    <td className="py-2 text-gray-900">{row.commander}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-gray-500">No alarm timeline recorded.</p>
        )}
      </CollapsibleSection>

      <CollapsibleSection title="F. Problems & Recommendations">
        <dl>
          {detail.problems_encountered &&
          detail.problems_encountered.length > 0 ? (
            <div className="mb-3">
              <dt className="mb-1 font-medium text-gray-500">
                Problems Encountered
              </dt>
              <dd>
                <ul className="ml-4 list-disc text-sm text-gray-900">
                  {detail.problems_encountered.map((p, i) => (
                    <li key={i}>{p}</li>
                  ))}
                </ul>
              </dd>
            </div>
          ) : (
            <FieldRow label="Problems Encountered" value="None reported" />
          )}
        </dl>
      </CollapsibleSection>

      <CollapsibleSection title="G. Narrative & Disposition">
        <p className="text-sm text-gray-500 italic mb-3">
          Narrative and disposition are protected information. Scroll down to
          the Sensitive Data section to access them.
        </p>
        <dl>
          <FieldRow
            label="Prepared By Officer"
            value="[Protected — see below]"
          />
          <FieldRow label="Noted By Officer" value="[Protected — see below]" />
          <FieldRow label="Disposition" value="[Protected — see below]" />
        </dl>
      </CollapsibleSection>

      <CollapsibleSection title="H. Provenance">
        <dl>
          <FieldRow label="Reference Number" value={detail.reference_number} />
          <FieldRow label="Encoder Username" value={detail.encoder_username} />
          <FieldRow
            label="Created At"
            value={formatDateTime(detail.created_at)}
          />
          <FieldRow label="Data Hash" value={detail.data_hash ?? "N/A"} />
          <FieldRow
            label="Analytics Sync Status"
            value={detail.sync_status ?? "N/A"}
          />
        </dl>
      </CollapsibleSection>

      {/* Wildland Section */}
      <WildlandSection detail={detail} />

      {/* Sensitive Data */}
      <SensitiveSection incidentId={incidentId} />
    </div>
  );
}
