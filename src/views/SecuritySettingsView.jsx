import { Fingerprint, Loader2, ShieldCheck, X } from "lucide-react";
import { useTranslation } from "react-i18next";

/**
 * Pure security panel rendered as a side sheet from the wellness hub.
 *
 * @param {{
 *   open: boolean,
 *   onClose: () => void,
 *   user: any|null,
 *   passkeyVm: ReturnType<typeof import('../viewmodels/usePasskeyViewModel.js').usePasskeyViewModel>,
 *   onLogOut: () => void,
 * }} props
 */
export function SecuritySettingsView({ open, onClose, user, passkeyVm, onLogOut }) {
  const { t } = useTranslation();
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-40 flex items-stretch justify-end bg-black/60 backdrop-blur-sm" role="dialog" aria-modal="true">
      <aside className="flex h-full w-full max-w-md flex-col bg-[#0b0d11] p-6 shadow-2xl ring-1 ring-white/10">
        <div className="mb-6 flex items-start justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-amber-200/60">
              {t("security.drawerLabel")}
            </p>
            <h2 className="mt-1 text-2xl font-semibold text-slate-50">{t("security.title")}</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-white/10 bg-white/5 p-2 text-slate-300 transition hover:bg-white/10"
            aria-label={t("common.cancel")}
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <section className="space-y-4 rounded-2xl border border-white/10 bg-white/[0.04] p-5">
          <header className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-300/80" />
            <h3 className="text-sm font-semibold text-slate-100">{t("security.signedInAs")}</h3>
          </header>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-slate-400">{t("security.fields.displayName")}</dt>
              <dd className="text-slate-100">{user?.display_name || "—"}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate-400">{t("security.fields.email")}</dt>
              <dd className="text-slate-100">{user?.email || "—"}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate-400">{t("security.fields.phone")}</dt>
              <dd className="text-slate-100">{user?.phone || "—"}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate-400">{t("security.fields.method")}</dt>
              <dd className="text-slate-100">{user?.primary_provider || "—"}</dd>
            </div>
          </dl>
        </section>

        <section className="mt-6 space-y-4 rounded-2xl border border-white/10 bg-white/[0.04] p-5">
          <header className="flex items-center gap-2">
            <Fingerprint className="h-4 w-4 text-emerald-300/80" />
            <h3 className="text-sm font-semibold text-slate-100">{t("security.passkeyTitle")}</h3>
          </header>
          <p className="text-sm text-slate-400">{t("security.passkeyDescription")}</p>
          {!passkeyVm.supported ? (
            <p className="rounded-lg border border-amber-400/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-200">
              {t("security.passkeyUnsupported")}
            </p>
          ) : (
            <button
              type="button"
              onClick={() => passkeyVm.register("This device")}
              disabled={passkeyVm.registering}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-500/90 px-4 py-2.5 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-slate-400"
            >
              {passkeyVm.registering ? <Loader2 className="h-4 w-4 animate-spin" /> : <Fingerprint className="h-4 w-4" />}
              {t("security.passkeyRegister")}
            </button>
          )}
          {passkeyVm.success ? (
            <p className="rounded-lg border border-emerald-400/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-200">
              {passkeyVm.success}
            </p>
          ) : null}
          {passkeyVm.error ? (
            <p role="alert" className="rounded-lg border border-rose-400/40 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
              {passkeyVm.error}
            </p>
          ) : null}
        </section>

        <div className="mt-auto pt-6">
          <button
            type="button"
            onClick={() => {
              onLogOut();
              onClose();
            }}
            className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-2.5 text-sm font-semibold text-rose-100 transition hover:border-rose-400/50 hover:bg-rose-500/20"
          >
            {t("common.logOut")}
          </button>
        </div>
      </aside>
    </div>
  );
}
