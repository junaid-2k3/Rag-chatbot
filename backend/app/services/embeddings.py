"""bge-small-en-v1.5 via ONNX Runtime. Shared by ingestion and backend so doc/query vectors match."""
import os
from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

MODEL_DIR = Path(os.environ.get("MODEL_DIR", Path(__file__).resolve().parents[3] / "models" / "bge-small"))
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
MAX_LEN = 512


class Embedder:
    def __init__(self, model_dir: Path = MODEL_DIR):
        self.tok = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
        self.tok.enable_truncation(max_length=MAX_LEN)
        self.tok.enable_padding()
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = int(os.environ.get("ORT_THREADS", "2"))
        self.sess = ort.InferenceSession(str(model_dir / "onnx" / "model.onnx"), opts, providers=["CPUExecutionProvider"])
        self.input_names = {i.name for i in self.sess.get_inputs()}

    def _embed(self, texts: list[str]) -> np.ndarray:
        enc = self.tok.encode_batch(texts)
        feeds = {
            "input_ids": np.array([e.ids for e in enc], dtype=np.int64),
            "attention_mask": np.array([e.attention_mask for e in enc], dtype=np.int64),
        }
        if "token_type_ids" in self.input_names:
            feeds["token_type_ids"] = np.zeros_like(feeds["input_ids"])
        cls = self.sess.run(None, feeds)[0][:, 0]  # bge uses the [CLS] token
        return (cls / np.linalg.norm(cls, axis=1, keepdims=True)).astype(np.float32)

    def embed_documents(self, texts: list[str], batch_size: int = 16) -> np.ndarray:
        return np.vstack([self._embed(texts[i : i + batch_size]) for i in range(0, len(texts), batch_size)])

    def embed_query(self, text: str) -> np.ndarray:
        return self._embed([QUERY_PREFIX + text])[0]
