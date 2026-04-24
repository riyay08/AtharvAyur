import { Building2, Cloud, Droplets, Leaf, MapPin, Sparkles, Sun, Wind } from "lucide-react";
import { useTranslation } from "react-i18next";

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
 * Presentational view for the daily environment tip card.
 */
export function DailyEnvironmentTipView({ userId, geoStatus, loading, error, data, accent }) {
  const { t } = useTranslation();
  const Icon = ICONS[data?.icon_name] || Sparkles;

  if (!userId) {
    return null;
  }

  return (
    <section
      className="relative flex h-full min-h-[14rem] flex-col overflow-hidden rounded-3xl border border-white/[0.08] bg-white/[0.04] p-6 shadow-[0_24px_80px_rgba(0,0,0,0.45)] backdrop-blur-xl"
      aria-label={t("tip.title")}
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
            {t("tip.label")}
          </p>
          <h2 className="mt-1 text-lg font-semibold tracking-tight text-slate-50">{t("tip.title")}</h2>
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

      {(geoStatus === "denied" || geoStatus === "unsupported" || geoStatus === "error") && (
        <div className="relative mt-5 flex flex-1 flex-col justify-center rounded-2xl border border-dashed border-white/15 bg-black/20 p-4 text-center">
          <MapPin className="mx-auto mb-2 h-8 w-8 text-slate-600" aria-hidden />
          <p className="text-sm text-slate-400">
            {geoStatus === "unsupported" ? t("tip.geoUnsupported") : t("tip.geoNeeded")}
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
              {t("tip.savedToday")}
            </p>
          )}
          <h3 className="text-base font-semibold leading-snug text-slate-100">{data.tip_title}</h3>
          <p className="mt-2 text-sm leading-relaxed text-slate-400">{data.tip_description}</p>
        </div>
      )}
    </section>
  );
}
