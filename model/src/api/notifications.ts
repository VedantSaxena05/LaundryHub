import { apiRequest } from "./client";

export interface NotificationLogEntry {
  id: string;
  student_id: string;
  event_type: string;
  language: string;
  title: string;
  body: string;
  sent_at: string;
  fcm_success: boolean;
}

export const notificationsApi = {
  /** Register or refresh the student's FCM device token */
  registerFcm: (token: string, fcmToken: string) =>
    apiRequest("/notifications/fcm/register", {
      method: "POST",
      token,
      body: { fcm_token: fcmToken },
    }),

  /** Remove FCM token on logout */
  unregisterFcm: (token: string) =>
    apiRequest("/notifications/fcm/unregister", {
      method: "DELETE",
      token,
    }),

  /** Fetch student's notification history */
  getHistory: (token: string, limit = 50) =>
    apiRequest<NotificationLogEntry[]>("/notifications/history", {
      token,
      params: { limit: String(limit) },
    }),
};
