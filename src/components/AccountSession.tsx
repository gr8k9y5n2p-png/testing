"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { fetchAccountMe } from "@/lib/account/client";
import type { PublicAccount } from "@/lib/account/store";

type AccountSessionValue = {
  account: PublicAccount | null | undefined;
  setAccount: (account: PublicAccount | null) => void;
};

const AccountSessionContext = createContext<AccountSessionValue | null>(null);

export function AccountSessionProvider({
  children,
  initialAccount = null,
}: {
  children: ReactNode;
  initialAccount?: PublicAccount | null;
}) {
  const [account, setAccount] = useState<PublicAccount | null | undefined>(
    initialAccount,
  );

  useEffect(() => {
    let cancelled = false;
    void fetchAccountMe()
      .then((next) => {
        if (!cancelled) setAccount(next);
      })
      .catch(() => {
        if (!cancelled) setAccount(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const persist = useCallback((next: PublicAccount | null) => {
    setAccount(next);
  }, []);

  const value = useMemo(
    () => ({ account, setAccount: persist }),
    [account, persist],
  );

  return (
    <AccountSessionContext.Provider value={value}>
      {children}
    </AccountSessionContext.Provider>
  );
}

export function useAccountSession(): AccountSessionValue {
  const context = useContext(AccountSessionContext);
  if (!context) {
    throw new Error("useAccountSession must be used within AccountSessionProvider");
  }
  return context;
}
