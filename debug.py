import subprocess
import time
from pathlib import Path
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

SERVER_SCRIPT = Path.cwd() / "server.py"
TAILWIND_CMD = "npx @tailwindcss/cli -i ./src/base.css -o ./static/css/main.css --watch"

class ChangeHandler(FileSystemEventHandler):
    def __init__(self, restart_func):
        self.restart_func = restart_func

    def on_modified(self, event):
        print(event.src_path)
        
        if (event.src_path.endswith(".py") or "tabs" in event.src_path) and "debug.py" not in event.src_path:
            print(f"\n[SISTEMA] Alteração detectada em: {event.src_path}. Reiniciando servidor...")
            self.restart_func()

class DevManager:
    def __init__(self):
        self.server_process = None
        self.tailwind_process = None

    def start_tailwind(self):
        print("[TAILWIND] Iniciando monitoramento de CSS...")
        self.tailwind_process = subprocess.Popen(TAILWIND_CMD, shell=True)

    def start_server(self):
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
        
        print("[PYTHON] Iniciando server.py...")
        self.server_process = subprocess.Popen(["python", SERVER_SCRIPT])

    def run(self):
        self.start_tailwind()
        
        self.start_server()

        path = os.path.dirname(SERVER_SCRIPT)
        event_handler = ChangeHandler(self.start_server)
        observer = Observer()
        observer.schedule(event_handler, path, recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[ENCERRANDO] Finalizando processos...")
            observer.stop()
            self.server_process.terminate()
            self.tailwind_process.terminate()
        
        observer.join()

if __name__ == "__main__":
    manager = DevManager()
    manager.run()