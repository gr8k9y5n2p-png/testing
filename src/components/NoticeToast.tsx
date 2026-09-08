"use client";

import { useEffect } from "react";

export function NoticeToast({
  message,
  onDismiss,
}: {
  message: string | null;
  onDismiss: () => void;
}) {
  useEffect(() => {
    if (!message) return;
    const handle = window.setTimeout(onDismiss, 5600);
    return () => window.clearTimeout(handle);
  }, [message, onDismiss]);

  if (!message) return null;

  return (
    <p
      role="status"
      aria-live="polite"
      className="fixed bottom-4 left-1/2 z-50 w-[min(32rem,calc(100%-2rem))] -translate-x-1/2 rounded-md border border-line bg-surface px-4 py-3 text-sm text-ink shadow-lg"
    >
      {message}
      <button
        type="button"
        className="ml-3 text-xs text-accent underline"
        onClick={onDismiss}
      >
        Dismiss
      </button>
    </p>
  );
}
