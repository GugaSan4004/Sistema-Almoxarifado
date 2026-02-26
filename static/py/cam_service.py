import os
import cv2
import time
import queue
import threading

from datetime import datetime


class CameraWorker(threading.Thread):
    def __init__(self):
        super().__init__()
        self.commands = queue.Queue()
        self.daemon = True
        self.running = True

    def run(self):
        print("> Initializing camera...")
        cam = cv2.VideoCapture(0)

        for _ in range(10):
            cam.read()
            time.sleep(0.1)

        print("> The camera is ready!")

        while self.running:
            try:
                comando = self.commands.get(timeout=0.1)
            except queue.Empty:
                continue

            if comando["action"] == "capture":
                code = comando["code"]
                result_queue = comando["ret"]

                ret, frame = cam.read()

                if not ret:
                    result_queue.put({"status": "ERRO"})
                    continue

                now = datetime.now()
                month_num = now.strftime("%m")
                months = {
                    "01": "jan", "02": "fev", "03": "mar", "04": "abr", "05": "mai", "06": "jun",
                    "07": "jul", "08": "ago", "09": "set", "10": "out", "11": "nov", "12": "dez"
                }

                main_folder = r"X:\OPERACOES\13-ALMOXARIFADO\0 - Sistema Almox\pictures\loans"
                year = now.strftime("%Y")
                month_name = months[month_num]

                final_folder = os.path.join(
                    main_folder, year, f"{month_num}_{month_name}")
                os.makedirs(final_folder, exist_ok=True)

                photo_path = os.path.join(final_folder, f"{code}.jpg")

                cv2.imwrite(photo_path, frame)

                result_queue.put({
                    "status": "OK",
                    "day": now.strftime("%d"),
                    "month": f"{month_num}_{month_name}",
                    "year": year,
                    "time": datetime.now().strftime("%H-%M")
                })

    def capture(self, code):
        """Envia comando e espera retorno."""
        ret = queue.Queue()
        self.commands.put({"action": "capture", "code": code, "ret": ret})

        try:
            return ret.get(timeout=5)
        except queue.Empty:
            return {"status": "ERRO", "msg": "Timeout da câmera"}


camera = CameraWorker()
camera.start()
