import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Shield, 
  Key, 
  Camera,
  Save,
  CheckCircle,
  MessageCircle,
  AlertTriangle
} from 'lucide-react';

export function Profile() {
  const { user } = useAuth();
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: '',
    phone: '',
  });

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setSuccess(false);
  };

  const handleSave = async () => {
    setLoading(true);
    // Mock API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setSuccess(true);
    setLoading(false);
  };

  const handleConnectTelegram = () => {
    alert('Подключение Telegram будет реализовано');
  };

  const handleChangePassword = () => {
    alert('Смена пароля будет реализована');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold">Профиль</h1>
      </div>

      <Tabs defaultValue="info" className="w-full">
        <TabsList className="grid w-full grid-cols-3 max-w-md">
          <TabsTrigger value="info">Информация</TabsTrigger>
          <TabsTrigger value="security">Безопасность</TabsTrigger>
          <TabsTrigger value="settings">Настройки</TabsTrigger>
        </TabsList>

        {/* Info Tab */}
        <TabsContent value="info" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Личная информация</CardTitle>
              <CardDescription>
                Управляйте вашими персональными данными
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {success && (
                <Alert className="bg-emerald-50 border-emerald-200">
                  <CheckCircle className="h-4 w-4 text-emerald-500" />
                  <AlertDescription className="text-emerald-700">
                    Изменения сохранены успешно
                  </AlertDescription>
                </Alert>
              )}

              {/* Avatar Section */}
              <div className="flex items-center gap-6">
                <div className="relative">
                  <Avatar className="h-24 w-24">
                    <AvatarImage src={user?.photo_url} />
                    <AvatarFallback className="text-2xl">
                      {user?.first_name?.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <Button 
                    size="icon" 
                    variant="secondary" 
                    className="absolute -bottom-2 -right-2 h-8 w-8 rounded-full"
                  >
                    <Camera className="h-4 w-4" />
                  </Button>
                </div>
                <div>
                  <h3 className="font-semibold text-lg">{user?.first_name} {user?.last_name}</h3>
                  <Badge variant="secondary" className="capitalize">{user?.role}</Badge>
                </div>
              </div>

              <Separator />

              {/* Form Fields */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="first_name">Имя</Label>
                  <Input
                    id="first_name"
                    value={formData.first_name}
                    onChange={(e) => handleChange('first_name', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="last_name">Фамилия</Label>
                  <Input
                    id="last_name"
                    value={formData.last_name}
                    onChange={(e) => handleChange('last_name', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="email@example.com"
                    value={formData.email}
                    onChange={(e) => handleChange('email', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Телефон</Label>
                  <Input
                    id="phone"
                    placeholder="+7 (999) 999-99-99"
                    value={formData.phone}
                    onChange={(e) => handleChange('phone', e.target.value)}
                  />
                </div>
              </div>

              <div className="flex justify-end">
                <Button onClick={handleSave} disabled={loading}>
                  {loading ? (
                    <div className="h-4 w-4 mr-2 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  ) : (
                    <Save className="h-4 w-4 mr-2" />
                  )}
                  Сохранить изменения
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Telegram Connection */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageCircle className="h-5 w-5 text-[#0088cc]" />
                Подключение Telegram
              </CardTitle>
              <CardDescription>
                Подключите Telegram для получения уведомлений и быстрого входа
              </CardDescription>
            </CardHeader>
            <CardContent>
              {user?.telegram_linked ? (
                <div className="flex items-center justify-between p-4 bg-emerald-50 dark:bg-emerald-950/20 rounded-lg">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="h-5 w-5 text-emerald-500" />
                    <div>
                      <p className="font-medium">Telegram подключен</p>
                      <p className="text-sm text-muted-foreground">@{user.username}</p>
                    </div>
                  </div>
                  <Button variant="outline" size="sm">Отключить</Button>
                </div>
              ) : (
                <div className="flex items-center justify-between p-4 bg-amber-50 dark:bg-amber-950/20 rounded-lg">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="h-5 w-5 text-amber-500" />
                    <div>
                      <p className="font-medium">Telegram не подключен</p>
                      <p className="text-sm text-muted-foreground">Подключите для удобного входа</p>
                    </div>
                  </div>
                  <Button onClick={handleConnectTelegram} size="sm" className="bg-[#0088cc] hover:bg-[#0077b3]">
                    Подключить
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="h-5 w-5" />
                Смена пароля
              </CardTitle>
              <CardDescription>
                Рекомендуется менять пароль каждые 3 месяца
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="current_password">Текущий пароль</Label>
                <Input id="current_password" type="password" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new_password">Новый пароль</Label>
                <Input id="new_password" type="password" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirm_password">Подтвердите пароль</Label>
                <Input id="confirm_password" type="password" />
              </div>
              <Button onClick={handleChangePassword}>
                <Key className="h-4 w-4 mr-2" />
                Изменить пароль
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Двухфакторная аутентификация
              </CardTitle>
              <CardDescription>
                Дополнительный уровень защиты вашего аккаунта
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center">
                    <Shield className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-medium">2FA отключена</p>
                    <p className="text-sm text-muted-foreground">Включите для повышенной безопасности</p>
                  </div>
                </div>
                <Button variant="outline">Включить</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Уведомления</CardTitle>
              <CardDescription>
                Настройте способы получения уведомлений
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">Email уведомления</p>
                  <p className="text-sm text-muted-foreground">Получать уведомления на email</p>
                </div>
                <Button variant="outline" size="sm">Настроить</Button>
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">Telegram уведомления</p>
                  <p className="text-sm text-muted-foreground">Получать уведомления в Telegram</p>
                </div>
                <Button variant="outline" size="sm">Настроить</Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-destructive">Опасная зона</CardTitle>
              <CardDescription>
                Действия, которые нельзя отменить
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between p-4 border border-destructive/20 rounded-lg bg-destructive/5">
                <div>
                  <p className="font-medium text-destructive">Удалить аккаунт</p>
                  <p className="text-sm text-muted-foreground">Это действие нельзя отменить</p>
                </div>
                <Button variant="destructive" size="sm">Удалить</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
