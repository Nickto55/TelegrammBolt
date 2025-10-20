#!/usr/bin/env python3
"""
Файл для тестового запуска веб-версии в режиме разработки
Запускает Flask приложение с debug режимом и auto-reload
"""

import os
import sys

# Добавляем текущую директорию в путь для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    print("="*80)
    print("🚀 Запуск веб-приложения в режиме разработки")
    print("="*80)
    print()
    print("📋 Параметры запуска:")
    print("   • Режим: Development (Debug)")
    print("   • Auto-reload: Включен")
    print("   • Хост: 127.0.0.1 (localhost)")
    print("   • Порт: 5000")
    print()
    print("🌐 Доступ к приложению:")
    print("   • http://127.0.0.1:5000")
    print("   • http://localhost:5000")
    print()
    print("💡 Подсказки:")
    print("   • Изменения в коде применяются автоматически")
    print("   • Для остановки нажмите Ctrl+C")
    print("   • Логи отображаются в реальном времени")
    print()
    print("="*80)
    print()
    
    # Импортируем приложение
    from web_app import app
    
    # Запускаем в режиме разработки
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        use_reloader=True,
        threaded=True
    )
