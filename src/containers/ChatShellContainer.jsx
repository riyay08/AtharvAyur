import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useAuthContext } from "../viewmodels/AuthContext.js";
import { useGeolocation } from "../viewmodels/useGeolocation.js";
import { AuthHeaderView } from "../views/AuthHeaderView.jsx";
import { WellnessHubNav } from "../views/WellnessHubNav.jsx";
import { WellnessHubOverview } from "../views/WellnessHubOverview.jsx";
import { DailyCheckInContainer } from "./DailyCheckInContainer.jsx";
import { DailyEnvironmentTipContainer } from "./DailyEnvironmentTipContainer.jsx";
import { HealthChatContainer } from "./HealthChatContainer.jsx";
import { SecuritySettingsContainer } from "./SecuritySettingsContainer.jsx";
import { WeeklyPlanContainer } from "./WeeklyPlanContainer.jsx";

/**
 * Composition root for the post-onboarding wellness hub. Uses a side rail /
 * tab navigation so each feature loads in its own panel instead of one crowded page.
 */
export function ChatShellContainer({ userId, onRestartOnboarding }) {
  const { t } = useTranslation();
  const { geoStatus, lat, lon } = useGeolocation();
  const auth = useAuthContext();
  const [securityOpen, setSecurityOpen] = useState(false);
  const [hubTab, setHubTab] = useState(/** @type {'overview'|'checkin'|'environment'|'plan'|'chat'} */ ("overview"));

  return (
    <main className="relative min-h-screen overflow-hidden bg-ink-900 p-4 md:p-8">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_70%_50%_at_50%_-10%,rgba(52,211,153,0.07),transparent_50%)]" />
      <div className="pointer-events-none absolute bottom-0 left-1/4 h-56 w-56 -translate-x-1/2 rounded-full bg-emerald-600/[0.05] blur-3xl" />

      <div className="relative mx-auto max-w-6xl space-y-10">
        <AuthHeaderView
          user={auth.user}
          isAuthenticated={auth.isAuthenticated}
          onOpenSecurity={() => setSecurityOpen(true)}
          onLogOut={auth.logOut}
          onRestartOnboarding={onRestartOnboarding}
        />

        <div className="flex flex-col gap-8 lg:flex-row lg:items-start lg:gap-10">
          <WellnessHubNav activeId={hubTab} onChange={setHubTab} />

          <div
            className="min-w-0 flex-1"
            role="tabpanel"
            id={`hub-panel-${hubTab}`}
            aria-labelledby={`hub-tab-${hubTab}`}
          >
            <div className="rounded-[1.75rem] border border-white/[0.07] bg-white/[0.035] p-6 shadow-panel backdrop-blur-xl md:p-8">
              {hubTab === "overview" ? (
                <WellnessHubOverview userId={userId} onGo={setHubTab} />
              ) : null}

              {hubTab === "checkin" ? <DailyCheckInContainer userId={userId} /> : null}

              {hubTab === "environment" ? (
                <DailyEnvironmentTipContainer
                  userId={userId}
                  latitude={lat}
                  longitude={lon}
                  geoStatus={geoStatus}
                />
              ) : null}

              {hubTab === "plan" ? <WeeklyPlanContainer userId={userId} /> : null}

              {hubTab === "chat" ? (
                <div className="space-y-6">
                  <div>
                    <p className="text-[0.65rem] font-semibold uppercase tracking-[0.22em] text-emerald-300/75">
                      {t("chat.label")}
                    </p>
                    <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-50 md:text-2xl">
                      {t("chat.title")}
                    </h2>
                    <p className="mt-2 max-w-measure text-sm leading-relaxed text-slate-400">{t("chat.subtitle")}</p>
                  </div>
                  <HealthChatContainer userId={userId} latitude={lat} longitude={lon} />
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </div>

      <SecuritySettingsContainer open={securityOpen} onClose={() => setSecurityOpen(false)} />
    </main>
  );
}
