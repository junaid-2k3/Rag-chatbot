"""Fetch the vector index and embedding model from S3 into local dirs (Lambda /tmp).

No-op when S3_BUCKET is unset (local development). /tmp survives between invocations of a warm
container, so files that already exist are not downloaded again.
"""
from .. import config
from . import embeddings


def _assets():
    idx, model = config.INDEX_DIR, embeddings.MODEL_DIR
    return [
        ("index/vectors.npy", idx / "vectors.npy"),
        ("index/chunks.jsonl", idx / "chunks.jsonl"),
        ("index/manifest.json", idx / "manifest.json"),
        ("models/bge-small/tokenizer.json", model / "tokenizer.json"),
        ("models/bge-small/onnx/model.onnx", model / "onnx" / "model.onnx"),
    ]


def ensure_assets() -> None:
    if not config.S3_BUCKET:
        return
    import boto3  # provided by the Lambda runtime; not bundled

    s3 = boto3.client("s3")
    for key, dest in _assets():
        if dest.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        s3.download_file(config.S3_BUCKET, key, str(dest))  # writes a temp file, then renames
