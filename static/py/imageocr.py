import os
import io
import unicodedata

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

    def extractInfo(self, path):
    #     with io.open(path, "rb") as img_file:
    #         content = img_file.read()

    #     result = self.ocrClient.analyze(
    #         image_data=content,
    #         visual_features=[self.VisualFeatures.READ]
    #     )

    #     text = ""
    #     lines = []

    #     if result.read is not None:
    #         for block in result.read.blocks:
    #             for line in block.lines:
    #                 text += " " + line.text
    #                 lines.append(line.text)

    #     def chunk_list(lst, size=5):
    #         for i in range(0, len(lst), size):
    #             yield lst[i:i + size]

    #     names = []

    #     for batch in chunk_list(lines, 5):
    #         lt = " ".join(batch)

    #         response = self.textClient.recognize_entities(
    #             documents=[lt],
    #             language="pt"
    #         )

    #         for doc in response:
    #             for ent in doc.entities:
    #                 # ent.category == "PersonType" or
    #                 if (ent.category == "Person") and ent.confidence_score >= 0.65:
    #                     names.append(ent.text)
    #     text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    #     return [text, names]
        return ["testee", ["Maria 123", "Jao foda"]]