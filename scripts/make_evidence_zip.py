#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import boto3


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True, help="Evidence key/prefix in S3 bucket")
    parser.add_argument("--output", required=True, help="Path to output zip")
    args = parser.parse_args()

    s3_endpoint = os.getenv("S3_ENDPOINT", "http://minio:9000")
    s3_key = os.getenv("S3_ACCESS_KEY", "tapmad")
    s3_secret = os.getenv("S3_SECRET_KEY", "tapmadsecret")
    s3_bucket = os.getenv("S3_BUCKET", "evidence")

    s3 = boto3.client(
        "s3",
        endpoint_url=s3_endpoint,
        aws_access_key_id=s3_key,
        aws_secret_access_key=s3_secret,
        region_name=os.getenv("S3_REGION", "us-east-1"),
    )

    prefix = args.key.rstrip("/") + "/"
    paginator = s3.get_paginator("list_objects_v2")
    to_download: list[str] = []
    for page in paginator.paginate(Bucket=s3_bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            to_download.append(obj["Key"])

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(out_path, "w", ZIP_DEFLATED) as zf:
        for key in to_download:
            body = s3.get_object(Bucket=s3_bucket, Key=key)["Body"].read()
            arcname = key[len(prefix) :]
            zf.writestr(arcname, body)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()


