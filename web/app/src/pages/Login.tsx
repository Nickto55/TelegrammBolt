import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { 
  Shield, 
  MessageCircle, 
  QrCode, 
  Camera, 
  CameraOff,
  CheckCircle,
  AlertCircle,
  Loader2,
  Eye,
  EyeOff
} from 'lucide-react';

// QR Scanner mock (в реальном приложении используйте библиотеку)
function useQRScanner(
  videoRef: React.RefObject<HTMLVideoElement | null>,
  onScan: (code: string) => void
) {
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setIsScanning(true);
      
      // Mock QR scan after 3 seconds for demo
      setTimeout(() => {
        onScan('DEMO-CODE-123');
      }, 3000);
    } catch (err) {
      setError('Не удалось получить доступ к камере');
    }
  };

  const stop = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    setIsScanning(false);
  };

  return { isScanning, error, start, stop };
}

export function Login() {
  const navigate = useNavigate();
  const { loginWithCredentials, loginWithTelegram, loginWithQR } = useAuth();
  const [activeTab, setActiveTab] = useState('admin');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  // Admin login form
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  
  // QR code
  const [qrCode, setQrCode] = useState('');
  const videoRef = useRef<HTMLVideoElement>(null);
  const { isScanning, error: qrError, start, stop } = useQRScanner(videoRef, (code) => {
    setQrCode(code);
    handleQRLogin(code);
  });

  useEffect(() => {
    return () => {
      stop();
    };
  }, []);

  const handleAdminLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await loginWithCredentials(username, password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Неверный логин или пароль');
    } finally {
      setLoading(false);
    }
  };

  const handleTelegramAuth = async () => {
    setError(null);
    setLoading(true);
    
    try {
      // Mock Telegram auth data
      await loginWithTelegram({
        id: Date.now(),
        first_name: 'Telegram User',
        username: 'telegram_user',
        photo_url: null
      });
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Ошибка авторизации через Telegram');
    } finally {
      setLoading(false);
    }
  };

  const handleQRLogin = async (code: string) => {
    setError(null);
    setLoading(true);
    
    try {
      await loginWithQR(code);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Неверный QR код');
    } finally {
      setLoading(false);
    }
  };

  const handleQRSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (qrCode.trim()) {
      handleQRLogin(qrCode.trim().toUpperCase());
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/20 via-primary/10 to-background p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-primary mb-4 shadow-lg shadow-primary/30">
            <svg width="60" height="60" viewBox="0 0 100 100" className="text-primary-foreground">
              <path d="M20,30 Q35,20 50,30 T80,30" fill="none" stroke="currentColor" strokeWidth="8" opacity="0.6" />
              <path d="M10,50 Q30,35 50,50 T90,50" fill="none" stroke="currentColor" strokeWidth="10" opacity="0.8" />
              <path d="M15,70 Q35,55 55,70 T85,70" fill="none" stroke="currentColor" strokeWidth="8" opacity="0.5" />
              <text x="50" y="65" fontSize="40" fontWeight="bold" fill="currentColor" textAnchor="middle">B</text>
            </svg>
          </div>
          <h1 className="text-3xl font-bold">BOLT</h1>
          <p className="text-muted-foreground mt-1">Система управления ДСЕ</p>
        </div>

        <Card className="shadow-xl border-0">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl text-center">Добро пожаловать</CardTitle>
            <CardDescription className="text-center">
              Выберите способ входа в систему
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-3 mb-6">
                <TabsTrigger value="admin" className="gap-2">
                  <Shield className="h-4 w-4" />
                  <span className="hidden sm:inline">Login</span>
                </TabsTrigger>
                <TabsTrigger value="telegram" className="gap-2">
                  <MessageCircle className="h-4 w-4" />
                  <span className="hidden sm:inline">Telegram</span>
                </TabsTrigger>
                <TabsTrigger value="qr" className="gap-2">
                  <QrCode className="h-4 w-4" />
                  <span className="hidden sm:inline">QR</span>
                </TabsTrigger>
              </TabsList>

              {/* Admin Login */}
              <TabsContent value="admin">
                <form onSubmit={handleAdminLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="username">Логин</Label>
                    <Input
                      id="username"
                      placeholder="Введите логин"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      disabled={loading}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password">Пароль</Label>
                    <div className="relative">
                      <Input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder="Введите пароль"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        disabled={loading}
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="absolute right-0 top-0 h-full px-3"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                  <Button 
                    type="submit" 
                    className="w-full" 
                    disabled={loading || !username || !password}
                  >
                    {loading ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                      <CheckCircle className="h-4 w-4 mr-2" />
                    )}
                    Войти
                  </Button>
                </form>
              </TabsContent>

              {/* Telegram Login */}
              <TabsContent value="telegram">
                <div className="space-y-4 text-center">
                  <p className="text-sm text-muted-foreground">
                    Войдите используя ваш Telegram аккаунт
                  </p>
                  <div className="flex justify-center">
                    <Button 
                      onClick={handleTelegramAuth} 
                      disabled={loading}
                      className="bg-[#0088cc] hover:bg-[#0077b3] text-white"
                    >
                      {loading ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      ) : (
                        <MessageCircle className="h-4 w-4 mr-2" />
                      )}
                      Войти через Telegram
                    </Button>
                  </div>
                  <Separator />
                  <p className="text-xs text-muted-foreground">
                    Не зарегистрированы? Обратитесь к администратору
                  </p>
                </div>
              </TabsContent>

              {/* QR Login */}
              <TabsContent value="qr">
                <div className="space-y-4">
                  {/* Camera Preview */}
                  <div className="relative aspect-video bg-muted rounded-lg overflow-hidden">
                    {isScanning ? (
                      <video
                        ref={videoRef}
                        className="w-full h-full object-cover"
                        playsInline
                      />
                    ) : (
                      <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                        <Camera className="h-12 w-12 mb-2" />
                        <p className="text-sm">Нажмите "Включить камеру"</p>
                      </div>
                    )}
                    {qrError && (
                      <div className="absolute inset-0 flex items-center justify-center bg-destructive/10">
                        <p className="text-destructive text-sm">{qrError}</p>
                      </div>
                    )}
                  </div>

                  {/* Camera Controls */}
                  <div className="flex justify-center gap-2">
                    {!isScanning ? (
                      <Button onClick={start} variant="outline">
                        <Camera className="h-4 w-4 mr-2" />
                        Включить камеру
                      </Button>
                    ) : (
                      <Button onClick={stop} variant="outline">
                        <CameraOff className="h-4 w-4 mr-2" />
                        Выключить
                      </Button>
                    )}
                  </div>

                  <Separator />

                  {/* Manual Input */}
                  <form onSubmit={handleQRSubmit} className="space-y-2">
                    <Label htmlFor="qr-code">Или введите код вручную</Label>
                    <div className="flex gap-2">
                      <Input
                        id="qr-code"
                        placeholder="Введите код приглашения"
                        value={qrCode}
                        onChange={(e) => setQrCode(e.target.value.toUpperCase())}
                        className="uppercase"
                      />
                      <Button type="submit" disabled={!qrCode.trim() || loading}>
                        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}
                      </Button>
                    </div>
                  </form>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-muted-foreground mt-6">
          При входе вы соглашаетесь с условиями использования
        </p>
      </div>
    </div>
  );
}
