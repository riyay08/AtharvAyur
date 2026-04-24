import { useEffect, useState } from "react";
import { getCurrentPosition } from "../services/geolocationService.js";

/**
 * ViewModel: browser geolocation. Returns a stable `geoStatus` + coords.
 *
 * @returns {{ geoStatus: 'pending'|'ok'|'denied'|'unsupported'|'error', lat: number | null, lon: number | null }}
 */
export function useGeolocation() {
  const [state, setState] = useState({ geoStatus: "pending", lat: null, lon: null });

  useEffect(() => {
    let cancelled = false;
    getCurrentPosition().then((result) => {
      if (cancelled) return;
      if (result.status === "ok") {
        setState({ geoStatus: "ok", lat: result.lat, lon: result.lon });
      } else {
        setState({ geoStatus: result.status, lat: null, lon: null });
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
