export {
  changeMyPassword,
  createAdminUser,
  createScheduledReport,
  deleteScheduledReport,
  deleteSyncOp,
  fetchActiveSessions,
  fetchAdminUsers,
  fetchAuditLogs,
  fetchFailedSyncOps,
  fetchMyProfile,
  fetchRateLimits,
  fetchScheduledReports,
  fetchSecurityLogs,
  fetchSystemHealth,
  fetchSystemMetrics,
  fetchWorkerStatus,
  fetchUserSessions,
  pruneWorkers,
  resendAdminUserCredentials,
  setAdminUserTemporaryPassword,
  retrySyncOp,
  revokeUserSessions,
  terminateUserSessions,
  updateAdminUser,
  updateMyProfile,
  updateRateLimits,
  updateScheduledReport,
} from './legacy';

export type {
  FailedSyncOp,
  KeycloakSession,
  RateLimitConfig,
  RelatedAlertItem,
  RelatedAuditItem,
  RelatedAuditResponse,
  WorkerStatusPaginatedResponse,
} from './legacy';
export type { ScheduledReport } from './legacy';

export {
  fetchSystemHealthOfflineAware,
  fetchSystemMetricsOfflineAware,
  fetchWorkerStatusOfflineAware,
  fetchActiveSessionsOfflineAware,
  fetchAuditLogsOfflineAware,
  fetchAnomaliesOfflineAware,
  fetchBreachesOfflineAware,
  fetchAdminConfigOfflineAware,
  fetchRateLimitsOfflineAware,
} from './offlineAdmin';

// Issue #7: OfflineAdminResult identity alias deleted. Consumers use
// OfflineResult<T> from './offlineBase' directly.
