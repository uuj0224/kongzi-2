import json
from dotenv import load_dotenv
from .retrieval import ROOT, Retriever

if __name__ == "__main__":
    load_dotenv(ROOT / ".env")
    passages = json.loads((ROOT / "data/passages.json").read_text())
    Retriever(passages).build()
    print(f"已建立 {len(passages)} 条原文的向量索引。")
