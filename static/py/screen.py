import time
import queue
import ctypes
import pyautogui
import threading

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint),
    ]

class ScreenWorker(threading.Thread):
    def __init__(self):
        super().__init__()
        self.commands = queue.Queue()
        self.daemon = True
        self.running = True
    
    def run(self):                    
        print("> The screen is always on!")

        while True:
            lastInputInfo = LASTINPUTINFO()
            lastInputInfo.cbSize = ctypes.sizeof(LASTINPUTINFO)

            ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo))
            millis = ctypes.windll.kernel32.GetTickCount() - lastInputInfo.dwTime

            if (millis / 1000.0) > 200:
                ctypes.windll.user32.keybd_event(0x7E, 0, 0, 0)
                ctypes.windll.user32.keybd_event(0x7E, 0, 0x0002, 0)
                
                pyautogui.click(677, 221)
                time.sleep(200)
            else:
                time.sleep(30)
            

screen = ScreenWorker()
screen.start()