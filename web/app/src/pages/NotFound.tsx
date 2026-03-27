import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ArrowLeft, Home, AlertTriangle } from 'lucide-react';

export function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="max-w-md w-full">
        <CardContent className="pt-12 pb-12 text-center">
          <div className="flex justify-center mb-6">
            <div className="h-20 w-20 rounded-full bg-amber-100 dark:bg-amber-950 flex items-center justify-center">
              <AlertTriangle className="h-10 w-10 text-amber-500" />
            </div>
          </div>
          
          <h1 className="text-4xl font-bold mb-2">404</h1>
          <h2 className="text-xl font-semibold mb-4">Страница не найдена</h2>
          <p className="text-muted-foreground mb-8">
            Запрашиваемая страница не существует или была перемещена.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Button variant="outline" onClick={() => window.history.back()}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Назад
            </Button>
            <Button asChild>
              <Link to="/dashboard">
                <Home className="h-4 w-4 mr-2" />
                На главную
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
