import { apiRequest } from "./client";

export interface Delay {
  id: string;
  reason: string;
  affected_date: string;
  note?: string;
  notification_sent: boolean;
  created_at: string;
}

export interface BlockedDate {
  date: string;
  reason: string;
  created_by?: string;
}

export interface TodaySummary {
  date: string;
  total_booked: number;
  bags_dropped: number;
  bags_ready: number;
  bags_collected: number;
}

export const staffApi = {
  reportDelay: (token: string, data: { reason: string; affected_date: string; note?: string }) =>
    apiRequest<Delay>("/staff/delays", { method: "POST", token, body: data }),

  listDelays: (token: string) =>
    apiRequest<Delay[]>("/staff/delays", { token }),

  addBlockedDate: (token: string, data: { date: string; reason: string }) =>
    apiRequest<BlockedDate>("/staff/blocked-dates", { method: "POST", token, body: data }),

  listBlockedDates: (token: string) =>
    apiRequest<BlockedDate[]>("/staff/blocked-dates", { token }),

  removeBlockedDate: (token: string, date: string) =>
    apiRequest(`/staff/blocked-dates/${date}`, { method: "DELETE", token }),

  getToday: (token: string) =>
    apiRequest<TodaySummary>("/staff/today", { token }),
};
