"use client";

import { useSyncExternalStore } from "react";

const STORAGE_KEY = "bunq-bloom:saved-goal";
const STORAGE_EVENT = "bunq-bloom:saved-goal-change";
let cachedRawValue: string | null | undefined;
let cachedSnapshot: SavedGoal | null = null;

export type SavedGoal = {
  label: string;
  amount: string;
};

function readSavedGoal(): SavedGoal | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const rawValue = window.localStorage.getItem(STORAGE_KEY);

    if (rawValue === cachedRawValue) {
      return cachedSnapshot;
    }

    cachedRawValue = rawValue;

    if (!rawValue) {
      cachedSnapshot = null;
      return null;
    }

    const parsed = JSON.parse(rawValue) as Partial<SavedGoal>;

    if (typeof parsed.label !== "string" || typeof parsed.amount !== "string") {
      cachedSnapshot = null;
      return null;
    }

    cachedSnapshot = {
      label: parsed.label,
      amount: parsed.amount
    };

    return cachedSnapshot;
  } catch {
    cachedRawValue = null;
    cachedSnapshot = null;
    return null;
  }
}

function subscribe(onStoreChange: () => void) {
  if (typeof window === "undefined") {
    return () => {};
  }

  const handleChange = () => onStoreChange();

  window.addEventListener("storage", handleChange);
  window.addEventListener(STORAGE_EVENT, handleChange);

  return () => {
    window.removeEventListener("storage", handleChange);
    window.removeEventListener(STORAGE_EVENT, handleChange);
  };
}

export function useSavedGoal() {
  const savedGoal = useSyncExternalStore(subscribe, readSavedGoal, () => null);

  function setSavedGoal(nextGoal: SavedGoal) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextGoal));
      window.dispatchEvent(new Event(STORAGE_EVENT));
    } catch {
      // Ignore storage write failures and keep the rest of the app usable.
    }
  }

  return {
    savedGoal,
    setSavedGoal
  };
}