"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";
import { AccountPanel } from "@/components/AccountPanel";

export function AccountMenu() {
  const pathname = usePathname();
  const [menuPath, setMenuPath] = useState<string | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelId = useId();
  const active = pathname === "/account";
  const open = menuPath === pathname;

  useEffect(() => {
    if (!open) return;

    function onPointerDown(event: PointerEvent) {
      const root = rootRef.current;
      if (root && !root.contains(event.target as Node)) {
        setMenuPath(null);
      }
    }

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setMenuPath(null);
    }

    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        aria-current={active ? "page" : undefined}
        onClick={() =>
          setMenuPath((current) => (current === pathname ? null : pathname))
        }
        className={`inline-flex h-9 items-center rounded-md px-3 text-sm ${
          open || active
            ? "bg-accent-soft font-medium text-ink"
            : "text-muted hover:bg-notice hover:text-ink"
        }`}
      >
        Account
      </button>
      {open ? (
        <div
          id={panelId}
          className="absolute right-0 z-40 mt-2 w-72 rounded-lg border border-line bg-surface p-4 shadow-lg"
        >
          <AccountPanel compact />
          <p className="mt-3 border-t border-line pt-3">
            <Link
              href="/account"
              className="text-xs text-accent underline decoration-accent/40 underline-offset-2 hover:decoration-accent"
            >
              Open account
            </Link>
          </p>
        </div>
      ) : null}
    </div>
  );
}
