import {
  CalendarRange,
  ClipboardList,
  LayoutGrid,
  Leaf,
  MessageCircle,
} from "lucide-react";
import { useTranslation } from "react-i18next";

/**
 * Vertical rail on lg+; horizontal scroll tabs on smaller breakpoints (single DOM tree — valid ids).
 *
 * @param {{
 *   activeId: string,
 *   onChange: (id: string) => void,
 * }} props
 */
export function WellnessHubNav({ activeId, onChange }) {
  const { t } = useTranslation();

  const items = [
    { id: "overview", icon: LayoutGrid, label: t("hub.nav.overview") },
    { id: "checkin", icon: ClipboardList, label: t("hub.nav.checkin") },
    { id: "environment", icon: Leaf, label: t("hub.nav.environment") },
    { id: "plan", icon: CalendarRange, label: t("hub.nav.plan") },
    { id: "chat", icon: MessageCircle, label: t("hub.nav.chat") },
  ];

  return (
    <nav className="mb-8 shrink-0 lg:mb-0 lg:w-52 xl:w-56" aria-label={t("hub.navAria")}>
      <p className="mb-3 hidden text-[0.65rem] font-semibold uppercase tracking-[0.22em] text-slate-500 lg:block">
        {t("hub.menuLabel")}
      </p>

      <ul
        role="tablist"
        className="flex gap-2 overflow-x-auto pb-1 [-ms-overflow-style:none] [scrollbar-width:none] lg:flex-col lg:gap-1 lg:overflow-visible lg:rounded-2xl lg:border lg:border-white/[0.07] lg:bg-black/25 lg:p-1.5 lg:pb-1.5 [&::-webkit-scrollbar]:hidden"
      >
        {items.map(({ id, icon: Icon, label }) => {
          const active = activeId === id;
          return (
            <li key={id} className="shrink-0 lg:w-full lg:shrink">
              <button
                type="button"
                role="tab"
                aria-selected={active}
                id={`hub-tab-${id}`}
                aria-controls={`hub-panel-${id}`}
                onClick={() => onChange(id)}
                className={`flex w-full items-center gap-2 rounded-xl px-3.5 py-2.5 text-left text-sm font-medium transition lg:gap-3 lg:py-2.5 ${
                  active
                    ? "bg-emerald-500/20 text-emerald-100 shadow-[inset_0_0_0_1px_rgba(52,211,153,0.25)] lg:bg-emerald-500/15 lg:shadow-[inset_0_0_0_1px_rgba(52,211,153,0.2)]"
                    : "border border-white/[0.06] bg-black/30 text-slate-400 hover:bg-white/[0.06] hover:text-slate-200 lg:border-0 lg:bg-transparent lg:hover:bg-white/[0.05]"
                }`}
              >
                <Icon className="h-4 w-4 shrink-0 opacity-90" aria-hidden />
                <span className="whitespace-nowrap">{label}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
