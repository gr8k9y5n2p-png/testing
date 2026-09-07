"use client";

import { useState } from "react";
import type { Facets, FundEstimateView, HighlightSets } from "@/data/types";
import { Dashboard } from "@/components/Dashboard";
import { DemoBanner } from "@/components/DemoBanner";
import { HighlightsSection } from "@/components/HighlightsSection";
import { Hero } from "@/components/landing/Hero";
import { IllustratePanel } from "@/components/illustrate/IllustratePanel";
import { PaywallDialog } from "@/components/paywall/PaywallDialog";
import { COPY, STRIPE, freeSearchLabel } from "@/lib/copy";
import { useFreemium } from "@/lib/freemium";

export function AftertaxApp({
  funds,
  highlights,
  facets,
}: {
  funds: FundEstimateView[];
  highlights: HighlightSets;
  facets: Facets;
}) {
  const [selected, setSelected] = useState<FundEstimateView | null>(null);
  const [paywallOpen, setPaywallOpen] = useState(false);
  const [unlockMessage, setUnlockMessage] = useState<string | null>(null);
  const freemium = useFreemium();

  function selectFund(fund: FundEstimateView) {
    const result = freemium.trySearch(fund.ticker);
    if (!result.allowed) {
      setPaywallOpen(true);
      return;
    }
    setSelected(fund);
    document.getElementById("illustrate")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function focusSearch() {
    const input = document.getElementById("fund-search");
    input?.scrollIntoView({ behavior: "smooth", block: "center" });
    if (input instanceof HTMLInputElement) input.focus();
  }

  async function unlock() {
    try {
      const response = await fetch("/api/checkout", { method: "POST" });
      const body = (await response.json()) as { detail?: string; price_id?: string };
      setUnlockMessage(
        `${body.detail ?? "Checkout is stubbed."} Price ${body.price_id ?? STRIPE.priceId}.`,
      );
    } catch {
      setUnlockMessage("Checkout is unavailable in this demo.");
    }
  }

  return (
    <>
      <DemoBanner />
      <div className="mb-2 flex justify-end">
        <p className="font-mono text-xs text-faint" aria-live="polite">
          {freemium.unlimited ? "Unlimited searches" : freeSearchLabel(freemium.remaining)}
        </p>
      </div>
      <Hero onSearch={focusSearch} onImport={() => setPaywallOpen(true)} />
      <IllustratePanel funds={funds} selected={selected} onSelect={selectFund} />
      <HighlightsSection highlights={highlights} />
      <Dashboard funds={funds} facets={facets} onIllustrate={selectFund} />
      <p className="mt-8 text-xs leading-relaxed text-muted">{COPY.disclaimer}</p>
      <PaywallDialog
        open={paywallOpen}
        remaining={freemium.remaining}
        onClose={() => setPaywallOpen(false)}
        onUnlock={() => {
          void unlock();
        }}
      />
      {unlockMessage ? (
        <p className="fixed bottom-4 left-1/2 z-50 w-[min(32rem,calc(100%-2rem))] -translate-x-1/2 rounded-md border border-line bg-surface px-4 py-3 text-sm text-ink shadow-lg">
          {unlockMessage}
          <button
            type="button"
            className="ml-3 text-xs text-teal underline"
            onClick={() => setUnlockMessage(null)}
          >
            Dismiss
          </button>
        </p>
      ) : null}
    </>
  );
}
