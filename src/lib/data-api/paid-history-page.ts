/**
 * Homepage Paid History: one GET /distributions page of finals/paid.
 * Never walks the year book. Never pulls Upcoming prelims.
 */

import { aggregateDistributions, type DataDistribution } from "@/data/aggregate-distributions";
import {
  isUpcomingFund,
  normalizePublicationStage,
} from "@/data/distribution-bucket";
import {
  clampOffset,
  clampPaidHistoryPageSize,
  offsetToPage,
  type FundPageQuery,
  type FundPageResult,
} from "@/data/pagination";
import {
  paidHistoryViews,
  paidHistoryYearOf,
  withPeerContext,
} from "@/data/queries";
import { collectTaxYearsFromFunds } from "@/data/tax-years";
import type { FundEstimateView } from "@/data/types";
import { isRemoteDataApi } from "@/lib/data-api/config";
import {
  loadDistributionPage,
  type DistributionPageResult,
} from "@/lib/data-api/distributions";

function isFinalOrPaidRow(row: DataDistribution): boolean {
  const stage = normalizePublicationStage(row.publication_stage);
  return stage === "final" || stage === "paid";
}

function fundHasPaidYear(fund: FundEstimateView, year?: number): boolean {
  if (year == null) return !isUpcomingFund(fund);
  return paidHistoryViews([fund], year).length > 0;
}

function applyLocalFilters(
  funds: FundEstimateView[],
  query: FundPageQuery,
): FundEstimateView[] {
  const family = query.family?.trim();
  const category = query.category?.trim();
  const hasCategory = funds.some(
    (fund) => fund.category && fund.category !== "—",
  );
  return funds.filter((fund) => {
    if (isUpcomingFund(fund)) return false;
    if (!fundHasPaidYear(fund, query.year)) return false;
    if (family && fund.family !== family) return false;
    if (category && hasCategory && fund.category !== category) return false;
    return true;
  });
}

export async function loadPaidHistoryPageFromDataApi(
  query: FundPageQuery = {},
): Promise<FundPageResult> {
  const limit = clampPaidHistoryPageSize(query.limit);
  const offset = clampOffset(query.offset);
  const empty: FundPageResult = {
    items: [],
    total: 0,
    limit,
    offset,
    years: [],
  };
  if (!isRemoteDataApi()) return empty;

  const page = offsetToPage(offset, limit);
  const shared = {
    q: query.query,
    fundFamily: query.family,
    category: query.category,
    year: query.year,
    page,
    pageSize: limit,
  };

  try {
    const [finals, paids]: DistributionPageResult[] = await Promise.all([
      loadDistributionPage({ ...shared, publicationStage: "final" }),
      loadDistributionPage({ ...shared, publicationStage: "paid" }),
    ]);
    const rows = [...finals.items, ...paids.items].filter(isFinalOrPaidRow);
    if (!rows.length) {
      return {
        ...empty,
        total: Math.max(finals.total, paids.total, 0),
      };
    }
    const funds = applyLocalFilters(
      withPeerContext(aggregateDistributions(rows)),
      query,
    );
    return {
      items: funds,
      total: Math.max(finals.total, paids.total, funds.length),
      limit,
      offset,
      years: collectTaxYearsFromFunds(funds),
    };
  } catch {
    return empty;
  }
}
