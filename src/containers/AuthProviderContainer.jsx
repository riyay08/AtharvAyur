import { useMemo } from "react";

import { AuthContext } from "../viewmodels/AuthContext.js";
import { useAuthProvider } from "../viewmodels/useAuthProvider.js";

/**
 * Composition root for the auth context. Drop this near the top of the
 * tree so any container/view can reach `useAuthContext()`.
 */
export function AuthProviderContainer({ children }) {
  const value = useAuthProvider();
  const memoed = useMemo(() => value, [value]);
  return <AuthContext.Provider value={memoed}>{children}</AuthContext.Provider>;
}
