#!/usr/bin/env python3
"""Build app/fund_categories.json from fixture identities + optional Yahoo.

Never invents a category. Yahoo fundProfile categoryName is stored only when it
canonicalizes to the Morningstar-style taxonomy used by the API.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.categories import (  # noqa: E402
    CANONICAL_CATEGORIES,
    _CURATED_IDENTIFIERS,
    _CURATED_TICKERS,
    _name_category,
    canonical_category,
    resolve_category,
)
from app.schemas import fund_identifier  # noqa: E402
from app.sources.registry import list_sources  # noqa: E402

OUT_PATH = ROOT / "app" / "fund_categories.json"


def _write_catalog(tickers: dict[str, str], identifiers: dict[str, str]) -> None:
    payload = {
        "version": 1,
        "taxonomy": "morningstar_us_broad",
        "notes": (
            "Identity-level Morningstar-style categories. Null when unknown. "
            "Never invent a wrong category. Sources: curated issuer/SEC-stable "
            "identities, conservative fund-name rules, optional Yahoo fundProfile "
            "categoryName when it matches the taxonomy."
        ),
        "tickers": dict(sorted(tickers.items())),
        "identifiers": dict(sorted(identifiers.items())),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _collect_fixture_funds() -> list[dict[str, str | None]]:
    seen: dict[str, dict[str, str | None]] = {}
    for source in list_sources():
        try:
            result = source.fetch(mode="fixture")
        except Exception as exc:  # pragma: no cover - harvest helper
            print(f"skip {source.slug}: {exc}", file=sys.stderr)
            continue
        for row in result.records:
            ticker = (row.ticker or "").strip().upper() or None
            if ticker in {"—", "-", "–", "NONE"}:
                ticker = None
            ident = fund_identifier(row.ticker, row.fund_name, row.fund_family)
            key = ident.lower()
            existing = seen.get(key)
            if existing is None:
                seen[key] = {
                    "ticker": ticker,
                    "fund_identifier": ident,
                    "fund_name": row.fund_name,
                    "fund_family": row.fund_family,
                }
            elif ticker and not existing.get("ticker"):
                existing["ticker"] = ticker
    return list(seen.values())


def _yahoo_session():
    import httpx

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    client = httpx.Client(headers=headers, follow_redirects=True, timeout=15.0)
    client.get("https://fc.yahoo.com")
    client.get("https://finance.yahoo.com/")
    client.get("https://finance.yahoo.com/quote/AGTHX/")
    crumb_resp = client.get("https://query1.finance.yahoo.com/v1/test/getcrumb")
    crumb = crumb_resp.text.strip() if crumb_resp.status_code == 200 else ""
    if not crumb or "<" in crumb:
        crumb_resp = client.get("https://query2.finance.yahoo.com/v1/test/getcrumb")
        crumb = crumb_resp.text.strip() if crumb_resp.status_code == 200 else ""
    if not crumb or "<" in crumb:
        raise RuntimeError(f"Yahoo crumb failed: {crumb_resp.status_code} {crumb_resp.text[:80]}")
    return client, crumb


def _yahoo_category(ticker: str, client, crumb: str) -> str | None:
    url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}"
    try:
        response = client.get(url, params={"modules": "fundProfile", "crumb": crumb})
    except Exception:
        return None
    if response.status_code != 200:
        return None
    try:
        payload = response.json()
    except ValueError:
        return None
    results = (payload.get("quoteSummary") or {}).get("result") or []
    if not results:
        return None
    profile = results[0].get("fundProfile") or {}
    raw = profile.get("categoryName") or profile.get("category")
    if not raw:
        return None
    return canonical_category(str(raw))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yahoo", action="store_true", help="Fill remaining tickers from Yahoo fundProfile")
    parser.add_argument("--sleep", type=float, default=0.05, help="Delay between Yahoo calls")
    parser.add_argument("--limit", type=int, default=0, help="Max Yahoo lookups (0 = all remaining)")
    args = parser.parse_args()

    funds = _collect_fixture_funds()
    tickers: dict[str, str] = dict(_CURATED_TICKERS)
    identifiers: dict[str, str] = dict(_CURATED_IDENTIFIERS)
    sources: dict[str, str] = {k: "curated" for k in tickers}
    ident_sources: dict[str, str] = {k: "curated" for k in identifiers}

    for fund in funds:
        ticker = fund.get("ticker")
        ident = fund.get("fund_identifier")
        name = fund.get("fund_name")
        family = fund.get("fund_family")
        resolved = resolve_category(
            ticker=ticker, fund_identifier=ident, fund_name=name, fund_family=family
        )
        if not resolved:
            resolved = _name_category(name)
        if not resolved:
            continue
        if ticker:
            tickers.setdefault(ticker, resolved)
            sources.setdefault(ticker, "name_rule" if ticker not in _CURATED_TICKERS else "curated")
        if ident:
            identifiers.setdefault(ident, resolved)
            ident_sources.setdefault(
                ident, "name_rule" if ident not in _CURATED_IDENTIFIERS else "curated"
            )

    yahoo_ok = 0
    yahoo_fail = 0
    if args.yahoo:
        remaining = []
        ticker_to_ident: dict[str, str] = {}
        seen_tickers: set[str] = set()
        ident_keys = {k.lower() for k in identifiers}
        for fund in funds:
            ticker = fund.get("ticker")
            ident = fund.get("fund_identifier") or ""
            if ticker and ident:
                ticker_to_ident.setdefault(ticker, ident)
            if not ticker or ticker in seen_tickers:
                continue
            seen_tickers.add(ticker)
            if ticker in tickers or ident.lower() in ident_keys:
                continue
            remaining.append(ticker)
        if args.limit:
            remaining = remaining[: args.limit]
        print(f"Yahoo lookups remaining: {len(remaining)}", flush=True)
        client, crumb = _yahoo_session()
        try:
            for index, ticker in enumerate(remaining, start=1):
                category = _yahoo_category(ticker, client, crumb)
                if category is None and index % 200 == 0:
                    # Crumb can expire; refresh and retry this ticker.
                    try:
                        client.close()
                        client, crumb = _yahoo_session()
                        category = _yahoo_category(ticker, client, crumb)
                    except Exception as exc:
                        print(f"crumb refresh failed: {exc}", file=sys.stderr)
                if category:
                    tickers[ticker] = category
                    sources[ticker] = "yahoo_fund_profile"
                    ident = ticker_to_ident.get(ticker)
                    if ident:
                        identifiers.setdefault(ident, category)
                    yahoo_ok += 1
                else:
                    yahoo_fail += 1
                if index % 50 == 0:
                    print(f"  yahoo {index}/{len(remaining)} ok={yahoo_ok} miss={yahoo_fail}", flush=True)
                    _write_catalog(tickers, identifiers)
                time.sleep(args.sleep)
        finally:
            client.close()

    # Coverage vs fixture identities (runtime resolve, including name rules).
    categorized = 0
    for fund in funds:
        if resolve_category(
            ticker=fund.get("ticker"),
            fund_identifier=fund.get("fund_identifier"),
            fund_name=fund.get("fund_name"),
            fund_family=fund.get("fund_family"),
        ):
            categorized += 1
    # Temporarily write so resolve_category sees new mappings... write first then recount.

    _write_catalog(tickers, identifiers)

    from app.categories import reload_catalog

    reload_catalog()
    categorized = 0
    by_cat: dict[str, int] = {}
    for fund in funds:
        category = resolve_category(
            ticker=fund.get("ticker"),
            fund_identifier=fund.get("fund_identifier"),
            fund_name=fund.get("fund_name"),
            fund_family=fund.get("fund_family"),
        )
        if category:
            categorized += 1
            by_cat[category] = by_cat.get(category, 0) + 1
    total = len(funds)
    print(
        json.dumps(
            {
                "funds": total,
                "categorized": categorized,
                "uncategorized": total - categorized,
                "coverage_pct": round(100.0 * categorized / total, 1) if total else 0.0,
                "catalog_tickers": len(tickers),
                "catalog_identifiers": len(identifiers),
                "yahoo_ok": yahoo_ok,
                "yahoo_fail": yahoo_fail,
                "canonical_categories_used": len(by_cat),
                "wrote": str(OUT_PATH),
            },
            indent=2,
        )
    )
    unused = sorted(CANONICAL_CATEGORIES - set(by_cat))
    if unused:
        print(f"canonical unused ({len(unused)}): {', '.join(unused[:12])}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
