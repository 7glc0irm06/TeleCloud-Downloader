"""
s3_upload.py - Upload a file to the Railway Bucket (S3-compatible) and return
a public download link based on RAILWAY_PUBLIC_DOMAIN.
"""

import os
import boto3
from config import (
    AWS_ENDPOINT_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
    AWS_DEFAULT_REGION, AWS_BUCKET_NAME, RAILWAY_PUBLIC_DOMAIN, UPLOAD_VOLUME,
)


def _client():
    return boto3.client(
        "s3",
        endpoint_url=AWS_ENDPOINT_URL,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_DEFAULT_REGION,
    )


def upload_to_s3(file_path: str, chat_id: int, status_msg=None) -> str | None:
    """Upload file_path to the bucket, return a public URL or None on failure."""
    if not AWS_BUCKET_NAME:
        return None
    fname = os.path.basename(file_path)
    key = f"files/{chat_id}/{fname}"
    try:
        _client().upload_file(file_path, AWS_BUCKET_NAME, key)
    except Exception as e:
        print(f"[s3] upload failed: {e}")
        return None

    base = RAILWAY_PUBLIC_DOMAIN or ""
    if not base:
        # Fallback: serve via local volume + tiny http server (not implemented here)
        return None
    base = base if base.startswith("http") else f"https://{base}"
    return f"{base.rstrip('/')}/files/{chat_id}/{fname}"
