import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { authApi } from '@/services/api';
import type { User, Permissions } from '@/types';

interface AuthContextType {
  user: User | null;
  permissions: Permissions;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (userData: User, perms: Permissions, token: string) => void;
  logout: () => void;
  hasPermission: (permission: keyof Permissions) => boolean;
  loginWithCredentials: (username: string, password: string) => Promise<void>;
  loginWithTelegram: (userData: any) => Promise<void>;
  loginWithQR: (code: string) => Promise<void>;
}

const defaultPermissions: Permissions = {
  dashboard: true,
  view_dse: true,
  create_dse: false,
  edit_dse: false,
  delete_dse: false,
  chat: true,
  admin_panel: false,
  manage_users: false,
  view_users: false,
  manage_invites: false,
  terminal: false,
  export_data: false,
  export_pdf: false,
  export_excel: false,
  approve_dse_requests: false,
  view_dashboard_stats: false,
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [permissions, setPermissions] = useState<Permissions>(defaultPermissions);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for stored auth data
    const storedToken = localStorage.getItem('bolt_token');
    const storedUser = localStorage.getItem('bolt_user');
    const storedPerms = localStorage.getItem('bolt_permissions');
    
    if (storedToken && storedUser) {
      try {
        setUser(JSON.parse(storedUser));
        if (storedPerms) {
          setPermissions(JSON.parse(storedPerms));
        }
        // Validate token by fetching user data
        authApi.getMe().catch(() => {
          logout();
        });
      } catch (e) {
        console.error('Failed to parse stored auth data');
        logout();
      }
    }
    setIsLoading(false);
  }, []);

  const login = useCallback((userData: User, perms: Permissions, token: string) => {
    setUser(userData);
    setPermissions(perms);
    localStorage.setItem('bolt_token', token);
    localStorage.setItem('bolt_user', JSON.stringify(userData));
    localStorage.setItem('bolt_permissions', JSON.stringify(perms));
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setPermissions(defaultPermissions);
    localStorage.removeItem('bolt_token');
    localStorage.removeItem('bolt_user');
    localStorage.removeItem('bolt_permissions');
  }, []);

  const hasPermission = useCallback((permission: keyof Permissions) => {
    return permissions[permission] === true;
  }, [permissions]);

  const loginWithCredentials = useCallback(async (username: string, password: string) => {
    const response = await authApi.login(username, password);
    const { user: userData, token, permissions: perms } = response.data;
    login(userData, perms || defaultPermissions, token);
  }, [login]);

  const loginWithTelegram = useCallback(async (telegramData: any) => {
    const response = await authApi.telegramAuth(telegramData);
    const { user: userData, token, permissions: perms } = response.data;
    login(userData, perms || defaultPermissions, token);
  }, [login]);

  const loginWithQR = useCallback(async (code: string) => {
    const response = await authApi.qrAuth(code);
    const { user: userData, token, permissions: perms } = response.data;
    login(userData, perms || defaultPermissions, token);
  }, [login]);

  return (
    <AuthContext.Provider value={{
      user,
      permissions,
      isAuthenticated: !!user,
      isLoading,
      login,
      logout,
      hasPermission,
      loginWithCredentials,
      loginWithTelegram,
      loginWithQR
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
