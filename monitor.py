#!/usr/bin/env python3
"""
TelegrammBolt Monitor - Интерактивная консоль мониторинга и управления ботом
Работает независимо от бота, обменивается данными через файлы
"""

import os
import sys
import time
import json
import curses
from datetime import datetime
from pathlib import Path


class BotMonitor:
    """Монитор бота с TUI интерфейсом"""
    
    def __init__(self):
        self.running = True
        self.current_tab = 0
        self.tabs = ["📊 Статистика", "📋 Логи", "👥 Пользователи", "⚙️ Управление"]
        self.log_scroll = 0
        self.users_scroll = 0
        
        # Пути к файлам обмена данными
        self.stats_file = "monitor_stats.json"
        self.commands_file = "monitor_commands.json"
        self.log_file = "bot_monitor.log"
        
        # Инициализация файлов
        self._init_files()
    
    def _init_files(self):
        """Инициализация файлов обмена данными"""
        if not os.path.exists(self.stats_file):
            self._write_json(self.stats_file, {
                "status": "unknown",
                "uptime": 0,
                "users_total": 0,
                "users_active": 0,
                "dse_total": 0,
                "requests_total": 0,
                "requests_per_minute": 0,
                "memory_mb": 0,
                "last_update": None
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
            return {}
        return {}
    
    def _write_json(self, filepath, data):
        """Запись JSON файла"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            return False
    
    def _send_command(self, command, params=None):
        """Отправка команды боту"""
        commands_data = self._read_json(self.commands_file)
        if "commands" not in commands_data:
            commands_data["commands"] = []
        
        commands_data["commands"].append({
            "command": command,
            "params": params or {},
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        })
        
        return self._write_json(self.commands_file, commands_data)
    
    def get_stats(self):
        """Получить текущую статистику"""
        return self._read_json(self.stats_file)
    
    def get_logs(self, lines=50):
        """Получить последние логи"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return f.readlines()[-lines:]
        except:
            pass
        return ["Лог-файл не найден или пуст"]
    
    def get_users(self):
        """Получить список пользователей"""
        try:
            from user_manager import get_all_users
            users = get_all_users()
            return [
                f"{u['user_id'][:10]}... | {u.get('username', 'N/A')[:15]} | {u.get('role', 'user')}"
                for u in users[:20]  # Первые 20
            ]
        except:
            return ["Ошибка загрузки пользователей"]
    
    def draw_header(self, stdscr, height, width):
        """Отрисовка заголовка"""
        title = "🤖 TelegrammBolt Monitor"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(0, 0, " " * width)
        stdscr.addstr(0, 2, title)
        stdscr.addstr(0, width - len(timestamp) - 2, timestamp)
        stdscr.attroff(curses.color_pair(1))
        
        # Табы
        x_offset = 2
        for i, tab in enumerate(self.tabs):
            if i == self.current_tab:
                stdscr.attron(curses.color_pair(2))
                stdscr.addstr(1, x_offset, f" {tab} ")
                stdscr.attroff(curses.color_pair(2))
            else:
                stdscr.addstr(1, x_offset, f" {tab} ")
            x_offset += len(tab) + 3
        
        # Разделитель
        stdscr.addstr(2, 0, "─" * width)
    
    def draw_stats_tab(self, stdscr, y_start, height, width):
        """Вкладка статистики"""
        stats = self.get_stats()
        
        y = y_start
        
        # Статус бота
        status = str(stats.get("status", "unknown"))
        status_color = 3 if status == "running" else 4
        stdscr.attron(curses.color_pair(status_color))
        stdscr.addstr(y, 2, f"● Статус: {status.upper()}")
        stdscr.attroff(curses.color_pair(status_color))
        y += 2
        
        # Основная статистика
        info = [
            ("⏱️  Uptime", f"{stats.get('uptime', 0)} сек"),
            ("👥 Всего пользователей", str(stats.get('users_total', 0))),
            ("✅ Активных пользователей", str(stats.get('users_active', 0))),
            ("📋 Всего ДСЕ", str(stats.get('dse_total', 0))),
            ("📊 Всего запросов", str(stats.get('requests_total', 0))),
            ("⚡ Запросов/мин", str(stats.get('requests_per_minute', 0))),
            ("💾 Память (MB)", str(stats.get('memory_mb', 0))),
        ]
        
        for label, value in info:
            stdscr.addstr(y, 4, f"{label:.<30} {value}")
            y += 1
        
        y += 1
        stdscr.addstr(y, 2, "Последнее обновление:")
        y += 1
        last_update = str(stats.get('last_update') or 'N/A')
        stdscr.addstr(y, 4, last_update)
    
    def draw_logs_tab(self, stdscr, y_start, height, width):
        """Вкладка логов"""
        logs = self.get_logs(height - y_start - 5)
        
        y = y_start
        stdscr.addstr(y, 2, "📋 Последние логи (↑↓ для прокрутки):")
        y += 2
        
        max_lines = height - y - 2
        visible_logs = logs[self.log_scroll:self.log_scroll + max_lines]
        
        for log_line in visible_logs:
            if y >= height - 2:
                break
            line = str(log_line or "").strip()[:width - 6]
            
            # Цветное выделение по уровню
            if "ERROR" in line or "❌" in line:
                stdscr.attron(curses.color_pair(4))
            elif "WARN" in line or "⚠️" in line:
                stdscr.attron(curses.color_pair(5))
            elif "SUCCESS" in line or "✅" in line:
                stdscr.attron(curses.color_pair(3))
            
            stdscr.addstr(y, 4, line)
            
            if "ERROR" in line or "❌" in line:
                stdscr.attroff(curses.color_pair(4))
            elif "WARN" in line or "⚠️" in line:
                stdscr.attroff(curses.color_pair(5))
            elif "SUCCESS" in line or "✅" in line:
                stdscr.attroff(curses.color_pair(3))
            
            y += 1
    
    def draw_users_tab(self, stdscr, y_start, height, width):
        """Вкладка пользователей"""
        users = self.get_users()
        
        y = y_start
        stdscr.addstr(y, 2, "👥 Пользователи бота (↑↓ для прокрутки):")
        y += 2
        
        # Заголовок таблицы
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(y, 4, f"{'ID':<15} | {'Username':<18} | {'Роль':<10}")
        stdscr.attroff(curses.color_pair(1))
        y += 1
        stdscr.addstr(y, 4, "─" * 50)
        y += 1
        
        max_lines = height - y - 2
        visible_users = users[self.users_scroll:self.users_scroll + max_lines]
        
        for user_line in visible_users:
            if y >= height - 2:
                break
            stdscr.addstr(y, 4, str(user_line or "")[:width - 6])
            y += 1
    
    def draw_control_tab(self, stdscr, y_start, height, width):
        """Вкладка управления"""
        y = y_start
        stdscr.addstr(y, 2, "⚙️  Команды управления:")
        y += 2
        
        commands = [
            ("R", "Перезапустить watcher"),
            ("C", "Очистить кэш"),
            ("S", "Сохранить статистику"),
            ("L", "Очистить логи"),
            ("E", "Экспорт данных"),
            ("T", "Тест уведомлений"),
        ]
        
        for key, description in commands:
            stdscr.attron(curses.color_pair(2))
            stdscr.addstr(y, 4, f"[{key}]")
            stdscr.attroff(curses.color_pair(2))
            stdscr.addstr(y, 8, f"- {description}")
            y += 1
        
        y += 2
        stdscr.addstr(y, 2, "Статус последних команд:")
        y += 1
        
        commands_data = self._read_json(self.commands_file)
        recent_commands = commands_data.get("commands", [])[-5:]
        
        for cmd in recent_commands:
            if y >= height - 2:
                break
            status_icon = "✅" if cmd.get("status") == "completed" else "⏳"
            cmd_name = str(cmd.get('command', 'unknown'))
            timestamp = str(cmd.get('timestamp', ''))[:19]
            line = f"{status_icon} {cmd_name} - {timestamp}"
            stdscr.addstr(y, 4, line[:width - 6])
            y += 1
    
    def draw_footer(self, stdscr, height, width):
        """Отрисовка подвала"""
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(height - 1, 0, " " * width)
        
        help_text = "[TAB] Вкладки | [Q] Выход | [F5] Обновить | [↑↓] Прокрутка"
        stdscr.addstr(height - 1, 2, help_text[:width - 4])
        stdscr.attroff(curses.color_pair(1))
    
    def handle_input(self, stdscr, key):
        """Обработка ввода"""
        if key == ord('q') or key == ord('Q'):
            self.running = False
        
        elif key == ord('\t') or key == curses.KEY_RIGHT:
            self.current_tab = (self.current_tab + 1) % len(self.tabs)
            self.log_scroll = 0
            self.users_scroll = 0
        
        elif key == curses.KEY_LEFT:
            self.current_tab = (self.current_tab - 1) % len(self.tabs)
            self.log_scroll = 0
            self.users_scroll = 0
        
        elif key == curses.KEY_UP:
            if self.current_tab == 1:  # Логи
                self.log_scroll = max(0, self.log_scroll - 1)
            elif self.current_tab == 2:  # Пользователи
                self.users_scroll = max(0, self.users_scroll - 1)
        
        elif key == curses.KEY_DOWN:
            if self.current_tab == 1:  # Логи
                self.log_scroll += 1
            elif self.current_tab == 2:  # Пользователи
                self.users_scroll += 1
        
        elif key == curses.KEY_F5:
            pass  # Обновление происходит автоматически
        
        # Команды управления
        elif self.current_tab == 3:  # Вкладка управления
            if key == ord('r') or key == ord('R'):
                self._send_command("restart_watcher")
            elif key == ord('c') or key == ord('C'):
                self._send_command("clear_cache")
            elif key == ord('s') or key == ord('S'):
                self._send_command("save_stats")
            elif key == ord('l') or key == ord('L'):
                self._send_command("clear_logs")
            elif key == ord('e') or key == ord('E'):
                self._send_command("export_data")
            elif key == ord('t') or key == ord('T'):
                self._send_command("test_notifications")
    
    def run(self, stdscr):
        """Главный цикл отрисовки"""
        # Настройка цветов
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)    # Заголовок
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)   # Активная вкладка
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Успех
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)     # Ошибка
        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Предупреждение
        
        # Настройка
        curses.curs_set(0)  # Скрыть курсор
        stdscr.nodelay(1)   # Неблокирующий ввод
        stdscr.timeout(100) # Таймаут 100мс
        
        while self.running:
            stdscr.clear()
            height, width = stdscr.getmaxyx()
            
            # Отрисовка интерфейса
            self.draw_header(stdscr, height, width)
            
            y_content_start = 4
            
            if self.current_tab == 0:
                self.draw_stats_tab(stdscr, y_content_start, height, width)
            elif self.current_tab == 1:
                self.draw_logs_tab(stdscr, y_content_start, height, width)
            elif self.current_tab == 2:
                self.draw_users_tab(stdscr, y_content_start, height, width)
            elif self.current_tab == 3:
                self.draw_control_tab(stdscr, y_content_start, height, width)
            
            self.draw_footer(stdscr, height, width)
            
            stdscr.refresh()
            
            # Обработка ввода
            try:
                key = stdscr.getch()
                if key != -1:
                    self.handle_input(stdscr, key)
            except:
                pass
            
            time.sleep(0.1)


def main():
    """Точка входа"""
    print("🚀 Запуск TelegrammBolt Monitor...")
    print("Для выхода нажмите 'Q'\n")
    time.sleep(1)
    
    monitor = BotMonitor()
    
    try:
        curses.wrapper(monitor.run)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print("\n✅ Монитор остановлен")


if __name__ == "__main__":
    main()
