import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { notificationsApi } from "@/api/notifications";
import { initializeApp, getApps } from "firebase/app";
import { getMessaging, getToken, onMessage, deleteToken } from "firebase/messaging";

const firebaseConfig = {
  apiKey: "AIzaSyD3WXiU1F21aKHnDQV5XrqVfsH0OmrNID8",
  authDomain: "ndry-b62c2.firebaseapp.com",
  projectId: "ndry-b62c2",
  storageBucket: "ndry-b62c2.firebasestorage.app",
  messagingSenderId: "152523657581",
  appId: "1:152523657581:web:a6a0a1d0292dff5f200a64",
};

const VAPID_KEY =
  "BI1BdoaUf0yMBG8fhlEoRzbxnW4Jhu-jJPGWXtvECojCZr5kRzqVyBuSwJWIcDECbKePrUvrwhBPKrtCuoJNpuM";

const app = getApps().length ? getApps()[0] : initializeApp(firebaseConfig);

type PushState = "loading" | "unsupported" | "prompt" | "denied" | "subscribed" | "unsubscribed" | "error";

export function usePushNotifications() {
  const { token: accessToken } = useAuth();
  const [state, setState] = useState<PushState>("loading");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined" || !("Notification" in window) || !("serviceWorker" in navigator)) {
      setState("unsupported");
      return;
    }
    const perm = Notification.permission;
    if (perm === "denied") {
      setState("denied");
    } else if (perm === "granted") {
      setState("subscribed");
    } else {
      setState("prompt");
    }
  }, []);

  useEffect(() => {
    try {
      const messaging = getMessaging(app);
      const unsub = onMessage(messaging, (payload) => {
        console.log("[FCM] Foreground message:", payload);
        const { title, body } = payload.notification ?? {};
        if (title && Notification.permission === "granted") {
          new Notification(title, { body: body ?? "" });
        }
      });
      return unsub;
    } catch {
      // messaging not supported in this environment
    }
  }, []);

  const subscribe = useCallback(async () => {
    if (!accessToken) return;
    setError(null);
    try {
      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        setState(permission === "denied" ? "denied" : "prompt");
        setError("Notification permission denied");
        return;
      }
      const messaging = getMessaging(app);
      const fcmToken = await getToken(messaging, { vapidKey: VAPID_KEY });
      if (!fcmToken) {
        setError("Failed to get FCM token");
        setState("error");
        return;
      }
      await notificationsApi.registerFcm(accessToken, fcmToken);
      setState("subscribed");
      console.log("[FCM] Token registered:", fcmToken);
    } catch (err: any) {
      setError(err.message ?? "Subscribe failed");
      setState("error");
    }
  }, [accessToken]);

  const unsubscribe = useCallback(async () => {
    if (!accessToken) return;
    try {
      const messaging = getMessaging(app);
      await deleteToken(messaging);
      await notificationsApi.unregisterFcm(accessToken);
      setState("unsubscribed");
    } catch (err: any) {
      setError(err.message ?? "Unsubscribe failed");
      setState("error");
    }
  }, [accessToken]);

  return { state, error, subscribe, unsubscribe };
}