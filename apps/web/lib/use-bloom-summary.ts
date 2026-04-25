"use client";

import { useEffect, useState } from "react";
import { ApiClientError, apiClient } from "@/lib/api-client";
import type { BalanceResponse, BloomReportResponse, Gig } from "@/lib/types";

type BloomSummaryState = {
  loading: boolean;
  error: string | null;
  balanceLoading: boolean;
  balanceError: string | null;
  reportLoading: boolean;
  reportError: string | null;
  gigs: Gig[];
  balanceResponse: BalanceResponse | null;
  report: BloomReportResponse | null;
};

const initialState: BloomSummaryState = {
  loading: true,
  error: null,
  balanceLoading: true,
  balanceError: null,
  reportLoading: true,
  reportError: null,
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

    void apiClient.listGigs().then(
      (gigsResponse) => {
        if (!active) {
          return;
        }

        setState((current) => ({
          ...current,
          loading: false,
          error: current.balanceError,
          gigs: gigsResponse.gigs
        }));
      },
      (reason: unknown) => {
        if (!active) {
          return;
        }

        setState((current) => ({
          ...current,
          loading: false,
          error: errorMessage(reason),
          gigs: []
        }));
      }
    );

    void apiClient.getKidBalance().then(
      (balanceResponse) => {
        if (!active) {
          return;
        }

        setState((current) => ({
          ...current,
          balanceLoading: false,
          balanceError: null,
          error: current.error,
          balanceResponse
        }));
      },
      (reason: unknown) => {
        if (!active) {
          return;
        }

        const message = errorMessage(reason);

        setState((current) => ({
          ...current,
          balanceLoading: false,
          balanceError: message,
          error: current.error ?? message
        }));
      }
    );

    void apiClient.getWeeklyBloomReport().then(
      (report) => {
        if (!active) {
          return;
        }

        setState((current) => ({
          ...current,
          reportLoading: false,
          reportError: null,
          report
        }));
      },
      (reason: unknown) => {
        if (!active) {
          return;
        }

        setState((current) => ({
          ...current,
          reportLoading: false,
          reportError: errorMessage(reason)
        }));
      }
    );

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
    reload: () => {
      setState((current) => ({
        ...current,
        loading: true,
        error: null,
        balanceLoading: true,
        balanceError: null,
        reportLoading: true,
        reportError: null
      }));
      setReloadKey((current) => current + 1);
    }
  };
}