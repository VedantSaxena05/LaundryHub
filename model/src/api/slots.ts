import { apiRequest } from "./client";

export interface SlotAvailability {
  date: string;
  blocks: Array<{
    block: string;
    dropoff_window: string;
    collection_window: string;
    block_limit: number;
    booked_count: number;
    remaining: number;
    is_available: boolean;
  }>;
}

export interface BlockAvailability {
  block: string;
  block_limit: number;
  booked_count: number;
  remaining: number;
  is_available: boolean;
  dropoff_window: string;
  collection_window: string;
}

export interface Slot {
  id: string;
  student_id?: string;
  date: string;
  status: string;
  month_index: number;
  block?: string;
  submission_start_time?: string;
  submission_window_minutes?: number;
  submission_window_start?: string;
  submission_expires_at?: string;
  created_at?: string;
  cancelled_at?: string;
}

export interface ExpireLapsedResponse {
  expired_slots: number;
}

export const slotsApi = {
  getAvailability: (token: string, date: string) =>
    apiRequest<SlotAvailability>(`/slots/availability/${date}`, { token }),

  getBlockAvailability: (token: string, date: string, block: string) =>
    apiRequest<BlockAvailability>(`/slots/availability/${date}/block/${block}`, { token }),

  book: (token: string, date: string, submissionStartTime: string = "10:00", submissionWindowMinutes: number = 30) =>
    apiRequest<Slot>("/slots/book", {
      method: "POST",
      token,
      body: { date, submission_start_time: submissionStartTime, submission_window_minutes: submissionWindowMinutes },
    }),

  cancel: (token: string, slotId: string) =>
    apiRequest<Slot>("/slots/cancel", { method: "POST", token, body: { slot_id: slotId } }),

  getMy: (token: string) =>
    apiRequest<Slot[]>("/slots/my", { token }),

  updateBlockLimit: (token: string, block: string, newLimit: number) =>
    apiRequest(`/slots/block-limit/${block}?new_limit=${newLimit}`, { method: "PATCH", token }),

  expireLapsed: (token: string) =>
    apiRequest<ExpireLapsedResponse>("/slots/expire-lapsed", { method: "POST", token }),
};
