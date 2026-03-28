import os
import io
import cv2
import unicodedata

from pyzbar.pyzbar import decode
from azure.core.credentials import AzureKeyCredential

class init:
    def __init__(self):
        VEND = os.getenv("VISION_ENDPOINT")
        TEND = os.getenv("TEXT_ENDPOINT")

        VKEY = os.getenv("VISION_KEY")
        TKEY = os.getenv("TEXT_KEY")

        from azure.ai.vision.imageanalysis import ImageAnalysisClient
        from azure.ai.vision.imageanalysis.models import VisualFeatures
        from azure.ai.textanalytics import TextAnalyticsClient

        self.VisualFeatures = VisualFeatures

        self.ocrClient = ImageAnalysisClient(
            endpoint=VEND,
            credential=AzureKeyCredential(VKEY)
        )

        self.textClient = TextAnalyticsClient(
            endpoint=TEND,
            credential=AzureKeyCredential(TKEY)
        )

    def extractInfo(self, path):
        with io.open(path, "rb") as img_file:
            content = img_file.read()

        result = self.ocrClient.analyze(
            image_data=content,
            visual_features=[self.VisualFeatures.READ]
        )

        text = ""
        lines = []

        if result.read is not None:
            for block in result.read.blocks:
                for line in block.lines:
                    text += " " + line.text
                    lines.append(line.text)

        def chunk_list(lst, size=5):
            for i in range(0, len(lst), size):
                yield lst[i:i + size]

        names = []
        
        for batch in chunk_list(lines, 5):
            lt = " ".join(batch)

            response = self.textClient.recognize_entities(
                documents=[lt],
                language="pt"
            )

            for doc in response:
                for ent in doc.entities:
                    # ent.category == "PersonType" or
                    if (ent.category == "Person") and ent.confidence_score >= 0.60:
                        names.append(ent.text)
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
        return [text, names]
        # return ["testee", ["Maria 123", "teste 456"]]

    def decode_qrcode(self, path):
        try:
            img = cv2.imread(str(path))
            if img is None:
                return None
            
            decoded_objects = decode(img)
            for obj in decoded_objects:
                if obj.type == 'QRCODE':
                    return obj.data.decode('utf-8')
            
            detector = cv2.QRCodeDetector()
            data, _, _ = detector.detectAndDecode(img)
            if data:
                return data
                
            return None
        except Exception as e:
            print(f"Error decoding QR code: {e}")
            return None