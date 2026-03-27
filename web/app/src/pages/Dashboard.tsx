import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { dseApi } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { 
  PlusCircle, 
  List, 
  Users, 
  FileSpreadsheet, 
  MessageSquare,
  ArrowRight,
  Info,
  Calendar,
  TrendingUp,
  PieChart,
  Clock
} from 'lucide-react';
import { 
  PieChart as RePieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer, 
  Tooltip as ReTooltip,
  Legend
} from 'recharts';
import type { DSE, DashboardStats } from '@/types';

const COLORS = ['#1E5EFF', '#00D4FF', '#5B9FFF', '#FF6B6B', '#4ECDC4', '#45B7D1'];

export function Dashboard() {
  const { user, hasPermission } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentDSE, setRecentDSE] = useState<DSE[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load stats
      if (hasPermission('view_dashboard_stats')) {
        const statsRes = await dseApi.getStats();
        setStats(statsRes.data);
      }
      
      // Load recent DSE
      const dseRes = await dseApi.getAll({ limit: 5, sort_by: 'date_desc' });
      setRecentDSE(dseRes.data.data || []);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const chartData = stats?.problem_types 
    ? Object.entries(stats.problem_types).map(([name, value]) => ({ name, value }))
    : [];

  const quickActions = [
    { 
      label: 'Создать заявку', 
      icon: PlusCircle, 
      path: '/dse/create', 
      permission: 'create_dse',
      variant: 'default' as const,
      color: 'bg-emerald-500 hover:bg-emerald-600',
    },
    { 
      label: 'Просмотр заявок', 
      icon: List, 
      path: '/dse', 
      permission: 'view_dse',
      variant: 'outline' as const,
      color: '',
    },
    { 
      label: 'Управление пользователями', 
      icon: Users, 
      path: '/users', 
      permission: 'manage_users',
      variant: 'outline' as const,
      color: '',
    },
    { 
      label: 'Экспорт Excel', 
      icon: FileSpreadsheet, 
      path: '#', 
      permission: 'export_excel',
      variant: 'outline' as const,
      color: '',
      onClick: async () => {
        try {
          const res = await dseApi.exportExcel();
          const blob = new Blob([res.data], { type: 'application/json' });
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = 'dse_export.json';
          a.click();
        } catch (error) {
          console.error('Export failed:', error);
        }
      },
    },
    { 
      label: 'Открыть чат', 
      icon: MessageSquare, 
      path: '/chat', 
      permission: 'chat',
      variant: 'outline' as const,
      color: '',
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Alert for QR users */}
      {user?.auth_type === 'qr' && !user.telegram_linked && (
        <Alert className="bg-blue-50 border-blue-200 dark:bg-blue-950/30 dark:border-blue-800">
          <Info className="h-4 w-4 text-blue-600" />
          <AlertDescription className="text-blue-700 dark:text-blue-300">
            <p className="mb-2">
              Вы вошли через QR код с ролью <strong>{user.role}</strong>. 
              Для получения полного доступа необходимо подключить Telegram аккаунт.
            </p>
            <Button size="sm" variant="outline" className="bg-white dark:bg-transparent">
              <MessageSquare className="h-4 w-4 mr-2" />
              Подключить Telegram
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary" />
            Быстрые действия
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
            {quickActions.map((action) => {
              if (action.permission && !hasPermission(action.permission as keyof typeof hasPermission)) {
                return null;
              }
              
              const Icon = action.icon;
              const buttonContent = (
                <>
                  <Icon className="h-6 w-6 mb-2" />
                  <span className="text-sm font-medium">{action.label}</span>
                </>
              );

              if (action.onClick) {
                return (
                  <Button
                    key={action.label}
                    variant={action.variant}
                    className={`h-auto py-4 flex flex-col items-center justify-center ${action.color}`}
                    onClick={action.onClick}
                  >
                    {buttonContent}
                  </Button>
                );
              }

              return (
                <Button
                  key={action.label}
                  variant={action.variant}
                  className={`h-auto py-4 flex flex-col items-center justify-center ${action.color}`}
                  asChild
                >
                  <Link to={action.path}>
                    {buttonContent}
                  </Link>
                </Button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Stats Cards */}
      {hasPermission('view_dashboard_stats') && stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-primary text-primary-foreground">
            <CardHeader className="pb-2">
              <CardDescription className="text-primary-foreground/80">
                Всего заявок
              </CardDescription>
              <CardTitle className="text-3xl">{stats.total_dse}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-sm text-primary-foreground/80">
                <List className="h-4 w-4" />
                <span>В работе</span>
              </div>
            </CardContent>
            <CardFooter className="pt-0">
              <Link 
                to="/dse" 
                className="text-sm text-primary-foreground/80 hover:text-primary-foreground flex items-center gap-1"
              >
                Перейти к списку <ArrowRight className="h-3 w-3" />
              </Link>
            </CardFooter>
          </Card>

          <Card className="bg-emerald-500 text-white">
            <CardHeader className="pb-2">
              <CardDescription className="text-white/80">
                Пользователей
              </CardDescription>
              <CardTitle className="text-3xl">{stats.active_users}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-sm text-white/80">
                <Users className="h-4 w-4" />
                <span>Активных в системе</span>
              </div>
            </CardContent>
            <CardFooter className="pt-0">
              <span className="text-sm text-white/60">
                Общая статистика
              </span>
            </CardFooter>
          </Card>

          <Card className="bg-cyan-500 text-white">
            <CardHeader className="pb-2">
              <CardDescription className="text-white/80">
                За неделю
              </CardDescription>
              <CardTitle className="text-3xl">{stats.recent_dse}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-sm text-white/80">
                <Calendar className="h-4 w-4" />
                <span>Новых записей</span>
              </div>
            </CardContent>
            <CardFooter className="pt-0">
              <span className="text-sm text-white/60">
                Последние 7 дней
              </span>
            </CardFooter>
          </Card>
        </div>
      )}

      {/* Charts and Stats Table */}
      {hasPermission('view_dashboard_stats') && stats?.problem_types && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pie Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="h-5 w-5 text-primary" />
                Распределение по типам проблем
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <RePieChart>
                    <Pie
                      data={chartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {chartData.map((_entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <ReTooltip 
                      formatter={(value: number, name: string) => {
                        const total = chartData.reduce((sum, item) => sum + item.value, 0);
                        const percent = total ? ((value / total) * 100).toFixed(1) : '0.0';
                        return [`${value} (${percent}%)`, name];
                      }}
                    />
                    <Legend />
                  </RePieChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Stats Table */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                Статистика по типам
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Тип проблемы</TableHead>
                    <TableHead className="text-right">Количество</TableHead>
                    <TableHead className="text-right">%</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {chartData
                    .sort((a, b) => b.value - a.value)
                    .map((item, index) => {
                      const total = chartData.reduce((sum, i) => sum + i.value, 0);
                      const percent = total ? ((item.value / total) * 100).toFixed(1) : '0.0';
                      return (
                        <TableRow key={item.name}>
                          <TableCell className="flex items-center gap-2">
                            <div 
                              className="w-3 h-3 rounded-full" 
                              style={{ backgroundColor: COLORS[index % COLORS.length] }}
                            />
                            {item.name}
                          </TableCell>
                          <TableCell className="text-right font-medium">{item.value}</TableCell>
                          <TableCell className="text-right">{percent}%</TableCell>
                        </TableRow>
                      );
                    })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Recent DSE Table */}
      {hasPermission('view_dse') && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-primary" />
              Последние заявки
            </CardTitle>
            <Button variant="outline" size="sm" asChild>
              <Link to="/dse">
                Показать все <ArrowRight className="h-4 w-4 ml-1" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ДСЕ</TableHead>
                  <TableHead>Тип проблемы</TableHead>
                  <TableHead>Описание</TableHead>
                  <TableHead>Дата</TableHead>
                  <TableHead className="text-right"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentDSE.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                      Нет данных
                    </TableCell>
                  </TableRow>
                ) : (
                  recentDSE.map((dse) => (
                    <TableRow key={dse.id}>
                      <TableCell>
                        <div className="font-medium">{dse.dse}</div>
                        <div className="text-sm text-muted-foreground">{dse.dse_name}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{dse.problem_type}</Badge>
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate">
                        {dse.description}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1 text-sm text-muted-foreground">
                          <Calendar className="h-3 w-3" />
                          {dse.datetime ? new Date(dse.datetime).toLocaleString('ru-RU') : '-'}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="sm" asChild>
                          <Link to={`/dse/${dse.id}`}>
                            Просмотр
                          </Link>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Welcome message for users without stats permission */}
      {!hasPermission('view_dashboard_stats') && (
        <Card className="border-dashed">
          <CardContent className="py-12 text-center">
            <Info className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">Добро пожаловать!</h3>
            <p className="text-muted-foreground max-w-md mx-auto">
              Используйте быстрые действия выше для работы с системой.
              {user?.role === 'initiator' && (
                <>
                  <br />
                  <strong>Роль инициатора:</strong> Вы можете создавать заявки и использовать чат.
                </>
              )}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
