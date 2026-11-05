import json
from pathlib import Path
import numpy as np
import pytest
from fastapi.testclient import TestClient
from backend import main
from backend.retrieval import Retriever


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB", tmp_path / "test.db")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-placeholder")
    with TestClient(main.app) as client:
        yield client


def stub(client, monkeypatch, ids=None, answer=None, insufficient=False):
    p = main.app.state.passages[0]
    monkeypatch.setattr(main.app.state.retriever, "search", lambda question: [dict(p, score=0.8)])
    async def generate(question, evidence):
        return main.Generated(answer=answer or "学习需要反复实践。", citation_ids=[p["id"]] if ids is None else ids, insufficient=insufficient), {"model": "test", "input_tokens": 1, "output_tokens": 1}
    monkeypatch.setattr(main, "generate", generate)
    return p


def test_catalog_original_and_pagination(client):
    catalog = client.get("/api/catalog").json()
    assert {x["name"] for x in catalog} == {"论语", "史记", "礼记"}
    assert len(next(x for x in catalog if x["name"] == "论语")["chapters"]) == 20
    item = client.get("/api/passages/ly-01-001").json()
    assert "学而时习之" in item["text"]
    assert len(client.get("/api/passages?page_size=2").json()["items"]) == 2
    assert client.get("/api/passages?page=0").status_code == 422
    assert client.get("/api/passages/missing").status_code == 404
    assert client.get("/api/passages?q=學而時習").json()["total"] > 0


def test_conversation_roundtrip(client, monkeypatch):
    p = stub(client, monkeypatch)
    response = client.post("/api/chat", json={"question": "如何学习？"})
    assert response.status_code == 200
    data = response.json()
    assert data["citations"][0]["text"] == p["text"]
    cid = data["conversation_id"]
    assert client.post("/api/chat", json={"question": "如何交友？", "conversation_id": cid}).status_code == 200
    assert len(client.get("/api/conversations/"+cid).json()["messages"]) == 2
    history = client.get("/api/conversations").json()
    assert len(history) == 1
    assert history[0]["message_count"] == 2
    assert history[0]["full_title"] == "如何学习？"
    assert history[0]["updated_at"]
    assert "学习需要反复实践" in history[0]["preview"]
    assert "last_response" not in history[0]


@pytest.mark.parametrize("ids,answer", [(["fake"], "杜撰的回答"), ([], "没有引用"), (["ly-01-001"], "杜撰出处 [fake]")])
def test_invalid_citations_suppress_answer(client, monkeypatch, ids, answer):
    stub(client, monkeypatch, ids=ids, answer=answer)
    result = client.post("/api/chat", json={"question": "如何学习？"}).json()
    assert result["status"] == "citation_warning"
    assert result["citations"] == []
    assert answer not in result["answer"]
    assert result["candidates"]


def test_insufficient_and_bad_inputs(client, monkeypatch):
    stub(client, monkeypatch, ids=[], answer="当前资料不足。", insufficient=True)
    assert client.post("/api/chat", json={"question": "孔子会写 Python 吗？"}).json()["status"] == "insufficient"
    for q in ["", "   ", "a"*1201]:
        assert client.post("/api/chat", json={"question": q}).status_code == 422
    assert client.post("/api/chat", json={"question": "你好", "conversation_id": "missing"}).status_code == 404


def test_missing_key_and_retrieval_failure_do_not_save(client, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY")
    assert client.post("/api/chat", json={"question": "你好"}).status_code == 503
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-placeholder")
    def fail(q): raise RuntimeError("private path")
    monkeypatch.setattr(main.app.state.retriever, "search", fail)
    response = client.post("/api/chat", json={"question": "你好"})
    assert response.status_code == 503
    assert "private path" not in response.text
    assert client.get("/api/conversations").json() == []


def test_dense_ranking_and_stale_index(tmp_path):
    passages = [{"id":"a","text":"甲"},{"id":"b","text":"乙"}]
    retriever = Retriever(passages, tmp_path/"index.npz")
    class Model:
        def encode(self, values, **kwargs): return np.array([[1.,0.]])
    retriever.model = Model()
    np.savez_compressed(retriever.path, vectors=np.array([[0.,1.],[1.,0.]]), fingerprint=np.array(retriever.fingerprint))
    assert retriever.search("问题")[0]["id"] == "b"
    stale = Retriever(passages + [{"id":"c","text":"丙"}], retriever.path)
    with pytest.raises(RuntimeError, match="变更"):
        stale.search("问题")


def test_corpus_integrity():
    rows = json.loads((main.ROOT / "data/passages.json").read_text())
    assert len({p["id"] for p in rows}) == len(rows)
    assert len([p for p in rows if p["note"]]) >= 80
    assert all(p["source_commit"] in p["source_url"] for p in rows)
    assert any("孔子生鲁昌平乡陬邑" in p["text"] for p in rows if p["book"] == "史记")
    assert any("教学相长" in p["text"] for p in rows if p["book"] == "礼记")


@pytest.mark.parametrize("code", [401, 402, 429, 500])
def test_provider_status_errors_are_safe(client, monkeypatch, code):
    import httpx
    from openai import APIStatusError
    stub(client, monkeypatch)
    async def fail(*args):
        response = httpx.Response(code, request=httpx.Request("POST", "https://example.invalid"))
        raise APIStatusError("sensitive-provider-detail", response=response, body=None)
    monkeypatch.setattr(main, "generate", fail)
    response = client.post("/api/chat", json={"question":"你好"})
    assert response.status_code in (502,503)
    assert "sensitive-provider-detail" not in response.text
    assert client.get("/api/conversations").json() == []


def test_timeout_and_malformed_response(client, monkeypatch):
    from openai import APITimeoutError
    import httpx
    stub(client, monkeypatch)
    async def timeout(*args):
        raise APITimeoutError(request=httpx.Request("POST", "https://example.invalid"))
    monkeypatch.setattr(main, "generate", timeout)
    assert client.post("/api/chat", json={"question":"你好"}).status_code == 504
    async def malformed(*args):
        main.Generated.model_validate_json("not json")
    monkeypatch.setattr(main, "generate", malformed)
    assert client.post("/api/chat", json={"question":"你好"}).status_code == 502
    assert client.get("/api/conversations").json() == []


def test_explicit_book_scope_keeps_dense_scores(tmp_path):
    passages=[{"id":"a","text":"甲","book":"论语"},{"id":"b","text":"乙","book":"礼记"}]
    retriever=Retriever(passages,tmp_path/"index.npz")
    class Model:
        def encode(self, *args, **kwargs): return np.array([[1.,0.]])
    retriever.model=Model()
    retriever.vectors=np.array([[1.,0.],[0.,1.]])
    assert retriever.search("请解释《礼记》")[0]["id"] == "b"
    assert retriever.search("一般问题")[0]["id"] == "a"


def test_real_sdk_request_contract_without_network(client, monkeypatch):
    import asyncio
    import httpx
    real_client = main.AsyncOpenAI
    passage = main.app.state.passages[0]
    def handler(request):
        body = json.loads(request.content)
        assert body["response_format"] == {"type":"json_object"}
        assert body["thinking"]["type"] == "disabled"
        evidence = json.loads(body["messages"][1]["content"])["evidence"]
        assert evidence[0]["text"] == passage["text"]
        content = json.dumps({"answer":"应按时温习与实践。", "citation_ids":[passage["id"]], "insufficient":False})
        return httpx.Response(200, json={"id":"test-completion","object":"chat.completion","created":0,"model":"test-fixed-model","choices":[{"index":0,"message":{"role":"assistant","content":content},"finish_reason":"stop"}],"usage":{"prompt_tokens":20,"completion_tokens":10,"total_tokens":30}})
    def factory(**kwargs):
        return real_client(**kwargs, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(main, "AsyncOpenAI", factory)
    result, usage = asyncio.run(main.generate("如何学习？", [passage]))
    assert result.citation_ids == [passage["id"]]
    assert usage["input_tokens"] == 20
    assert usage["model"] == "test-fixed-model"
