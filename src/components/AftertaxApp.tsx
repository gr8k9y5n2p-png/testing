"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { Facets, FundEstimateView, HighlightSets } from "@/data/types";
import { Dashboard } from "@/components/Dashboard";
import { DemoBanner } from "@/components/DemoBanner";
import { HighlightsSection } from "@/components/HighlightsSection";
import { Hero } from "@/components/landing/Hero";
import { IllustratePanel } from "@/components/illustrate/IllustratePanel";
import { PaywallDialog } from "@/components/paywall/PaywallDialog";
import { CoverageProvider, useCoverage } from "@/components/coverage/CoverageProvider";
import { Disclaimer } from "@/components/Disclaimer";
import { NoticeToast } from "@/components/NoticeToast";
import { STRIPE } from "@/lib/copy";
import type { FundFamilyCoverage } from "@/lib/coverage";
import { reportCoverageGap } from "@/lib/coverage";
import { isFreemiumDisabled, useFreemium } from "@/lib/freemium";
import {
  FUND_HISTORY_HASH,
  resolveFundView,
} from "@/lib/illustrate/fund-history";
import {
  compareTickersPath,
  parseCompareQueryTickers,
} from "@/lib/illustrate/compare-workspace";

function scrollToId(id: string) {
  requestAnimationFrame(() => {
    document.getElementById(id)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  });
}

export type CheckoutReturn = "success" | "cancel" | null;

const CHECKOUT_SUCCESS_MESSAGE = `Checkout is not live yet. Test mode comes later (price ${STRIPE.priceId}). You’ll stay in this search flow.`;

export function AftertaxApp({
  funds,
  highlights,
  facets,
  coverageFamilies,
  checkout = null,
  ticker = null,
}: {
  funds: FundEstimateView[];
  highlights: HighlightSets;
  facets: Facets;
  coverageFamilies: FundFamilyCoverage[];
  checkout?: CheckoutReturn;
  /** Portfolio review drill-in. Preselects this ticker's Upcoming + dollar illustration. */
  ticker?: string | null;
}) {
  return (
    <CoverageProvider families={coverageFamilies}>
      <AftertaxAppInner
        funds={funds}
        highlights={highlights}
        facets={facets}
        checkout={checkout}
        ticker={ticker}
      />
    </CoverageProvider>
  );
}

function AftertaxAppInner({
  funds,
  highlights,
  facets,
  checkout = null,
  ticker = null,
}: {
  funds: FundEstimateView[];
  highlights: HighlightSets;
  facets: Facets;
  checkout?: CheckoutReturn;
  ticker?: string | null;
}) {
  const router = useRouter();
  const focusedFund = useMemo(
    () => (ticker ? resolveFundView(funds, ticker) ?? null : null),
    [funds, ticker],
  );
  const [picked, setPicked] = useState<FundEstimateView | null | undefined>(
    undefined,
  );
  const selected = picked !== undefined ? picked : focusedFund;
  const [paywallOpen, setPaywallOpen] = useState(
    checkout === "cancel" && !isFreemiumDisabled(),
  );
  const [notice, setNotice] = useState<string | null>(
    checkout === "success" ? CHECKOUT_SUCCESS_MESSAGE : null,
  );
  const onNotice = useCallback((message: string) => {
    setNotice(message);
  }, []);
  const dismissNotice = useCallback(() => {
    setNotice(null);
  }, []);
  const freemium = useFreemium();
  const coverage = useCoverage();

  useEffect(() => {
    const id = window.location.hash.replace(/^#/, "");
    if (id === "portfolio-compare") {
      router.replace("/portfolio");
      return;
    }
    if (id === "fund-compare") {
      const search = new URLSearchParams(window.location.search);
      router.replace(
        compareTickersPath(
          parseCompareQueryTickers({
            tickers: search.getAll("tickers"),
            ticker: search.get("ticker") ?? undefined,
            left: search.get("left") ?? undefined,
            right: search.get("right") ?? undefined,
          }),
        ),
      );
      return;
    }
    if (id === "illustrate" || id === FUND_HISTORY_HASH || id === "growth-and-tax") {
      scrollToId("illustrate");
    }
  }, [router]);

  useEffect(() => {
    if (!ticker) return;
    if (focusedFund && !coverage.isLive(focusedFund.family)) {
      void reportCoverageGap({
        ticker: focusedFund.ticker,
        fund_name: focusedFund.fundName,
        fund_family: focusedFund.family,
      });
    }
    scrollToId("illustrate");
  }, [coverage, focusedFund, ticker]);

  function selectFund(fund: FundEstimateView) {
    const result = freemium.trySearch(fund.ticker);
    if (!result.allowed) {
      setPaywallOpen(true);
      return;
    }
    setPicked(fund);
    if (!coverage.isLive(fund.family)) {
      void reportCoverageGap({
        ticker: fund.ticker,
        fund_name: fund.fundName,
        fund_family: fund.family,
      });
    }
    scrollToId("illustrate");
  }

  function clearFund() {
    setPicked(null);
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
      setNotice(
        `${body.detail ?? "Checkout is stubbed."} Price ${body.price_id ?? STRIPE.priceId}.`,
      );
    } catch {
      setNotice("Checkout is unavailable in this demo.");
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
        onClear={clearFund}
        onNotice={onNotice}
      />

      {selected ? (
        <div className="mb-10">
          <IllustratePanel selected={selected} />
        </div>
      ) : null}

      <section
        className="mt-4 border-t border-line pt-10"
        aria-labelledby="universe-heading"
      >
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">
          Live estimates
        </p>
        <h2
          id="universe-heading"
          className="mt-1 font-serif text-xl tracking-tight text-ink"
        >
          Estimates behind the search
        </h2>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Search a fund to open Upcoming / announced estimates, Paid history,
          and a dollar illustration. Search and Sample Estimates read GET
          /funds for identity and GET /distributions for unpaid Upcoming and
          paid / final history. Upcoming stays unpaid announced only —
          undisclosed is never invented from paid history. Missing or
          uncovered values stay empty, N/A, or Undisclosed.
        </p>
        <div className="mt-5">
          <DemoBanner />
        </div>
        <div className="mt-8">
          <HighlightsSection highlights={highlights} onSelect={selectFund} />
          <Dashboard
            funds={funds}
            facets={facets}
            onIllustrate={selectFund}
            onNotice={onNotice}
            ticker={selected?.ticker}
          />
        </div>
      </section>

      <Disclaimer className="mt-8 text-xs leading-relaxed text-muted" />
      <PaywallDialog
        open={paywallOpen && !freemium.bypass}
        remaining={freemium.remaining}
        onClose={() => setPaywallOpen(false)}
        onUnlock={() => {
          void unlock();
        }}
      />
      <NoticeToast message={notice} onDismiss={dismissNotice} />
    </>
  );
}
