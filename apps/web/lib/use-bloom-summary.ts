"use client";

import { useEffect, useState } from "react";
import { ApiClientError, apiClient } from "@/lib/api-client";
import type { BalanceResponse, BloomReportResponse, Gig } from "@/lib/types";

type BloomSummaryState = {
  loading: boolean;
  error: string | null;
  gigs: Gig[];
  balanceResponse: BalanceResponse | null;
  report: BloomReportResponse | null;
};

const initialState: BloomSummaryState = {
  loading: true,
  error: null,
  gigs: [],
  balanceResponse: null,
  report: null
};

function errorMessage(reason: unknown): string {
  if (reason instanceof ApiClientError) {
    return reason.message;
  }

  if (reason instanceof Error) {
    return reason.message;
  }

  return "Could not load Bloom data. Try again.";
}

export function useBloomSummary() {
  const [state, setState] = useState<BloomSummaryState>(initialState);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;

    async function loadSummary() {
      setState((current) => ({ ...current, loading: true, error: null }));

      const [gigsResult, balanceResult, reportResult] = await Promise.allSettled([
        apiClient.listGigs(),
        apiClient.getKidBalance(),
        apiClient.getWeeklyBloomReport()
      ]);

      if (!active) {
        return;
      }

      const nextState: BloomSummaryState = {
        loading: false,
        error: null,
        gigs: gigsResult.status === "fulfilled" ? gigsResult.value.gigs : [],
        balanceResponse: balanceResult.status === "fulfilled" ? balanceResult.value : null,
        report: reportResult.status === "fulfilled" ? reportResult.value : null
      };

      const firstFailure = [gigsResult, balanceResult, reportResult].find(
        (result) => result.status === "rejected"
      );

      if (firstFailure && firstFailure.status === "rejected") {
        nextState.error = errorMessage(firstFailure.reason);
      }

      setState(nextState);
    }

    void loadSummary();

    return () => {
      active = false;
    };
  }, [reloadKey]);

  const paidGigs = [...state.gigs]
    .filter((gig) => gig.status === "paid")
    .sort((left, right) => Date.parse(right.updated_at ?? "") - Date.parse(left.updated_at ?? ""));

  const openGigs = state.gigs.filter((gig) => gig.status === "open");
  const modes: string[] = [];

  if (state.balanceResponse?.mode) {
    modes.push(state.balanceResponse.mode);
  }

  if (state.report?.mode) {
    modes.push(state.report.mode);
  }

  const fallbackMode =
    state.balanceResponse?.fallback_mode === true || state.report?.fallback_mode === true;

  return {
    ...state,
    openGigs,
    paidGigs,
    fallbackMode,
    modes,
    reload: () => setReloadKey((current) => current + 1)
  };
}