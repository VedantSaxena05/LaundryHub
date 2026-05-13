import { apiRequest } from "./client";

export interface Device {
  id: string;
  device_name: string;
  location_tag: string;
  is_active: boolean;
}

export interface RfidTag {
  id: string;
  tag_uid: string;
  tag_type: "bag" | "id_card";
  student_id: string | null;
  linked_by: string | null;
  linked_at: string | null;
  is_active: boolean;
  created_at: string;
}

export interface ScanResult {
  scan_event_id?: string;
  tag_uid?: string;
  device_id?: string;
  scan_type?: string;
  timestamp?: string;
  /** "success" | "wrong_state" | "unknown_tag" | "no_active_bag" | "no_slot_booked" | "student_not_found" | "missing_bag_id" | "bag_not_found" | "unknown_id_card" | "id_card_not_linked" */
  result: string;
  message: string;
  student_name?: string | null;
  student_id?: string | null;
  bag_id?: string | null;
  /** Current bag status AFTER the transition */
  bag_status?: string | null;
  /** For pickup_id scans — who tapped their ID card */
  pickup_tapped_by_student_id?: string | null;
  pickup_tapped_by_student_name?: string | null;
}

export interface ScanLogEntry {
  id: string;
  tag_uid: string;
  device_id: string;
  scan_type: string;
  result: string;
  message: string;
  bag_id?: string | null;
  pickup_scanned_by_student_id?: string | null;
  timestamp: string;
}

export const devicesApi = {
  register: (token: string, data: { device_name: string; location_tag: string }) =>
    apiRequest<Device>("/devices", { method: "POST", token, body: data }),

  list: (token: string) =>
    apiRequest<Device[]>("/devices", { token }),

  deactivate: (token: string, deviceId: string) =>
    apiRequest(`/devices/${deviceId}`, { method: "DELETE", token }),
};

export const rfidApi = {
  /** Link a bag RFID tag to a student (one-time enrollment) */
  linkBagTag: (token: string, data: { tag_uid: string; student_id: string }) =>
    apiRequest<RfidTag>("/rfid/link-bag-tag", { method: "POST", token, body: data }),

  /** Link a college ID card to a student (one-time enrollment) */
  linkIdCard: (token: string, data: { tag_uid: string; student_id: string }) =>
    apiRequest<RfidTag>("/rfid/link-id-card", { method: "POST", token, body: data }),

  listTags: (token: string) =>
    apiRequest<RfidTag[]>("/rfid/tags", { token }),

  getTag: (token: string, tagUid: string) =>
    apiRequest<RfidTag>(`/rfid/tags/${tagUid}`, { token }),

  deleteTag: (token: string, tagUid: string) =>
    apiRequest(`/rfid/tags/${tagUid}`, { method: "DELETE", token }),

  scan: (token: string, data: { tag_uid: string; device_id: string; scan_type: string; bag_id?: string }) =>
    apiRequest<ScanResult>("/rfid/scan", { method: "POST", token, body: data }),

  unlinkTag: (token: string, tagUid: string) =>
    apiRequest<RfidTag>(`/rfid/unlink/${tagUid}`, { method: "POST", token }),

  scanLog: (token: string, limit = 100) =>
    apiRequest<ScanLogEntry[]>(`/rfid/scan-log?limit=${limit}`, { token }),
};
