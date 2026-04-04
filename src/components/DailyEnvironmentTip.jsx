import { useEffect, useMemo, useState } from "react";
import {
  Building2,
  Cloud,
  Droplets,
  Leaf,
  MapPin,
  Sparkles,
  Sun,
  Wind,
} from "lucide-react";
import { postEnvironmentDailyTip } from "../api";

const ICONS = {
  leaf: Leaf,
  building: Building2,
  droplets: Droplets,
  sun: Sun,
  cloud: Cloud,
  wind: Wind,
  sparkles: Sparkles,
};

/**
 * Weather-tinged glass card: dosha + environment tip (cached per user per UTC day on server).
 * @param {{ userId: string | null, latitude?: number, longitude?: number, geoStatus: 'pending'|'ok'|'denied'|'unsupported' }} props
 */
export function DailyEnvironmentTip({ userId, latitude, longitude, geoStatus }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const canFetch =
    userId &&
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
    postEnvironmentDailyTip(userId, latitude, longitude)
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
  }, [userId, latitude, longitude, canFetch]);

  const Icon = ICONS[data?.icon_name] || Sparkles;

  const accent = useMemo(() => {
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
  }, [data]);

  if (!userId) {
    return null;
  }

  return (
    <section
      className="relative flex h-full min-h-[14rem] flex-col overflow-hidden rounded-3xl border border-white/[0.08] bg-white/[0.04] p-6 shadow-[0_24px_80px_rgba(0,0,0,0.45)] backdrop-blur-xl"
      aria-label="Daily environment tip"
    >
      <div
        className={`pointer-events-none absolute -right-12 -top-12 h-36 w-36 rounded-full ${accent.blob} blur-3xl`}
      />
      <div
        className={`pointer-events-none absolute -bottom-16 -left-8 h-40 w-40 rounded-full bg-gradient-to-tr ${accent.ring} to-transparent opacity-90 blur-2xl`}
      />

      <div className="relative flex items-start justify-between gap-3">
        <div>
          <p className="text-[0.65rem] font-semibold uppercase tracking-[0.28em] text-sky-200/70">
            Environment &amp; you
          </p>
          <h2 className="mt-1 text-lg font-semibold tracking-tight text-slate-50">Daily tip</h2>
        </div>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-black/30 text-sky-200/80">
          <Icon className="h-5 w-5" strokeWidth={1.75} aria-hidden />
        </div>
      </div>

      {geoStatus === "pending" && (
        <div className="relative mt-5 flex-1 space-y-3 animate-pulse">
          <div className="h-4 w-3/4 rounded-lg bg-white/10" />
          <div className="h-3 w-full rounded-lg bg-white/[0.06]" />
          <div className="h-3 w-5/6 rounded-lg bg-white/[0.06]" />
          <div className="h-3 w-2/3 rounded-lg bg-white/[0.06]" />
        </div>
      )}

      {(geoStatus === "denied" || geoStatus === "unsupported") && (
        <div className="relative mt-5 flex flex-1 flex-col justify-center rounded-2xl border border-dashed border-white/15 bg-black/20 p-4 text-center">
          <MapPin className="mx-auto mb-2 h-8 w-8 text-slate-600" aria-hidden />
          <p className="text-sm text-slate-400">
            {geoStatus === "unsupported"
              ? "Location isn’t available in this browser."
              : "Allow location to get a personalized environment tip for today."}
          </p>
        </div>
      )}

      {geoStatus === "ok" && loading && (
        <div className="relative mt-5 flex-1 space-y-3">
          <div className="h-4 w-2/3 rounded-lg bg-gradient-to-r from-white/10 via-white/5 to-white/10 animate-pulse" />
          <div className="h-3 w-full rounded-lg bg-white/[0.06] animate-pulse" />
          <div className="h-3 w-full rounded-lg bg-white/[0.06] animate-pulse delay-75" />
          <div className="h-3 w-4/5 rounded-lg bg-white/[0.06] animate-pulse delay-150" />
        </div>
      )}

      {geoStatus === "ok" && error && !loading && (
        <p className="relative mt-5 flex-1 text-sm text-rose-300/90">{error}</p>
      )}

      {geoStatus === "ok" && data && !loading && (
        <div className="relative mt-4 flex-1">
          {data.cached && (
            <p className="mb-2 text-[0.65rem] font-medium uppercase tracking-wider text-slate-500">
              Today&apos;s saved tip
            </p>
          )}
          <h3 className="text-base font-semibold leading-snug text-slate-100">{data.tip_title}</h3>
          <p className="mt-2 text-sm leading-relaxed text-slate-400">{data.tip_description}</p>
        </div>
      )}
    </section>
  );
}
