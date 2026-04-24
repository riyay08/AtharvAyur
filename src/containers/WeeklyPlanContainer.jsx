import { useWeeklyPlanViewModel } from "../viewmodels/useWeeklyPlanViewModel.js";
import { WeeklyPlanView } from "../views/WeeklyPlanView.jsx";

export function WeeklyPlanContainer({ userId }) {
  const vm = useWeeklyPlanViewModel({ userId });

  return (
    <WeeklyPlanView
      userId={userId}
      plan={vm.plan}
      loading={vm.loading}
      genLoading={vm.genLoading}
      error={vm.error}
      weekDayIndex={vm.weekDayIndex}
      showLegacy={vm.showLegacy}
      showEnvelope={vm.showEnvelope}
      onGenerate={vm.generate}
      onPlanUpdated={vm.setPlan}
      onError={vm.setError}
    />
  );
}
