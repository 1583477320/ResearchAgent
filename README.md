# Research Agent

输入研究主题 → AI 自动搜索顶会论文 → 分析研究空白 → 生成完整研究报告

## Demo

![Demo](demo.gif)

## 功能

- **自动化研究流程**：输入主题，AI 自动完成文献搜索、论文分析、空白识别、方案设计
- **8 Agent 协作**：Planner → Researcher → Reader → Gap → Critic ⇄ Solution → Experiment，评审循环保证分析质量
- **顶会过滤**：搜索范围限定 NeurIPS / ICML / ICLR / CVPR / ACL / OSDI 等 20+ 顶会顶刊
- **年份限定**：自由设置搜索年份范围
- **LLM 缓存**：精确 + 语义两级缓存，重复 prompt 免 API 调用，节省 50%+ 费用
- **研究历史**：每次研究自动保存，可回看历史、查看每步耗时
- **步骤追踪**：实时显示当前执行步骤和耗时（`[3/8] read: 10.3s`）
- **报告导出**：自动生成结构化 JSON + Markdown 报告

## 安装

```bash
git clone git@github.com:1583477320/ResearchAgent.git
cd ResearchAgent

# 后端
cd backend && pip install -r requirements.txt

# 前端
cd ../frontend && npm install
```

## 运行

```bash
# 配置 API Key
cp backend/.env.example backend/.env
# 编辑 backend/.env：DEEPSEEK_API_KEY=sk-xxx

# 一键启动
bash start.sh
```

打开 `http://localhost:3000`，输入研究主题即可。

> 前端内置 API 代理，无需分别访问前后端端口。

## 配置 (`.env`)

```ini
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-xxx

# 搜索设置
SEARCH_VENUES=NeurIPS,ICML,ICLR,CVPR,ACL,OSDI,SOSP,...
DEFAULT_MAX_PAPERS=5

# 性能
MAX_CRITIC_ITERATIONS=2    # 评审循环次数 (1=快, 3=深入)
LLM_CACHE_ENABLED=true
```

## 架构

```
用户输入 → Next.js :3000 ──代理──→ FastAPI :8000
                                      │
                                 LangGraph 工作流
                                      │
                   ┌──────────────────┼──────────────────┐
              Planner          Researcher(MCP)        Reader
                   │                                    │
              GapAgent ←──→ CriticAgent (循环评审)      │
                   │                                    │
              SolutionAgent → ExperimentAgent → Package │
                                      │
                                 SQLite + FAISS
                              (历史 / 缓存 / 知识库)
```

## 截图

![主界面](<img width="1811" height="975" alt="image" src="https://github.com/user-attachments/assets/93b2b931-3166-4400-bd00-2aeaeb764c6c" />
)

## Roadmap

- [x] LLM 响应缓存
- [x] 研究历史 + 步骤时间线
- [x] 顶会/顶刊过滤
- [x] 年份范围限定
- [x] 前端设置面板

## 技术栈

Python 3.10+, FastAPI, LangChain, LangGraph, Next.js 14, React 18, TypeScript, Tailwind CSS, SQLite, FAISS

## 许可证

MIT
