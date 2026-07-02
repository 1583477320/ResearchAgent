# Research Agent - 智能研究助手

一个基于 AI 的自动化研究工具。你只需输入一个研究主题，它就能帮你搜索学术论文、分析研究现状、发现研究空白，并生成完整的研究分析报告。

## 一句话理解

**输入研究主题 -> 自动搜论文 -> 自动生成研究报告**

就像雇了一个全天候工作的研究助理，帮你完成文献调研的繁琐工作。

## 它能做什么

当你输入一个研究主题（比如"大语言模型微调"）后，系统会自动完成以下步骤：

1. **制定研究计划** - AI 分析你的主题，确定搜索关键词和检索策略
2. **搜索学术论文** - 通过学术搜索引擎查找相关论文
3. **阅读与分析** - 逐篇阅读论文，提取核心信息（解决的问题、使用的方法、实验结果等）
4. **分类整理** - 将论文按研究方向自动分类，识别研究热点
5. **发现研究空白** - 分析哪些问题是已有研究没有解决的
6. **提出解决方案** - 针对找到的研究空白，提出可能的解决思路
7. **设计实验方案** - 如���确定了研究方向，还会帮你设计具体的实验计划
8. **生成研究报告** - 最后输出一份结构完整的 Markdown 格式研究报告

整个过程全自动完成，你只需要等待即可。

## 系统架构

```
┌─────────────────────────────────────────────────┐
│                   前端界面                        │
│         Next.js + React + Tailwind CSS           │
│                                                   │
│   输入研究主题 ──► 查看论文列表 ──► 下载报告       │
└──────────────────────┬──────────────────────────┘
                       │ HTTP API
┌──────────────────────▼──────────────────────────┐
│                   后端服务                        │
│         FastAPI (Python)                         │
│                                                   │
│   接收请求 ──► 启动工作流 ──► 返回结果             │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│               AI 智能体团队                       │
│                                                   │
│  规划师 ──► 研究员 ──► 阅读者 ──► 分类专家        │
│                                          │       │
│                                         评审员 ◄──┘
│                                          │ (循环改进)
│  空白分析师 ──► 方案专家 ──► 实验设计师 ──► 撰稿人 │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│                  外部服务                         │
│                                                   │
│   学术论文搜索 (MCP 协议)                          │
│   大语言模型 (DeepSeek / Qwen / OpenAI)           │
└──────────────────────────────────────────────────┘
```

## 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- 一个大语言模型的 API Key（推荐 DeepSeek 或通义千问）

### 第一步：获取 API Key

你需要一个大语言模型的 API Key。以 DeepSeek 为例：

1. 访问 [DeepSeek 官网](https://platform.deepseek.com/) 注册账号
2. 在控制台创建一个 API Key
3. 复制这个 Key，后面会用到

### 第二步：安装后端

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate    # Mac/Linux
# 或
venv\Scripts\activate       # Windows

# 安装依赖
pip install -r requirements.txt
```

### 第三步：配置 API Key

在后端目录下创建 `.env` 文件：

```bash
# 复制示例配置文件
cp .env.example .env
# 如果没有示例文件，直接创建 .env 文件
```

编辑 `.env` 文件，填入你的 API Key：

```ini
# 使用 DeepSeek
DEEPSEEK_API_KEY=你的_api_key

# 或使用通义千问
# LLM_API_KEY=你的_api_key
# LLM_PROVIDER=qwen
```

### 第四步：启动后端

```bash
# 确保已在 backend 目录下，且虚拟环境已激活
python run.py
```

看到类似下面的输出就说明启动成功了：

```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

此时后端已经运行，你可以在浏览器打开 `http://localhost:8000` 确认。

### 第五步：启动前端

```bash
# 打开一个新的终端，进入前端目录
cd frontend

# 安装依赖（首次使用需要）
npm install

# 启动开发服务器
npm run dev
```

看到类似下面的输出就说明启动成功了：

```
✓ Ready in 2s
- Local:   http://localhost:3000
```

### 第六步：开始使用

打开浏览器访问 `http://localhost:3000`，你会看到一个搜索框。

1. 在搜索框中输入一个研究主题，例如："大语言模型"
2. 点击"开始研究"按钮
3. 等待 AI 自动完成分析（可能需要几分钟）
4. 查看生成的论文列表、研究空白分析和研究报告

## 项目结构

```
ResearchAgent/
├── backend/                    # 后端服务
│   ├── run.py                  # 启动入口
│   ├── requirements.txt        # Python 依赖
│   └── src/
│       ├── api/                # 接口层
│       │   ├── main.py         #   FastAPI 应用主文件
│       │   └── endpoints/      #   API 路由
│       ├── agents/             # AI 智能体（每个角色一个文件）
│       │   ├── planner.py      #   规划师：制定研究计划
│       │   ├── researcher.py   #   研究员：搜索论文
│       │   ├── reader.py       #   阅读者：分析论文内容
│       │   ├── classification.py # 分类专家：整理论文类别
│       │   ├── gap.py          #   空白分析师：发现研究缺口
│       │   ├── solution.py     #   方案专家：提出解决思路
│       │   ├── experiment.py   #   实验设计师：设计实验方案
│       │   ├── writer.py       #   撰稿人：生成最终报告
│       │   └── critic.py       #   评审员：审核分析质量
│       ├── workflow/           # 工作流引擎
│       │   └── research_workflow.py  # 串联所有智能体的流程
│       ├── services/           # 业务服务
│       │   ├── paper_search.py     # 学术论文搜索
│       │   └── paper_repository.py # 论文仓库管理
│       ├── schemas/            # 数据结构定义
│       └── utils/              # 工具函数
│           ├── config.py       #   配置管理
│           ├── llm_client.py   #   大模型客户端
│           ├── prompts.py      #   提示词模板
│           └── logger.py       #   日志工具
├── frontend/                   # 前端界面
│   ├── package.json            # Node.js 依赖
│   ├── app/                    # Next.js 页面
│   │   ├── page.tsx            #   主页（搜索 + 结果展示）
│   │   └── layout.tsx          #   全局布局
│   └── components/             # 可复用组件
│       ├── Header.tsx          #   顶部导航栏
│       ├── SearchInput.tsx     #   搜索输入框
│       ├── PaperTable.tsx      #   论文列表表格
│       ├── GapAnalysis.tsx     #   研究空白分析面板
│       └── FileLibrary.tsx     #   文件上传与管理
└── README.md                   # 本文件
```

## 支持的 AI 模型

系统默认使用 DeepSeek，也支持切换到其他模型：

| 模型 | 配置变量 | 说明 |
|------|---------|------|
| DeepSeek | `DEEPSEEK_API_KEY` | 默认，性价比高 |
| 通义千问 | `LLM_API_KEY` + `LLM_PROVIDER=qwen` | 阿里出品 |
| GPT | `OPENAI_API_KEY` + `LLM_PROVIDER=openai` | 需配置 base_url |

在 `.env` 文件中修改 `LLM_PROVIDER` 即可切换。

## 常见问题

**Q: 为什么启动后搜索没有反应？**

A: 请检查以下几点：
- 后端是否正常运行（访问 `http://localhost:8000` 应该能看到 API 信息）
- 前端是否正常运行（访问 `http://localhost:3000`）
- `.env` 文件中的 API Key 是否正确填写
- 网络是否能正常访问 AI 模型的 API 服务

**Q: 搜索论文时一直转圈怎么办？**

A: 这通常是因为：
- API Key 无效或余额不足
- 网络连接不稳定
- 论文数量设置太多（默认 10 篇，可以尝试减少）
- 查看后端终端的日志输出，通常会显示具体错误信息

**Q: 能分析中文论文吗？**

A: 可以。系统在搜索和分析时都会使用你输入的主题语言，中文主题会搜索中文相关论文。

**Q: 生成的报告能导出吗？**

A: 报告以 Markdown 格式保存，你可以用任何 Markdown 编辑器打开，也可以复制到 Word、Notion 等工具中使用。

**Q: 为什么有些论文打不开？**

A: 论文链接来自学术搜索引擎，部分论文可能需要通过学校或机构的数据库权限才能访问全文。

## 技术栈

- **后端**: Python 3.10+, FastAPI, LangChain, LangGraph
- **前端**: Next.js 14, React, TypeScript, Tailwind CSS
- **AI**: LangChain + OpenAI 兼容 API
- **数据库**: 本地文件系统（JSON + Markdown）
- **向量存储**: FAISS（可选）

## 许可证

本项目仅供学习和研究使用。
