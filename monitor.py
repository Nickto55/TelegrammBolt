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
        # Только ASCII для совместимости
        self.tabs = ["[1] Stats", "[2] Logs", "[3] Users", "[4] Control"]
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
                    log_lines = f.readlines()[-lines:]
                # Конвертируем в ASCII-безопасный формат
                safe_logs = []
                for line in log_lines:
                    # Заменяем не-ASCII символы на '?'
                    safe_line = line.encode('ascii', 'replace').decode('ascii')
                    safe_logs.append(safe_line)
                return safe_logs
        except Exception as e:
            pass
        return ["Log file not found or empty"]
    
    def get_users(self):
        """Получить список пользователей"""
        try:
            from user_manager import get_all_users
            users = get_all_users()
            result = []
            for u in users[:20]:  # Первые 20
                # Конвертируем всё в ASCII-безопасный формат
                user_id = str(u.get('user_id', 'N/A'))[:10]
                username = str(u.get('username', 'N/A'))[:15]
                # Заменяем не-ASCII символы
                username = username.encode('ascii', 'replace').decode('ascii')
                role = str(u.get('role', 'user'))
                result.append(f"{user_id}... | {username} | {role}")
            return result
        except Exception as e:
            return [f"Error loading users: {str(e)}"]
    
    def draw_progress_bar(self, stdscr, y, x, width, percentage, label=""):
        """Рисует прогресс-бар как в htop"""
        bar_width = width - len(label) - 10  # Оставляем место для метки и процентов
        filled = int(bar_width * percentage / 100)
        
        # Метка
        stdscr.addstr(y, x, label)
        x_bar = x + len(label) + 1
        
        # Выбор цвета в зависимости от заполненности
        if percentage < 50:
            color = 10  # Зеленый
        elif percentage < 80:
            color = 11  # Желтый
        else:
            color = 12  # Красный
        
        # Рисуем заполненную часть
        if filled > 0:
            stdscr.attron(curses.color_pair(color))
            stdscr.addstr(y, x_bar, " " * filled)
            stdscr.attroff(curses.color_pair(color))
        
        # Рисуем пустую часть
        empty = bar_width - filled
        if empty > 0:
            stdscr.addstr(y, x_bar + filled, "." * empty)
        
        # Процент
        percent_str = f"{percentage:5.1f}%"
        stdscr.addstr(y, x_bar + bar_width + 1, percent_str)
    
    def draw_header(self, stdscr, height, width):
        """Отрисовка заголовка в стиле htop"""
        # Верхняя строка с названием и временем
        stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(0, 0, " " * width)
        
        title = " TelegrammBolt Monitor "
        stdscr.addstr(0, 2, title)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stdscr.addstr(0, width - len(timestamp) - 2, timestamp)
        stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
        
        # Строка с табами
        y = 1
        x_offset = 1
        
        for i, tab in enumerate(self.tabs):
            if i == self.current_tab:
                # Активная вкладка - зеленая с жирным шрифтом
                stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
                stdscr.addstr(y, x_offset, f" {tab} ")
                stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
            else:
                # Неактивная вкладка
                stdscr.attron(curses.color_pair(9))
                stdscr.addstr(y, x_offset, f" {tab} ")
                stdscr.attroff(curses.color_pair(9))
            x_offset += len(tab) + 3
        
        # Разделительная линия
        stdscr.attron(curses.color_pair(6))
        stdscr.addstr(2, 0, "=" * width)
        stdscr.attroff(curses.color_pair(6))
    
    def draw_stats_tab(self, stdscr, y_start, height, width):
        """Вкладка статистики в стиле htop"""
        stats = self.get_stats()
        
        y = y_start
        
        # Заголовок секции
        stdscr.attron(curses.color_pair(6) | curses.A_BOLD)
        stdscr.addstr(y, 2, "BOT STATUS")
        stdscr.attroff(curses.color_pair(6) | curses.A_BOLD)
        y += 1
        
        # Статус бота с цветным индикатором
        status = str(stats.get("status", "unknown"))
        stdscr.addstr(y, 4, "Status: ")
        
        if status == "running":
            stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr("RUNNING")
            stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)
        else:
            stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
            stdscr.addstr(status.upper())
            stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
        y += 2
        
        # Uptime
        uptime_sec = stats.get('uptime', 0)
        hours = uptime_sec // 3600
        minutes = (uptime_sec % 3600) // 60
        seconds = uptime_sec % 60
        
        stdscr.attron(curses.color_pair(6))
        stdscr.addstr(y, 4, f"Uptime: ")
        stdscr.attroff(curses.color_pair(6))
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        stdscr.attroff(curses.color_pair(3))
        y += 2
        
        # Секция RESOURCES с прогресс-барами
        stdscr.attron(curses.color_pair(6) | curses.A_BOLD)
        stdscr.addstr(y, 2, "RESOURCES")
        stdscr.attroff(curses.color_pair(6) | curses.A_BOLD)
        y += 1
        
        # Memory usage (предполагаем максимум 500MB)
        memory_mb = float(stats.get('memory_mb', 0))
        memory_percent = min(100, (memory_mb / 500) * 100)
        self.draw_progress_bar(stdscr, y, 4, width - 8, memory_percent, f"Memory [{memory_mb:.1f}MB]:")
        y += 2
        
        # Requests per minute (предполагаем максимум 100 req/min)
        req_per_min = float(stats.get('requests_per_minute', 0))
        req_percent = min(100, (req_per_min / 100) * 100)
        self.draw_progress_bar(stdscr, y, 4, width - 8, req_percent, f"Req/min [{req_per_min:.1f}]:")
        y += 2
        
        # Секция STATISTICS
        stdscr.attron(curses.color_pair(6) | curses.A_BOLD)
        stdscr.addstr(y, 2, "STATISTICS")
        stdscr.attroff(curses.color_pair(6) | curses.A_BOLD)
        y += 1
        
        # Статистика в две колонки
        col1_x = 4
        col2_x = width // 2
        
        stats_data = [
            ("Users (total)", stats.get('users_total', 0)),
            ("Users (active)", stats.get('users_active', 0)),
            ("DSE records", stats.get('dse_total', 0)),
            ("Total requests", stats.get('requests_total', 0)),
        ]
        
        for i, (label, value) in enumerate(stats_data):
            x_pos = col1_x if i % 2 == 0 else col2_x
            if i % 2 == 0 and i > 0:
                y += 1
            
            stdscr.attron(curses.color_pair(6))
            stdscr.addstr(y, x_pos, f"{label}:")
            stdscr.attroff(curses.color_pair(6))
            stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(y, x_pos + len(label) + 2, str(value))
            stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)
        
        y += 2
        
        # Last update
        stdscr.attron(curses.color_pair(5))
        stdscr.addstr(y, 4, "Last update: ")
        stdscr.attroff(curses.color_pair(5))
        last_update = str(stats.get('last_update') or 'N/A')[:19]
        stdscr.addstr(last_update)
    
    def draw_logs_tab(self, stdscr, y_start, height, width):
        """Вкладка логов с цветным выделением"""
        logs = self.get_logs(height - y_start - 5)
        
        y = y_start
        
        # Заголовок
        stdscr.attron(curses.color_pair(6) | curses.A_BOLD)
        stdscr.addstr(y, 2, f"RECENT LOGS ({len(logs)} entries)")
        stdscr.attroff(curses.color_pair(6) | curses.A_BOLD)
        
        stdscr.attron(curses.color_pair(5))
        stdscr.addstr(y, width - 30, "[UP/DOWN to scroll]")
        stdscr.attroff(curses.color_pair(5))
        y += 1
        
        # Разделитель
        stdscr.attron(curses.color_pair(6))
        stdscr.addstr(y, 2, "-" * (width - 4))
        stdscr.attroff(curses.color_pair(6))
        y += 1
        
        max_lines = height - y - 2
        visible_logs = logs[self.log_scroll:self.log_scroll + max_lines]
        
        for log_line in visible_logs:
            if y >= height - 2:
                break
            
            line = str(log_line or "").strip()
            if not line:
                continue
            
            # Парсим уровень лога
            color = 0
            prefix = ""
            
            if "ERROR" in line:
                color = 4  # Красный
                prefix = "[ERR]"
            elif "WARN" in line:
                color = 5  # Желтый
                prefix = "[WRN]"
            elif "SUCCESS" in line:
                color = 3  # Зеленый
                prefix = "[OK ]"
            elif "INFO" in line:
                color = 6  # Cyan
                prefix = "[INF]"
            else:
                color = 0  # Default
                prefix = "[---]"
            
            # Префикс с цветом
            if color:
                stdscr.attron(curses.color_pair(color) | curses.A_BOLD)
            stdscr.addstr(y, 3, prefix)
            if color:
                stdscr.attroff(curses.color_pair(color) | curses.A_BOLD)
            
            # Текст лога
            log_text = line[:width - 12]
            stdscr.addstr(y, 9, log_text)
            
            y += 1
        
        # Индикатор позиции скролла
        if len(logs) > max_lines:
            scroll_pos = int((self.log_scroll / max(1, len(logs) - max_lines)) * 100)
            stdscr.attron(curses.color_pair(5))
            stdscr.addstr(height - 2, width - 10, f"[{scroll_pos:3d}%]")
            stdscr.attroff(curses.color_pair(5))
    
    def draw_users_tab(self, stdscr, y_start, height, width):
        """Вкладка пользователей"""
        users = self.get_users()
        
        y = y_start
        stdscr.addstr(y, 2, "Bot users (use arrows to scroll):")
        y += 2
        
        # Заголовок таблицы
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(y, 4, f"{'ID':<15} | {'Username':<18} | {'Role':<10}")
        stdscr.attroff(curses.color_pair(1))
        y += 1
        stdscr.addstr(y, 4, "-" * 50)
        y += 1
        
        max_lines = height - y - 2
        visible_users = users[self.users_scroll:self.users_scroll + max_lines]
        
        for user_line in visible_users:
            if y >= height - 2:
                break
            stdscr.addstr(y, 4, str(user_line or "")[:width - 6])
            y += 1
    
    def draw_control_tab(self, stdscr, y_start, height, width):
        """Вкладка управления с улучшенным интерфейсом"""
        y = y_start
        
        # Заголовок
        stdscr.attron(curses.color_pair(6) | curses.A_BOLD)
        stdscr.addstr(y, 2, "CONTROL PANEL")
        stdscr.attroff(curses.color_pair(6) | curses.A_BOLD)
        y += 1
        
        stdscr.attron(curses.color_pair(6))
        stdscr.addstr(y, 2, "-" * (width - 4))
        stdscr.attroff(curses.color_pair(6))
        y += 2
        
        # Команды в рамках
        stdscr.attron(curses.color_pair(5))
        stdscr.addstr(y, 4, "Available commands:")
        stdscr.attroff(curses.color_pair(5))
        y += 2
        
        commands = [
            ("R", "Restart watcher", "Restart DSE monitoring service"),
            ("C", "Clear cache", "Clear all cached data"),
            ("S", "Save stats", "Force save current statistics"),
            ("L", "Clear logs", "Remove old log entries"),
            ("E", "Export data", "Export all data to file"),
            ("T", "Test notify", "Send test notification"),
        ]
        
        for key, name, desc in commands:
            # Клавиша
            stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(y, 6, f"[{key}]")
            stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
            
            # Название
            stdscr.attron(curses.color_pair(3))
            stdscr.addstr(y, 12, name)
            stdscr.attroff(curses.color_pair(3))
            
            # Описание
            stdscr.attron(curses.color_pair(6))
            stdscr.addstr(y, 30, f"- {desc}")
            stdscr.attroff(curses.color_pair(6))
            
            y += 1
        
        y += 2
        
        # История команд
        stdscr.attron(curses.color_pair(6) | curses.A_BOLD)
        stdscr.addstr(y, 2, "COMMAND HISTORY")
        stdscr.attroff(curses.color_pair(6) | curses.A_BOLD)
        y += 1
        
        stdscr.attron(curses.color_pair(6))
        stdscr.addstr(y, 2, "-" * (width - 4))
        stdscr.attroff(curses.color_pair(6))
        y += 1
        
        commands_data = self._read_json(self.commands_file)
        recent_commands = commands_data.get("commands", [])[-5:]
        
        if not recent_commands:
            stdscr.attron(curses.color_pair(5))
            stdscr.addstr(y, 4, "No commands executed yet")
            stdscr.attroff(curses.color_pair(5))
        else:
            for cmd in recent_commands:
                if y >= height - 2:
                    break
                
                status = cmd.get("status", "pending")
                cmd_name = str(cmd.get('command', 'unknown'))
                timestamp = str(cmd.get('timestamp', ''))[:19]
                
                # Статус с цветом
                if status == "completed":
                    stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
                    status_text = "[OK]"
                elif status == "failed":
                    stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
                    status_text = "[ERR]"
                else:
                    stdscr.attron(curses.color_pair(5) | curses.A_BOLD)
                    status_text = "[...]"
                
                stdscr.addstr(y, 4, status_text)
                stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)
                stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
                stdscr.attroff(curses.color_pair(5) | curses.A_BOLD)
                
                # Команда и время
                stdscr.attron(curses.color_pair(6))
                line = f" {cmd_name:<20} {timestamp}"
                stdscr.addstr(y, 10, line[:width - 14])
                stdscr.attroff(curses.color_pair(6))
                
                y += 1
    
    def draw_footer(self, stdscr, height, width):
        """Отрисовка подвала в стиле htop"""
        y = height - 1
        
        # Фон для футера
        stdscr.attron(curses.color_pair(8) | curses.A_BOLD)
        stdscr.addstr(y, 0, " " * width)
        
        # Команды с цветными клавишами
        commands = [
            ("F1", "Help"),
            ("F5", "Refresh"),
            ("Tab", "Next"),
            ("Q", "Quit"),
        ]
        
        x_offset = 2
        for key, desc in commands:
            # Клавиша
            stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
            stdscr.addstr(y, x_offset, key)
            stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
            
            x_offset += len(key)
            
            # Описание
            stdscr.attron(curses.color_pair(8) | curses.A_BOLD)
            stdscr.addstr(y, x_offset, f" {desc} ")
            stdscr.attroff(curses.color_pair(8) | curses.A_BOLD)
            
            x_offset += len(desc) + 3
        
        stdscr.attroff(curses.color_pair(8) | curses.A_BOLD)
    
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
        # Настройка цветов (палитра как в htop)
        curses.start_color()
        curses.use_default_colors()
        
        # Основные пары цветов
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)      # Заголовок
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)     # Активная вкладка
        curses.init_pair(3, curses.COLOR_GREEN, -1)                     # Успех / Running
        curses.init_pair(4, curses.COLOR_RED, -1)                       # Ошибка / Stopped
        curses.init_pair(5, curses.COLOR_YELLOW, -1)                    # Предупреждение
        curses.init_pair(6, curses.COLOR_CYAN, -1)                      # Информация
        curses.init_pair(7, curses.COLOR_MAGENTA, -1)                   # Специальное
        curses.init_pair(8, curses.COLOR_WHITE, curses.COLOR_BLUE)      # Футер
        curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_WHITE)     # Неактивная вкладка
        
        # Прогресс-бары
        curses.init_pair(10, curses.COLOR_GREEN, curses.COLOR_GREEN)    # Зеленый бар
        curses.init_pair(11, curses.COLOR_YELLOW, curses.COLOR_YELLOW)  # Желтый бар
        curses.init_pair(12, curses.COLOR_RED, curses.COLOR_RED)        # Красный бар
        
        # Настройка
        curses.curs_set(0)  # Скрыть курсор
        stdscr.nodelay(1)   # Неблокирующий ввод
        stdscr.timeout(100) # Таймаут 100мс
        
        while self.running:
            try:
                stdscr.clear()
                height, width = stdscr.getmaxyx()
                
                # Проверка минимального размера
                if height < 20 or width < 80:
                    stdscr.addstr(0, 0, "Terminal too small! Min: 80x20")
                    stdscr.refresh()
                    time.sleep(0.5)
                    continue
                
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
                key = stdscr.getch()
                if key != -1:
                    self.handle_input(stdscr, key)
            except curses.error:
                pass  # Игнорируем ошибки отрисовки при изменении размера терминала
            except Exception as e:
                # В случае критической ошибки - показываем и выходим
                stdscr.clear()
                stdscr.addstr(0, 0, f"Critical error: {str(e)}")
                stdscr.refresh()
                time.sleep(2)
                break
            
            time.sleep(0.1)


def main():
    """Точка входа"""
    print("=> Starting TelegrammBolt Monitor...")
    print("Press 'Q' to exit\n")
    time.sleep(1)
    
    monitor = BotMonitor()
    
    try:
        curses.wrapper(monitor.run)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"[!] Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n[OK] Monitor stopped")


if __name__ == "__main__":
    main()
