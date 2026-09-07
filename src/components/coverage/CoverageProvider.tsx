"use client";

import { createContext, useContext, type ReactNode } from "react";
import {
  TOP_ADVISOR_FAMILIES,
  findFamilyCoverage,
  isLiveCoveredFamily,
  type FundFamilyCoverage,
} from "@/lib/coverage";

const CoverageContext = createContext<FundFamilyCoverage[]>(TOP_ADVISOR_FAMILIES);

export function CoverageProvider({
  families,
  children,
}: {
  families: FundFamilyCoverage[];
  children: ReactNode;
}) {
  return (
    <CoverageContext.Provider value={families.length ? families : TOP_ADVISOR_FAMILIES}>
      {children}
    </CoverageContext.Provider>
  );
}

export function useCoverage() {
  const families = useContext(CoverageContext);
  return {
    families,
    isLive: (family: string) => isLiveCoveredFamily(family, families),
    familyMeta: (family: string) => findFamilyCoverage(family, families),
  };
}
