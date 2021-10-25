import json
import logging
import os

import azure.functions as func
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials

def main(event: func.EventGridEvent, doc: func.Out[func.Document]):
    FACE_KEY = os.getenv("FaceAPIKey")
    FACE_ENDPOINT = "https://demo-mask-recognition.cognitiveservices.azure.com/"
    face_client = FaceClient(FACE_ENDPOINT, CognitiveServicesCredentials(FACE_KEY))
    
    face_image_url = "https://demostorage1245.blob.core.windows.net/face-img-upload-blob/simDevice/test.jpg?sp=r&st=2021-10-22T04:16:21Z&se=2021-10-25T12:16:21Z&spr=https&sv=2020-08-04&sr=b&sig=6Mv3j4obIPkvyWv1blD4LZ2c6ZMu2pEBuimjEaZDy%2Bc%3D"
    detected_faces = face_client.face.detect_with_url(url=face_image_url, detection_model="detection_03", return_face_attributes=["Mask"])

    if detected_faces:
        result = json.dumps({
            'id': event.id,
            'data': event.get_json(),
            'topic': event.topic,
            'subject': event.subject,
            'event_type': event.event_type,
            'mask': str(detected_faces[0].face_attributes.mask)
            })

    doc.set(func.Document.from_json(result))

    logging.info('some custom stuff. Python EventGrid trigger processed an event: %s', result)
