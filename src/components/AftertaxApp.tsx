"use client";

import { useState } from "react";
import type { Facets, FundEstimateView, HighlightSets } from "@/data/types";
import { Dashboard } from "@/components/Dashboard";
import { DemoBanner } from "@/components/DemoBanner";
import { HighlightsSection } from "@/components/HighlightsSection";
import { Hero } from "@/components/landing/Hero";
import { FundCompareRail } from "@/components/illustrate/FundCompareRail";
import { IllustratePanel } from "@/components/illustrate/IllustratePanel";
import { PaywallDialog } from "@/components/paywall/PaywallDialog";
import { CoverageProvider, useCoverage } from "@/components/coverage/CoverageProvider";
import { Disclaimer } from "@/components/Disclaimer";
import { STRIPE } from "@/lib/copy";
import type { FundFamilyCoverage } from "@/lib/coverage";
import { reportCoverageGap } from "@/lib/coverage";
import { useFreemium } from "@/lib/freemium";

export type CheckoutReturn = "success" | "cancel" | null;

const CHECKOUT_SUCCESS_MESSAGE = `Checkout is not live yet. Test mode comes later (price ${STRIPE.priceId}). You’ll stay in this search flow.`;

export function AftertaxApp({
  funds,
  highlights,
  facets,
  coverageFamilies,
  checkout = null,
}: {
  funds: FundEstimateView[];
  highlights: HighlightSets;
  facets: Facets;
  coverageFamilies: FundFamilyCoverage[];
  checkout?: CheckoutReturn;
}) {
  return (
    <CoverageProvider families={coverageFamilies}>
      <AftertaxAppInner
        funds={funds}
        highlights={highlights}
        facets={facets}
        checkout={checkout}
      />
    </CoverageProvider>
  );
}

function AftertaxAppInner({
  funds,
  highlights,
  facets,
  checkout = null,
}: {
  funds: FundEstimateView[];
  highlights: HighlightSets;
  facets: Facets;
  checkout?: CheckoutReturn;
}) {
  const [selected, setSelected] = useState<FundEstimateView | null>(null);
  const [paywallOpen, setPaywallOpen] = useState(checkout === "cancel");
  const [unlockMessage, setUnlockMessage] = useState<string | null>(
    checkout === "success" ? CHECKOUT_SUCCESS_MESSAGE : null,
  );
  const freemium = useFreemium();
  const coverage = useCoverage();

  function selectFund(fund: FundEstimateView) {
    const result = freemium.trySearch(fund.ticker);
    if (!result.allowed) {
      setPaywallOpen(true);
      return;
    }
    setSelected(fund);
    if (!coverage.isLive(fund.family)) {
      void reportCoverageGap({
        ticker: fund.ticker,
        fund_name: fund.fundName,
        fund_family: fund.family,
      });
    }
    requestAnimationFrame(() => {
      document.getElementById("illustrate")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  }

  function openImportPaywall() {
    setPaywallOpen(true);
  }

  async function unlock() {
    try {
      const response = await fetch("/api/checkout", { method: "POST" });
      const body = (await response.json()) as {
        url?: string;
        detail?: string;
        price_id?: string;
      };
      if (body.url) {
        window.location.assign(body.url);
        return;
      }
      setPaywallOpen(false);
      setUnlockMessage(
        `${body.detail ?? "Checkout is stubbed."} Price ${body.price_id ?? STRIPE.priceId}.`,
      );
    } catch {
      setUnlockMessage("Checkout is unavailable in this demo.");
    }
  }

  return (
    <>
      <Hero
        funds={funds}
        selected={selected}
        remaining={freemium.remaining}
        unlimited={freemium.unlimited}
        onSelect={selectFund}
        onImport={openImportPaywall}
      />

      {selected ? (
        <div className="mb-10 grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(20rem,26.25rem)]">
          <IllustratePanel selected={selected} />
          <FundCompareRail funds={funds} selected={selected} />
        </div>
      ) : null}

      <section
        className="mt-4 border-t border-line pt-10"
        aria-labelledby="universe-heading"
      >
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">
          Sample universe
        </p>
        <h2
          id="universe-heading"
          className="mt-1 font-serif text-xl tracking-tight text-ink"
        >
          Estimates behind the search
        </h2>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          The dollar illustration is the product. This table is the sample
          dataset search reads from — not a feature grid.
        </p>
        <div className="mt-5">
          <DemoBanner />
        </div>
        <div className="mt-8">
          <HighlightsSection highlights={highlights} />
          <Dashboard funds={funds} facets={facets} onIllustrate={selectFund} />
        </div>
      </section>

      <Disclaimer className="mt-8 text-xs leading-relaxed text-muted" />
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
            className="ml-3 text-xs text-accent underline"
            onClick={() => setUnlockMessage(null)}
          >
            Dismiss
          </button>
        </p>
      ) : null}
    </>
  );
}
