import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import config  # noqa: E402
from app.services import embeddings, storage  # noqa: E402


def test_noop_without_bucket(monkeypatch):
    monkeypatch.setattr(config, "S3_BUCKET", "")
    monkeypatch.delitem(sys.modules, "boto3", raising=False)
    storage.ensure_assets()
    assert "boto3" not in sys.modules  # local dev never needs boto3


def test_downloads_missing_files_once(monkeypatch, tmp_path):
    calls = []

    class FakeS3:
        def download_file(self, bucket, key, dest):
            calls.append((bucket, key))
            Path(dest).write_bytes(b"x")

    monkeypatch.setitem(sys.modules, "boto3", types.SimpleNamespace(client=lambda name: FakeS3()))
    monkeypatch.setattr(config, "S3_BUCKET", "bkt")
    monkeypatch.setattr(config, "INDEX_DIR", tmp_path / "index")
    monkeypatch.setattr(embeddings, "MODEL_DIR", tmp_path / "model")

    storage.ensure_assets()
    assert len(calls) == 5 and all(b == "bkt" for b, _ in calls)
    assert (tmp_path / "model" / "onnx" / "model.onnx").exists()
    assert (tmp_path / "index" / "vectors.npy").exists()

    calls.clear()
    storage.ensure_assets()  # warm container: nothing re-downloaded
    assert calls == []
