import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ArrowLeft, Save, CheckCircle, AlertCircle } from 'lucide-react';
import { Link } from 'react-router-dom';

const PROBLEM_TYPES = [
  'Программирование',
  'Наладка',
  'Инструмент',
  'Конструкция',
  'Материал',
  'Другое',
];

export function CreateDSE() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({
    dse: '',
    dse_name: '',
    problem_type: '',
    description: '',
    machine_number: '',
    installer_fio: '',
    programmer_name: '',
  });

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!formData.dse || !formData.problem_type) {
      setError('Заполните обязательные поля (ДСЕ и Тип проблемы)');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      setSuccess(true);
      
      // Reset form after success
      setTimeout(() => {
        navigate('/dse');
      }, 2000);
    } catch (err) {
      setError('Ошибка при создании заявки');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="max-w-2xl mx-auto">
        <Card>
          <CardContent className="py-12 text-center">
            <CheckCircle className="h-16 w-16 text-emerald-500 mx-auto mb-4" />
            <h2 className="text-2xl font-semibold mb-2">Заявка создана!</h2>
            <p className="text-muted-foreground mb-4">
              Ваша заявка успешно добавлена в систему.
            </p>
            <Button asChild>
              <Link to="/dse">Перейти к списку</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center gap-4 mb-6">
        <Button variant="outline" size="icon" asChild>
          <Link to="/dse">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <h1 className="text-2xl font-bold">Создать заявку ДСЕ</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Новая заявка</CardTitle>
          <CardDescription>
            Заполните информацию о проблеме. Поля, отмеченные *, обязательны для заполнения.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-6">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* DSE Number */}
              <div className="space-y-2">
                <Label htmlFor="dse">
                  ДСЕ <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="dse"
                  placeholder="Номер ДСЕ"
                  value={formData.dse}
                  onChange={(e) => handleChange('dse', e.target.value)}
                  disabled={loading}
                />
              </div>

              {/* DSE Name */}
              <div className="space-y-2">
                <Label htmlFor="dse_name">Наименование</Label>
                <Input
                  id="dse_name"
                  placeholder="Наименование детали"
                  value={formData.dse_name}
                  onChange={(e) => handleChange('dse_name', e.target.value)}
                  disabled={loading}
                />
              </div>

              {/* Problem Type */}
              <div className="space-y-2">
                <Label>
                  Тип проблемы <span className="text-destructive">*</span>
                </Label>
                <Select 
                  value={formData.problem_type} 
                  onValueChange={(value) => handleChange('problem_type', value)}
                  disabled={loading}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Выберите тип проблемы" />
                  </SelectTrigger>
                  <SelectContent>
                    {PROBLEM_TYPES.map(type => (
                      <SelectItem key={type} value={type}>{type}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Machine Number */}
              <div className="space-y-2">
                <Label htmlFor="machine_number">Номер станка</Label>
                <Input
                  id="machine_number"
                  placeholder="Например: CNC-01"
                  value={formData.machine_number}
                  onChange={(e) => handleChange('machine_number', e.target.value)}
                  disabled={loading}
                />
              </div>

              {/* Installer */}
              <div className="space-y-2">
                <Label htmlFor="installer_fio">Наладчик</Label>
                <Input
                  id="installer_fio"
                  placeholder="ФИО наладчика"
                  value={formData.installer_fio}
                  onChange={(e) => handleChange('installer_fio', e.target.value)}
                  disabled={loading}
                />
              </div>

              {/* Programmer */}
              <div className="space-y-2">
                <Label htmlFor="programmer_name">Программист</Label>
                <Input
                  id="programmer_name"
                  placeholder="ФИО программиста"
                  value={formData.programmer_name}
                  onChange={(e) => handleChange('programmer_name', e.target.value)}
                  disabled={loading}
                />
              </div>
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">Описание проблемы</Label>
              <Textarea
                id="description"
                placeholder="Подробно опишите проблему..."
                rows={5}
                value={formData.description}
                onChange={(e) => handleChange('description', e.target.value)}
                disabled={loading}
              />
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-4">
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => navigate('/dse')}
                disabled={loading}
              >
                Отмена
              </Button>
              <Button 
                type="submit" 
                disabled={loading}
              >
                {loading ? (
                  <>
                    <div className="h-4 w-4 mr-2 animate-spin rounded-full border-2 border-current border-t-transparent" />
                    Сохранение...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Создать заявку
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
