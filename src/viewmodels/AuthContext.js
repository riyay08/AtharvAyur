import { createContext, useContext } from "react";

/**
 * Read-only view of the auth state. Mutations always go through the
 * provider's exposed methods (login, logout, refresh).
 *
 * @typedef {{
 *   user_id: string|null,
 *   email: string|null,
 *   phone: string|null,
 *   display_name: string|null,
 *   primary_provider: string|null,
 *   email_verified: boolean,
 *   phone_verified: boolean,
 *   has_password: boolean,
 *   has_passkey: boolean,
 * }} AuthUser
 *
 * @typedef {{
 *   user: AuthUser|null,
 *   isAuthenticated: boolean,
 *   isAnonymous: boolean,
 *   anonymousUserId: string|null,
 *   hasProfile: boolean,
 *   profileChecked: boolean,
 *   loadingMe: boolean,
 *   handleSession: (session: any) => void,
 *   markProfileSaved: () => void,
 *   refreshMe: () => Promise<void>,
 *   logOut: () => void,
 * }} AuthContextValue
 */

export const AuthContext = createContext(/** @type {AuthContextValue|null} */ (null));

export function useAuthContext() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuthContext must be used inside <AuthProvider>");
  }
  return ctx;
}
