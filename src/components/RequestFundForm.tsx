"use client";

import { useState, type FormEvent } from "react";
import { TICKER_REQUEST } from "@/lib/copy";
import {
  noticeForTickerRequest,
  requestTicker,
} from "@/lib/request-ticker";

export function RequestFundForm({
  onNotice,
  className = "",
}: {
  onNotice: (message: string) => void;
  className?: string;
}) {
  const [ticker, setTicker] = useState("");
  const [note, setNote] = useState("");
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    try {
      const result = await requestTicker({
        ticker,
        note,
        source: "web",
      });
      const message = noticeForTickerRequest(result, "web");
      if (message) onNotice(message);
      if (result.kind === "queued" || result.kind === "already_covered") {
        setTicker("");
        setNote("");
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <form
      id="request-a-fund"
      onSubmit={(event) => {
        void onSubmit(event);
      }}
      className={`rounded-lg border border-line bg-surface p-3 shadow-[0_1px_2px_rgba(26,29,26,0.04)] ${className}`}
    >
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 className="text-[11px] font-semibold uppercase tracking-[0.12em] text-faint">
            {TICKER_REQUEST.formTitle}
          </h2>
          <p className="mt-1 max-w-xl text-xs text-muted">
            {TICKER_REQUEST.formHint}
          </p>
        </div>
      </div>
      <div className="mt-3 grid gap-2 sm:grid-cols-[8rem_minmax(0,1fr)_auto]">
        <label className="block min-w-0">
          <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.12em] text-faint">
            {TICKER_REQUEST.tickerLabel}
          </span>
          <input
            name="ticker"
            type="text"
            value={ticker}
            onChange={(event) => setTicker(event.target.value.toUpperCase())}
            autoComplete="off"
            spellCheck={false}
            maxLength={5}
            placeholder="ABCDX"
            className="h-10 w-full rounded-md border border-line bg-paper px-3 font-mono text-sm uppercase tracking-wide text-ink placeholder:normal-case placeholder:tracking-normal placeholder:text-faint"
          />
        </label>
        <label className="block min-w-0">
          <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.12em] text-faint">
            {TICKER_REQUEST.noteLabel}
          </span>
          <input
            name="note"
            type="text"
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="Optional"
            className="h-10 w-full rounded-md border border-line bg-paper px-3 text-sm text-ink placeholder:text-faint"
          />
        </label>
        <button
          type="submit"
          disabled={pending}
          className="h-10 rounded-md bg-accent px-3 text-sm text-white hover:bg-accent-hover disabled:opacity-60 sm:mt-6"
        >
          {pending ? TICKER_REQUEST.submitting : TICKER_REQUEST.submit}
        </button>
      </div>
    </form>
  );
}
