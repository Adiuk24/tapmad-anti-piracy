from __future__ import annotations

import json
import os
from typing import Any
from pathlib import Path

from .config import settings


def _make_client(endpoint_url: str | None):
    """Create S3 client with fallback to local storage"""
    try:
        import boto3
        from botocore.config import Config
        
        return boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )
    except ImportError:
        print("Warning: boto3 not available, using local storage fallback")
        return None


def get_s3():
    """Get S3 client or None if not available"""
    return _make_client(settings.s3_endpoint)


def put_json(key: str, data: dict[str, Any]) -> None:
    """Store JSON data to S3 or local filesystem"""
    try:
        s3 = get_s3()
        if s3:
            s3.put_object(Bucket=settings.s3_bucket, Key=key, Body=json.dumps(data).encode("utf-8"))
            print(f"✅ Stored to S3: {key}")
        else:
            # Fallback to local storage
            _store_local_json(key, data)
    except Exception as e:
        print(f"Warning: S3 storage failed, using local fallback: {e}")
        _store_local_json(key, data)


def put_bytes(key: str, data: bytes) -> None:
    """Store binary data to S3 or local filesystem"""
    try:
        s3 = get_s3()
        if s3:
            s3.put_object(Bucket=settings.s3_bucket, Key=key, Body=data)
            print(f"✅ Stored to S3: {key}")
        else:
            # Fallback to local storage
            _store_local_bytes(key, data)
    except Exception as e:
        print(f"Warning: S3 storage failed, using local fallback: {e}")
        _store_local_bytes(key, data)


def presign_get_url(key: str, expires_seconds: int = 300) -> str:
    """Generate presigned URL or local file path"""
    try:
        s3 = get_s3()
        if s3:
            return s3.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": settings.s3_bucket, "Key": key},
                ExpiresIn=expires_seconds,
            )
        else:
            # Return local file path
            local_path = _get_local_path(key)
            return f"file://{local_path}"
    except Exception as e:
        print(f"Warning: S3 presigned URL failed, using local path: {e}")
        local_path = _get_local_path(key)
        return f"file://{local_path}"


def _store_local_json(key: str, data: dict[str, Any]) -> None:
    """Store JSON data to local filesystem"""
    local_path = _get_local_path(key)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(local_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Stored locally: {local_path}")


def _store_local_bytes(key: str, data: bytes) -> None:
    """Store binary data to local filesystem"""
    local_path = _get_local_path(key)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(local_path, 'wb') as f:
        f.write(data)
    
    print(f"✅ Stored locally: {local_path}")


def _get_local_path(key: str) -> Path:
    """Get local file path for a given S3 key"""
    # Create local storage directory
    local_storage = Path("local_storage")
    local_storage.mkdir(exist_ok=True)
    
    # Convert S3 key to local path
    local_path = local_storage / key.replace("/", "_")
    return local_path


def list_objects(prefix: str = "") -> list[dict[str, Any]]:
    """List objects in S3 or local storage"""
    try:
        s3 = get_s3()
        if s3:
            response = s3.list_objects_v2(Bucket=settings.s3_bucket, Prefix=prefix)
            return response.get('Contents', [])
        else:
            # List local files
            return _list_local_objects(prefix)
    except Exception as e:
        print(f"Warning: S3 listing failed, using local fallback: {e}")
        return _list_local_objects(prefix)


def _list_local_objects(prefix: str = "") -> list[dict[str, Any]]:
    """List objects in local storage"""
    local_storage = Path("local_storage")
    if not local_storage.exists():
        return []
    
    objects = []
    for file_path in local_storage.rglob("*"):
        if file_path.is_file():
            key = str(file_path.relative_to(local_storage)).replace("_", "/")
            if prefix == "" or key.startswith(prefix):
                objects.append({
                    'Key': key,
                    'Size': file_path.stat().st_size,
                    'LastModified': file_path.stat().st_mtime
                })
    
    return objects


def delete_object(key: str) -> bool:
    """Delete object from S3 or local storage"""
    try:
        s3 = get_s3()
        if s3:
            s3.delete_object(Bucket=settings.s3_bucket, Key=key)
            print(f"✅ Deleted from S3: {key}")
            return True
        else:
            # Delete local file
            return _delete_local_object(key)
    except Exception as e:
        print(f"Warning: S3 deletion failed, trying local: {e}")
        return _delete_local_object(key)


def _delete_local_object(key: str) -> bool:
    """Delete object from local storage"""
    try:
        local_path = _get_local_path(key)
        if local_path.exists():
            local_path.unlink()
            print(f"✅ Deleted locally: {local_path}")
            return True
        return False
    except Exception as e:
        print(f"Error deleting local file: {e}")
        return False


