import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { 
  ArrowLeft, 
  Edit2, 
  Trash2, 
  MessageSquare, 
  Clock,
  User,
  FileText,
  CheckCircle,
  Send
} from 'lucide-react';
import type { DSE } from '@/types';

// Mock data
const mockDSE: DSE = {
  id: '1',
  dse: '12345',
  dse_name: 'Деталь А',
  problem_type: 'Программирование',
  description: 'Ошибка в программе обработки детали. Требуется корректировка траектории инструмента. При обработке происходит столкновение с зажимным приспособлением.',
  machine_number: 'CNC-01',
  installer_fio: 'Петров Иван Сергеевич',
  programmer_name: 'Сидоров Алексей Владимирович',
  datetime: '2024-01-15 14:30:00',
  user_id: 'user_1',
  status: 'В работе',
};

interface Comment {
  id: string;
  author: string;
  avatar?: string;
  text: string;
  timestamp: string;
}

const mockComments: Comment[] = [
  { 
    id: '1', 
    author: 'Иван Петров', 
    text: 'Принял в работу. Начинаю анализ проблемы.',
    timestamp: '2024-01-15 14:35:00'
  },
  { 
    id: '2', 
    author: 'Алексей Сидоров', 
    text: 'Проверил программу. Необходимо изменить точку подхода.',
    timestamp: '2024-01-15 15:20:00'
  },
];

export function DSEDetail() {
  const { id: _id } = useParams<{ id: string }>();
  const { hasPermission } = useAuth();
  const [dse] = useState<DSE>(mockDSE);
  const [comments, setComments] = useState<Comment[]>(mockComments);
  const [newComment, setNewComment] = useState('');

  const handleAddComment = () => {
    if (!newComment.trim()) return;
    
    const comment: Comment = {
      id: Date.now().toString(),
      author: 'Вы',
      text: newComment.trim(),
      timestamp: new Date().toLocaleString('ru-RU'),
    };
    
    setComments(prev => [...prev, comment]);
    setNewComment('');
  };

  const handleStatusChange = () => {
    alert('Статус изменен');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="icon" asChild>
            <Link to="/dse">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-bold">ДСЕ {dse.dse}</h1>
            <p className="text-muted-foreground">{dse.dse_name}</p>
          </div>
        </div>
        <div className="flex gap-2">
          {hasPermission('edit_dse') && (
            <Button variant="outline">
              <Edit2 className="h-4 w-4 mr-2" />
              Редактировать
            </Button>
          )}
          {hasPermission('delete_dse') && (
            <Button variant="destructive">
              <Trash2 className="h-4 w-4 mr-2" />
              Удалить
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Info */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Информация о заявке
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Тип проблемы</p>
                  <Badge variant="secondary" className="mt-1">{dse.problem_type}</Badge>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Статус</p>
                  <Badge variant="default" className="mt-1">{dse.status}</Badge>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Станок</p>
                  <p className="font-medium">{dse.machine_number}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Дата создания</p>
                  <p className="font-medium">{dse.datetime}</p>
                </div>
              </div>

              <Separator />

              <div>
                <p className="text-sm text-muted-foreground mb-2">Описание проблемы</p>
                <p className="text-sm leading-relaxed">{dse.description}</p>
              </div>

              <Separator />

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Наладчик</p>
                  <div className="flex items-center gap-2 mt-1">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <p className="font-medium">{dse.installer_fio}</p>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Программист</p>
                  <div className="flex items-center gap-2 mt-1">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <p className="font-medium">{dse.programmer_name}</p>
                  </div>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex gap-2">
              <Button onClick={handleStatusChange} className="flex-1">
                <CheckCircle className="h-4 w-4 mr-2" />
                Отметить выполненной
              </Button>
              <Button variant="outline" className="flex-1">
                <MessageSquare className="h-4 w-4 mr-2" />
                Написать в чат
              </Button>
            </CardFooter>
          </Card>

          {/* Comments */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Комментарии
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4">
                {comments.map((comment) => (
                  <div key={comment.id} className="flex gap-3">
                    <Avatar className="h-8 w-8">
                      <AvatarImage src={comment.avatar} />
                      <AvatarFallback>{comment.author.charAt(0)}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{comment.author}</span>
                        <span className="text-xs text-muted-foreground">{comment.timestamp}</span>
                      </div>
                      <p className="text-sm mt-1">{comment.text}</p>
                    </div>
                  </div>
                ))}
              </div>

              <Separator />

              <div className="flex gap-2">
                <Textarea
                  placeholder="Добавить комментарий..."
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  className="flex-1 min-h-[80px]"
                />
              </div>
              <div className="flex justify-end">
                <Button onClick={handleAddComment} disabled={!newComment.trim()}>
                  <Send className="h-4 w-4 mr-2" />
                  Отправить
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>История</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex gap-3">
                  <Clock className="h-4 w-4 text-muted-foreground mt-0.5" />
                  <div>
                    <p className="text-sm">Заявка создана</p>
                    <p className="text-xs text-muted-foreground">{dse.datetime}</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <User className="h-4 w-4 text-muted-foreground mt-0.5" />
                  <div>
                    <p className="text-sm">Назначен ответственный</p>
                    <p className="text-xs text-muted-foreground">{dse.installer_fio}</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <CheckCircle className="h-4 w-4 text-emerald-500 mt-0.5" />
                  <div>
                    <p className="text-sm">Принята в работу</p>
                    <p className="text-xs text-muted-foreground">2024-01-15 14:35</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Связанные файлы</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-4 text-muted-foreground">
                <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Нет прикрепленных файлов</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
