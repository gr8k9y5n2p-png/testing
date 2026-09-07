"use client";

import { useCallback, useSyncExternalStore } from "react";
import { FREE_SEARCH_LIMIT } from "@/lib/copy";

const STORAGE_KEY = "aftertax.freemium.v1";

type FreemiumState = {
  tickers: string[];
  unlocked: boolean;
};

const empty: FreemiumState = { tickers: [], unlocked: false };
const listeners = new Set<() => void>();

function read(): FreemiumState {
  if (typeof window === "undefined") return empty;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return empty;
    const parsed = JSON.parse(raw) as FreemiumState;
    return {
      tickers: Array.isArray(parsed.tickers) ? parsed.tickers : [],
      unlocked: Boolean(parsed.unlocked),
    };
  } catch {
    return empty;
  }
}

function write(next: FreemiumState) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function useFreemium() {
  const state = useSyncExternalStore(subscribe, read, () => empty);
  const used = state.unlocked ? 0 : state.tickers.length;
  const remaining = state.unlocked
    ? Number.POSITIVE_INFINITY
    : Math.max(0, FREE_SEARCH_LIMIT - used);

  const trySearch = useCallback(
    (ticker: string): { allowed: boolean; remaining: number; isNew: boolean } => {
      const current = read();
      const normalized = ticker.toUpperCase();
      if (current.unlocked) {
        return { allowed: true, remaining: Number.POSITIVE_INFINITY, isNew: false };
      }
      if (current.tickers.includes(normalized)) {
        return {
          allowed: true,
          remaining: Math.max(0, FREE_SEARCH_LIMIT - current.tickers.length),
          isNew: false,
        };
      }
      if (current.tickers.length >= FREE_SEARCH_LIMIT) {
        return { allowed: false, remaining: 0, isNew: true };
      }
      const tickers = [...current.tickers, normalized];
      write({ ...current, tickers });
      return {
        allowed: true,
        remaining: Math.max(0, FREE_SEARCH_LIMIT - tickers.length),
        isNew: true,
      };
    },
    [],
  );

  const unlockStub = useCallback(() => {
    write({ ...read(), unlocked: true });
  }, []);

  return {
    remaining: Number.isFinite(remaining) ? remaining : FREE_SEARCH_LIMIT,
    unlimited: state.unlocked,
    searchedTickers: state.tickers,
    trySearch,
    unlockStub,
  };
}
