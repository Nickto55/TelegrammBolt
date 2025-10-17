# -*- coding: utf-8 -*-
"""
Windows Service для TelegrammBolt
"""
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import subprocess
import time

class TelegrammBoltService(win32serviceutil.ServiceFramework):
    _svc_name_ = "TelegrammBolt"
    _svc_display_name_ = "TelegrammBolt Telegram Bot Service"
    _svc_description_ = "Telegram Bot for DSE Management System"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_alive = True
        self.process = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False
        if self.process:
            self.process.terminate()

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()

    def main(self):
        # Определяем путь к скрипту бота
        service_dir = os.path.dirname(os.path.abspath(__file__))
        bot_script = os.path.join(service_dir, 'bot.py')
        python_exe = os.path.join(service_dir, '.venv', 'Scripts', 'python.exe')
        
        # Проверяем существование файлов
        if not os.path.exists(bot_script):
            servicemanager.LogErrorMsg(f"Bot script not found: {bot_script}")
            return
            
        if not os.path.exists(python_exe):
            servicemanager.LogErrorMsg(f"Python executable not found: {python_exe}")
            return

        while self.is_alive:
            try:
                # Запускаем бота
                servicemanager.LogInfoMsg("Starting TelegrammBolt...")
                
                self.process = subprocess.Popen(
                    [python_exe, bot_script],
                    cwd=service_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                # Ждем завершения процесса или сигнала остановки
                while self.is_alive and self.process.poll() is None:
                    time.sleep(1)
                
                if self.process.poll() is not None and self.is_alive:
                    # Процесс завершился неожиданно, перезапускаем
                    servicemanager.LogErrorMsg("Bot process crashed, restarting in 10 seconds...")
                    time.sleep(10)
                
            except Exception as e:
                servicemanager.LogErrorMsg(f"Error in service main loop: {str(e)}")
                time.sleep(30)  # Ждем перед повторной попыткой

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(TelegrammBoltService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(TelegrammBoltService)