"""Growth of $X total-return series for Modules charts.

Independent of tax / illustrate / weekly distribution refresh.
v1 uses free public Yahoo Finance monthly adjusted close (split + dividend
adjusted) as a total-return proxy. Default benchmarks are ETFs only:

- equity → SPY (tracks S&P 500)
- fixed_income → AGG (tracks Bloomberg US Aggregate)
- international → VXUS (tracks MSCI ACWI ex USA)

v1 has no licensed-index path. The plotted series is always the ETF.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any, Literal

import httpx
from fastapi import HTTPException

from app.config import settings
from app.schemas import PerformanceGrowthRequest

AssetClass = Literal["equity", "fixed_income", "international"]

YAHOO_CHART = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    "?interval=1mo&range=10y&events=div%2Csplit"
)

DISCLAIMERS = (
    "Performance is illustrative only and is not tax advice.",
    "Taxable distribution estimates and YoY tax bars stay on POST /illustrate and POST /illustrate/compare.",
    "Monthly points use Yahoo Finance adjusted close (splits and dividends). That is a free public total-return proxy, not an official index level.",
    "Default benchmarks are ETFs (SPY, AGG, VXUS), not licensed S&P 500, Bloomberg US Aggregate, or MSCI ACWI ex USA index feeds.",
    "Past performance does not predict future results.",
)

# Slug / alias → listed ticker for the performance catalog.
FUND_ALIASES: dict[str, str] = {
    "AGTHX": "AGTHX",
    "THE-GROWTH-FUND-OF-AMERICA": "AGTHX",
    "THEGROWTHFUNDOFAMERICA": "AGTHX",
    "AMCPX": "AMCPX",
    "AMCAP": "AMCPX",
    "AMCAP-FUND": "AMCPX",
    "ABALX": "ABALX",
    "AMERICAN-BALANCED-FUND": "ABALX",
    "FBGRX": "FBGRX",
    "VFIAX": "VFIAX",
    "VIGAX": "VIGAX",
    "VBIAX": "VBIAX",
    "DODIX": "DODIX",
    "DODGX": "DODGX",
    "VTIAX": "VTIAX",
    "TRBCX": "TRBCX",
    "SWTSX": "SWTSX",
    "SWANX": "SWANX",
    "NOSIX": "NOSIX",
    "MDDVX": "MDDVX",
    "JDCAX": "JDCAX",
    "ALLW": "ALLW",
    "SPY": "SPY",
    "AGG": "AGG",
    "VXUS": "VXUS",
    "SGENX": "SGENX",
    "FEVAX": "FEVAX",
    "GDX": "GDX",
    "SMH": "SMH",
    "GTR": "GTR",
    "WTPI": "WTPI",
    "HACAX": "HACAX",
    "HAVLX": "HAVLX",
    "VETAX": "VETAX",
    "FEFAX": "FEFAX",
    "YACKX": "YACKX",
    "NWHOX": "NWHOX",
    "NLCAX": "NLCAX",
    "OAKMX": "OAKMX",
    "TBGVX": "TBGVX",
    "GABGX": "GABGX",
    "RYTRX": "RYTRX",
    "MMEAX": "MMEAX",
    "BAFFX": "BAFFX",
    "BGFIX": "BGFIX",
    "AQGIX": "AQGIX",
    "CIVIX": "CIVIX",
    "CHUSX": "CHUSX",
    "HLMNX": "HLMNX",
    "MAPTX": "MAPTX",
    "TGDIX": "TGDIX",
    "BGLD": "BGLD",
    "MWMIX": "MWMIX",
    "FEGE": "FEGE",
    "INIVX": "INIVX",
    "FEOE": "FEOE",
    "XC": "XC",
    "FVD": "FVD",
    "JENSX": "JENSX",
}

FUND_META: dict[str, dict[str, str]] = {
    "AGTHX": {"name": "The Growth Fund of America", "asset_class": "equity"},
    "AMCPX": {"name": "AMCAP Fund", "asset_class": "equity"},
    "ABALX": {"name": "American Balanced Fund", "asset_class": "equity"},
    "FBGRX": {"name": "Fidelity Blue Chip Growth", "asset_class": "equity"},
    "VFIAX": {"name": "Vanguard 500 Index Admiral", "asset_class": "equity"},
    "VIGAX": {"name": "Vanguard Growth Index Admiral", "asset_class": "equity"},
    "VBIAX": {"name": "Vanguard Balanced Index Admiral", "asset_class": "equity"},
    "DODIX": {"name": "Dodge & Cox Income", "asset_class": "fixed_income"},
    "DODGX": {"name": "Dodge & Cox Stock", "asset_class": "equity"},
    "VTIAX": {"name": "Vanguard Total International Stock Index Admiral", "asset_class": "international"},
    "TRBCX": {"name": "T. Rowe Price Blue Chip Growth", "asset_class": "equity"},
    "SWTSX": {"name": "Schwab Total Stock Market Index", "asset_class": "equity"},
    "SWANX": {"name": "Schwab Core Equity", "asset_class": "equity"},
    "NOSIX": {"name": "Northern Stock Index", "asset_class": "equity"},
    "MDDVX": {"name": "BlackRock Equity Dividend Investor A", "asset_class": "equity"},
    "JDCAX": {"name": "Janus Henderson Forty A", "asset_class": "equity"},
    "ALLW": {"name": "SPDR Bridgewater All Weather ETF", "asset_class": "equity"},
    "SPY": {"name": "SPDR S&P 500 ETF Trust", "asset_class": "equity"},
    "AGG": {"name": "iShares Core U.S. Aggregate Bond ETF", "asset_class": "fixed_income"},
    "VXUS": {"name": "Vanguard Total International Stock ETF", "asset_class": "international"},
    "SGENX": {"name": "First Eagle Global Fund A", "asset_class": "equity"},
    "FEVAX": {"name": "First Eagle U.S. Fund A", "asset_class": "equity"},
    "GDX": {"name": "VanEck Gold Miners ETF", "asset_class": "equity"},
    "SMH": {"name": "VanEck Semiconductor ETF", "asset_class": "equity"},
    "GTR": {"name": "WisdomTree Target Range Fund", "asset_class": "equity"},
    "WTPI": {"name": "WisdomTree Equity Premium Income Fund", "asset_class": "equity"},
    "HACAX": {"name": "Harbor Capital Appreciation Institutional", "asset_class": "equity"},
    "HAVLX": {"name": "Harbor Large Cap Value Institutional", "asset_class": "equity"},
    "VETAX": {"name": "Victory Sycamore Established Value A", "asset_class": "equity"},
    "FEFAX": {"name": "First Eagle Rising Dividend Fund A", "asset_class": "equity"},
    "YACKX": {"name": "AMG Yacktman Fund I", "asset_class": "equity"},
    "NWHOX": {"name": "Nationwide Bailard Technology & Science A", "asset_class": "equity"},
    "NLCAX": {"name": "Voya Large-Cap Growth A", "asset_class": "equity"},
    "OAKMX": {"name": "Oakmark Fund Investor", "asset_class": "equity"},
    "TBGVX": {"name": "Tweedy, Browne International Value", "asset_class": "international"},
    "GABGX": {"name": "Gabelli Growth AAA", "asset_class": "equity"},
    "RYTRX": {"name": "Royce Small-Cap Total Return Investment", "asset_class": "equity"},
    "MMEAX": {"name": "Victory Integrity Discovery A", "asset_class": "equity"},
    "BAFFX": {"name": "Brown Advisory Flexible Equity Institutional", "asset_class": "equity"},
    "BGFIX": {"name": "William Blair Growth I", "asset_class": "equity"},
    "AQGIX": {"name": "AQR Global Equity I", "asset_class": "equity"},
    "CIVIX": {"name": "Causeway International Value Institutional", "asset_class": "international"},
    "CHUSX": {"name": "Alger Global Equity A", "asset_class": "equity"},
    "HLMNX": {"name": "Harding Loevner International Equity Investor", "asset_class": "international"},
    "MAPTX": {"name": "Matthews Pacific Tiger Investor", "asset_class": "international"},
    "TGDIX": {"name": "TCW Relative Value Large Cap I", "asset_class": "equity"},
    "BGLD": {"name": "FT Vest Gold Strategy Quarterly Buffer ETF", "asset_class": "equity"},
    "MWMIX": {"name": "VanEck Morningstar Wide Moat I", "asset_class": "equity"},
    "FEGE": {"name": "First Eagle Global Equity ETF", "asset_class": "equity"},
    "INIVX": {"name": "VanEck International Investors Gold Fund A", "asset_class": "equity"},
    "FEOE": {"name": "First Eagle Overseas Equity ETF", "asset_class": "international"},
    "XC": {
        "name": "WisdomTree True Emerging Markets Fund",
        "asset_class": "international",
    },
    "FVD": {"name": "First Trust Value Line Dividend Index Fund", "asset_class": "equity"},
    "JENSX": {"name": "Jensen Quality Growth Fund J", "asset_class": "equity"},
}

DEFAULT_BENCHMARKS: dict[AssetClass, dict[str, str]] = {
    "equity": {
        "ticker": "SPY",
        "label": "S&P 500 (via SPY ETF total return)",
        "tracks": "S&P 500",
    },
    "fixed_income": {
        "ticker": "AGG",
        "label": "Bloomberg US Aggregate (via AGG ETF total return)",
        "tracks": "Bloomberg US Aggregate",
    },
    "international": {
        "ticker": "VXUS",
        "label": "MSCI ACWI ex USA (via VXUS ETF total return)",
        "tracks": "MSCI ACWI ex USA",
    },
}

PROXY_BENCHMARKS = frozenset({"SPY", "AGG", "VXUS"})


@dataclass(frozen=True)
class PricePoint:
    date: date
    adj_close: Decimal


@dataclass
class LoadedSeries:
    ticker: str
    name: str
    source: str
    source_url: str
    points: list[PricePoint]
    as_of: date


def _norm_key(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value.strip().upper()).strip("-")


def resolve_ticker(ticker: str | None, fund_identifier: str | None) -> str:
    for raw in (ticker, fund_identifier):
        if not raw:
            continue
        key = _norm_key(raw)
        if key in FUND_ALIASES:
            return FUND_ALIASES[key]
        compact = key.replace("-", "")
        if compact in FUND_ALIASES:
            return FUND_ALIASES[compact]
        if raw.strip().isalpha() and 2 <= len(raw.strip()) <= 5:
            return raw.strip().upper()
    raise HTTPException(status_code=404, detail="Unknown fund ticker or fund_identifier for performance.")


def infer_asset_class(ticker: str, explicit: AssetClass | None) -> AssetClass:
    if explicit:
        return explicit
    meta = FUND_META.get(ticker)
    if meta:
        return meta["asset_class"]  # type: ignore[return-value]
    return "equity"


def resolve_benchmark(
    *,
    explicit: str | None,
    asset_class: AssetClass,
) -> tuple[str, str, str, bool]:
    if explicit:
        bench = explicit.upper()
        spec = next((row for row in DEFAULT_BENCHMARKS.values() if row["ticker"] == bench), None)
        if spec:
            return bench, spec["label"], spec["tracks"], bench in PROXY_BENCHMARKS
        name = FUND_META.get(bench, {}).get("name") or bench
        return bench, name, name, False
    spec = DEFAULT_BENCHMARKS[asset_class]
    return spec["ticker"], spec["label"], spec["tracks"], spec["ticker"] in PROXY_BENCHMARKS


def _fixtures_dir() -> Path:
    return Path(settings.fixtures_dir) / "performance"


def _load_fixture(ticker: str) -> LoadedSeries:
    path = _fixtures_dir() / f"{ticker.upper()}.json"
    if not path.exists():
        raise FileNotFoundError(f"No performance fixture for {ticker}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    points = [
        PricePoint(date=date.fromisoformat(row["date"]), adj_close=Decimal(str(row["adj_close"])))
        for row in payload["points"]
        if row.get("adj_close") is not None
    ]
    if not points:
        raise FileNotFoundError(f"Empty performance fixture for {ticker}")
    return LoadedSeries(
        ticker=str(payload.get("ticker") or ticker).upper(),
        name=str(payload.get("name") or FUND_META.get(ticker, {}).get("name") or ticker),
        source="fixture",
        source_url=str(payload.get("source_url") or path.name),
        points=points,
        as_of=date.fromisoformat(payload["as_of"]) if payload.get("as_of") else points[-1].date,
    )


def _parse_yahoo_chart(payload: dict[str, Any], ticker: str, source_url: str) -> LoadedSeries:
    results = (payload.get("chart") or {}).get("result") or []
    if not results:
        raise ValueError(f"Yahoo chart returned no result for {ticker}")
    result = results[0]
    timestamps = result.get("timestamp") or []
    adj = ((result.get("indicators") or {}).get("adjclose") or [{}])[0].get("adjclose") or []
    points: list[PricePoint] = []
    from datetime import datetime, timezone

    for ts, value in zip(timestamps, adj):
        if value is None:
            continue
        when = datetime.fromtimestamp(int(ts), tz=timezone.utc).date()
        points.append(
            PricePoint(
                date=when,
                adj_close=Decimal(str(value)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN),
            )
        )
    if not points:
        raise ValueError(f"Yahoo chart had no adjusted-close points for {ticker}")
    meta = result.get("meta") or {}
    return LoadedSeries(
        ticker=str(meta.get("symbol") or ticker).upper(),
        name=str(meta.get("longName") or meta.get("shortName") or FUND_META.get(ticker, {}).get("name") or ticker),
        source="yahoo_chart",
        source_url=source_url,
        points=points,
        as_of=points[-1].date,
    )


def _fetch_yahoo(ticker: str) -> LoadedSeries:
    url = YAHOO_CHART.format(ticker=ticker.upper())
    headers = {
        "User-Agent": settings.http_user_agent,
        "Accept": "application/json",
    }
    with httpx.Client(timeout=settings.http_timeout_seconds, follow_redirects=True) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return _parse_yahoo_chart(response.json(), ticker, url)


def load_series(ticker: str, mode: str) -> LoadedSeries:
    ticker = ticker.upper()
    notes_mode = mode
    if notes_mode == "fixture":
        return _load_fixture(ticker)
    if notes_mode == "live":
        try:
            return _fetch_yahoo(ticker)
        except Exception:
            fixture = _load_fixture(ticker)
            fixture.source = "fixture_fallback"
            return fixture
    # auto
    try:
        return _fetch_yahoo(ticker)
    except Exception:
        fixture = _load_fixture(ticker)
        fixture.source = "fixture_fallback"
        return fixture


def _month_key(when: date) -> tuple[int, int]:
    return (when.year, when.month)


def _by_month(points: list[PricePoint]) -> dict[tuple[int, int], PricePoint]:
    out: dict[tuple[int, int], PricePoint] = {}
    for point in points:
        out[_month_key(point.date)] = point
    return out


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def _ret(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)


def build_growth(
    *,
    fund: LoadedSeries,
    benchmark: LoadedSeries,
    start_dollars: Decimal,
    start_date: date | None,
    end_date: date | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], date, date]:
    fund_m = _by_month(fund.points)
    bench_m = _by_month(benchmark.points)
    months = sorted(set(fund_m) & set(bench_m))
    if start_date:
        months = [m for m in months if date(m[0], m[1], 1) >= date(start_date.year, start_date.month, 1)]
    if end_date:
        months = [m for m in months if date(m[0], m[1], 1) <= date(end_date.year, end_date.month, 1)]
    if len(months) < 2:
        raise HTTPException(
            status_code=422,
            detail="Not enough overlapping monthly points in the requested date range.",
        )

    fund_base = fund_m[months[0]].adj_close
    bench_base = bench_m[months[0]].adj_close
    if fund_base <= 0 or bench_base <= 0:
        raise HTTPException(status_code=422, detail="Invalid adjusted-close base for growth.")

    fund_out: list[dict[str, Any]] = []
    bench_out: list[dict[str, Any]] = []
    prev_fund: Decimal | None = None
    prev_bench: Decimal | None = None
    for month in months:
        fpt = fund_m[month]
        bpt = bench_m[month]
        fund_ret = None if prev_fund is None else _ret((fpt.adj_close / prev_fund) - Decimal("1"))
        bench_ret = None if prev_bench is None else _ret((bpt.adj_close / prev_bench) - Decimal("1"))
        fund_out.append(
            {
                "date": fpt.date,
                "adj_close": fpt.adj_close,
                "monthly_return": fund_ret,
                "growth_of_x": _money(start_dollars * (fpt.adj_close / fund_base)),
            }
        )
        bench_out.append(
            {
                "date": bpt.date,
                "adj_close": bpt.adj_close,
                "monthly_return": bench_ret,
                "growth_of_x": _money(start_dollars * (bpt.adj_close / bench_base)),
            }
        )
        prev_fund = fpt.adj_close
        prev_bench = bpt.adj_close

    return fund_out, bench_out, fund_out[0]["date"], fund_out[-1]["date"]


def growth_of_x(payload: PerformanceGrowthRequest) -> dict[str, Any]:
    resolved_mode = (payload.mode or settings.fetch_mode or "fixture").strip().lower()
    if resolved_mode not in {"fixture", "live", "auto"}:
        resolved_mode = "fixture"

    fund_ticker = resolve_ticker(payload.ticker, payload.fund_identifier)
    hint = payload.asset_class or payload.benchmark_hint
    klass = infer_asset_class(fund_ticker, hint)
    bench_ticker, bench_label, bench_tracks, is_proxy = resolve_benchmark(
        explicit=payload.benchmark,
        asset_class=klass,
    )

    try:
        fund_series = load_series(fund_ticker, resolved_mode)
        bench_series = load_series(bench_ticker, resolved_mode)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    fund_points, bench_points, first, last = build_growth(
        fund=fund_series,
        benchmark=bench_series,
        start_dollars=payload.start_dollars,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )

    source = fund_series.source
    if fund_series.source != bench_series.source:
        source = f"{fund_series.source}+{bench_series.source}"

    fund_name = FUND_META.get(fund_ticker, {}).get("name") or fund_series.name
    return {
        "fund_ticker": fund_ticker,
        "fund_identifier": (payload.fund_identifier or fund_ticker),
        "fund_name": fund_name,
        "asset_class": klass,
        "start_dollars": payload.start_dollars,
        "start_date": first,
        "end_date": last,
        "as_of": max(fund_series.as_of, bench_series.as_of, last),
        "frequency": "monthly",
        "mode": resolved_mode if source == "yahoo_chart" else (
            "fixture" if source.startswith("fixture") else resolved_mode
        ),
        "source": source,
        "source_urls": list(dict.fromkeys([fund_series.source_url, bench_series.source_url])),
        "benchmark_id": bench_ticker,
        "benchmark_label": bench_label,
        "benchmark_tracks": bench_tracks,
        "is_proxy": is_proxy,
        "fund": {
            "ticker": fund_ticker,
            "name": fund_name,
            "currency": "USD",
            "price_unit": "usd_per_share_adjusted",
            "return_unit": "decimal",
            "growth_unit": "usd",
            "points": fund_points,
        },
        "benchmark": {
            "ticker": bench_ticker,
            "name": bench_series.name,
            "currency": "USD",
            "price_unit": "usd_per_share_adjusted",
            "return_unit": "decimal",
            "growth_unit": "usd",
            "points": bench_points,
        },
        "disclaimers": list(DISCLAIMERS),
    }
