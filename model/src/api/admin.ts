import { apiRequest } from "./client";

export interface OverviewAnalytics {
  active_students: number;
  active_staff: number;
  slots_booked_today: number;
  bags_in_flight: number;
  block_usage_today: Record<string, { booked: number; limit: number }>;
}

export interface SlotAnalytics {
  from_date: string;
  to_date: string;
  total_booked: number;
  used: number;
  cancelled: number;
  missed: number;
  utilisation_rate: number;
  by_block: Record<string, { limit_per_day: number; total_booked: number; used: number }>;
}

export interface BagAnalytics {
  pending: number;
  dropped: number;
  washing: number;
  ready: number;
  collected: number;
  missed: number;
}

export interface NotificationAnalytics {
  total_sent: number;
  fcm_success: number;
  fcm_failure: number;
  success_rate: number;
  by_event_type: Record<string, number>;
}

export interface AdminStudent {
  id: string;
  registration_number: string;
  name: string;
  email: string;
  block: string;
  is_active: boolean;
}

export interface AdminStaff {
  id: string;
  employee_id: string;
  name: string;
  role: string;
  is_active: boolean;
}

export const adminApi = {
  getOverview: (token: string) =>
    apiRequest<OverviewAnalytics>("/admin/analytics/overview", { token }),

  getSlotAnalytics: (token: string, fromDate: string, toDate: string) =>
    apiRequest<SlotAnalytics>(`/admin/analytics/slots`, {
      token,
      params: { from_date: fromDate, to_date: toDate },
    }),

  getBagAnalytics: (token: string) =>
    apiRequest<BagAnalytics>("/admin/analytics/bags", { token }),

  getNotificationAnalytics: (token: string, fromDate: string, toDate: string) =>
    apiRequest<NotificationAnalytics>("/admin/analytics/notifications", {
      token,
      params: { from_date: fromDate, to_date: toDate },
    }),

  listStudents: (token: string, activeOnly = true, page = 1, pageSize = 50) =>
    apiRequest<AdminStudent[]>("/admin/students", {
      token,
      params: { active_only: String(activeOnly), page: String(page), page_size: String(pageSize) },
    }),

  listStaff: (token: string, activeOnly = true) =>
    apiRequest<AdminStaff[]>("/admin/staff", {
      token,
      params: { active_only: String(activeOnly) },
    }),

  deactivateStaff: (token: string, staffId: string) =>
    apiRequest(`/admin/staff/${staffId}/deactivate`, { method: "PATCH", token }),
};
