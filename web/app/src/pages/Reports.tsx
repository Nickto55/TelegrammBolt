import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
// import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Calendar } from '@/components/ui/calendar';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { 
  FileText, 
  FileSpreadsheet, 
  FileDown,
  Calendar as CalendarIcon,
  Download,
  BarChart3,
  PieChart,
  TrendingUp
} from 'lucide-react';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

interface Report {
  id: string;
  name: string;
  type: 'excel' | 'pdf' | 'csv';
  created_at: string;
  size: string;
}

// Mock data
const mockReports: Report[] = [
  { id: '1', name: 'Отчет_ДСЕ_Январь2024.xlsx', type: 'excel', created_at: '2024-01-31', size: '45 KB' },
  { id: '2', name: 'Статистика_проблем.pdf', type: 'pdf', created_at: '2024-01-25', size: '128 KB' },
  { id: '3', name: 'Экспорт_пользователей.csv', type: 'csv', created_at: '2024-01-20', size: '12 KB' },
];

export function Reports() {
  const [reports, setReports] = useState<Report[]>(mockReports);
  const [date, setDate] = useState<Date>();
  const [reportType, setReportType] = useState('dse');
  const [format_type, setFormatType] = useState('excel');

  const handleGenerateReport = () => {
    const newReport: Report = {
      id: Date.now().toString(),
      name: `Отчет_${reportType}_${format(new Date(), 'ddMMyyyy')}.${format_type === 'excel' ? 'xlsx' : format_type}`,
      type: format_type as 'excel' | 'pdf' | 'csv',
      created_at: new Date().toISOString().split('T')[0],
      size: `${Math.floor(Math.random() * 200 + 10)} KB`,
    };
    setReports(prev => [newReport, ...prev]);
    alert('Отчет сгенерирован успешно');
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'excel':
        return <FileSpreadsheet className="h-5 w-5 text-emerald-500" />;
      case 'pdf':
        return <FileText className="h-5 w-5 text-red-500" />;
      case 'csv':
        return <FileDown className="h-5 w-5 text-blue-500" />;
      default:
        return <FileText className="h-5 w-5" />;
    }
  };

  const getTypeBadge = (type: string) => {
    switch (type) {
      case 'excel':
        return <Badge variant="outline" className="text-emerald-500 border-emerald-500">Excel</Badge>;
      case 'pdf':
        return <Badge variant="outline" className="text-red-500 border-red-500">PDF</Badge>;
      case 'csv':
        return <Badge variant="outline" className="text-blue-500 border-blue-500">CSV</Badge>;
      default:
        return <Badge variant="outline">{type}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Отчеты</h1>
          <p className="text-muted-foreground">Генерация и экспорт отчетов</p>
        </div>
      </div>

      <Tabs defaultValue="generate" className="w-full">
        <TabsList className="grid w-full grid-cols-2 max-w-md">
          <TabsTrigger value="generate">Создать отчет</TabsTrigger>
          <TabsTrigger value="history">История</TabsTrigger>
        </TabsList>

        <TabsContent value="generate" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Параметры отчета
              </CardTitle>
              <CardDescription>
                Выберите тип отчета и период
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Report Type */}
                <div className="space-y-2">
                  <Label>Тип отчета</Label>
                  <Select value={reportType} onValueChange={setReportType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="dse">Отчет по ДСЕ</SelectItem>
                      <SelectItem value="problems">Статистика проблем</SelectItem>
                      <SelectItem value="users">Отчет по пользователям</SelectItem>
                      <SelectItem value="activity">Активность системы</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Format */}
                <div className="space-y-2">
                  <Label>Формат</Label>
                  <Select value={format_type} onValueChange={setFormatType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="excel">Excel (.xlsx)</SelectItem>
                      <SelectItem value="pdf">PDF (.pdf)</SelectItem>
                      <SelectItem value="csv">CSV (.csv)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Date Range */}
                <div className="space-y-2">
                  <Label>Дата начала</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className="w-full justify-start text-left font-normal"
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {date ? format(date, 'PPP', { locale: ru }) : <span>Выберите дату</span>}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <Calendar
                        mode="single"
                        selected={date}
                        onSelect={setDate}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>

                {/* End Date */}
                <div className="space-y-2">
                  <Label>Дата окончания</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className="w-full justify-start text-left font-normal"
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        <span>Выберите дату</span>
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <Calendar
                        mode="single"
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>
              </div>

              <div className="flex justify-end">
                <Button onClick={handleGenerateReport}>
                  <TrendingUp className="h-4 w-4 mr-2" />
                  Сгенерировать отчет
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Quick Reports */}
          <Card>
            <CardHeader>
              <CardTitle>Быстрые отчеты</CardTitle>
              <CardDescription>
                Предустановленные отчеты за текущий месяц
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Button variant="outline" className="h-auto py-4 flex flex-col items-center gap-2">
                  <FileSpreadsheet className="h-8 w-8 text-emerald-500" />
                  <span>Все ДСЕ</span>
                </Button>
                <Button variant="outline" className="h-auto py-4 flex flex-col items-center gap-2">
                  <PieChart className="h-8 w-8 text-blue-500" />
                  <span>Статистика</span>
                </Button>
                <Button variant="outline" className="h-auto py-4 flex flex-col items-center gap-2">
                  <FileText className="h-8 w-8 text-red-500" />
                  <span>PDF отчет</span>
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>История отчетов</CardTitle>
              <CardDescription>
                Ранее сгенерированные отчеты
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {reports.map((report) => (
                  <div
                    key={report.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      {getTypeIcon(report.type)}
                      <div>
                        <p className="font-medium">{report.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {report.created_at} • {report.size}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {getTypeBadge(report.type)}
                      <Button variant="ghost" size="icon">
                        <Download className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
