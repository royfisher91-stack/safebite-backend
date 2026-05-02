import { PropsWithChildren, createContext, useCallback, useContext, useMemo, useState } from 'react';
import {
  getCurrentUser,
  loginAccount,
  logoutAccount,
  registerAccount,
  setAccessToken,
} from '../api/client';
import { User } from '../types/api';

type AuthContextValue = {
  user: User | null;
  token: string | null;
  loading: boolean;
  isSignedIn: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const applySession = useCallback((nextToken: string | null, nextUser: User | null) => {
    setToken(nextToken);
    setAccessToken(nextToken);
    setUser(nextUser);
  }, []);

  const signIn = useCallback(
    async (email: string, password: string) => {
      setLoading(true);
      try {
        const session = await loginAccount(email, password);
        applySession(session.access_token, session.user);
      } finally {
        setLoading(false);
      }
    },
    [applySession],
  );

  const register = useCallback(
    async (email: string, password: string) => {
      setLoading(true);
      try {
        const session = await registerAccount(email, password);
        applySession(session.access_token, session.user);
      } finally {
        setLoading(false);
      }
    },
    [applySession],
  );

  const signOut = useCallback(async () => {
    setLoading(true);
    try {
      if (token) {
        await logoutAccount();
      }
    } finally {
      applySession(null, null);
      setLoading(false);
    }
  }, [applySession, token]);

  const refreshUser = useCallback(async () => {
    if (!token) {
      return;
    }
    const nextUser = await getCurrentUser();
    setUser(nextUser);
  }, [token]);

  const value = useMemo(
    () => ({
      user,
      token,
      loading,
      isSignedIn: Boolean(user && token),
      signIn,
      register,
      signOut,
      refreshUser,
    }),
    [loading, refreshUser, register, signIn, signOut, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return value;
}
