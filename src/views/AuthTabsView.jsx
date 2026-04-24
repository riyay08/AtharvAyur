import { useTranslation } from "react-i18next";

/**
 * Pure tab strip used by both login and signup screens.
 *
 * @param {{
 *   tabs: { id: string, label: string, disabled?: boolean }[],
 *   activeId: string,
 *   onChange: (id: string) => void,
 * }} props
 */
export function AuthTabsView({ tabs, activeId, onChange }) {
  const { t } = useTranslation();
  return (
    <div
      role="tablist"
      aria-label={t("auth.tabs.email") + " / " + t("auth.tabs.phone")}
      className="mb-5 grid grid-flow-col auto-cols-fr gap-2 rounded-xl border border-white/10 bg-black/40 p-1"
    >
      {tabs.map((tab) => {
        const active = tab.id === activeId;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={active}
            disabled={tab.disabled}
            onClick={() => onChange(tab.id)}
            className={[
              "rounded-lg px-3 py-2 text-sm font-medium transition",
              active
                ? "bg-white/10 text-slate-50 shadow-inner shadow-white/5"
                : "text-slate-400 hover:text-slate-200",
              tab.disabled ? "cursor-not-allowed opacity-50" : "",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
