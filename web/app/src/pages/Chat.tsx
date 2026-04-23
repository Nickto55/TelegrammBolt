import { useState, useRef, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
// import { Separator } from '@/components/ui/separator';
import { Send, Paperclip, Smile, MoreVertical, Phone, Video } from 'lucide-react';

interface Message {
  id: string;
  senderId: string;
  senderName: string;
  senderAvatar?: string;
  text: string;
  timestamp: Date;
  isOwn: boolean;
}

interface ChatRoom {
  id: string;
  name: string;
  avatar?: string;
  lastMessage?: string;
  lastMessageTime?: Date;
  unreadCount: number;
  isOnline?: boolean;
}

// Mock data
const mockRooms: ChatRoom[] = [
  { id: '1', name: 'Общий чат', lastMessage: 'Привет всем!', lastMessageTime: new Date(Date.now() - 3600000), unreadCount: 0 },
  { id: '2', name: 'Поддержка ДСЕ', lastMessage: 'Проблема решена', lastMessageTime: new Date(Date.now() - 7200000), unreadCount: 2, isOnline: true },
  { id: '3', name: 'Администратор', lastMessage: 'Проверьте заявку #123', lastMessageTime: new Date(Date.now() - 86400000), unreadCount: 0 },
];

const mockMessages: Message[] = [
  { id: '1', senderId: '2', senderName: 'Поддержка', text: 'Здравствуйте! Чем могу помочь?', timestamp: new Date(Date.now() - 3600000), isOwn: false },
  { id: '2', senderId: '1', senderName: 'Вы', text: 'Проблема с ДСЕ 12345', timestamp: new Date(Date.now() - 3500000), isOwn: true },
  { id: '3', senderId: '2', senderName: 'Поддержка', text: 'Опишите подробнее, пожалуйста', timestamp: new Date(Date.now() - 3400000), isOwn: false },
  { id: '4', senderId: '1', senderName: 'Вы', text: 'Ошибка в программе обработки', timestamp: new Date(Date.now() - 3300000), isOwn: true },
  { id: '5', senderId: '2', senderName: 'Поддержка', text: 'Понял, передаю программисту', timestamp: new Date(Date.now() - 3200000), isOwn: false },
  { id: '6', senderId: '2', senderName: 'Поддержка', text: 'Проблема решена', timestamp: new Date(Date.now() - 7200000), isOwn: false },
];

export function Chat() {
  // const { user } = useAuth();
  // const [rooms] = useState<ChatRoom[]>(mockRooms);
  // const [selectedRoom, setSelectedRoom] = useState<ChatRoom | null>(mockRooms[1]);
  // const [messages, setMessages] = useState<Message[]>(mockMessages);
  // const [newMessage, setNewMessage] = useState('');
  // const messagesEndRef = useRef<HTMLDivElement>(null);

  const { user } = useAuth();
  const [rooms] = useState<ChatRoom[]>();
  const [selectedRoom, setSelectedRoom] = useState<ChatRoom | null>();
  const [messages, setMessages] = useState<Message[]>();
  const [newMessage, setNewMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = () => {
    if (!newMessage.trim() || !selectedRoom) return;

    const message: Message = {
      id: Date.now().toString(),
      senderId: user?.id || '1',
      senderName: user?.first_name || 'Вы',
      senderAvatar: user?.photo_url,
      text: newMessage.trim(),
      timestamp: new Date(),
      isOwn: true,
    };

    setMessages((prev: any) => [...prev, message]);
    setNewMessage('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="h-[calc(100vh-180px)]">
      <Card className="h-full flex overflow-hidden">
        {/* Rooms List */}
        <div className="w-80 border-r flex flex-col">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Чаты</CardTitle>
          </CardHeader>
          <ScrollArea className="flex-1">
            <div className="space-y-1 p-2">
              {rooms.map((room: { id: any; avatar: any; name: string; isOnline: any; lastMessageTime: Date; lastMessage: any; unreadCount: number; }) => (
                <button
                  key={room.id}
                  onClick={() => setSelectedRoom(room)}
                  className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition-colors ${
                    selectedRoom?.id === room.id 
                      ? 'bg-primary text-primary-foreground' 
                      : 'hover:bg-accent'
                  }`}
                >
                  <div className="relative">
                    <Avatar className="h-10 w-10">
                      <AvatarImage src={room.avatar} />
                      <AvatarFallback>{room.name.charAt(0).toUpperCase()}</AvatarFallback>
                    </Avatar>
                    {room.isOnline && (
                      <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-emerald-500 border-2 border-background" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="font-medium truncate">{room.name}</span>
                      {room.lastMessageTime && (
                        <span className={`text-xs ${selectedRoom?.id === room.id ? 'text-primary-foreground/70' : 'text-muted-foreground'}`}>
                          {formatTime(room.lastMessageTime)}
                        </span>
                      )}
                    </div>
                    {room.lastMessage && (
                      <p className={`text-sm truncate ${selectedRoom?.id === room.id ? 'text-primary-foreground/70' : 'text-muted-foreground'}`}>
                        {room.lastMessage}
                      </p>
                    )}
                  </div>
                  {room.unreadCount > 0 && (
                    <Badge variant={selectedRoom?.id === room.id ? 'secondary' : 'default'} className="ml-2">
                      {room.unreadCount}
                    </Badge>
                  )}
                </button>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {selectedRoom ? (
            <>
              {/* Header */}
              <CardHeader className="pb-3 border-b">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Avatar className="h-10 w-10">
                      <AvatarImage src={selectedRoom.avatar} />
                      <AvatarFallback>{selectedRoom.name.charAt(0).toUpperCase()}</AvatarFallback>
                    </Avatar>
                    <div>
                      <CardTitle className="text-lg">{selectedRoom.name}</CardTitle>
                      {selectedRoom.isOnline && (
                        <p className="text-xs text-emerald-500">в сети</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="ghost" size="icon">
                      <Phone className="h-5 w-5" />
                    </Button>
                    <Button variant="ghost" size="icon">
                      <Video className="h-5 w-5" />
                    </Button>
                    <Button variant="ghost" size="icon">
                      <MoreVertical className="h-5 w-5" />
                    </Button>
                  </div>
                </div>
              </CardHeader>

              {/* Messages */}
              <ScrollArea className="flex-1 p-4">
                <div className="space-y-4">
                  {messages.map((message: { senderId: any; id: any; isOwn: any; senderAvatar: any; senderName: string; text: any; timestamp: Date; }, index: number) => {
                    const showAvatar = index === 0 || messages[index - 1].senderId !== message.senderId;
                    
                    return (
                      <div
                        key={message.id}
                        className={`flex gap-3 ${message.isOwn ? 'flex-row-reverse' : ''}`}
                      >
                        {showAvatar && !message.isOwn ? (
                          <Avatar className="h-8 w-8 mt-1">
                            <AvatarImage src={message.senderAvatar} />
                            <AvatarFallback>{message.senderName.charAt(0).toUpperCase()}</AvatarFallback>
                          </Avatar>
                        ) : (
                          <div className="w-8" />
                        )}
                        <div className={`max-w-[70%] ${message.isOwn ? 'items-end' : 'items-start'}`}>
                          {showAvatar && (
                            <p className={`text-xs text-muted-foreground mb-1 ${message.isOwn ? 'text-right' : ''}`}>
                              {message.senderName}
                            </p>
                          )}
                          <div
                            className={`px-4 py-2 rounded-2xl ${
                              message.isOwn
                                ? 'bg-primary text-primary-foreground rounded-br-md'
                                : 'bg-muted rounded-bl-md'
                            }`}
                          >
                            <p>{message.text}</p>
                          </div>
                          <p className={`text-xs text-muted-foreground mt-1 ${message.isOwn ? 'text-right' : ''}`}>
                            {formatTime(message.timestamp)}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>

              {/* Input */}
              <CardContent className="pt-0 pb-4">
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="icon">
                    <Paperclip className="h-5 w-5" />
                  </Button>
                  <Input
                    placeholder="Введите сообщение..."
                    value={newMessage}
                    onChange={(e: { target: { value: any; }; }) => setNewMessage(e.target.value)}
                    onKeyDown={handleKeyPress}
                    className="flex-1"
                  />
                  <Button variant="ghost" size="icon">
                    <Smile className="h-5 w-5" />
                  </Button>
                  <Button onClick={handleSendMessage} disabled={!newMessage.trim()}>
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-muted-foreground">
              <p>Выберите чат для начала общения</p>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}