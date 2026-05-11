import { useCallback, useEffect, useState } from "react";

import { fetchProfileMe } from "../services/profileService.js";

/**
 * Loads GET /profile/me for the Overview dashboard snapshot.
 *
 * @param {string | undefined | null} userId
 */
export function useWellnessDashboard(userId) {
  const [me, setMe] = useState(/** @type {any | null} */ (null));
  const [loading, setLoading] = useState(() => Boolean(userId));
  const [error, setError] = useState(/** @type {Error | null} */ (null));

  const load = useCallback(async () => {
    if (!userId) {
      setMe(null);
      setError(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setMe(await fetchProfileMe());
    } catch (e) {
      setMe(null);
      setError(e instanceof Error ? e : new Error(String(e)));
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    load();
  }, [load]);

  return { me, loading, error, refetch: load };
}
