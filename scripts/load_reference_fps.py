#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import psycopg


def compute_audio_fp(path: Path) -> str:
    result = subprocess.run(["fpcalc", "-json", str(path)], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"fpcalc failed: {result.stderr}")
    data = json.loads(result.stdout)
    return data.get("fingerprint", "")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True, help="Directory with official clips")
    parser.add_argument("--content-id", help="Override content id for all")
    args = parser.parse_args()

    pg_host = os.getenv("PGHOST", "postgres")
    pg_port = int(os.getenv("PGPORT", "5432"))
    pg_db = os.getenv("PGDATABASE", "antipiracy")
    pg_user = os.getenv("PGUSER", "postgres")
    pg_pass = os.getenv("PGPASSWORD", "postgres")

    source_dir = Path(args.path)
    if not source_dir.exists():
        print(f"Directory not found: {source_dir}", file=sys.stderr)
        sys.exit(1)

    with psycopg.connect(
        host=pg_host, port=pg_port, dbname=pg_db, user=pg_user, password=pg_pass
    ) as conn:
        with conn.cursor() as cur:
            for file in source_dir.iterdir():
                if not file.is_file():
                    continue
                cid = args.content_id or file.stem
                try:
                    audio_fp = compute_audio_fp(file)
                except Exception as e:  # noqa: BLE001
                    print(f"Skipping {file}: {e}", file=sys.stderr)
                    continue

                cur.execute(
                    """
                    INSERT INTO reference_fingerprints(content_id, kind, hash)
                    VALUES (%s, 'audio', %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (cid, audio_fp),
                )
            conn.commit()
    print("Loaded reference audio fingerprints.")


if __name__ == "__main__":
    main()


