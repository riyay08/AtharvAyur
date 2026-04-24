import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { useAuthContext } from "../viewmodels/AuthContext.js";
import { usePasskeyViewModel } from "../viewmodels/usePasskeyViewModel.js";
import { SecuritySettingsView } from "../views/SecuritySettingsView.jsx";

export function SecuritySettingsContainer({ open, onClose }) {
  const { t } = useTranslation();
  const auth = useAuthContext();
  const passkeyVm = usePasskeyViewModel({
    onRegistered: () => auth.refreshMe(),
    t,
  });

  const handleLogOut = useCallback(() => {
    auth.logOut();
  }, [auth]);

  return (
    <SecuritySettingsView
      open={open}
      onClose={onClose}
      user={auth.user}
      passkeyVm={passkeyVm}
      onLogOut={handleLogOut}
    />
  );
}
