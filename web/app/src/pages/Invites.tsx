import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
// import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { 
  Plus, 
  QrCode, 
  Copy, 
  Trash2, 
  Download
} from 'lucide-react';

interface Invite {
  id: string;
  code: string;
  role: string;
  created_at: string;
  expires_at: string;
  used_by?: string;
  used_at?: string;
  status: 'active' | 'used' | 'expired';
}

// Mock data
const mockInvites: Invite[] = [
  { 
    id: '1', 
    code: 'BOLT-ABC123', 
    role: 'initiator', 
    created_at: '2024-01-20', 
    expires_at: '2024-02-20',
    status: 'active'
  },
  { 
    id: '2', 
    code: 'BOLT-DEF456', 
    role: 'user', 
    created_at: '2024-01-15', 
    expires_at: '2024-02-15',
    used_by: 'user_123',
    used_at: '2024-01-16',
    status: 'used'
  },
  { 
    id: '3', 
    code: 'BOLT-GHI789', 
    role: 'initiator', 
    created_at: '2023-12-01', 
    expires_at: '2024-01-01',
    status: 'expired'
  },
];

const ROLE_LABELS: Record<string, string> = {
  admin: 'Администратор',
  responder: 'Ответственный',
  initiator: 'Инициатор',
  user: 'Пользователь',
};

export function Invites() {
  const [invites, setInvites] = useState<Invite[]>(mockInvites);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [qrDialogOpen, setQrDialogOpen] = useState(false);
  const [selectedInvite, setSelectedInvite] = useState<Invite | null>(null);
  const [newInviteRole, setNewInviteRole] = useState('initiator');

  const handleCreateInvite = () => {
    const newInvite: Invite = {
      id: Date.now().toString(),
      code: `BOLT-${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
      role: newInviteRole,
      created_at: new Date().toISOString().split('T')[0],
      expires_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      status: 'active',
    };
    setInvites(prev => [newInvite, ...prev]);
    setSelectedInvite(newInvite);
    setCreateDialogOpen(false);
    setQrDialogOpen(true);
  };

  const handleDeleteInvite = (id: string) => {
    setInvites(prev => prev.filter(i => i.id !== id));
  };

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    alert('Код скопирован в буфер обмена');
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="default" className="bg-emerald-500">Активен</Badge>;
      case 'used':
        return <Badge variant="secondary">Использован</Badge>;
      case 'expired':
        return <Badge variant="outline">Истек</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">QR Приглашения</h1>
          <p className="text-muted-foreground">Управление пригласительными кодами</p>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Создать приглашение
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{invites.length}</div>
            <p className="text-sm text-muted-foreground">Всего приглашений</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-emerald-500">
              {invites.filter(i => i.status === 'active').length}
            </div>
            <p className="text-sm text-muted-foreground">Активных</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-blue-500">
              {invites.filter(i => i.status === 'used').length}
            </div>
            <p className="text-sm text-muted-foreground">Использованных</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-gray-500">
              {invites.filter(i => i.status === 'expired').length}
            </div>
            <p className="text-sm text-muted-foreground">Истекших</p>
          </CardContent>
        </Card>
      </div>

      {/* Invites Table */}
      <Card>
        <CardHeader>
          <CardTitle>Список приглашений</CardTitle>
          <CardDescription>
            Все созданные пригласительные коды
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Код</TableHead>
                <TableHead>Роль</TableHead>
                <TableHead>Создан</TableHead>
                <TableHead>Истекает</TableHead>
                <TableHead>Статус</TableHead>
                <TableHead className="text-right">Действия</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {invites.map((invite) => (
                <TableRow key={invite.id}>
                  <TableCell>
                    <code className="px-2 py-1 bg-muted rounded text-sm font-mono">
                      {invite.code}
                    </code>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{ROLE_LABELS[invite.role]}</Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {invite.created_at}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {invite.expires_at}
                  </TableCell>
                  <TableCell>{getStatusBadge(invite.status)}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      {invite.status === 'active' && (
                        <>
                          <Button 
                            variant="ghost" 
                            size="icon"
                            onClick={() => {
                              setSelectedInvite(invite);
                              setQrDialogOpen(true);
                            }}
                            title="Показать QR"
                          >
                            <QrCode className="h-4 w-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="icon"
                            onClick={() => handleCopyCode(invite.code)}
                            title="Копировать код"
                          >
                            <Copy className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                      <Button 
                        variant="ghost" 
                        size="icon"
                        onClick={() => handleDeleteInvite(invite.id)}
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Create Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Создать приглашение</DialogTitle>
            <DialogDescription>
              Выберите роль для нового пользователя
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Роль пользователя</Label>
              <Select value={newInviteRole} onValueChange={setNewInviteRole}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="initiator">Инициатор</SelectItem>
                  <SelectItem value="user">Пользователь</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm text-muted-foreground">
                Приглашение будет действительно в течение 30 дней
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
              Отмена
            </Button>
            <Button onClick={handleCreateInvite}>
              <Plus className="h-4 w-4 mr-2" />
              Создать
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* QR Dialog */}
      <Dialog open={qrDialogOpen} onOpenChange={setQrDialogOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-center">QR Код приглашения</DialogTitle>
            <DialogDescription className="text-center">
              Отсканируйте код или скопируйте для отправки
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col items-center py-6">
            {/* Mock QR Code */}
            <div className="w-48 h-48 bg-white p-4 rounded-lg border-2 border-dashed border-muted-foreground/30 flex items-center justify-center mb-4">
              <QrCode className="w-32 h-32 text-foreground" />
            </div>
            <code className="px-4 py-2 bg-muted rounded-lg text-lg font-mono mb-4">
              {selectedInvite?.code}
            </code>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => handleCopyCode(selectedInvite?.code || '')}>
                <Copy className="h-4 w-4 mr-2" />
                Копировать
              </Button>
              <Button variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Скачать
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
