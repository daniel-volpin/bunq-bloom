"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiClientError, apiClient } from "@/lib/api-client";
import type { KidNotification } from "@/lib/types";

export function useKidNotifications() {
  const [notifications, setNotifications] = useState<KidNotification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;
    void apiClient.listKidNotifications().then(
      (response) => {
        if (!active) {
          return;
        }
        setNotifications(response.notifications);
        setLoading(false);
      },
      (caught) => {
        if (!active) {
          return;
        }
        setError(caught instanceof ApiClientError ? caught.message : "Notifications could not load.");
        setLoading(false);
      }
    );

    return () => {
      active = false;
    };
  }, [reloadKey]);

  useEffect(() => {
    const interval = window.setInterval(() => {
      setReloadKey((current) => current + 1);
    }, 6000);

    return () => window.clearInterval(interval);
  }, []);

  const reload = useCallback(() => {
    setLoading(true);
    setError(null);
    setReloadKey((current) => current + 1);
  }, []);

  async function dismiss(notificationId: string) {
    setNotifications((current) => current.filter((notification) => notification.id !== notificationId));
    try {
      await apiClient.dismissKidNotification(notificationId);
    } catch {
      reload();
    }
  }

  return {
    notifications,
    loading,
    error,
    reload,
    dismiss
  };
}
