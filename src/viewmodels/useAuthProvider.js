/**
 * State + behavior for the global auth context. Wired into
 * `<AuthProvider>` and consumed via `useAuthContext`.
 *
 * Owns:
 *   - the current authenticated user (hydrated from localStorage on
 *     mount, then re-fetched from `/auth/me`)
 *   - whether the user has saved a HealthProfile yet (drives the
 *     "show quiz vs. show wellness hub" decision after auth)
 *   - `handleSession` — called by login/signup VMs after a successful
 *     auth response
 *   - `markProfileSaved` — called by the quiz container after the
 *     profile is persisted
 *   - `logOut` — wipes JWT + cached user
 */

import { useCallback, useEffect, useRef, useState } from "react";

import {
  fetchAuthenticatedUser,
  hasHealthProfile,
  logOut as logOutService,
} from "../services/authService.js";
import {
  clearHolisticaSession,
  getStoredAccessToken,
  getStoredAuthUser,
  getStoredUserId,
  setStoredAuthUser,
} from "../services/storage.js";

function meResponseToAuthUser(me) {
  if (!me) return null;
  return {
    user_id: me.user_id ?? null,
    email: me.email ?? null,
    phone: me.phone ?? null,
    display_name: me.display_name ?? null,
    primary_provider: me.primary_provider ?? null,
    email_verified: !!me.email_verified,
    phone_verified: !!me.phone_verified,
    has_password: !!me.has_password,
    has_passkey: (me.passkey_count ?? 0) > 0,
  };
}

export function useAuthProvider() {
  const [user, setUser] = useState(() => getStoredAuthUser() || null);
  const [loadingMe, setLoadingMe] = useState(false);
  const [hasProfile, setHasProfile] = useState(false);
  const [profileChecked, setProfileChecked] = useState(false);
  const profileCheckInFlightRef = useRef(false);

  const checkProfile = useCallback(async () => {
    if (!getStoredAccessToken()) {
      setHasProfile(false);
      setProfileChecked(true);
      return;
    }
    if (profileCheckInFlightRef.current) return;
    profileCheckInFlightRef.current = true;
    try {
      const present = await hasHealthProfile();
      setHasProfile(present);
    } catch {
      // Network/auth blip — treat as "unknown" but resolved so we don't
      // block the UI. The user can manually retake the quiz.
      setHasProfile(false);
    } finally {
      profileCheckInFlightRef.current = false;
      setProfileChecked(true);
    }
  }, []);

  const refreshMe = useCallback(async () => {
    if (!getStoredAccessToken()) return;
    setLoadingMe(true);
    try {
      const me = await fetchAuthenticatedUser();
      const next = meResponseToAuthUser(me);
      if (next && (next.email || next.phone || next.primary_provider !== "anonymous")) {
        setUser(next);
        setStoredAuthUser(next);
      }
    } catch {
      // Silent: a 401 here just means our token is stale.
    } finally {
      setLoadingMe(false);
    }
  }, []);

  useEffect(() => {
    if (getStoredAccessToken() && getStoredAuthUser()) {
      refreshMe();
      checkProfile();
    } else {
      setProfileChecked(true);
    }
  }, [refreshMe, checkProfile]);

  const handleSession = useCallback(
    (session) => {
      if (!session || typeof session !== "object") return;
      const next = {
        user_id: session.user_id ?? null,
        email: session.email ?? null,
        phone: session.phone ?? null,
        display_name: session.display_name ?? null,
        primary_provider: session.primary_provider ?? null,
        email_verified: !!session.email_verified,
        phone_verified: !!session.phone_verified,
        has_password: !!session.has_password,
        has_passkey: !!session.has_passkey,
      };
      setUser(next);
      // Brand-new accounts can't have a profile — short-circuit to the quiz
      // without a network round-trip. For existing users we still need to
      // ask the backend.
      if (session.is_new_user) {
        setHasProfile(false);
        setProfileChecked(true);
      } else {
        setProfileChecked(false);
        checkProfile();
      }
    },
    [checkProfile]
  );

  const markProfileSaved = useCallback(() => {
    setHasProfile(true);
    setProfileChecked(true);
  }, []);

  const logOut = useCallback(() => {
    logOutService();
    setUser(null);
    setHasProfile(false);
    setProfileChecked(true);
  }, []);

  const wipeEverything = useCallback(() => {
    clearHolisticaSession();
    setUser(null);
    setHasProfile(false);
    setProfileChecked(true);
  }, []);

  const isAuthenticated = !!(user && (user.email || user.phone || user.user_id));
  const anonymousUserId = !isAuthenticated ? getStoredUserId() : null;
  const isAnonymous = !isAuthenticated && !!anonymousUserId;

  return {
    user,
    isAuthenticated,
    isAnonymous,
    anonymousUserId,
    hasProfile,
    profileChecked,
    loadingMe,
    handleSession,
    markProfileSaved,
    refreshMe,
    logOut,
    wipeEverything,
  };
}
