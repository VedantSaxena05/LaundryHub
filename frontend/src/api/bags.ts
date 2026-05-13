import { apiRequest } from "./client";

export interface Bag {
  id: string;
  student_id: string;
  status: string;
  date: string;
  tag_uid?: string;
}

export interface BagLog {
  id: string;
  bag_id: string;
  from_status: string;
  to_status: string;
  timestamp: string;
  pickup_scanned_by_student?: string | null;
}

/** Human-readable labels for each bag status */
export const BAG_STATUS_LABELS: Record<string, string> = {
  pending: "Waiting for drop-off",
  dropped: "Received at laundry",
  washing: "Being washed",
  ready: "Ready for collection",
  awaiting_id_scan: "Awaiting ID verification",
  collected: "Collected by student",
  missed: "Missed / expired",
};

/** Which scan type advances from each status — for UI hints */
export const NEXT_SCAN_FOR_STATUS: Record<string, string> = {
  pending: "dropoff",
  dropped: "ready",
  ready: "pickup_bag",
  awaiting_id_scan: "pickup_id",
};

export const bagsApi = {
  getMy: (token: string) =>
    apiRequest<Bag>("/bags/my", { token }),

  getHistory: (token: string) =>
    apiRequest<Bag[]>("/bags/my/history", { token }),

  getLogs: (token: string, bagId: string) =>
    apiRequest<BagLog[]>(`/bags/${bagId}/logs`, { token }),
};
