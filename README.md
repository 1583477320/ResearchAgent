# Research Agent - 智能研究助手

一个基于 AI 的自动化研究工具。输入研究主题，自动搜索论文、分析研究现状、发现研究空白、生成研究报告。

## 一句话理解

**输入研究主题 → 自动搜论文 → 自动生成研究报告**

## 系统架构

```
前端 (Next.js :3000) ── API代理 ──► 后端 (FastAPI :8000)
                                        │
                                   AI Agent 团队
                                   (Planner → Researcher → Reader →
                                    Gap → Critic ⇄ Solution → Experiment)
                                        │
                                   记忆系统 (SQLite + FAISS)
                                   (LLM缓存 / 研究历史 / 知识库)
```

- 前后端通过 Next.js rewrites 统一到一个端口，**无 CORS 问题**
- 任何人只需一个 `http://<IP>:3000` 地址即可使用

## 快速开始

### 1. 获取 API Key

访问 [DeepSeek 平台](https://platform.deepseek.com/) 注册并创建 API Key。

### 2. 安装依赖

```bash
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
```

### 3. 配置

```bash
cd ../backend
cp .env.example .env
# 编辑 .env，填入 API Key: DEEPSEEK_API_KEY=sk-xxx
```

### 4. 启动

```bash
cd ..
bash start.sh
```

打开 `http://<服务器IP>:3000` 即可使用。

## 配置参考 (`.env`)

```ini
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_MODEL_NAME=deepseek-chat

# 记忆系统
MEMORY_ENABLED=true
LLM_CACHE_ENABLED=true

# 性能调优
MAX_CRITIC_ITERATIONS=2      # 循环评审次数 (1=快, 3=深入)
DEFAULT_MAX_PAPERS=5

# 语义搜索（可选）
# EMBEDDING_MODEL_NAME=text-embedding-3-small
```

## 记忆系统

| 能力 | 说明 |
|------|------|
| LLM 缓存 | 精确 + 语义两级缓存，节省 API 费用 |
| 研究历史 | 每次研究自动保存，可回看、删除 |
| 知识库 | FTS5 全文搜索 + FAISS 语义搜索 |
| 时间线 | 每步耗时记录，定位瓶颈 |

## API 端点

```
POST   /api/query                  提交研究主题
GET    /api/status/{id}            查询进度 (含进度消息)
GET    /api/report/{id}            获取报告
GET    /api/history                历史研究列表
GET    /api/history/{id}           研究详情 + 步骤时间线
DELETE /api/history/{id}           删除记录
GET    /api/knowledge/search?q=    知识库搜索
```

## 项目结构

```
ResearchAgent/
├── start.sh                  一键启动脚本
├── backend/
│   ├── run.py                后端入口
│   └── src/
│       ├── api/              FastAPI 路由
│       ├── agents/           8 个 AI Agent
│       ├── workflow/         LangGraph 工作流
│       ├── memory/           记忆系统 (SQLite + FAISS)
│       ├── services/         论文搜索 / 仓库
│       ├── schemas/          数据模型
│       └── utils/            配置 / LLM客户端 / 日志
└── frontend/
    ├── next.config.mjs       API 代理配置
    └── app/                  Next.js 页面 + 组件
```

## 技术栈

- **后端**: Python 3.10+, FastAPI, LangChain, LangGraph
- **前端**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **存储**: SQLite (stdlib) + FAISS (向量搜索) + FTS5 (全文搜索)
- **AI**: OpenAI 兼容 API (DeepSeek / Qwen / OpenAI)

## 许可证

仅供学习和研究使用。
