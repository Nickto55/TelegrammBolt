import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { dseApi } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
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
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { 
  Search, 
  Filter, 
  X, 
  FileSpreadsheet, 
  Eye, 
  EyeOff,
  Grid3X3,
  Table as TableIcon,
  RotateCcw,
  AlertTriangle,
  Hourglass
} from 'lucide-react';
import type { DSE } from '@/types';

const PROBLEM_TYPES = [
  'Программирование',
  'Наладка',
  'Инструмент',
  'Конструкция',
  'Материал',
  'Другое',
];

export function DSEList() {
  const { hasPermission, user } = useAuth();
  const [, setData] = useState<DSE[]>([]);
  const [filteredData, setFilteredData] = useState<DSE[]>([]);
  const [pendingRequests, setPendingRequests] = useState<DSE[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  
  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [problemTypeFilter, setProblemTypeFilter] = useState('');
  const [sortBy, setSortBy] = useState('date_desc');
  const [showHidden, setShowHidden] = useState(false);
  
  // View
  const [viewMode, setViewMode] = useState<'table' | 'card'>('table');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;
  
  // Dialogs
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedDSE, setSelectedDSE] = useState<DSE | null>(null);

  const totalPages = Math.ceil(totalCount / itemsPerPage);

  useEffect(() => {
    loadData();
  }, [currentPage, sortBy, problemTypeFilter, showHidden]);

  useEffect(() => {
    if (hasPermission('approve_dse_requests')) {
      loadPendingRequests();
    }
  }, [hasPermission]);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await dseApi.getAll({
        page: currentPage,
        limit: itemsPerPage,
        sort_by: sortBy,
        problem_type: problemTypeFilter || undefined,
        search: searchQuery || undefined,
        include_hidden: showHidden ? '1' : undefined
      });
      
      setData(res.data.data || []);
      setFilteredData(res.data.data || []);
      setTotalCount(res.data.pagination?.total || 0);
    } catch (error) {
      console.error('Failed to load DSE data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPendingRequests = async () => {
    try {
      const res = await dseApi.getPending();
      setPendingRequests(res.data.requests || []);
    } catch (error) {
      console.error('Failed to load pending requests:', error);
    }
  };

  const handleSearch = () => {
    setCurrentPage(1);
    loadData();
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setProblemTypeFilter('');
    setSortBy('date_desc');
    setShowHidden(false);
    setCurrentPage(1);
    loadData();
  };

  const handleHideDSE = (dse: DSE) => {
    setSelectedDSE(dse);
    setDeleteDialogOpen(true);
  };

  const confirmHide = async () => {
    if (!selectedDSE) return;
    
    try {
      if (selectedDSE.hidden) {
        await dseApi.restore(selectedDSE.id);
      } else {
        await dseApi.delete(selectedDSE.id);
      }
      await loadData();
    } catch (error) {
      console.error('Failed to toggle DSE visibility:', error);
    } finally {
      setDeleteDialogOpen(false);
      setSelectedDSE(null);
    }
  };

  const handleApproveRequest = async (requestId: string) => {
    try {
      await dseApi.approve(requestId);
      await loadPendingRequests();
      await loadData();
    } catch (error) {
      console.error('Failed to approve request:', error);
    }
  };

  const handleRejectRequest = async (requestId: string) => {
    try {
      await dseApi.reject(requestId);
      await loadPendingRequests();
    } catch (error) {
      console.error('Failed to reject request:', error);
    }
  };

  const handleExportExcel = async () => {
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
  };

  return (
    <div className="space-y-6">
      {/* Pending Requests Section */}
      {hasPermission('approve_dse_requests') && pendingRequests.length > 0 && (
        <Card className="border-amber-200 bg-amber-50 dark:bg-amber-950/20">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-amber-800 dark:text-amber-200">
              <Hourglass className="h-5 w-5" />
              Новые заявки на проверку
              <Badge variant="default" className="ml-2">{pendingRequests.length}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>ДСЕ</TableHead>
                  <TableHead>Наименование</TableHead>
                  <TableHead>Тип проблемы</TableHead>
                  <TableHead>Дата</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pendingRequests.map((req) => (
                  <TableRow key={req.id}>
                    <TableCell>{req.id?.slice(0, 8)}</TableCell>
                    <TableCell className="font-medium">{req.dse}</TableCell>
                    <TableCell>{req.dse_name}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{req.problem_type}</Badge>
                    </TableCell>
                    <TableCell>
                      {req.created_at ? new Date(req.created_at).toLocaleString('ru-RU') : '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button 
                          size="sm" 
                          variant="default"
                          onClick={() => handleApproveRequest(req.id!)}
                        >
                          Утвердить
                        </Button>
                        <Button 
                          size="sm" 
                          variant="destructive"
                          onClick={() => handleRejectRequest(req.id!)}
                        >
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

      {/* Filters */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Фильтры и поиск
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label htmlFor="search">Поиск</Label>
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="search"
                  placeholder="ДСЕ, описание..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  className="pl-9"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label>Тип проблемы</Label>
              <Select value={problemTypeFilter} onValueChange={setProblemTypeFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Все типы" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Все типы</SelectItem>
                  {PROBLEM_TYPES.map(type => (
                    <SelectItem key={type} value={type}>{type}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Сортировка</Label>
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="date_desc">Сначала новые</SelectItem>
                  <SelectItem value="date_asc">Сначала старые</SelectItem>
                  <SelectItem value="dse_asc">По ДСЕ (A-Z)</SelectItem>
                  <SelectItem value="dse_desc">По ДСЕ (Z-A)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2 flex items-end">
              <Button onClick={handleSearch} className="w-full">
                <Search className="h-4 w-4 mr-2" />
                Искать
              </Button>
            </div>
          </div>
          
          <div className="flex flex-wrap items-center gap-4 mt-4">
            {user?.role !== 'user' && (
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="showHidden"
                  checked={showHidden}
                  onCheckedChange={(checked) => setShowHidden(checked as boolean)}
                />
                <Label htmlFor="showHidden" className="text-sm cursor-pointer">
                  Показывать скрытые
                </Label>
              </div>
            )}
            
            <div className="flex-1" />
            
            <Button variant="outline" onClick={handleResetFilters}>
              <X className="h-4 w-4 mr-2" />
              Сбросить
            </Button>
            
            {hasPermission('export_data') && (
              <Button variant="outline" onClick={handleExportExcel}>
                <FileSpreadsheet className="h-4 w-4 mr-2" />
                Экспорт Excel
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Results Info */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          <strong>{totalCount}</strong> записей найдено
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant={viewMode === 'table' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('table')}
          >
            <TableIcon className="h-4 w-4 mr-1" />
            Таблица
          </Button>
          <Button
            variant={viewMode === 'card' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('card')}
          >
            <Grid3X3 className="h-4 w-4 mr-1" />
            Карточки
          </Button>
        </div>
      </div>

      {/* Data Display */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle>Список ДСЕ</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </div>
          ) : viewMode === 'table' ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ДСЕ</TableHead>
                  <TableHead>Тип проблемы</TableHead>
                  <TableHead>Станок</TableHead>
                  <TableHead>Наладчик</TableHead>
                  <TableHead>Программист</TableHead>
                  <TableHead>Описание</TableHead>
                  <TableHead>Дата</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredData.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                      Нет данных для отображения
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredData.map((item) => (
                    <TableRow key={item.id} className={item.hidden ? 'opacity-50' : ''}>
                      <TableCell>
                        <div className="font-medium">{item.dse}</div>
                        <div className="text-sm text-muted-foreground">{item.dse_name}</div>
                        {item.hidden && (
                          <Badge variant="secondary" className="mt-1">Скрыто</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{item.problem_type}</Badge>
                      </TableCell>
                      <TableCell>{item.machine_number}</TableCell>
                      <TableCell className="text-sm">{item.installer_fio}</TableCell>
                      <TableCell className="text-sm">{item.programmer_name}</TableCell>
                      <TableCell className="max-w-[200px] truncate text-sm">
                        {item.description}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {item.datetime ? new Date(item.datetime).toLocaleString('ru-RU') : '-'}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="icon" asChild>
                            <Link to={`/dse/${item.id}`}>
                              <Eye className="h-4 w-4" />
                            </Link>
                          </Button>
                          {hasPermission('delete_dse') && (
                            <Button 
                              variant="ghost" 
                              size="icon"
                              onClick={() => handleHideDSE(item)}
                            >
                              {item.hidden ? (
                                <RotateCcw className="h-4 w-4 text-emerald-500" />
                              ) : (
                                <EyeOff className="h-4 w-4 text-destructive" />
                              )}
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredData.length === 0 ? (
                <div className="col-span-full text-center py-8 text-muted-foreground">
                  Нет данных для отображения
                </div>
              ) : (
                filteredData.map((item) => (
                  <Card key={item.id} className={item.hidden ? 'opacity-50' : ''}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-medium">{item.dse}</h4>
                          <p className="text-sm text-muted-foreground">{item.dse_name}</p>
                        </div>
                        <Badge variant="outline">{item.problem_type}</Badge>
                      </div>
                      
                      <p className="text-sm mb-3 line-clamp-2">{item.description}</p>
                      
                      <div className="text-xs text-muted-foreground space-y-1 mb-3">
                        <div>Станок: {item.machine_number}</div>
                        <div>Наладчик: {item.installer_fio}</div>
                        <div>Программист: {item.programmer_name}</div>
                        <div>Дата: {item.datetime ? new Date(item.datetime).toLocaleString('ru-RU') : '-'}</div>
                      </div>
                      
                      {item.hidden && (
                        <Badge variant="secondary" className="mb-2">Скрыто</Badge>
                      )}
                      
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" className="flex-1" asChild>
                          <Link to={`/dse/${item.id}`}>
                            <Eye className="h-4 w-4 mr-1" />
                            Просмотр
                          </Link>
                        </Button>
                        {hasPermission('delete_dse') && (
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => handleHideDSE(item)}
                          >
                            {item.hidden ? (
                              <RotateCcw className="h-4 w-4 text-emerald-500" />
                            ) : (
                              <EyeOff className="h-4 w-4 text-destructive" />
                            )}
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <Pagination>
          <PaginationContent>
            <PaginationItem>
              <PaginationPrevious 
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                className={currentPage === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
              />
            </PaginationItem>
            
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
              <PaginationItem key={page}>
                <PaginationLink
                  onClick={() => setCurrentPage(page)}
                  isActive={currentPage === page}
                  className="cursor-pointer"
                >
                  {page}
                </PaginationLink>
              </PaginationItem>
            ))}
            
            <PaginationItem>
              <PaginationNext 
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                className={currentPage === totalPages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
              />
            </PaginationItem>
          </PaginationContent>
        </Pagination>
      )}

      {/* Hide/Restore Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              {selectedDSE?.hidden ? 'Восстановить заявку?' : 'Скрыть заявку?'}
            </DialogTitle>
            <DialogDescription>
              {selectedDSE?.hidden 
                ? 'Заявка снова будет видна в списке.' 
                : 'Заявка будет скрыта из списка, но останется в базе данных.'}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Отмена
            </Button>
            <Button 
              variant={selectedDSE?.hidden ? 'default' : 'destructive'}
              onClick={confirmHide}
            >
              {selectedDSE?.hidden ? (
                <><RotateCcw className="h-4 w-4 mr-2" /> Восстановить</>
              ) : (
                <><EyeOff className="h-4 w-4 mr-2" /> Скрыть</>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
