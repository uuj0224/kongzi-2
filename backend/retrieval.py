"""Phase-one dense retrieval. No silent lexical fallback."""
import hashlib
import json
import os
import re
import threading
from pathlib import Path
import numpy as np
from opencc import OpenCC

ROOT = Path(__file__).resolve().parents[1]
NORMALIZER = OpenCC("t2s")
LOCK = threading.Lock()


def normalize(text):
    return NORMALIZER.convert(text).replace("爲", "为").strip()


class Retriever:
    def __init__(self, passages, index_path=None):
        self.passages = passages
        self.path = Path(index_path or ROOT / "data/index.npz")
        local = ROOT / "data/models/bge-small-zh-v1.5"
        self.model_name = os.getenv("EMBEDDING_MODEL") or (str(local) if (local / "download_manifest.json").exists() else "BAAI/bge-small-zh-v1.5")
        self.fingerprint = hashlib.sha256(json.dumps([self.model_name, passages], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        self.model = None
        self.vectors = None

    def load_model(self, local_only=False):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name, device="cpu", local_files_only=local_only)
        return self.model

    def build(self):
        texts = [normalize(p["text"] + " " + p.get("note", "")) for p in self.passages]
        vectors = self.load_model().encode(texts, normalize_embeddings=True, show_progress_bar=True)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(self.path, vectors=vectors, fingerprint=np.array(self.fingerprint))
        self.vectors = vectors

    def search(self, question, limit=5):
        with LOCK:
            if self.vectors is None:
                if not self.path.exists():
                    raise RuntimeError("检索索引尚未建立，请运行 python -m backend.index。")
                with np.load(self.path, allow_pickle=False) as cached:
                    if str(cached["fingerprint"]) != self.fingerprint:
                        raise RuntimeError("知识库或嵌入模型已变更，请重建检索索引。")
                    self.vectors = cached["vectors"].copy()
                if self.vectors.ndim != 2 or self.vectors.shape[0] != len(self.passages):
                    raise RuntimeError("检索索引损坏，请重建索引。")
            vector = self.load_model(local_only=True).encode(["为这个句子生成表示以用于检索相关文章：" + normalize(question)], normalize_embeddings=True)[0]
            scores = self.vectors @ vector
            # Respect an explicit book title without changing dense scoring.
            titles = re.findall(r"《([^》]+)》", normalize(question))
            scoped_books = {p.get("book") for p in self.passages if any(t.split("·")[0] == normalize(p.get("book", "")) for t in titles)}
            candidates = np.array([i for i,p in enumerate(self.passages) if not scoped_books or p.get("book") in scoped_books], dtype=int)
            order = candidates[np.argsort(-scores[candidates], kind="stable")[:limit]]
            return [dict(self.passages[int(i)], score=round(float(scores[i]), 4)) for i in order]
