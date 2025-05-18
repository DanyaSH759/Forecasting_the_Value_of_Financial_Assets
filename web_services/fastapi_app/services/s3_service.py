import boto3
import os
from core.config import settings

s3 = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    endpoint_url=settings.S3_ENDPOINT_URL
)

def download_model_from_s3(asset: str) -> str:
    model_key = f"all_models/{asset}/model.pkl"
    local_model_path = f"/tmp/{asset}_model.pkl"
    os.makedirs(os.path.dirname(local_model_path), exist_ok=True)

    try:
        s3.download_file(
            Bucket=settings.S3_BUCKET_NAME,
            Key=model_key,
            Filename=local_model_path
        )
    except Exception as e:
        raise RuntimeError(f"Ошибка при скачивании модели с S3: {e}  model_key = {model_key } local_model_path = {local_model_path}")

    return local_model_path
