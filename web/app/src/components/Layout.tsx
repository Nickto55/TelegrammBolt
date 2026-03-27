import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { cn } from '@/lib/utils';

export function Layout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      <Sidebar 
        collapsed={sidebarCollapsed} 
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} 
      />
      
      <div
        className={cn(
          'flex min-h-screen flex-col transition-all duration-300',
          sidebarCollapsed ? 'ml-[70px]' : 'ml-[260px]'
        )}
      >
        <Header />
        
        <main className="flex-1 p-6">
          <Outlet />
        </main>
        
        <footer className="border-t py-4 px-6">
          <p className="text-center text-sm text-muted-foreground">
            BOLT &copy; {new Date().getFullYear()} - Система управления ДСЕ
          </p>
        </footer>
      </div>
    </div>
  );
}
