import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { 
  Save, 
  Bell, 
  Shield, 
  Database, 
  Mail, 
  Globe,
  CheckCircle
} from 'lucide-react';

export function Settings() {
  const [saved, setSaved] = useState(false);
  const [settings, setSettings] = useState({
    notifications_email: true,
    notifications_telegram: false,
    notifications_push: true,
    dark_mode: false,
    auto_logout: 30,
    language: 'ru',
  });

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleToggle = (key: string) => {
    setSettings(prev => ({ ...prev, [key]: !prev[key as keyof typeof prev] }));
    setSaved(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Настройки системы</h1>
          <p className="text-muted-foreground">Управление параметрами приложения</p>
        </div>
        {saved && (
          <Badge variant="outline" className="text-emerald-500 border-emerald-500">
            <CheckCircle className="h-4 w-4 mr-1" />
            Сохранено
          </Badge>
        )}
      </div>

      <Tabs defaultValue="general" className="w-full">
        <TabsList className="grid w-full grid-cols-4 max-w-lg">
          <TabsTrigger value="general">Общие</TabsTrigger>
          <TabsTrigger value="notifications">Уведомления</TabsTrigger>
          <TabsTrigger value="security">Безопасность</TabsTrigger>
          <TabsTrigger value="system">Система</TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5" />
                Общие настройки
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label>Название организации</Label>
                <Input placeholder="ООО Пример" defaultValue="BOLT Systems" />
              </div>
              
              <div className="space-y-2">
                <Label>Язык интерфейса</Label>
                <div className="flex gap-2">
                  <Button variant="default" size="sm">Русский</Button>
                  <Button variant="outline" size="sm">English</Button>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Темная тема</Label>
                  <p className="text-sm text-muted-foreground">
                    Использовать темную тему оформления
                  </p>
                </div>
                <Switch 
                  checked={settings.dark_mode}
                  onCheckedChange={() => handleToggle('dark_mode')}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                Уведомления
              </CardTitle>
              <CardDescription>
                Настройте способы получения уведомлений
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className="flex items-center gap-2">
                    <Mail className="h-4 w-4" />
                    Email уведомления
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    Получать уведомления на электронную почту
                  </p>
                </div>
                <Switch 
                  checked={settings.notifications_email}
                  onCheckedChange={() => handleToggle('notifications_email')}
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className="flex items-center gap-2">
                    <Bell className="h-4 w-4" />
                    Push-уведомления
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    Браузерные push-уведомления
                  </p>
                </div>
                <Switch 
                  checked={settings.notifications_push}
                  onCheckedChange={() => handleToggle('notifications_push')}
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className="flex items-center gap-2">
                    <Database className="h-4 w-4" />
                    Telegram уведомления
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    Уведомления через Telegram бота
                  </p>
                </div>
                <Switch 
                  checked={settings.notifications_telegram}
                  onCheckedChange={() => handleToggle('notifications_telegram')}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Безопасность
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label>Автоматический выход (минут)</Label>
                <Input 
                  type="number" 
                  value={settings.auto_logout}
                  onChange={(e) => setSettings(prev => ({ ...prev, auto_logout: parseInt(e.target.value) }))}
                />
                <p className="text-sm text-muted-foreground">
                  Время бездействия до автоматического выхода из системы
                </p>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Двухфакторная аутентификация</Label>
                  <p className="text-sm text-muted-foreground">
                    Требовать 2FA для входа администраторов
                  </p>
                </div>
                <Switch />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Журналирование действий</Label>
                  <p className="text-sm text-muted-foreground">
                    Записывать все действия пользователей
                  </p>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="system" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Система
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label>Версия системы</Label>
                <p className="text-sm">BOLT v2.0.0</p>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>Резервное копирование</Label>
                <div className="flex gap-2">
                  <Button variant="outline">Создать бэкап</Button>
                  <Button variant="outline">Восстановить</Button>
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label className="text-destructive">Опасная зона</Label>
                <div className="flex gap-2">
                  <Button variant="destructive">Очистить кэш</Button>
                  <Button variant="outline" className="text-destructive border-destructive">
                    Сбросить настройки
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="flex justify-end">
        <Button onClick={handleSave}>
          <Save className="h-4 w-4 mr-2" />
          Сохранить настройки
        </Button>
      </div>
    </div>
  );
}
