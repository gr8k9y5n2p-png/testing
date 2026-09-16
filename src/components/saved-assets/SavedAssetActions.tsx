"use client";

import { useEffect, useId, useState, type ReactNode } from "react";
import {
  LISTS_NAME_PLACEHOLDER,
  LISTS_OPEN,
  LISTS_OPEN_EMPTY,
  LISTS_OPEN_TITLE,
  LISTS_OPENED,
  LISTS_SAVE,
  LISTS_SAVE_EMPTY,
  LISTS_SAVE_TITLE,
  LISTS_SAVED,
  PORTFOLIO_NAME_PLACEHOLDER,
  PORTFOLIO_OPEN,
  PORTFOLIO_OPEN_EMPTY,
  PORTFOLIO_OPEN_TITLE,
  PORTFOLIO_OPENED,
  PORTFOLIO_SAVE,
  PORTFOLIO_SAVE_EMPTY,
  PORTFOLIO_SAVE_TITLE,
  PORTFOLIO_SAVED,
  SAVED_ASSET_CANCEL,
  SAVED_ASSET_CONFIRM_OPEN,
  SAVED_ASSET_CONFIRM_SAVE,
  SAVED_ASSET_ERROR,
  SAVED_ASSET_NAME_LABEL,
  SAVED_ASSET_SIGN_IN,
} from "@/lib/copy";
import { savedPortfolioSubtitle } from "@/lib/illustrate/portfolio-save-open";
import {
  listSavedAssets,
  saveSavedAsset,
  SavedAssetsClientError,
} from "@/lib/saved-assets/client";
import type { SavedAsset, SavedAssetType } from "@/lib/saved-assets/types";

const COPY = {
  list: {
    save: LISTS_SAVE,
    open: LISTS_OPEN,
    saveTitle: LISTS_SAVE_TITLE,
    openTitle: LISTS_OPEN_TITLE,
    namePlaceholder: LISTS_NAME_PLACEHOLDER,
    saveEmpty: LISTS_SAVE_EMPTY,
    openEmpty: LISTS_OPEN_EMPTY,
    saved: LISTS_SAVED,
    opened: LISTS_OPENED,
  },
  portfolio: {
    save: PORTFOLIO_SAVE,
    open: PORTFOLIO_OPEN,
    saveTitle: PORTFOLIO_SAVE_TITLE,
    openTitle: PORTFOLIO_OPEN_TITLE,
    namePlaceholder: PORTFOLIO_NAME_PLACEHOLDER,
    saveEmpty: PORTFOLIO_SAVE_EMPTY,
    openEmpty: PORTFOLIO_OPEN_EMPTY,
    saved: PORTFOLIO_SAVED,
    opened: PORTFOLIO_OPENED,
  },
} as const;

const buttonClass =
  "inline-flex h-11 items-center rounded-md border border-line px-4 text-sm text-ink hover:border-line-strong disabled:cursor-not-allowed disabled:opacity-50";
const primaryClass =
  "inline-flex h-11 items-center justify-center rounded-md bg-accent px-4 text-sm font-medium text-white hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50";
const inputClass =
  "h-11 w-full rounded-md border border-line bg-surface px-3 text-sm text-ink placeholder:text-faint";

export function SavedAssetActions({
  type,
  getPayload,
  onOpen,
  canSave,
  onNotice,
}: {
  type: SavedAssetType;
  getPayload: () => unknown;
  onOpen: (asset: SavedAsset) => void;
  canSave: boolean | (() => boolean);
  onNotice?: (message: string) => void;
}) {
  function payloadSavable(): boolean {
    return typeof canSave === "function" ? canSave() : canSave;
  }

  function errorMessage(caught: unknown): string {
    if (caught instanceof SavedAssetsClientError) {
      return caught.status === 401 ? SAVED_ASSET_SIGN_IN : caught.detail;
    }
    return SAVED_ASSET_ERROR;
  }
  const copy = COPY[type];
  const saveTitleId = useId();
  const openTitleId = useId();
  const nameId = useId();
  const [dialog, setDialog] = useState<"save" | "open" | null>(null);
  const [name, setName] = useState("");
  const [items, setItems] = useState<SavedAsset[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function openPicker() {
    setSelectedId(null);
    setError(null);
    setItems([]);
    setDialog("open");
    setBusy(true);
    try {
      const next = await listSavedAssets(type);
      setItems(next);
      setSelectedId(next[0]?.id ?? null);
    } catch (caught) {
      setItems([]);
      setError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  function close() {
    if (busy) return;
    setDialog(null);
    setError(null);
  }

  async function onSaveSubmit() {
    if (!payloadSavable()) {
      setError(copy.saveEmpty);
      return;
    }
    const trimmed = name.trim();
    if (!trimmed) {
      setError("Name is required.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await saveSavedAsset({
        type,
        name: trimmed,
        payload: getPayload(),
      });
      setDialog(null);
      onNotice?.(copy.saved);
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  function onOpenSubmit() {
    const item = items.find((row) => row.id === selectedId);
    if (!item) {
      setError(copy.openEmpty);
      return;
    }
    onOpen(item);
    setDialog(null);
    onNotice?.(copy.opened);
  }

  return (
    <div className="flex shrink-0 flex-wrap items-center gap-2">
      <button
        type="button"
        className={buttonClass}
        onClick={() => {
          void openPicker();
        }}
      >
        {copy.open}
      </button>
      <button
        type="button"
        className={buttonClass}
        onClick={() => {
          setName("");
          setError(payloadSavable() ? null : copy.saveEmpty);
          setDialog("save");
        }}
      >
        {copy.save}
      </button>

      {dialog === "save" ? (
        <DialogShell labelledBy={saveTitleId} onClose={close}>
          <h2 id={saveTitleId} className="font-serif text-xl text-ink">
            {copy.saveTitle}
          </h2>
          <label className="mt-4 block text-sm text-ink" htmlFor={nameId}>
            {SAVED_ASSET_NAME_LABEL}
          </label>
          <input
            id={nameId}
            className={`mt-1.5 ${inputClass}`}
            value={name}
            placeholder={copy.namePlaceholder}
            autoComplete="off"
            disabled={busy}
            onChange={(event) => setName(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                void onSaveSubmit();
              }
            }}
          />
          {error ? (
            <p className="mt-2 text-sm text-muted" role="alert">
              {error}
            </p>
          ) : null}
          <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <button type="button" className={buttonClass} onClick={close} disabled={busy}>
              {SAVED_ASSET_CANCEL}
            </button>
            <button
              type="button"
              className={primaryClass}
              disabled={busy || !payloadSavable()}
              onClick={() => void onSaveSubmit()}
            >
              {SAVED_ASSET_CONFIRM_SAVE}
            </button>
          </div>
        </DialogShell>
      ) : null}

      {dialog === "open" ? (
        <DialogShell labelledBy={openTitleId} onClose={close}>
          <h2 id={openTitleId} className="font-serif text-xl text-ink">
            {copy.openTitle}
          </h2>
          {busy && items.length === 0 && !error ? (
            <p className="mt-4 text-sm text-muted">Loading…</p>
          ) : items.length === 0 ? (
            <p className="mt-4 text-sm text-muted">{error ?? copy.openEmpty}</p>
          ) : (
            <ul className="mt-4 max-h-64 space-y-1 overflow-y-auto">
              {items.map((item) => {
                const selected = item.id === selectedId;
                return (
                  <li key={item.id}>
                    <button
                      type="button"
                      onClick={() => setSelectedId(item.id)}
                      className={`flex w-full flex-col rounded-md border px-3 py-2 text-left text-sm ${
                        selected
                          ? "border-accent bg-accent-soft text-ink"
                          : "border-line text-ink hover:border-line-strong"
                      }`}
                    >
                      <span className="font-medium">{item.name}</span>
                      <span className="mt-0.5 text-[11px] text-muted">
                        {subtitleFor(item)}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
          {error && items.length > 0 ? (
            <p className="mt-2 text-sm text-muted" role="alert">
              {error}
            </p>
          ) : null}
          <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <button type="button" className={buttonClass} onClick={close} disabled={busy}>
              {SAVED_ASSET_CANCEL}
            </button>
            <button
              type="button"
              className={primaryClass}
              disabled={busy || !selectedId}
              onClick={onOpenSubmit}
            >
              {SAVED_ASSET_CONFIRM_OPEN}
            </button>
          </div>
        </DialogShell>
      ) : null}
    </div>
  );
}

function subtitleFor(item: SavedAsset): string {
  if (item.type === "list") {
    const tickers = (item.payload as { tickers?: unknown })?.tickers;
    const count = Array.isArray(tickers) ? tickers.length : 0;
    return count === 1 ? "1 ticker" : `${count} tickers`;
  }
  return savedPortfolioSubtitle(item.payload);
}

function DialogShell({
  labelledBy,
  onClose,
  children,
}: {
  labelledBy: string;
  onClose: () => void;
  children: ReactNode;
}) {
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby={labelledBy}
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="w-full max-w-md rounded-lg border border-line bg-surface p-6 shadow-xl">
        {children}
      </div>
    </div>
  );
}
