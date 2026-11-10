"""Cosine top-k over a normalized vector matrix (dot product == cosine)."""
import json
from pathlib import Path

import numpy as np


class Index:
    def __init__(self, index_dir: Path):
        self.vectors = np.load(index_dir / "vectors.npy")
        with (index_dir / "chunks.jsonl").open() as f:
            self.chunks = [json.loads(line) for line in f]
        assert len(self.chunks) == len(self.vectors), "index files out of sync"

    def search(self, query_vec: np.ndarray, k: int = 5):
        scores = self.vectors @ query_vec
        top = np.argsort(-scores)[:k]
        return [{**self.chunks[i], "score": float(scores[i])} for i in top]
