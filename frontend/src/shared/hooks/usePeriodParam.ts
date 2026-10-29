import { useCallback } from "react";
import { useSearchParams } from "react-router";

import { currentPeriod, isFuturePeriod, isPeriod, type Period } from "@/shared/lib/period";

const PARAM = "period";

export function usePeriodParam(): [Period, (period: Period) => void] {
  const [searchParams, setSearchParams] = useSearchParams();
  const raw = searchParams.get(PARAM);
  const period = isPeriod(raw) && !isFuturePeriod(raw) ? raw : currentPeriod();

  const setPeriod = useCallback(
    (next: Period) => {
      setSearchParams(
        (params) => {
          params.set(PARAM, next);
          return params;
        },
        { replace: true },
      );
    },
    [setSearchParams],
  );

  return [period, setPeriod];
}
