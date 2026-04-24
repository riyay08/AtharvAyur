import { useDailyTipViewModel } from "../viewmodels/useDailyTipViewModel.js";
import { DailyEnvironmentTipView } from "../views/DailyEnvironmentTipView.jsx";

export function DailyEnvironmentTipContainer({ userId, latitude, longitude, geoStatus }) {
  const vm = useDailyTipViewModel({ userId, latitude, longitude, geoStatus });

  return (
    <DailyEnvironmentTipView
      userId={userId}
      geoStatus={geoStatus}
      loading={vm.loading}
      error={vm.error}
      data={vm.data}
      accent={vm.accent}
    />
  );
}
