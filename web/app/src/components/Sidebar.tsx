import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
// import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  LayoutDashboard,
  List,
  PlusCircle,
  MessageSquare,
  Users,
  QrCode,
  FileText,
  Clock,
  UserCircle,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Hourglass,
} from 'lucide-react';

interface NavItem {
  label: string;
  icon: React.ElementType;
  path: string;
  permission?: string;
  badge?: number;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

export function Sidebar({ 
  collapsed, 
  onToggle 
}: { 
  collapsed: boolean; 
  onToggle: () => void;
}) {
  const location = useLocation();
  const { user, hasPermission, logout } = useAuth();
  const [pendingCount] = useState(0);

  const navGroups: NavGroup[] = [
    {
      label: 'Основное',
      items: [
        { label: 'Главная', icon: LayoutDashboard, path: '/dashboard', permission: 'dashboard' },
        { label: 'ДСЕ', icon: List, path: '/dse', permission: 'view_dse' },
        { label: 'Создать заявку', icon: PlusCircle, path: '/dse/create', permission: 'create_dse' },
        { label: 'На проверку', icon: Hourglass, path: '/dse/pending', permission: 'approve_dse_requests', badge: pendingCount },
      ],
    },
    {
      label: 'Коммуникация',
      items: [
        { label: 'Чат', icon: MessageSquare, path: '/chat', permission: 'chat' },
      ],
    },
    {
      label: 'Администрирование',
      items: [
        { label: 'Пользователи', icon: Users, path: '/users', permission: 'manage_users' },
        { label: 'QR Приглашения', icon: QrCode, path: '/invites', permission: 'manage_invites' },
        { label: 'Логи', icon: Clock, path: '/logs', permission: 'terminal' },
        { label: 'Отчеты', icon: FileText, path: '/reports', permission: 'export_data' },
      ],
    },
  ];

  const isActive = (path: string) => {
    if (path === '/dashboard') {
      return location.pathname === '/dashboard' || location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const renderNavItem = (item: NavItem) => {
    if (item.permission && !hasPermission(item.permission as keyof typeof hasPermission)) {
      return null;
    }

    const active = isActive(item.path);
    const Icon = item.icon;

    const content = (
      <Link
        to={item.path}
        className={cn(
          'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200',
          active
            ? 'bg-primary text-primary-foreground shadow-sm'
            : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
          collapsed && 'justify-center px-2'
        )}
      >
        <Icon className={cn('h-5 w-5 flex-shrink-0', active && 'text-primary-foreground')} />
        {!collapsed && (
          <>
            <span className="flex-1 truncate">{item.label}</span>
            {item.badge ? (
              <Badge variant={active ? 'secondary' : 'default'} className="h-5 min-w-[20px] px-1 text-xs">
                {item.badge}
              </Badge>
            ) : null}
          </>
        )}
      </Link>
    );

    if (collapsed) {
      return (
        <Tooltip key={item.path} delayDuration={0}>
          <TooltipTrigger asChild>{content}</TooltipTrigger>
          <TooltipContent side="right" className="flex items-center gap-2">
            {item.label}
            {item.badge ? (
              <Badge variant="default" className="h-5 min-w-[20px] px-1 text-xs">
                {item.badge}
              </Badge>
            ) : null}
          </TooltipContent>
        </Tooltip>
      );
    }

    return content;
  };

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        className={cn(
          'fixed left-0 top-0 z-40 flex h-screen flex-col border-r bg-card transition-all duration-300',
          collapsed ? 'w-[70px]' : 'w-[260px]'
        )}
      >
        {/* Header */}
        <div className="flex h-16 items-center justify-between border-b px-4">
          {!collapsed ? (
            <Link to="/dashboard" className="flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
                <svg width="24" height="24" viewBox="0 0 100 100" className="text-primary-foreground">
                  <path d="M20,30 Q35,20 50,30 T80,30" fill="none" stroke="currentColor" strokeWidth="8" opacity="0.6" />
                  <path d="M10,50 Q30,35 50,50 T90,50" fill="none" stroke="currentColor" strokeWidth="10" opacity="0.8" />
                  <path d="M15,70 Q35,55 55,70 T85,70" fill="none" stroke="currentColor" strokeWidth="8" opacity="0.5" />
                  <text x="50" y="65" fontSize="40" fontWeight="bold" fill="currentColor" textAnchor="middle">B</text>
                </svg>
              </div>
              <span className="text-lg font-bold">BOLT</span>
            </Link>
          ) : (
            <Link to="/dashboard" className="mx-auto">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
                <svg width="20" height="20" viewBox="0 0 100 100" className="text-primary-foreground">
                  <path d="M20,30 Q35,20 50,30 T80,30" fill="none" stroke="currentColor" strokeWidth="8" opacity="0.6" />
                  <path d="M10,50 Q30,35 50,50 T90,50" fill="none" stroke="currentColor" strokeWidth="10" opacity="0.8" />
                  <path d="M15,70 Q35,55 55,70 T85,70" fill="none" stroke="currentColor" strokeWidth="8" opacity="0.5" />
                  <text x="50" y="65" fontSize="40" fontWeight="bold" fill="currentColor" textAnchor="middle">B</text>
                </svg>
              </div>
            </Link>
          )}
          <Button
            variant="ghost"
            size="icon"
            className={cn('h-8 w-8', collapsed && 'hidden')}
            onClick={onToggle}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
        </div>

        {/* Navigation */}
        <ScrollArea className="flex-1 px-3 py-4">
          <nav className="flex flex-col gap-6">
            {navGroups.map((group, _idx) => {
              const visibleItems = group.items.filter(item => 
                !item.permission || hasPermission(item.permission as keyof typeof hasPermission)
              );
              
              if (visibleItems.length === 0) return null;

              return (
                <div key={group.label} className="flex flex-col gap-1">
                  {!collapsed && (
                    <h4 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      {group.label}
                    </h4>
                  )}
                  {visibleItems.map((item) => renderNavItem(item))}
                </div>
              );
            })}
          </nav>
        </ScrollArea>

        {/* Footer */}
        <div className="border-t p-3">
          <div className={cn('flex flex-col gap-1', collapsed && 'items-center')}>
            {!collapsed && user && (
              <div className="mb-3 flex items-center gap-3 rounded-lg bg-accent/50 px-3 py-2">
                {user.photo_url ? (
                  <img
                    src={user.photo_url}
                    alt={user.first_name}
                    className="h-8 w-8 rounded-full object-cover"
                  />
                ) : (
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
                    {user.first_name.charAt(0).toUpperCase()}
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="truncate text-sm font-medium">{user.first_name}</p>
                  <p className="truncate text-xs text-muted-foreground capitalize">{user.role}</p>
                </div>
              </div>
            )}

            {collapsed && user && (
              <Tooltip delayDuration={0}>
                <TooltipTrigger asChild>
                  <Link to="/profile">
                    {user.photo_url ? (
                      <img
                        src={user.photo_url}
                        alt={user.first_name}
                        className="h-8 w-8 rounded-full object-cover mb-2"
                      />
                    ) : (
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium mb-2">
                        {user.first_name.charAt(0).toUpperCase()}
                      </div>
                    )}
                  </Link>
                </TooltipTrigger>
                <TooltipContent side="right">
                  {user.first_name} ({user.role})
                </TooltipContent>
              </Tooltip>
            )}

            {!collapsed ? (
              <>
                <Link
                  to="/profile"
                  className={cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                    isActive('/profile')
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  )}
                >
                  <UserCircle className="h-5 w-5" />
                  Профиль
                </Link>
                <button
                  onClick={logout}
                  className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
                >
                  <LogOut className="h-5 w-5" />
                  Выход
                </button>
              </>
            ) : (
              <>
                <Tooltip delayDuration={0}>
                  <TooltipTrigger asChild>
                    <Link
                      to="/profile"
                      className={cn(
                        'flex h-9 w-9 items-center justify-center rounded-lg transition-colors',
                        isActive('/profile')
                          ? 'bg-primary text-primary-foreground'
                          : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                      )}
                    >
                      <UserCircle className="h-5 w-5" />
                    </Link>
                  </TooltipTrigger>
                  <TooltipContent side="right">Профиль</TooltipContent>
                </Tooltip>
                <Tooltip delayDuration={0}>
                  <TooltipTrigger asChild>
                    <button
                      onClick={logout}
                      className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
                    >
                      <LogOut className="h-5 w-5" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="right">Выход</TooltipContent>
                </Tooltip>
              </>
            )}

            <Button
              variant="ghost"
              size="icon"
              className={cn('mt-2', !collapsed && 'hidden')}
              onClick={onToggle}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </aside>
    </TooltipProvider>
  );
}
