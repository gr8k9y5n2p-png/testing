"""Weekly NAV / last liquid close for every listed fund ticker.

Eric lock (2026-09-09): $/share tax math needs NAV universe-wide.

- Dist $ = est $/share × (holding $ / NAV)
- % of NAV = est $/share ÷ NAV

Never invent NAV or estimate amounts. Unknown tickers stay null.

Source preference:

1. Yahoo Finance last **regular close** (daily ``close``, not ``adjclose``).
   Mutual-fund prints are NAV; ETF prints are the last liquid close.
2. Issuer quote when a family adapter supplies one (none in v1).
3. Bundled fixture catalog / performance last close (tests + offline seed).
"""

from __future__ import annotations

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any, Iterable

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.aliases import display_ticker
from app.config import settings
from app.models import DistributionEstimate, FundNav

logger = logging.getLogger(__name__)

NAV_MODES = ("auto", "live", "fixture")
SOURCE_YAHOO = "yahoo_last_close"
SOURCE_ISSUER = "issuer"
SOURCE_FIXTURE = "fixture"
SOURCE_FIXTURE_FALLBACK = "fixture_fallback"

YAHOO_DAILY = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    "?interval=1d&range=10d"
)
YAHOO_SPARK = (
    "https://query1.finance.yahoo.com/v8/finance/spark"
    "?symbols={symbols}&range=10d&interval=1d"
)

NAV_PLACES = Decimal("0.000001")
_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9./-]{0,7}$")
_SKIP_PREFIXES = ("ZZ",)
_LIVE_WORKERS = 12
_SPARK_BATCH = 40


@dataclass(frozen=True)
class NavTarget:
    ticker: str
    fund_identifier: str | None = None
    fund_family: str | None = None
    fund_name: str | None = None


@dataclass(frozen=True)
class NavQuote:
    ticker: str
    nav_per_share: Decimal
    nav_as_of: date
    source: str
    source_url: str | None = None
    fund_identifier: str | None = None
    fund_family: str | None = None
    fund_name: str | None = None


@dataclass
class NavRefreshSummary:
    mode: str
    tickers_attempted: int = 0
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    unknown: int = 0
    errors: list[str] = field(default_factory=list)
    live_count: int = 0
    fixture_count: int = 0
    sample: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "tickers_attempted": self.tickers_attempted,
            "created": self.created,
            "updated": self.updated,
            "unchanged": self.unchanged,
            "unknown": self.unknown,
            "errors": list(self.errors),
            "live_count": self.live_count,
            "fixture_count": self.fixture_count,
            "sample": dict(self.sample),
        }

    def format_text(self) -> str:
        lines = [
            f"Weekly NAV refresh (mode={self.mode})",
            f"  tickers_attempted: {self.tickers_attempted}",
            f"  created: {self.created}",
            f"  updated: {self.updated}",
            f"  unchanged: {self.unchanged}",
            f"  unknown (null, not invented): {self.unknown}",
            f"  live={self.live_count} fixture={self.fixture_count}",
        ]
        if self.errors:
            lines.append("  errors: " + ", ".join(self.errors[:8]))
        for ticker, row in self.sample.items():
            lines.append(
                f"  {ticker}: nav_per_share={row.get('nav_per_share')} "
                f"nav_as_of={row.get('nav_as_of')} source={row.get('source')}"
            )
        return "\n".join(lines)

    def format_markdown(self) -> str:
        lines = [
            "## Weekly NAV refresh",
            "",
            f"- Mode: `{self.mode}`",
            f"- Tickers attempted: **{self.tickers_attempted}**",
            f"- Created: **{self.created}**",
            f"- Updated: **{self.updated}**",
            f"- Unchanged: **{self.unchanged}**",
            f"- Unknown (left null, never invented): **{self.unknown}**",
            f"- live={self.live_count}, fixture={self.fixture_count}",
            "",
        ]
        if self.sample:
            lines.extend(
                [
                    "| Ticker | NAV / share | As of | Source |",
                    "| --- | ---: | --- | --- |",
                ]
            )
            for ticker, row in self.sample.items():
                lines.append(
                    f"| `{ticker}` | {row.get('nav_per_share')} | "
                    f"{row.get('nav_as_of')} | {row.get('source')} |"
                )
            lines.append("")
        return "\n".join(lines)


def _money_nav(value: Decimal) -> Decimal:
    return value.quantize(NAV_PLACES, rounding=ROUND_HALF_EVEN)


def looks_like_ticker(value: str | None) -> bool:
    if not value:
        return False
    ticker = value.strip().upper()
    if any(ticker.startswith(prefix) for prefix in _SKIP_PREFIXES):
        return False
    return bool(_TICKER_RE.fullmatch(ticker))


def listed_ticker(ticker: str | None, fund_identifier: str | None) -> str | None:
    """Share-class ticker used for Yahoo / GET /funds. Null when unknown."""
    raw = display_ticker(ticker, fund_identifier)
    if looks_like_ticker(raw):
        return raw.strip().upper()
    if looks_like_ticker(ticker):
        return ticker.strip().upper()
    if looks_like_ticker(fund_identifier):
        return fund_identifier.strip().upper()
    return None


def _fixtures_nav_path() -> Path:
    return Path(settings.fixtures_dir) / "nav" / "latest.json"


def _performance_path(ticker: str) -> Path:
    return Path(settings.fixtures_dir) / "performance" / f"{ticker.upper()}.json"


def load_fixture_catalog() -> dict[str, NavQuote]:
    """Offline NAV catalog from fixtures/nav/latest.json. Never invents rows."""
    catalog: dict[str, NavQuote] = {}
    path = _fixtures_nav_path()
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        items = payload.get("items") if isinstance(payload, dict) else payload
        for row in items or []:
            quote = _quote_from_mapping(row, default_source=SOURCE_FIXTURE)
            if quote:
                catalog[quote.ticker] = quote
    return catalog


def _quote_from_mapping(row: dict[str, Any], *, default_source: str) -> NavQuote | None:
    ticker = listed_ticker(str(row.get("ticker") or ""), None)
    raw = row.get("nav_per_share")
    as_of_raw = row.get("nav_as_of") or row.get("as_of")
    if not ticker or raw is None or not as_of_raw:
        return None
    try:
        nav = _money_nav(Decimal(str(raw)))
        as_of = date.fromisoformat(str(as_of_raw))
    except (ArithmeticError, ValueError, TypeError):
        return None
    if nav <= 0:
        return None
    source = str(row.get("source") or default_source)
    if source == SOURCE_YAHOO:
        # Snapshot was captured from Yahoo; serving it offline is still a fixture.
        source = SOURCE_FIXTURE
    return NavQuote(
        ticker=ticker,
        nav_per_share=nav,
        nav_as_of=as_of,
        source=source,
        source_url=row.get("source_url"),
        fund_identifier=row.get("fund_identifier"),
        fund_family=row.get("fund_family"),
        fund_name=row.get("fund_name"),
    )


def _quote_from_performance(path: Path) -> NavQuote | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    ticker = listed_ticker(str(payload.get("ticker") or path.stem), None)
    points = payload.get("points") or []
    close = None
    as_of = None
    for row in reversed(points):
        raw = row.get("close")
        if raw is None:
            continue
        try:
            close = _money_nav(Decimal(str(raw)))
            as_of = date.fromisoformat(str(row.get("date")))
        except (ArithmeticError, ValueError, TypeError):
            continue
        if close > 0:
            break
        close = None
    if not ticker or close is None or as_of is None:
        return None
    return NavQuote(
        ticker=ticker,
        nav_per_share=close,
        nav_as_of=as_of,
        source=SOURCE_FIXTURE,
        source_url=str(payload.get("source_url") or path.name),
        fund_name=payload.get("name"),
    )


def fixture_quote(ticker: str, catalog: dict[str, NavQuote] | None = None) -> NavQuote | None:
    """latest.json first, then performance last regular close. None when unknown."""
    symbol = ticker.strip().upper()
    fixtures = catalog if catalog is not None else load_fixture_catalog()
    if symbol in fixtures:
        return fixtures[symbol]
    path = _performance_path(symbol)
    if path.exists():
        return _quote_from_performance(path)
    return None


def _parse_yahoo_closes(
    timestamps: list[Any],
    closes: list[Any],
    ticker: str,
    source_url: str,
    *,
    meta: dict[str, Any] | None = None,
) -> NavQuote | None:
    last: tuple[date, Decimal] | None = None
    for ts, value in zip(timestamps, closes):
        if value is None or ts is None:
            continue
        try:
            when = datetime.fromtimestamp(int(ts), tz=timezone.utc).date()
            price = _money_nav(Decimal(str(value)))
        except (ArithmeticError, ValueError, TypeError, OSError):
            continue
        if price > 0:
            last = (when, price)
    if last is None and meta:
        raw = meta.get("regularMarketPrice") or meta.get("chartPreviousClose")
        ts = meta.get("regularMarketTime")
        if raw is not None and ts is not None:
            try:
                when = datetime.fromtimestamp(int(ts), tz=timezone.utc).date()
                price = _money_nav(Decimal(str(raw)))
                if price > 0:
                    last = (when, price)
            except (ArithmeticError, ValueError, TypeError, OSError):
                last = None
    if last is None:
        return None
    when, price = last
    return NavQuote(
        ticker=ticker.upper(),
        nav_per_share=price,
        nav_as_of=when,
        source=SOURCE_YAHOO,
        source_url=source_url,
        fund_name=(meta or {}).get("longName") or (meta or {}).get("shortName"),
    )


def parse_yahoo_chart(payload: dict[str, Any], ticker: str, source_url: str) -> NavQuote | None:
    results = (payload.get("chart") or {}).get("result") or []
    if not results:
        return None
    result = results[0]
    timestamps = result.get("timestamp") or []
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    closes = quote.get("close") or []
    return _parse_yahoo_closes(
        timestamps, closes, ticker, source_url, meta=result.get("meta") or {}
    )


def parse_yahoo_spark(payload: dict[str, Any], source_url: str) -> dict[str, NavQuote]:
    out: dict[str, NavQuote] = {}
    results = (payload.get("spark") or {}).get("result") or []
    for result in results:
        symbol = str(result.get("symbol") or "").upper()
        responses = result.get("response") or []
        if not symbol or not responses:
            continue
        chart = responses[0]
        timestamps = chart.get("timestamp") or []
        quote = ((chart.get("indicators") or {}).get("quote") or [{}])[0]
        closes = quote.get("close") or []
        parsed = _parse_yahoo_closes(
            timestamps, closes, symbol, source_url, meta=chart.get("meta") or {}
        )
        if parsed:
            out[symbol] = parsed
    return out


def _yahoo_headers() -> dict[str, str]:
    return {
        "User-Agent": settings.http_user_agent,
        "Accept": "application/json",
    }


def fetch_yahoo_last_close(ticker: str, *, client: httpx.Client | None = None) -> NavQuote | None:
    """Last regular close / NAV. Returns None when Yahoo has no print — never invents."""
    symbol = ticker.strip().upper()
    url = YAHOO_DAILY.format(ticker=symbol)
    owns = client is None
    http = client or httpx.Client(timeout=settings.http_timeout_seconds, follow_redirects=True)
    try:
        response = http.get(url, headers=_yahoo_headers())
        response.raise_for_status()
        return parse_yahoo_chart(response.json(), symbol, url)
    except Exception as exc:
        logger.debug("Yahoo NAV miss for %s: %s", symbol, exc)
        return None
    finally:
        if owns:
            http.close()


def fetch_yahoo_spark_batch(
    tickers: list[str], *, client: httpx.Client | None = None
) -> dict[str, NavQuote]:
    symbols = [t.strip().upper() for t in tickers if looks_like_ticker(t)]
    if not symbols:
        return {}
    url = YAHOO_SPARK.format(symbols=",".join(symbols))
    owns = client is None
    http = client or httpx.Client(timeout=settings.http_timeout_seconds, follow_redirects=True)
    try:
        response = http.get(url, headers=_yahoo_headers())
        response.raise_for_status()
        return parse_yahoo_spark(response.json(), url)
    except Exception as exc:
        logger.debug("Yahoo spark miss for %s: %s", ",".join(symbols[:8]), exc)
        return {}
    finally:
        if owns:
            http.close()


def quote_for_ticker(
    ticker: str,
    *,
    mode: str,
    catalog: dict[str, NavQuote] | None = None,
    client: httpx.Client | None = None,
) -> NavQuote | None:
    symbol = ticker.strip().upper()
    requested = (mode or "auto").strip().lower()
    if requested not in NAV_MODES:
        requested = "auto"
    fixtures = catalog if catalog is not None else load_fixture_catalog()

    def from_fixture() -> NavQuote | None:
        quote = fixture_quote(symbol, catalog=fixtures)
        if quote is None:
            return None
        if requested != "fixture" and quote.source == SOURCE_FIXTURE:
            return NavQuote(
                ticker=quote.ticker,
                nav_per_share=quote.nav_per_share,
                nav_as_of=quote.nav_as_of,
                source=SOURCE_FIXTURE_FALLBACK,
                source_url=quote.source_url,
                fund_identifier=quote.fund_identifier,
                fund_family=quote.fund_family,
                fund_name=quote.fund_name,
            )
        return quote

    if requested == "fixture":
        return from_fixture()
    live = fetch_yahoo_last_close(symbol, client=client)
    if live:
        return live
    return from_fixture()


def list_nav_targets(session: Session) -> list[NavTarget]:
    """Distinct listed tickers already in the distribution book. Never invents funds."""
    rows = session.execute(
        select(
            DistributionEstimate.ticker,
            DistributionEstimate.fund_identifier,
            DistributionEstimate.fund_family,
            DistributionEstimate.fund_name,
        )
    ).all()
    seen: dict[str, NavTarget] = {}
    for ticker, ident, family, name in rows:
        listed = listed_ticker(ticker, ident)
        if not listed or listed in seen:
            continue
        seen[listed] = NavTarget(
            ticker=listed,
            fund_identifier=ident,
            fund_family=family,
            fund_name=name,
        )
    return [seen[key] for key in sorted(seen)]


def get_nav(session: Session, ticker: str | None) -> FundNav | None:
    listed = listed_ticker(ticker, ticker)
    if not listed:
        return None
    return session.scalar(select(FundNav).where(FundNav.ticker == listed))


def get_nav_map(session: Session, tickers: Iterable[str | None]) -> dict[str, FundNav]:
    keys = []
    for raw in tickers:
        listed = listed_ticker(raw, raw)
        if listed:
            keys.append(listed)
    if not keys:
        return {}
    rows = session.scalars(select(FundNav).where(FundNav.ticker.in_(set(keys)))).all()
    return {row.ticker: row for row in rows}


def lookup_nav(
    session: Session,
    *,
    ticker: str | None = None,
    fund_identifier: str | None = None,
) -> FundNav | None:
    listed = listed_ticker(ticker, fund_identifier)
    if listed:
        row = get_nav(session, listed)
        if row:
            return row
    if fund_identifier:
        return session.scalar(
            select(FundNav).where(FundNav.fund_identifier == fund_identifier.strip())
        )
    return None


def resolve_nav_per_share(
    session: Session,
    *,
    requested: Decimal | None,
    ticker: str | None = None,
    fund_identifier: str | None = None,
    rows: Iterable[Any] | None = None,
) -> tuple[Decimal | None, FundNav | None, str | None]:
    """Caller-supplied NAV wins. Otherwise use the stored weekly print."""
    if requested is not None:
        return requested, None, None
    if rows:
        for row in rows:
            found = lookup_nav(
                session,
                ticker=getattr(row, "ticker", None),
                fund_identifier=getattr(row, "fund_identifier", None),
            )
            if found:
                note = (
                    f"Used stored weekly NAV ({found.source} as of {found.nav_as_of.isoformat()})."
                )
                return found.nav_per_share, found, note
    found = lookup_nav(session, ticker=ticker, fund_identifier=fund_identifier)
    if found:
        note = f"Used stored weekly NAV ({found.source} as of {found.nav_as_of.isoformat()})."
        return found.nav_per_share, found, note
    return None, None, None


def upsert_nav(session: Session, quote: NavQuote) -> str:
    """Persist a real print. Older as_of does not overwrite a newer stored NAV."""
    if quote.nav_per_share <= 0:
        return "unknown"
    existing = session.scalar(select(FundNav).where(FundNav.ticker == quote.ticker))
    now = datetime.now(timezone.utc)
    if existing:
        if existing.nav_as_of and quote.nav_as_of < existing.nav_as_of:
            return "unchanged"
        same = (
            existing.nav_per_share == quote.nav_per_share
            and existing.nav_as_of == quote.nav_as_of
            and existing.source == quote.source
        )
        existing.nav_per_share = quote.nav_per_share
        existing.nav_as_of = quote.nav_as_of
        existing.source = quote.source
        existing.source_url = quote.source_url
        existing.fund_identifier = quote.fund_identifier or existing.fund_identifier
        existing.fund_family = quote.fund_family or existing.fund_family
        existing.fund_name = quote.fund_name or existing.fund_name
        existing.updated_at = now
        session.add(existing)
        session.flush()
        return "unchanged" if same else "updated"
    session.add(
        FundNav(
            ticker=quote.ticker,
            fund_identifier=quote.fund_identifier,
            fund_family=quote.fund_family,
            fund_name=quote.fund_name,
            nav_per_share=quote.nav_per_share,
            nav_as_of=quote.nav_as_of,
            source=quote.source,
            source_url=quote.source_url,
            updated_at=now,
        )
    )
    session.flush()
    return "created"


def nav_coverage(session: Session) -> dict[str, Any]:
    """Unique-fund NAV coverage. Denominator is listed-ticker funds, not name-only rows."""
    targets = list_nav_targets(session)
    stored = get_nav_map(session, [row.ticker for row in targets])
    with_nav = sum(1 for row in targets if row.ticker in stored)
    total = len(targets)
    return {
        "listed_tickers": total,
        "with_nav": with_nav,
        "unknown": total - with_nav,
        "coverage_pct": round(100.0 * with_nav / total, 1) if total else 0.0,
    }


def _attach_target(quote: NavQuote, target: NavTarget) -> NavQuote:
    return NavQuote(
        ticker=quote.ticker,
        nav_per_share=quote.nav_per_share,
        nav_as_of=quote.nav_as_of,
        source=quote.source,
        source_url=quote.source_url,
        fund_identifier=target.fund_identifier or quote.fund_identifier,
        fund_family=target.fund_family or quote.fund_family,
        fund_name=target.fund_name or quote.fund_name,
    )


def _fetch_live_quotes(targets: list[NavTarget]) -> dict[str, NavQuote]:
    found: dict[str, NavQuote] = {}
    batches = [targets[i : i + _SPARK_BATCH] for i in range(0, len(targets), _SPARK_BATCH)]
    with httpx.Client(timeout=settings.http_timeout_seconds, follow_redirects=True) as client:
        for batch in batches:
            spark = fetch_yahoo_spark_batch([row.ticker for row in batch], client=client)
            found.update(spark)
        missing = [row for row in targets if row.ticker not in found]

        def _one(target: NavTarget) -> tuple[str, NavQuote | None]:
            return target.ticker, fetch_yahoo_last_close(target.ticker, client=None)

        if missing:
            workers = min(_LIVE_WORKERS, max(1, len(missing)))
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(_one, target) for target in missing]
                for future in as_completed(futures):
                    ticker, quote = future.result()
                    if quote:
                        found[ticker] = quote
    return found


def refresh_navs(
    session: Session,
    *,
    mode: str = "auto",
    tickers: list[str] | None = None,
    sample_tickers: tuple[str, ...] = ("ABALX", "VFIAX", "SPY", "DBEF"),
) -> NavRefreshSummary:
    """Refresh NAV for every registered listed ticker. Null when unknown."""
    requested = (mode or "auto").strip().lower()
    if requested not in NAV_MODES:
        raise ValueError(f"NAV mode must be one of {NAV_MODES}, got {mode!r}")

    targets = list_nav_targets(session)
    if tickers:
        wanted = {item.strip().upper() for item in tickers if item}
        extra = [
            NavTarget(ticker=item)
            for item in sorted(wanted)
            if item not in {row.ticker for row in targets} and looks_like_ticker(item)
        ]
        targets = [row for row in targets if row.ticker in wanted] + extra

    summary = NavRefreshSummary(mode=requested, tickers_attempted=len(targets))
    catalog = load_fixture_catalog()
    live_map: dict[str, NavQuote] = {}
    if requested in {"auto", "live"} and targets:
        try:
            live_map = _fetch_live_quotes(targets)
        except Exception as exc:
            summary.errors.append(str(exc))
            live_map = {}

    for target in targets:
        quote: NavQuote | None = live_map.get(target.ticker)
        if quote is None:
            fixture = fixture_quote(target.ticker, catalog=catalog)
            if fixture:
                if requested == "fixture":
                    quote = fixture
                else:
                    quote = NavQuote(
                        ticker=fixture.ticker,
                        nav_per_share=fixture.nav_per_share,
                        nav_as_of=fixture.nav_as_of,
                        source=SOURCE_FIXTURE_FALLBACK,
                        source_url=fixture.source_url,
                        fund_identifier=fixture.fund_identifier,
                        fund_family=fixture.fund_family,
                        fund_name=fixture.fund_name,
                    )
        if quote is None:
            summary.unknown += 1
            continue
        quote = _attach_target(quote, target)
        action = upsert_nav(session, quote)
        if action == "created":
            summary.created += 1
        elif action == "updated":
            summary.updated += 1
        else:
            summary.unchanged += 1
        if quote.source == SOURCE_YAHOO:
            summary.live_count += 1
        else:
            summary.fixture_count += 1

    session.flush()
    stored = get_nav_map(session, list(sample_tickers))
    for ticker in sample_tickers:
        row = stored.get(ticker)
        summary.sample[ticker] = (
            {
                "nav_per_share": str(row.nav_per_share),
                "nav_as_of": row.nav_as_of.isoformat(),
                "source": row.source,
            }
            if row
            else {"nav_per_share": None, "nav_as_of": None, "source": None}
        )
    return summary


def write_fixture_catalog(session: Session, path: Path | None = None) -> Path:
    """Dump stored NAVs for offline seed. Only real prints — never invented rows."""
    dest = path or _fixtures_nav_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    rows = list(session.scalars(select(FundNav).order_by(FundNav.ticker.asc())).all())
    payload = {
        "field": "regular_close",
        "field_notes": (
            "Last liquid close / mutual-fund NAV (Yahoo daily close, not adjclose). "
            "Null when unknown — never invented."
        ),
        "as_of": date.today().isoformat(),
        "count": len(rows),
        "items": [
            {
                "ticker": row.ticker,
                "nav_per_share": str(row.nav_per_share),
                "nav_as_of": row.nav_as_of.isoformat(),
                "source": SOURCE_YAHOO if row.source == SOURCE_YAHOO else SOURCE_FIXTURE,
                "source_url": row.source_url,
                "fund_identifier": row.fund_identifier,
                "fund_family": row.fund_family,
                "fund_name": row.fund_name,
            }
            for row in rows
        ],
    }
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return dest


def unique_fund_nav_coverage(session: Session) -> dict[str, Any]:
    """Coverage against unique stored funds (GET /funds denominator)."""
    from app.crud import _summary_from_row, _unique_fund_query

    stmt, total = _unique_fund_query(session)
    funds = [_summary_from_row(row) for row in session.execute(stmt).all()]
    tickers = [listed_ticker(item.ticker, item.fund_identifier) for item in funds]
    stored = get_nav_map(session, tickers)
    with_nav = sum(1 for ticker in tickers if ticker and ticker in stored)
    return {
        "unique_funds": total,
        "with_nav": with_nav,
        "unknown": total - with_nav,
        "coverage_pct": round(100.0 * with_nav / total, 1) if total else 0.0,
    }
