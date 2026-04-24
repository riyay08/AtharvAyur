import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useAuthContext } from "../viewmodels/AuthContext.js";
import { useGeolocation } from "../viewmodels/useGeolocation.js";
import { AuthHeaderView } from "../views/AuthHeaderView.jsx";
import { DailyCheckInContainer } from "./DailyCheckInContainer.jsx";
import { DailyEnvironmentTipContainer } from "./DailyEnvironmentTipContainer.jsx";
import { HealthChatContainer } from "./HealthChatContainer.jsx";
import { SecuritySettingsContainer } from "./SecuritySettingsContainer.jsx";
import { WeeklyPlanContainer } from "./WeeklyPlanContainer.jsx";

/**
 * Composition root for the post-onboarding wellness hub. Wires
 * geolocation into the panels that need coordinates and exposes the
 * auth header (security drawer, log out, retake quiz) above the existing
 * layout.
 */
export function ChatShellContainer({ userId, onRestartOnboarding }) {
  const { t } = useTranslation();
  const { geoStatus, lat, lon } = useGeolocation();
  const auth = useAuthContext();
  const [securityOpen, setSecurityOpen] = useState(false);

  return (
    <main className="min-h-screen bg-[#0b0d11] p-4 md:p-8">
      <div className="mx-auto max-w-6xl space-y-8">
        <AuthHeaderView
          user={auth.user}
          isAuthenticated={auth.isAuthenticated}
          onOpenSecurity={() => setSecurityOpen(true)}
          onLogOut={auth.logOut}
          onRestartOnboarding={onRestartOnboarding}
        />

        <div className="grid gap-6 lg:grid-cols-12 lg:items-start">
          <div className="space-y-6 lg:col-span-5">
            <div className="grid gap-6 lg:grid-cols-2 lg:items-stretch">
              <DailyCheckInContainer userId={userId} />
              <DailyEnvironmentTipContainer
                userId={userId}
                latitude={lat}
                longitude={lon}
                geoStatus={geoStatus}
              />
            </div>
            <WeeklyPlanContainer userId={userId} />
          </div>
          <div className="lg:col-span-7">
            <div className="rounded-3xl border border-white/[0.08] bg-white/[0.04] p-5 shadow-[0_24px_80px_rgba(0,0,0,0.45)] backdrop-blur-xl md:p-8">
              <p className="text-xs uppercase tracking-[0.2em] text-emerald-400/70">{t("chat.label")}</p>
              <h2 className="mt-1 text-xl font-semibold text-slate-50">{t("chat.title")}</h2>
              <p className="mt-1 text-sm text-slate-400">{t("chat.subtitle")}</p>
              <div className="mt-5">
                <HealthChatContainer userId={userId} latitude={lat} longitude={lon} />
              </div>
            </div>
          </div>
        </div>
      </div>

      <SecuritySettingsContainer open={securityOpen} onClose={() => setSecurityOpen(false)} />
    </main>
  );
}
