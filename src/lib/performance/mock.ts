import {
  DEFAULT_START_DOLLARS,
  type PerformanceAssetClass,
  type PerformanceGrowthRequest,
  type PerformancePoint,
  type PerformanceResponse,
  type PerformanceSeriesOut,
} from "@/lib/performance/types";

type FundSpec = {
  ticker: string;
  name: string;
  asset_class: PerformanceAssetClass;
  aliases: string[];
  seed: number;
  cagr: number;
  vol: number;
  startAdj: number;
};

const FUND_SPECS: FundSpec[] = [
  {
    ticker: "AGTHX",
    name: "The Growth Fund of America",
    asset_class: "equity",
    aliases: ["THE-GROWTH-FUND-OF-AMERICA", "THEGROWTHFUNDOFAMERICA"],
    seed: 11,
    cagr: 0.125,
    vol: 0.034,
    startAdj: 20.73,
  },
  {
    ticker: "AMCPX",
    name: "AMCAP Fund",
    asset_class: "equity",
    aliases: ["AMCAP", "AMCAP-FUND"],
    seed: 22,
    cagr: 0.112,
    vol: 0.03,
    startAdj: 18.4,
  },
  {
    ticker: "FBGRX",
    name: "Fidelity Blue Chip Growth",
    asset_class: "equity",
    aliases: [],
    seed: 33,
    cagr: 0.158,
    vol: 0.042,
    startAdj: 62.1,
  },
  {
    ticker: "VFIAX",
    name: "Vanguard 500 Index Admiral",
    asset_class: "equity",
    aliases: [],
    seed: 44,
    cagr: 0.132,
    vol: 0.028,
    startAdj: 198.5,
  },
  {
    ticker: "DODIX",
    name: "Dodge & Cox Income",
    asset_class: "fixed_income",
    aliases: [],
    seed: 55,
    cagr: 0.022,
    vol: 0.012,
    startAdj: 12.8,
  },
  {
    ticker: "VTIAX",
    name: "Vanguard Total International Stock Index Admiral",
    asset_class: "international",
    aliases: [],
    seed: 66,
    cagr: 0.061,
    vol: 0.026,
    startAdj: 24.2,
  },
  {
    ticker: "SPY",
    name: "SPDR S&P 500 ETF Trust",
    asset_class: "equity",
    aliases: [],
    seed: 77,
    cagr: 0.135,
    vol: 0.027,
    startAdj: 214.2,
  },
  {
    ticker: "AGG",
    name: "iShares Core U.S. Aggregate Bond ETF",
    asset_class: "fixed_income",
    aliases: [],
    seed: 88,
    cagr: 0.018,
    vol: 0.01,
    startAdj: 108.4,
  },
  {
    ticker: "VXUS",
    name: "Vanguard Total International Stock ETF",
    asset_class: "international",
    aliases: [],
    seed: 99,
    cagr: 0.058,
    vol: 0.025,
    startAdj: 44.6,
  },
];

const DEFAULT_BENCHMARKS: Record<
  PerformanceAssetClass,
  { ticker: string; label: string; tracks: string }
> = {
  equity: {
    ticker: "SPY",
    label: "S&P 500 (via SPY ETF total return)",
    tracks: "S&P 500",
  },
  fixed_income: {
    ticker: "AGG",
    label: "Bloomberg US Aggregate (via AGG ETF total return)",
    tracks: "Bloomberg US Aggregate",
  },
  international: {
    ticker: "VXUS",
    label: "MSCI ACWI ex USA (via VXUS ETF total return)",
    tracks: "MSCI ACWI ex USA",
  },
};

const PROXY_BENCHMARKS = new Set(["SPY", "AGG", "VXUS"]);

const DISCLAIMERS = [
  "Performance is illustrative only and is not tax advice.",
  "Taxable distribution estimates and YoY tax bars stay on POST /illustrate and POST /illustrate/compare.",
  "Monthly points are a localhost fixture approximating Yahoo Finance adjusted close. That is a free public total-return proxy, not an official index level.",
  "Default benchmarks are ETFs (SPY, AGG, VXUS), not licensed S&P 500, Bloomberg US Aggregate, or MSCI ACWI ex USA index feeds.",
  "Past performance does not predict future results.",
];

export class PerformanceMockError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

function normKey(value: string): string {
  return value
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function findSpec(raw: string): FundSpec | undefined {
  const key = normKey(raw);
  const compact = key.replace(/-/g, "");
  return FUND_SPECS.find(
    (spec) =>
      spec.ticker === key ||
      spec.ticker === compact ||
      spec.aliases.includes(key) ||
      spec.aliases.includes(compact),
  );
}

export function resolvePerformanceTicker(
  ticker?: string | null,
  fundIdentifier?: string | null,
): string {
  for (const raw of [ticker, fundIdentifier]) {
    if (!raw?.trim()) continue;
    const spec = findSpec(raw);
    if (spec) return spec.ticker;
    const trimmed = raw.trim();
    if (/^[A-Za-z]{2,5}$/.test(trimmed)) {
      throw new PerformanceMockError(`No performance fixture for ${trimmed.toUpperCase()}`, 404);
    }
  }
  throw new PerformanceMockError("Unknown fund ticker or fund_identifier for performance.", 404);
}

function specFor(ticker: string): FundSpec {
  const spec = FUND_SPECS.find((row) => row.ticker === ticker);
  if (!spec) {
    throw new PerformanceMockError(`No performance fixture for ${ticker}`, 404);
  }
  return spec;
}

function mulberry32(seed: number) {
  let a = seed;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function money(value: number): number {
  return Math.round(value * 100) / 100;
}

function ret(value: number): number {
  return Math.round(value * 1_000_000) / 1_000_000;
}

function monthDates(): string[] {
  const out: string[] = [];
  for (let year = 2016; year <= 2026; year += 1) {
    const startMonth = year === 2016 ? 10 : 1;
    const endMonth = year === 2026 ? 9 : 12;
    for (let month = startMonth; month <= endMonth; month += 1) {
      out.push(`${year}-${String(month).padStart(2, "0")}-01`);
    }
  }
  return out;
}

function generateAdjCloses(spec: FundSpec): { date: string; adj_close: number }[] {
  const dates = monthDates();
  const rng = mulberry32(spec.seed * 997);
  const monthly = (1 + spec.cagr) ** (1 / 12) - 1;
  let price = spec.startAdj;
  return dates.map((date) => {
    const shock = (rng() - 0.48) * spec.vol;
    price = Math.max(0.5, price * (1 + monthly + shock));
    return { date, adj_close: Math.round(price * 1_000_000) / 1_000_000 };
  });
}

function windowPoints(
  points: { date: string; adj_close: number }[],
  startDate?: string | null,
  endDate?: string | null,
) {
  return points.filter((point) => {
    if (startDate && point.date < startDate.slice(0, 7)) return false;
    if (endDate && point.date > endDate.slice(0, 7) + "-31") return false;
    return true;
  });
}

function toSeries(
  spec: FundSpec,
  startDollars: number,
  startDate?: string | null,
  endDate?: string | null,
): { series: PerformanceSeriesOut; first: string; last: string } {
  const raw = windowPoints(generateAdjCloses(spec), startDate, endDate);
  if (raw.length < 2) {
    throw new PerformanceMockError(
      "Not enough overlapping monthly points in the requested date range.",
      422,
    );
  }
  const base = raw[0].adj_close;
  if (!(base > 0)) {
    throw new PerformanceMockError("Invalid adjusted-close base for growth.", 422);
  }
  const points: PerformancePoint[] = raw.map((row, index) => {
    const prev = index === 0 ? null : raw[index - 1].adj_close;
    return {
      date: row.date,
      adj_close: row.adj_close,
      monthly_return: prev == null ? null : ret(row.adj_close / prev - 1),
      growth_of_x: money(startDollars * (row.adj_close / base)),
    };
  });
  return {
    series: {
      ticker: spec.ticker,
      name: spec.name,
      currency: "USD",
      price_unit: "usd_per_share_adjusted",
      return_unit: "decimal",
      growth_unit: "usd",
      points,
    },
    first: points[0].date,
    last: points[points.length - 1].date,
  };
}

function resolveBenchmark(
  explicit: string | null | undefined,
  assetClass: PerformanceAssetClass,
) {
  if (explicit?.trim()) {
    const ticker = explicit.trim().toUpperCase();
    const preset = Object.values(DEFAULT_BENCHMARKS).find((row) => row.ticker === ticker);
    if (preset) {
      return {
        ticker,
        label: preset.label,
        tracks: preset.tracks,
        isProxy: PROXY_BENCHMARKS.has(ticker),
      };
    }
    const spec = specFor(ticker);
    return { ticker, label: spec.name, tracks: spec.name, isProxy: false };
  }
  const preset = DEFAULT_BENCHMARKS[assetClass];
  return {
    ticker: preset.ticker,
    label: preset.label,
    tracks: preset.tracks,
    isProxy: true,
  };
}

export const PERFORMANCE_CATALOG = FUND_SPECS.filter((spec) =>
  ["AGTHX", "AMCPX", "FBGRX", "VFIAX", "DODIX", "VTIAX"].includes(spec.ticker),
).map((spec) => ({ ticker: spec.ticker, name: spec.name }));

export function mockPerformanceResponse(
  request: PerformanceGrowthRequest,
): PerformanceResponse {
  const ticker = resolvePerformanceTicker(request.ticker, request.fund_identifier);
  const fundSpec = specFor(ticker);
  const hint = request.asset_class ?? request.benchmark_hint ?? null;
  const assetClass = hint ?? fundSpec.asset_class;
  const bench = resolveBenchmark(request.benchmark, assetClass);
  const benchSpec = specFor(bench.ticker);
  const startDollars =
    request.start_dollars && request.start_dollars > 0
      ? request.start_dollars
      : DEFAULT_START_DOLLARS;

  const fund = toSeries(fundSpec, startDollars, request.start_date, request.end_date);
  const benchmark = toSeries(benchSpec, startDollars, request.start_date, request.end_date);

  const months = new Set(fund.series.points.map((point) => point.date.slice(0, 7)));
  const overlap = benchmark.series.points.filter((point) =>
    months.has(point.date.slice(0, 7)),
  );
  const fundOverlap = fund.series.points.filter((point) =>
    overlap.some((row) => row.date.slice(0, 7) === point.date.slice(0, 7)),
  );
  if (fundOverlap.length < 2 || overlap.length < 2) {
    throw new PerformanceMockError(
      "Not enough overlapping monthly points in the requested date range.",
      422,
    );
  }

  const rebase = (series: PerformanceSeriesOut, points: PerformancePoint[]) => {
    const base = points[0].growth_of_x / startDollars || 1;
    let prev: number | null = null;
    return {
      ...series,
      points: points.map((point) => {
        const growth = money(point.growth_of_x / base);
        const monthly =
          prev == null ? null : ret(point.adj_close / prev - 1);
        prev = point.adj_close;
        return { ...point, monthly_return: monthly, growth_of_x: growth };
      }),
    };
  };

  const fundSeries = rebase(fund.series, fundOverlap);
  const benchSeries = rebase(benchmark.series, overlap);
  const first = fundSeries.points[0].date;
  const last = fundSeries.points[fundSeries.points.length - 1].date;

  return {
    fund_ticker: ticker,
    fund_identifier: request.fund_identifier?.trim() || ticker,
    fund_name: fundSpec.name,
    asset_class: assetClass,
    start_dollars: startDollars,
    start_date: first,
    end_date: last,
    as_of: last,
    frequency: "monthly",
    mode: "fixture",
    source: "fixture",
    source_urls: ["mock://performance"],
    benchmark_id: bench.ticker,
    benchmark_label: bench.label,
    benchmark_tracks: bench.tracks,
    is_proxy: bench.isProxy,
    fund: fundSeries,
    benchmark: benchSeries,
    disclaimers: DISCLAIMERS,
  };
}

export function isPerformanceRequestValid(
  request: PerformanceGrowthRequest,
): string | null {
  if (!request.ticker?.trim() && !request.fund_identifier?.trim()) {
    return "ticker or fund_identifier is required";
  }
  if (request.start_dollars != null && !(request.start_dollars > 0)) {
    return "start_dollars must be greater than 0";
  }
  return null;
}
