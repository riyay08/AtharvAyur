import { useDailyCheckInViewModel } from "../viewmodels/useDailyCheckInViewModel.js";
import { DailyCheckInView } from "../views/DailyCheckInView.jsx";

/**
 * Container for the Daily Check-in feature. Wires the ViewModel to the View
 * and normalizes the water-glass tap semantics (the view emits a glass index,
 * the ViewModel expects an absolute count).
 */
export function DailyCheckInContainer({ userId }) {
  const vm = useDailyCheckInViewModel({ userId });

  return (
    <DailyCheckInView
      userId={userId}
      stripDays={vm.stripDays}
      weekLoading={vm.weekLoading}
      weekError={vm.weekError}
      selectedDate={vm.selectedDate}
      todayStr={vm.todayStr}
      isFormExpanded={vm.isFormExpanded}
      sleepQuality={vm.sleepQuality}
      digestion={vm.digestion}
      energyState={vm.energyState}
      movement={vm.movement}
      water={vm.water}
      status={vm.status}
      message={vm.message}
      onSelectDay={vm.selectDay}
      onExpand={() => vm.setIsFormExpanded(true)}
      onSleepChange={vm.setSleepQuality}
      onDigestionChange={vm.setDigestion}
      onEnergyChange={vm.setEnergyState}
      onMovementChange={vm.setMovement}
      onWaterTap={(index) => vm.setWater(index + 1)}
      onSubmit={vm.submit}
    />
  );
}
