import { useEffect, useMemo, useState } from "react";

import { postEnvironmentDailyTip as postEnvironmentDailyTipApi } from "../services/environmentService.js";

/**
 * ViewModel for the daily environment tip. No UI-state mixing; it just
 * dispatches when coords become valid and cancels on effect teardown.
 *
 * @param {{
 *   userId: string | null,
 *   latitude: number | null | undefined,
 *   longitude: number | null | undefined,
 *   geoStatus: string,
 *   fetchDailyTip?: typeof postEnvironmentDailyTipApi,
 * }} params
 */
export function useDailyTipViewModel({
  userId,
  latitude,
  longitude,
  geoStatus,
  fetchDailyTip = postEnvironmentDailyTipApi,
}) {
  const [data, setData] = useState(/** @type {any} */ (null));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(/** @type {string | null} */ (null));

  const canFetch =
    Boolean(userId) &&
    geoStatus === "ok" &&
    typeof latitude === "number" &&
    typeof longitude === "number";

  useEffect(() => {
    if (!canFetch) {
      setData(null);
      setError(null);
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchDailyTip(/** @type {number} */ (latitude), /** @type {number} */ (longitude))
      .then((res) => {
        if (!cancelled) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Could not load tip.");
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [userId, latitude, longitude, canFetch, fetchDailyTip]);

  const accent = useMemo(() => computeAccent(data), [data]);

  return { data, loading, error, accent, canFetch };
}

function computeAccent(data) {
  if (!data?.tip_title) return { blob: "bg-sky-500/10", ring: "from-sky-500/20" };
  const t = `${data.tip_title} ${data.tip_description}`.toLowerCase();
  if (t.includes("urban") || t.includes("city") || data.icon_name === "building") {
    return { blob: "bg-emerald-500/12", ring: "from-emerald-500/25" };
  }
  if (t.includes("cold") || t.includes("cool") || t.includes("dry air")) {
    return { blob: "bg-sky-500/15", ring: "from-sky-400/30" };
  }
  if (t.includes("hot") || t.includes("heat") || t.includes("sun")) {
    return { blob: "bg-amber-500/15", ring: "from-amber-500/30" };
  }
  if (t.includes("damp") || t.includes("humid") || t.includes("rain")) {
    return { blob: "bg-cyan-500/10", ring: "from-cyan-500/25" };
  }
  return { blob: "bg-violet-500/10", ring: "from-violet-500/25" };
}
