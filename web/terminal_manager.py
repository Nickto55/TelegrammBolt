#!/usr/bin/env python3
"""
Web Terminal Manager
Управление веб-терминалом для удаленного доступа к машине
"""

import os
import sys
import subprocess
import threading
import logging
import queue
import platform

logger = logging.getLogger(__name__)

# Проверяем платформу
IS_WINDOWS = platform.system() == 'Windows'

if not IS_WINDOWS:
    import pty
    import select
    import termios
    import struct
    import fcntl


class TerminalSession:
    """Класс для управления сессией терминала"""
    
    def __init__(self, session_id, user_id):
        self.session_id = session_id
        self.user_id = user_id
        self.process = None
        self.fd = None
        self.running = False
        self.output_queue = queue.Queue()
        self.lock = threading.Lock()
        
    def start(self, cols=80, rows=24):
        """Запуск терминальной сессии"""
        try:
            if IS_WINDOWS:
                self._start_windows(cols, rows)
            else:
                self._start_unix(cols, rows)
            
            self.running = True
            logger.info(f"Terminal session {self.session_id} started for user {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to start terminal session: {e}")
            return False
    
    def _start_windows(self, cols, rows):
        """Запуск терминала на Windows"""
        # На Windows используем subprocess с cmd.exe или PowerShell
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        # Используем PowerShell для лучшей совместимости
        self.process = subprocess.Popen(
            ['powershell.exe', '-NoLogo', '-NoProfile'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            startupinfo=startupinfo,
            bufsize=0,
            universal_newlines=False
        )
        
        # Запускаем поток для чтения вывода
        self.read_thread = threading.Thread(target=self._read_output_windows)
        self.read_thread.daemon = True
        self.read_thread.start()
    
    def _start_unix(self, cols, rows):
        """Запуск терминала на Unix/Linux"""
        # Создаем псевдотерминал
        pid, self.fd = pty.fork()
        
        if pid == 0:
            # Дочерний процесс - запускаем shell
            shell = os.environ.get('SHELL', '/bin/bash')
            os.execvp(shell, [shell])
        else:
            # Родительский процесс
            self.process = pid
            
            # Устанавливаем размер терминала
            self.resize(cols, rows)
            
            # Устанавливаем неблокирующий режим
            flags = fcntl.fcntl(self.fd, fcntl.F_GETFL)
            fcntl.fcntl(self.fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            
            # Запускаем поток для чтения вывода
            self.read_thread = threading.Thread(target=self._read_output_unix)
            self.read_thread.daemon = True
            self.read_thread.start()
    
    def _read_output_windows(self):
        """Чтение вывода процесса на Windows"""
        while self.running and self.process and self.process.poll() is None:
            try:
                data = self.process.stdout.read(1024)
                if data:
                    self.output_queue.put(data)
            except Exception as e:
                logger.error(f"Error reading output: {e}")
                break
    
    def _read_output_unix(self):
        """Чтение вывода PTY на Unix/Linux"""
        while self.running:
            try:
                r, w, e = select.select([self.fd], [], [], 0.1)
                if r:
                    data = os.read(self.fd, 1024)
                    if data:
                        self.output_queue.put(data)
            except OSError:
                break
            except Exception as e:
                logger.error(f"Error reading output: {e}")
                break
    
    def write(self, data):
        """Отправка данных в терминал"""
        try:
            with self.lock:
                if IS_WINDOWS:
                    if self.process and self.process.poll() is None:
                        self.process.stdin.write(data.encode('utf-8'))
                        self.process.stdin.flush()
                else:
                    if self.fd:
                        os.write(self.fd, data.encode('utf-8'))
                return True
        except Exception as e:
            logger.error(f"Error writing to terminal: {e}")
            return False
    
    def read(self, timeout=0.1):
        """Чтение данных из терминала"""
        try:
            data = self.output_queue.get(timeout=timeout)
            return data
        except queue.Empty:
            return None
    
    def resize(self, cols, rows):
        """Изменение размера терминала"""
        try:
            if not IS_WINDOWS and self.fd:
                size = struct.pack('HHHH', rows, cols, 0, 0)
                fcntl.ioctl(self.fd, termios.TIOCSWINSZ, size)
                logger.debug(f"Terminal resized to {cols}x{rows}")
                return True
        except Exception as e:
            logger.error(f"Error resizing terminal: {e}")
        return False
    
    def stop(self):
        """Остановка терминальной сессии"""
        self.running = False
        
        try:
            if IS_WINDOWS:
                if self.process:
                    self.process.terminate()
                    self.process.wait(timeout=2)
            else:
                if self.fd:
                    os.close(self.fd)
                if self.process:
                    os.kill(self.process, 15)  # SIGTERM
                    os.waitpid(self.process, 0)
        except Exception as e:
            logger.error(f"Error stopping terminal: {e}")
        
        logger.info(f"Terminal session {self.session_id} stopped")


class TerminalManager:
    """Менеджер терминальных сессий"""
    
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()
    
    def create_session(self, session_id, user_id, cols=80, rows=24):
        """Создание новой терминальной сессии"""
        with self.lock:
            if session_id in self.sessions:
                logger.warning(f"Session {session_id} already exists")
                return self.sessions[session_id]
            
            session = TerminalSession(session_id, user_id)
            if session.start(cols, rows):
                self.sessions[session_id] = session
                logger.info(f"Created terminal session {session_id}")
                return session
            else:
                logger.error(f"Failed to create terminal session {session_id}")
                return None
    
    def get_session(self, session_id):
        """Получение сессии по ID"""
        return self.sessions.get(session_id)
    
    def remove_session(self, session_id):
        """Удаление сессии"""
        with self.lock:
            session = self.sessions.pop(session_id, None)
            if session:
                session.stop()
                logger.info(f"Removed terminal session {session_id}")
                return True
            return False
    
    def cleanup_inactive_sessions(self):
        """Очистка неактивных сессий"""
        with self.lock:
            inactive = []
            for session_id, session in self.sessions.items():
                if not session.running:
                    inactive.append(session_id)
            
            for session_id in inactive:
                self.remove_session(session_id)
            
            if inactive:
                logger.info(f"Cleaned up {len(inactive)} inactive sessions")


# Глобальный экземпляр менеджера
terminal_manager = TerminalManager()
