import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/hooks/useAuth';
import { Layout } from '@/components/Layout';
import {
  Login,
  Dashboard,
  DSEList,
  DSEDetail,
  CreateDSE,
  DSEPending,
  Chat,
  Profile,
  Users,
  Invites,
  Reports,
  Logs,
  Settings,
  NotFound,
} from '@/pages';
import './App.css';

// Protected Route component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

// Permission Route component
function PermissionRoute({ 
  children, 
  permission 
}: { 
  children: React.ReactNode; 
  permission: string;
}) {
  const { hasPermission, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!hasPermission(permission as keyof typeof hasPermission)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<Login />} />

      {/* Protected routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        
        {/* DSE Routes */}
        <Route path="dse" element={<DSEList />} />
        <Route path="dse/create" element={
          <PermissionRoute permission="create_dse">
            <CreateDSE />
          </PermissionRoute>
        } />
        <Route path="dse/pending" element={
          <PermissionRoute permission="approve_dse_requests">
            <DSEPending />
          </PermissionRoute>
        } />
        <Route path="dse/:id" element={<DSEDetail />} />
        
        {/* Chat */}
        <Route path="chat" element={
          <PermissionRoute permission="chat">
            <Chat />
          </PermissionRoute>
        } />
        
        {/* Profile */}
        <Route path="profile" element={<Profile />} />
        <Route path="settings" element={<Settings />} />
        
        {/* Admin Routes */}
        <Route path="users" element={
          <PermissionRoute permission="manage_users">
            <Users />
          </PermissionRoute>
        } />
        <Route path="invites" element={
          <PermissionRoute permission="manage_invites">
            <Invites />
          </PermissionRoute>
        } />
        <Route path="reports" element={
          <PermissionRoute permission="export_data">
            <Reports />
          </PermissionRoute>
        } />
        <Route path="logs" element={
          <PermissionRoute permission="terminal">
            <Logs />
          </PermissionRoute>
        } />

        {/* 404 */}
        <Route path="*" element={<NotFound />} />
      </Route>

      {/* Global 404 */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
