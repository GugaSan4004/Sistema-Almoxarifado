import os, re

import io
import datetime
from pdf2image import convert_from_path

from azure.core.credentials import AzureKeyCredential

class init:
    def __init__(self):
        VEND = os.environ["VISION_ENDPOINT"]
        TEND = os.environ["TEXT_ENDPOINT"]

        VKEY = os.environ["VISION_KEY"]
        TKEY = os.environ["TEXT_KEY"]

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

    def load_image(self, img_path: str):
        if img_path.lower().endswith(".pdf"):
            pages = convert_from_path(img_path, dpi=200)
            temp_img = img_path.replace(".pdf", "_page1.jpg")
            pages[0].save(temp_img, "JPEG")
            return temp_img

        return img_path

    def extractInfo(self, path):
        path = self.load_image(path)

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
                    if (ent.category == "Person") and ent.confidence_score >= 0.65:
                        names.append(ent.text)

        return [text, names]