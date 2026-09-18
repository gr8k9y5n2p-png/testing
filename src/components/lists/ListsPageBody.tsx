"use client";

import { SoftWall } from "@/components/paywall/SoftWall";
import { ListsWorkspace } from "@/components/lists/ListsWorkspace";
import { useBilling } from "@/components/BillingProvider";
import type { FundEstimateView } from "@/data/types";
import type { ListRow } from "@/lib/lists/rows";

export function ListsPageBody({
  funds,
  initialTickers = [],
  initialRows = [],
}: {
  funds: FundEstimateView[];
  initialTickers?: string[];
  initialRows?: ListRow[];
}) {
  const billing = useBilling();
  return (
    <SoftWall
      active={billing.walls.lists}
      surface="lists"
      className="min-h-[40rem]"
    >
      <ListsWorkspace
        funds={funds}
        initialTickers={initialTickers}
        initialRows={initialRows}
      />
    </SoftWall>
  );
}
