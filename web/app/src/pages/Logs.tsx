import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Clock, 
  RefreshCw, 
  Download, 
  Filter,
  AlertTriangle,
  CheckCircle,
  Info,
  XCircle
} from 'lucide-react';

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
  user?: string;
  action: string;
}

// Mock data
const mockLogs: LogEntry[] = [
  { id: '1', timestamp: '2024-01-20 14:30:15', level: 'info', message: 'Пользователь вошел в систему', user: 'Иван Петров', action: 'LOGIN' },
  { id: '2', timestamp: '2024-01-20 14:25:32', level: 'success', message: 'ДСЕ #12345 создана успешно', user: 'Мария Сидорова', action: 'CREATE_DSE' },
  { id: '3', timestamp: '2024-01-20 14:20:10', level: 'warning', message: 'Попытка несанкционированного доступа', user: 'Неизвестный', action: 'ACCESS_DENIED' },
  { id: '4', timestamp: '2024-01-20 14:15:45', level: 'info', message: 'Отчет сгенерирован', user: 'Алексей Иванов', action: 'GENERATE_REPORT' },
  { id: '5', timestamp: '2024-01-20 14:10:22', level: 'error', message: 'Ошибка подключения к базе данных', action: 'DB_ERROR' },
  { id: '6', timestamp: '2024-01-20 14:05:18', level: 'success', message: 'Пользователь создан', user: 'Администратор', action: 'CREATE_USER' },
  { id: '7', timestamp: '2024-01-20 14:00:00', level: 'info', message: 'Система запущена', action: 'SYSTEM_START' },
  { id: '8', timestamp: '2024-01-20 13:55:33', level: 'warning', message: 'Высокая нагрузка на сервер', action: 'SYSTEM_WARNING' },
  { id: '9', timestamp: '2024-01-20 13:50:12', level: 'info', message: 'Резервное копирование завершено', action: 'BACKUP_COMPLETE' },
  { id: '10', timestamp: '2024-01-20 13:45:00', level: 'success', message: 'QR приглашение активировано', user: 'Ольга Козлова', action: 'ACTIVATE_INVITE' },
];

export function Logs() {
  const [logs] = useState<LogEntry[]>(mockLogs);
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredLogs = logs.filter(log => {
    const matchesFilter = filter === 'all' || log.level === filter;
    const matchesSearch = !searchQuery || 
      log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.user?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.action.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'info':
        return <Info className="h-4 w-4 text-blue-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-amber-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-emerald-500" />;
      default:
        return <Info className="h-4 w-4" />;
    }
  };

  const getLevelBadge = (level: string) => {
    switch (level) {
      case 'info':
        return <Badge variant="outline" className="text-blue-500">INFO</Badge>;
      case 'warning':
        return <Badge variant="outline" className="text-amber-500">WARN</Badge>;
      case 'error':
        return <Badge variant="outline" className="text-red-500">ERROR</Badge>;
      case 'success':
        return <Badge variant="outline" className="text-emerald-500">SUCCESS</Badge>;
      default:
        return <Badge variant="outline">{level}</Badge>;
    }
  };

  const handleRefresh = () => {
    // Mock refresh
    alert('Логи обновлены');
  };

  const handleExport = () => {
    alert('Логи экспортированы');
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Логи системы</h1>
          <p className="text-muted-foreground">Журнал действий и событий</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Обновить
          </Button>
          <Button variant="outline" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            Экспорт
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <Input
                placeholder="Поиск в логах..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <Select value={filter} onValueChange={setFilter}>
              <SelectTrigger className="w-[180px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Фильтр" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Все уровни</SelectItem>
                <SelectItem value="info">Информация</SelectItem>
                <SelectItem value="warning">Предупреждения</SelectItem>
                <SelectItem value="error">Ошибки</SelectItem>
                <SelectItem value="success">Успех</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Logs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Журнал событий
          </CardTitle>
          <CardDescription>
            Показано {filteredLogs.length} из {logs.length} записей
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px]">
            <div className="space-y-2">
              {filteredLogs.map((log) => (
                <div
                  key={log.id}
                  className="flex items-start gap-4 p-3 border rounded-lg hover:bg-accent/50 transition-colors"
                >
                  <div className="mt-0.5">{getLevelIcon(log.level)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      {getLevelBadge(log.level)}
                      <span className="text-sm text-muted-foreground font-mono">
                        {log.timestamp}
                      </span>
                      <span className="text-xs px-2 py-0.5 bg-muted rounded font-mono">
                        {log.action}
                      </span>
                    </div>
                    <p className="mt-1">{log.message}</p>
                    {log.user && (
                      <p className="text-sm text-muted-foreground mt-1">
                        Пользователь: {log.user}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
