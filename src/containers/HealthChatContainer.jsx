import { useHealthChatViewModel } from "../viewmodels/useHealthChatViewModel.js";
import { HealthChatView } from "../views/HealthChatView.jsx";

export function HealthChatContainer({ userId, latitude, longitude }) {
  const vm = useHealthChatViewModel({ userId, latitude, longitude });

  return (
    <HealthChatView
      userId={userId}
      messages={vm.messages}
      input={vm.input}
      loading={vm.loading}
      error={vm.error}
      onInputChange={vm.setInput}
      onSend={vm.send}
    />
  );
}
