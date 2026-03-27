import { useState } from 'react';
// import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
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
  Hourglass, 
  CheckCircle, 
  XCircle, 
  Eye,
  AlertTriangle
} from 'lucide-react';

interface PendingRequest {
  id: string;
  dse: string;
  dse_name?: string;
  problem_type: string;
  description?: string;
  user_id?: string;
  user_name?: string;
  created_at: string;
}

// Mock data
const mockPendingRequests: PendingRequest[] = [
  { 
    id: '1', 
    dse: '99999', 
    dse_name: 'Новая деталь X', 
    problem_type: 'Программирование',
    description: 'Требуется создание управляющей программы',
    user_name: 'Иван Петров',
    created_at: '2024-01-20T14:30:00'
  },
  { 
    id: '2', 
    dse: '99998', 
    dse_name: 'Новая деталь Y', 
    problem_type: 'Наладка',
    description: 'Переналадка станка под новую деталь',
    user_name: 'Мария Сидорова',
    created_at: '2024-01-20T13:15:00'
  },
  { 
    id: '3', 
    dse: '99997', 
    dse_name: 'Деталь Z', 
    problem_type: 'Инструмент',
    description: 'Подбор инструмента для обработки',
    user_name: 'Алексей Иванов',
    created_at: '2024-01-20T11:45:00'
  },
];

export function DSEPending() {
  // const navigate = useNavigate();
  const [requests, setRequests] = useState<PendingRequest[]>(mockPendingRequests);
  const [selectedRequest, setSelectedRequest] = useState<PendingRequest | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [approveDialogOpen, setApproveDialogOpen] = useState(false);
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);

  const handleView = (request: PendingRequest) => {
    setSelectedRequest(request);
    setViewDialogOpen(true);
  };

  const handleApprove = (request: PendingRequest) => {
    setSelectedRequest(request);
    setApproveDialogOpen(true);
  };

  const handleReject = (request: PendingRequest) => {
    setSelectedRequest(request);
    setRejectDialogOpen(true);
  };

  const confirmApprove = () => {
    if (selectedRequest) {
      setRequests(prev => prev.filter(r => r.id !== selectedRequest.id));
      alert('Заявка утверждена и добавлена в базу');
    }
    setApproveDialogOpen(false);
    setSelectedRequest(null);
  };

  const confirmReject = () => {
    if (selectedRequest) {
      setRequests(prev => prev.filter(r => r.id !== selectedRequest.id));
      alert('Заявка отклонена');
    }
    setRejectDialogOpen(false);
    setSelectedRequest(null);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ru-RU');
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Заявки на проверку</h1>
          <p className="text-muted-foreground">
            Новые заявки, ожидающие утверждения
          </p>
        </div>
        <Badge variant="default" className="text-lg px-4 py-2">
          <Hourglass className="h-4 w-4 mr-2" />
          {requests.length} ожидает
        </Badge>
      </div>

      {requests.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="py-12 text-center">
            <CheckCircle className="h-16 w-16 text-emerald-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">Все заявки обработаны!</h3>
            <p className="text-muted-foreground">
              Нет новых заявок на проверку
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Список заявок</CardTitle>
            <CardDescription>
              Проверьте и утвердите или отклоните заявки
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>ДСЕ</TableHead>
                  <TableHead>Тип проблемы</TableHead>
                  <TableHead>Пользователь</TableHead>
                  <TableHead>Дата</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {requests.map((request) => (
                  <TableRow key={request.id}>
                    <TableCell>{request.id}</TableCell>
                    <TableCell>
                      <div className="font-medium">{request.dse}</div>
                      <div className="text-sm text-muted-foreground">{request.dse_name}</div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{request.problem_type}</Badge>
                    </TableCell>
                    <TableCell>{request.user_name}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDate(request.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button 
                          variant="ghost" 
                          size="icon"
                          onClick={() => handleView(request)}
                          title="Просмотр"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button 
                          variant="default" 
                          size="sm"
                          onClick={() => handleApprove(request)}
                        >
                          <CheckCircle className="h-4 w-4 mr-1" />
                          Утвердить
                        </Button>
                        <Button 
                          variant="destructive" 
                          size="sm"
                          onClick={() => handleReject(request)}
                        >
                          <XCircle className="h-4 w-4 mr-1" />
                          Отклонить
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* View Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Просмотр заявки #{selectedRequest?.id}</DialogTitle>
            <DialogDescription>
              Детальная информация о заявке
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">ДСЕ</p>
                <p className="font-medium">{selectedRequest?.dse}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Наименование</p>
                <p className="font-medium">{selectedRequest?.dse_name}</p>
              </div>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Тип проблемы</p>
              <Badge variant="secondary" className="mt-1">
                {selectedRequest?.problem_type}
              </Badge>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Описание</p>
              <p className="mt-1">{selectedRequest?.description}</p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Пользователь</p>
                <p className="font-medium">{selectedRequest?.user_name}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Дата создания</p>
                <p className="font-medium">
                  {selectedRequest?.created_at && formatDate(selectedRequest.created_at)}
                </p>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setViewDialogOpen(false)}>
              Закрыть
            </Button>
            <Button 
              variant="default" 
              onClick={() => {
                setViewDialogOpen(false);
                if (selectedRequest) handleApprove(selectedRequest);
              }}
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Утвердить
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Approve Dialog */}
      <Dialog open={approveDialogOpen} onOpenChange={setApproveDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-emerald-500" />
              Утвердить заявку?
            </DialogTitle>
            <DialogDescription>
              Заявка #{selectedRequest?.id} будет добавлена в базу данных ДСЕ.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setApproveDialogOpen(false)}>
              Отмена
            </Button>
            <Button onClick={confirmApprove}>
              <CheckCircle className="h-4 w-4 mr-2" />
              Утвердить
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reject Dialog */}
      <Dialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" />
              Отклонить заявку?
            </DialogTitle>
            <DialogDescription>
              Заявка #{selectedRequest?.id} будет отклонена и архивирована.
              Это действие нельзя отменить.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRejectDialogOpen(false)}>
              Отмена
            </Button>
            <Button variant="destructive" onClick={confirmReject}>
              <XCircle className="h-4 w-4 mr-2" />
              Отклонить
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
