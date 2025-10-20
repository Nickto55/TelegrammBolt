"""
Bot Monitor Integration Module
Модуль интеграции с monitor.py для сбора статистики и обработки команд
"""

import os
import json
import psutil
import asyncio
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class BotMonitorIntegration:
    """Интеграция бота с системой мониторинга"""
    
    def __init__(self):
        self.stats_file = "monitor_stats.json"
        self.commands_file = "monitor_commands.json"
        self.log_file = "bot_monitor.log"
        
        self.start_time = datetime.now()
        self.request_count = 0
        self.last_request_time = datetime.now()
        self.requests_last_minute = []
        
        # Инициализация
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """Создание файлов, если не существуют"""
        if not os.path.exists(self.stats_file):
            self._write_stats({
                "status": "starting",
                "uptime": 0,
                "users_total": 0,
                "users_active": 0,
                "dse_total": 0,
                "requests_total": 0,
                "requests_per_minute": 0,
                "memory_mb": 0,
                "last_update": datetime.now().isoformat()
            })
        
        if not os.path.exists(self.commands_file):
            self._write_json(self.commands_file, {"commands": []})
    
    def _read_json(self, filepath):
        """Чтение JSON файла"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка чтения {filepath}: {e}")
            return {}
        return {}
    
    def _write_json(self, filepath, data):
        """Запись JSON файла"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Ошибка записи {filepath}: {e}")
            return False
    
    def _write_stats(self, stats_data):
        """Запись статистики"""
        return self._write_json(self.stats_file, stats_data)
    
    def log_to_monitor(self, message, level="INFO"):
        """Запись лога для монитора"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"[{timestamp}] [{level}] {message}\n"
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_line)
            
            # Ограничиваем размер лог-файла (последние 1000 строк)
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                if len(lines) > 1000:
                    with open(self.log_file, 'w', encoding='utf-8') as f:
                        f.writelines(lines[-1000:])
        except Exception as e:
            logger.error(f"Ошибка записи лога монитора: {e}")
    
    def increment_request(self):
        """Увеличить счетчик запросов"""
        self.request_count += 1
        self.requests_last_minute.append(datetime.now())
        
        # Очищаем старые запросы (старше 1 минуты)
        one_minute_ago = datetime.now().timestamp() - 60
        self.requests_last_minute = [
            t for t in self.requests_last_minute 
            if t.timestamp() > one_minute_ago
        ]
    
    def get_memory_usage(self):
        """Получить использование памяти в MB"""
        try:
            process = psutil.Process(os.getpid())
            return round(process.memory_info().rss / 1024 / 1024, 2)
        except:
            return 0
    
    def update_stats(self):
        """Обновление статистики"""
        try:
            from user_manager import get_all_users
            from dse_manager import get_all_dse_records
            
            users = get_all_users()
            dse_records = get_all_dse_records()
            
            # Безопасная проверка - users это список user_id (строки)
            users_total = len(users) if users else 0
            
            # Активные пользователи - для простоты считаем всех зарегистрированных
            active_users = users_total
            
            # Безопасная проверка - dse_records это список словарей
            dse_total = len(dse_records) if dse_records else 0
            
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            stats = {
                "status": "running",
                "uptime": int(uptime),
                "users_total": users_total,
                "users_active": active_users,
                "dse_total": dse_total,
                "requests_total": self.request_count,
                "requests_per_minute": len(self.requests_last_minute),
                "memory_mb": self.get_memory_usage(),
                "last_update": datetime.now().isoformat()
            }
            
            self._write_stats(stats)
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления статистики: {e}")
            return False
    
    def process_commands(self, application):
        """Обработка команд от монитора"""
        try:
            commands_data = self._read_json(self.commands_file)
            commands = commands_data.get("commands", [])
            
            updated = False
            for cmd in commands:
                if cmd.get("status") == "pending":
                    result = self._execute_command(cmd["command"], cmd.get("params", {}), application)
                    cmd["status"] = "completed" if result else "failed"
                    cmd["completed_at"] = datetime.now().isoformat()
                    updated = True
                    
                    self.log_to_monitor(
                        f"Команда {cmd['command']} выполнена: {'успешно' if result else 'ошибка'}",
                        "SUCCESS" if result else "ERROR"
                    )
            
            if updated:
                self._write_json(self.commands_file, commands_data)
            
            return True
        except Exception as e:
            logger.error(f"Ошибка обработки команд: {e}")
            return False
    
    def _execute_command(self, command, params, application):
        """Выполнение команды"""
        try:
            if command == "restart_watcher":
                # Перезапуск watcher'а
                self.log_to_monitor("Перезапуск DSE Watcher...", "INFO")
                # TODO: реализовать перезапуск watcher
                return True
            
            elif command == "clear_cache":
                # Очистка кэша
                self.log_to_monitor("Очистка кэша...", "INFO")
                # TODO: реализовать очистку кэша
                return True
            
            elif command == "save_stats":
                # Сохранение статистики
                self.log_to_monitor("Сохранение статистики...", "INFO")
                return self.update_stats()
            
            elif command == "clear_logs":
                # Очистка логов
                self.log_to_monitor("Очистка логов...", "INFO")
                if os.path.exists(self.log_file):
                    open(self.log_file, 'w').close()
                return True
            
            elif command == "export_data":
                # Экспорт данных
                self.log_to_monitor("Экспорт данных...", "INFO")
                # TODO: реализовать экспорт
                return True
            
            elif command == "test_notifications":
                # Тест уведомлений
                self.log_to_monitor("Тест уведомлений...", "INFO")
                # TODO: реализовать тест уведомлений
                return True
            
            else:
                self.log_to_monitor(f"Неизвестная команда: {command}", "WARN")
                return False
        
        except Exception as e:
            logger.error(f"Ошибка выполнения команды {command}: {e}")
            return False


# Глобальный экземпляр
_monitor_integration = None


def get_monitor_integration():
    """Получить экземпляр интеграции монитора"""
    global _monitor_integration
    if _monitor_integration is None:
        _monitor_integration = BotMonitorIntegration()
    return _monitor_integration


async def start_monitor_integration(application):
    """Запуск фоновой задачи интеграции с монитором"""
    monitor = get_monitor_integration()
    
    monitor.log_to_monitor("🚀 Бот запущен", "SUCCESS")
    monitor.update_stats()
    
    async def monitor_loop():
        """Цикл обновления статистики и обработки команд"""
        while True:
            try:
                # Обновляем статистику каждые 5 секунд
                monitor.update_stats()
                
                # Обрабатываем команды
                monitor.process_commands(application)
                
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Ошибка в monitor_loop: {e}")
                await asyncio.sleep(5)
    
    # Запускаем фоновую задачу
    asyncio.create_task(monitor_loop())
    logger.info("✅ Интеграция монитора запущена")
