import { useDynamicCategoryStackViewModel } from "../viewmodels/useDynamicCategoryStackViewModel.js";
import { DynamicCategoryStackView } from "../views/DynamicCategoryStackView.jsx";

export function DynamicCategoryStackContainer({ plan, userId, weekDayIndex, onPlanUpdated, onError }) {
  const vm = useDynamicCategoryStackViewModel({
    plan,
    userId,
    weekDayIndex,
    onPlanUpdated,
    onError,
  });

  if (!vm.isValidEnvelope) {
    return (
      <p className="text-sm text-slate-400">
        This plan is missing daily task data. Try generating a new plan.
      </p>
    );
  }

  return (
    <DynamicCategoryStackView
      day={vm.day}
      focusMessage={vm.focusMessage}
      expanded={vm.expanded}
      slideOut={vm.slideOut}
      greenKey={vm.greenKey}
      busy={vm.busy}
      onToggleExpand={vm.toggleExpand}
      onCompleteTask={vm.completeTask}
    />
  );
}
