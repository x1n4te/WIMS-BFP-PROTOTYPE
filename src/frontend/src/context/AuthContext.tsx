'use client';

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  useRef,
  ReactNode,
} from 'react';
import { useRouter } from 'next/navigation';
import { createUserManager } from '@/lib/oidc';

export interface User {
  id: string;
  sub?: string;
  email?: string;
  preferred_username?: string;
  role?: string;
  assignedRegionId?: number | null;
}

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  loggingOut: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);
const PROACTIVE_REFRESH_INTERVAL_MS = 4 * 60 * 1000; // refresh before 5-minute access token expiry

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [loggingOut, setLoggingOut] = useState(false);
  const refreshInFlightRef = useRef(false);
  const router = useRouter();

  useEffect(() => {
    if (loading) {
      console.log('[AuthContext] loading=true - session check in progress. If stuck, verify authority URL is reachable: http://localhost/auth/realms/bfp');
    }
  }, [loading]);

  const refreshAccessToken = useCallback(async (): Promise<boolean> => {
    if (refreshInFlightRef.current) {
      return true;
    }

    refreshInFlightRef.current = true;
    try {
      const res = await fetch('/api/auth/refresh', { method: 'POST' });
      if (!res.ok) {
        console.log('[AuthContext] refreshAccessToken: refresh failed', res.status);
        return false;
      }
      console.log('[AuthContext] refreshAccessToken: token refreshed');
      return true;
    } catch (err) {
      console.error('[AuthContext] refreshAccessToken: request failed', err);
      return false;
    } finally {
      refreshInFlightRef.current = false;
    }
  }, []);

  const fetchSession = useCallback(async () => {
    console.log('[AuthContext] fetchSession: starting');
    try {
      const requestSession = () => fetch('/api/auth/session');
      let res = await requestSession();

      if (res.status === 401) {
        const refreshed = await refreshAccessToken();
        if (refreshed) {
          res = await requestSession();
        }
      }

      if (res.ok) {
        const data = await res.json();
        if (data.user) {
          setUser(data.user);
          console.log('[AuthContext] fetchSession: user loaded', data.user?.email ?? data.user?.id);
        } else {
          setUser(null);
          console.log('[AuthContext] fetchSession: no user in session');
        }
      } else {
        setUser(null);
        console.log('[AuthContext] fetchSession: session fetch not ok', res.status);
      }
    } catch (err) {
      setUser(null);
      console.error('[AuthContext] fetchSession: initialization failed:', err);
    } finally {
      setLoading(false);
      console.log('[AuthContext] fetchSession: loading=false');
    }
  }, [refreshAccessToken]);

  useEffect(() => {
    console.log('[AuthContext] useEffect: initializing auth');
    fetchSession();
  }, [fetchSession]);

  useEffect(() => {
    if (!user || loggingOut) {
      return;
    }

    const refreshAndReloadSession = async () => {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        await fetchSession();
        return;
      }
      setUser(null);
    };

    const intervalId = window.setInterval(
      () => void refreshAndReloadSession(),
      PROACTIVE_REFRESH_INTERVAL_MS
    );

    const refreshWhenVisible = () => {
      if (document.visibilityState === 'visible') {
        void refreshAndReloadSession();
      }
    };

    window.addEventListener('focus', refreshWhenVisible);
    document.addEventListener('visibilitychange', refreshWhenVisible);

    return () => {
      window.clearInterval(intervalId);
      window.removeEventListener('focus', refreshWhenVisible);
      document.removeEventListener('visibilitychange', refreshWhenVisible);
    };
  }, [fetchSession, loggingOut, refreshAccessToken, user]);

  const login = useCallback(async () => {
    console.log('[AuthContext] login: called');
    try {
      const userManager = createUserManager();
      console.log('[AuthContext] login: UserManager created, calling signinRedirect');
      await userManager.signinRedirect();
      console.log('[AuthContext] login: signinRedirect completed (redirect should occur)');
    } catch (err) {
      console.error('[AuthContext] login: signinRedirect error:', err);
      throw err;
    }
  }, []);

  const logout = useCallback(async () => {
    setLoggingOut(true);
    try {
      console.log('[AuthContext] logout: clearing local session');
      await fetch('/api/auth/logout', { method: 'POST' });

      console.log('[AuthContext] logout: calling Keycloak signoutRedirect');
      const userManager = createUserManager();
      const currentUser = await userManager.getUser();

      // Clear local OIDC state before redirecting away to avoid stale client-side sessions.
      await userManager.removeUser();

      // Explicit id_token_hint improves Keycloak end-session behavior in some deployments.
      await userManager.signoutRedirect({
        id_token_hint: currentUser?.id_token,
        post_logout_redirect_uri: `${window.location.origin}/login`,
      });
    } catch (err) {
      console.error('[AuthContext] logout: failed during signoutRedirect', err);
      setUser(null);
      setLoggingOut(false);
      router.push('/login');
    }
  }, [router]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        loading,
        loggingOut,
        login,
        logout,
        refreshSession: fetchSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
