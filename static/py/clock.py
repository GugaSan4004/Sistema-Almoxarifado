import os
import sys
import time
import queue
import ctypes
import datetime
import threading
import subprocess

class clock(threading.Thread):
    def __init__(self):
        super().__init__()
        self.commands = queue.Queue()
        self.daemon = True
        self.running = True
        self.executed = False
        
        print("> Controle de Higiênico - clock on!")

    def run(self):
        while True:
            now = datetime.datetime.now()

            weekdays = {
                "0": "Segunda",
                "1": "Terça",
                "2": "Quarta",
                "3": "Quinta",
                "4": "Sexta",
                "5": "Sabado",
                "6": "Domingo"
            }

            print(f"\n>> {weekdays[str(now.weekday())]} - {now.hour:02d}:{now.minute:02d}")

            if (now.weekday() == 2 and now.hour >= 6) and not self.executed:
                self.executed = True
                
                ctypes.windll.user32.ShowWindow(
                    ctypes.windll.user32.GetForegroundWindow(), 6
                )
                ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)
                ctypes.windll.user32.keybd_event(0x44, 0, 0, 0)
                ctypes.windll.user32.keybd_event(0x44, 0, 2, 0)
                ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)

                script = r"\\192.168.7.252\dados\OPERACOES\13-ALMOXARIFADO\1 - Controle de Higienicos\higienicos.py"

                subprocess.Popen([
                    sys.executable,
                    script,
                    "1"
                ], cwd=os.path.dirname(script))


            if now.weekday() != 2:
                self.executed = False

            time.sleep(60 * 25)

control = clock()
control.start()