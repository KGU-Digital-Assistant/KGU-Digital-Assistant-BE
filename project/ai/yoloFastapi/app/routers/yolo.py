# For API operations and standards
from fastapi import APIRouter, Response, status, HTTPException, Depends
import urllib3
# Our detector objects
from detectors import yolov8
# For encoding images
import cv2
# For response schemas
from schemas.yolo import ImageAnalysisResponse
# Gcp
from google.cloud import storage
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Nutritions

# A new router object that we can add endpoints to.
# Note that the prefix is /yolo, so all endpoints from
# here on will be relative to /yolo
router = APIRouter(tags=["Image Upload and analysis"], prefix="/yolo")

# A cache of annotated images. Note that this would typically
# be some sort of persistent storage (think maybe postgres + S3)
# but for simplicity, we can keep things in memory
images = []

bucket_name = 'my-project-1497313167705.appspot.com'    # 서비스 계정 생성한 bucket 이름 입력
destination_blob_name = 'test'    # 업로드할 파일을 GCP에 저장할 때의 이름

storage_client = storage.Client(project="my-project-1497313167705")
bucket = storage_client.bucket(bucket_name)
blob = bucket.blob(destination_blob_name)

@router.post("/",
             status_code=status.HTTP_201_CREATED,
             responses={
                 201: {"description": "Successfully Analyzed Image."}
             },
             response_model=ImageAnalysisResponse,
             )
async def yolo_image_upload(url: str, db: Session = Depends(get_db)) -> ImageAnalysisResponse:
    http = urllib3.PoolManager()
    contents = http.request('GET', url, preload_content=False).read()
    dt = yolov8.YoloV8ImageObjectDetection(chunked=contents)
    frame, labels = await dt()
    print(labels)
    #query = db.query(Nutritions).filter(Nutritions.id == int(list(labels)[0]))
    #nuts = query.all()
    #data = [{'id': nut.id, 'name': nut.name, 'kcal': nut.kcal} for nut in nuts]
    data = [{'id': '1234', 'name': 'dish', 'kcal': '123'}]
    success, encoded_image = cv2.imencode(".png", frame)
    if success:
        # 인코딩된 바이트 배열을 파일로 저장
        with open('encoded_image.jpg', 'wb') as f:
            f.write(encoded_image)
    blob.upload_from_filename('encoded_image.jpg')
    images.append(encoded_image)
    return ImageAnalysisResponse(id=len(images), labels=labels, name=data[0]['name'], kcal=data[0]['kcal'])

@router.get(
    "/{image_id}",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"content": {"image/png": {}}},
        404: {"description": "Image ID Not Found."}
    },
    response_class=Response,
)
async def yolo_image_download(image_id: int) -> Response:
    """Takes an image id as a path param and returns that encoded
    image from the images array

    Arguments:
        image_id (int): The image ID to download

    Returns:
        response (Response): The encoded image in PNG format

    Examlple cURL:
        curl -X 'GET' \
            'http://localhost/yolo/1' \
            -H 'accept: image/png'

    Example Return: A Binary Image
    """
    try:
        return Response(content=images[image_id - 1].tobytes(), media_type="image/png")
    except IndexError:
        raise HTTPException(status_code=404, detail="Image not found")