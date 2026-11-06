# 孔子问答 · 第一期

基于原典和史传的可追溯问答系统。Vue 3 + TypeScript + Element Plus / FastAPI / SQLite / BGE 中文向量检索 / DeepSeek API。

问答设定：用户以孔子弟子的身份请教，智能体以孔子的口吻引用或结合文献回答，温和启发，并联系具体困惑给出建议。角色为 AI 模拟，原文引用、史传记述和现代延伸解读分别标明；资料不足时不编造言论或经历。

## 快速启动

需要 Python 3.11+（本机验证使用 3.13）、Node.js 20.19+ 或 22.12+、建议 16GB 内存。首次安装和下载嵌入模型需要网络。

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

在 `.env` 中填写**新生成的** `DEEPSEEK_API_KEY`，不要将其提交到仓库。可设置 `DEEPSEEK_MODEL`、`DEEPSEEK_BASE_URL` 与 `EMBEDDING_MODEL`。默认使用 `deepseek-flash`，非思考模式。API 按实际用量计费。

```sh
python scripts/import_data.py
python -m backend.index
cd frontend
npm ci
npm run build
cd ..
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

打开 http://127.0.0.1:8000 。第一次建立索引会从 Hugging Face 下载 `BAAI/bge-small-zh-v1.5`；可预先下载模型，并将 `EMBEDDING_MODEL` 设置为本地目录。如 Hugging Face 连接持续失败，可选运行 `python scripts/download_model.py` 从 ModelScope 固定版本下载并校验相同模型，下载完整后自动采用本地模型。模型或知识库变更后须重新运行 `python -m backend.index`。

开发模式：后端同上，另一个终端在 `frontend` 运行 `npm run dev`，浏览器打开 http://127.0.0.1:5173 。`/api` 自动代理到 8000 端口。

没有 Key 或索引时，原文浏览、来源查看和历史记录仍可用，问答会明确提示配置问题，不生成模拟答案。索引与模型缓存准备完成后，原文浏览和本地检索不需要远程模型服务；生成答案需要联网。

## 验证

```sh
python -m pytest backend -q
cd frontend
npm run build
```

精确的本机验证版本保存在 `requirements.lock.txt`（Python 3.13 / macOS arm64）。可选浏览器验收：安装 `playwright` 后运行 `python scripts/browser_qa.py`，使用本机 Google Chrome，仅检查桌面浏览器。

测试使用明确的模型替身，不产生 API 费用；真实问答需要自行配置新密钥。接口文档：http://127.0.0.1:8000/docs 。

## 知识库

- 《论语》二十篇全文，按资料底本章次编号。
- 《史记》孔子世家、仲尼弟子列传全文，按最长约 460 字分段。
- 《礼记》学记、礼运、仲尼燕居、孔子闲居、儒行选篇全文。
- 80 条项目整理释义，明确标记为待教师复核，不冒充权威译注。
- 《孔子家语》仅作为候选下载，当前底本正文与注释混杂，暂不入库。

数据来源、固定提交号和 SHA-256 在 `data/sources.json`。来源及使用边界见 [资料来源说明](docs/资料来源说明.md)。

## 使用范围

单机单用户课设；每次提问独立检索；显式使用《书名》时先限制资料范围，再按向量相似度排序。不支持省略上下文的连续追问。引用编号有效仅证明出处存在，不代表已自动验证整段回答的真实性。一期依靠提示词说明证据不足；自动阈值拒答与效果评测属于二期。

模型 Key 只保存在后端环境；不接受前端传入服务地址或 Key。模型出错时不保存半条问答，输入采用参数化 SQL，模型文本采用 Vue 文本插值，不渲染 HTML。默认仅监听本机；不包含公网鉴权、多租户或公开部署配置。

[两期建设方案](docs/孔子问答系统_两期建设方案.md) · [一期验收与演示](docs/一期验收.md)

## 界面交付范围

仅支持桌面浏览器 Web 端，建议窗口宽度至少 1100px；不提供手机布局、App、小程序或桌面安装客户端。

## 前端维护

项目已安装 Impeccable 4.8.0，技能入口 `.agents/skills/impeccable/SKILL.md`，后续对话可继续使用。桌面交互补充检查：安装可选的 Playwright 后，运行 `python scripts/frontend_qa.py`；脚本需要本机 Chrome、已启动的服务、已就绪的模型配置以及至少一条已保存的回答，用于检查引用与复制功能。异常请求由测试拦截，不调用付费模型。

## 展览式桌面界面

当前界面采用顶部导航与历史抽屉、完整孔子读书画卷、专注问答阅读及篇章目录。示例问题只填入输入框，点击“问一问”才发送。桌面回归命令为 `python scripts/exhibition_qa.py`（旧的两个QA入口转发到该脚本）；需要已启动的服务、可用知识库配置和至少一条已有会话。异常请求由测试拦截，无新增模型费用。设计记录见 `PRODUCT.md`、`DESIGN.md` 及 `docs/展览式前端设计说明.md`。

界面评审修复回归：`python scripts/refinement_qa.py`。需要本机 Chrome、Playwright 和已启动的服务；使用隔离浏览器及模拟历史，拦截全部模型请求，不改动已保存问答。覆盖草稿保护、历史检索、原文提问准备、分页与释义折叠、回答段落、出处失败重试、停止等待及无障碍状态，截图与检查结果保存在 `artifacts/refined-*.png`、`artifacts/refinement-checks.json`。
