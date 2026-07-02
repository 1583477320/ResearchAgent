from langchain.prompts import ChatPromptTemplate
from typing import Dict


PLANNER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
你是一位专业的研究规划师。你的任务是分析用户的研究主题，制定详细的研究计划。

请输出JSON格式，包含：
1. 研究主题分析
2. 中文搜索关键词
3. 英文搜索关键词
4. 检索策略
"""),
    ("human", """
研究主题：{topic}

请为上述研究主题制定研究计划。

输出格式：
{{
  "topic_analysis": "主题分析",
  "keywords_cn": ["中文关键词1", "中文关键词2", ...],
  "keywords_en": ["english keyword1", "english keyword2", ...],
  "search_strategy": "检索策略描述"
}}
""")
])


RESEARCHER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
你是一位专业的文献检索专家。你的任务是根据关键词搜索相关论文。
"""),
    ("human", """
搜索关键词：{keywords}

请搜索相关学术论文，并按以下格式输出：
{{
  "papers": [
    {{
      "title": "论文标题",
      "authors": ["作者1", "作者2"],
      "year": "年份",
      "venue": "期刊/会议",
      "abstract": "摘要",
      "url": "论文链接",
      "citations": 引用次数
    }}
  ]
}}
""")
])


READER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
你是一位专业的论文阅读专家。你的任务是深度阅读论文，提取关键信息。

请从论文中提取：
1. Problem（解决的问题）
2. Method（使用的方法）
3. Dataset（数据集）
4. Metric（评估指标）
5. Results（实验结果）
6. Limitation（局限性）
7. Contribution（贡献）
"""),
    ("human", """
论文信息：
标题：{title}
摘要：{abstract}
全文：{full_text}（如可用）

请分析这篇论文并输出：
{{
  "problem": "论文解决的核心问题",
  "method": "使用的方法和技术",
  "dataset": "使用的数据集",
  "metric": "评估指标",
  "results": {{
    "指标1": "结果1",
    "指标2": "结果2"
  }},
  "limitation": "论文的局限性",
  "contribution": "主要贡献"
}}
""")
])


CLASSIFICATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
你是一位专业的学术分类专家。你的任务是对论文进行分类，构建研究领域地图。

请输出：
1. 分类体系
2. 研究领域层次结构
3. 研究热点分析
"""),
    ("human", """
论文列表：
{papers}

请对上述论文进行分类并构建研究领域地图：
{{
  "categories": [
    {{
      "name": "类别名称",
      "description": "类别描述",
      "papers": ["论文标题1", "论文标题2"]
    }}
  ],
  "hierarchy": {{
    "level1": ["一级类别1", "一级类别2"],
    "level2": {{
      "一级类别1": ["二级类别1-1", "二级类别1-2"]
    }}
  }},
  "hot_topics": [
    {{
      "topic": "热点主题",
      "热度": 5,
      "representative_papers": ["论文标题"]
    }}
  ]
}}
""")
])


GAP_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
你是一位专业的研究空白分析专家。你的任务是分析现有研究，发现研究空白并提出研究问题。

请输出：
1. 已解决的问题
2. 研究空白
3. 研究问题
4. 研究假设
"""),
    ("human", """
论文分析结果：
{papers_analysis}

分类数据：
{classification}

请分析研究空白并提出研究问题：
{{
  "solved_problems": [
    {{
      "problem": "已解决的问题",
      "solution": "解决方案",
      "representative_work": "代表性工作"
    }}
  ],
  "research_gaps": [
    {{
      "description": "研究空白描述",
      "importance": 5,
      "feasibility": 4,
      "potential_value": "潜在价值"
    }}
  ],
  "research_questions": [
    {{
      "question": "研究问题",
      "background": "背景说明",
      "importance": 5,
      "assumptions": ["假设1", "假设2"]
    }}
  ]
}}
""")
])


SOLUTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
你是一位专业的科研解决方案专家。你的任务是针对研究空白提出创新性的解决方案。

请输出：
1. 解决思路
2. 技术方案
3. 创新点
4. 预期效果
"""),
    ("human", """
研究空白：
{research_gaps}

研究问题：
{research_questions}

请提出解决方案：
{{
  "approach": "解决思路",
  "methodology": "方法论",
  "innovation_points": ["创新点1", "创新点2"],
  "expected_results": {{
    "指标1": "预期值",
    "指标2": "预期值"
  }},
  "implementation_plan": ["步骤1", "步骤2", "步骤3"]
}}
""")
])


EXPERIMENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
你是一位专业的实验设计专家。你的任务是设计科学严谨的实验方案。

请输出：
1. 实验目标
2. 数据集选择
3. 评估指标
4. 实验步骤
5. 对比方法
"""),
    ("human", """
解决方案：
{solution}

请设计实验方案：
{{
  "objectives": ["实验目标1", "实验目标2"],
  "datasets": [
    {{
      "name": "数据集名称",
      "size": "数据规模",
      "source": "来源",
      "characteristics": ["特征1", "特征2"]
    }}
  ],
  "metrics": {{
    "指标1": "计算方式",
    "指标2": "计算方式"
  }},
  "baselines": [
    {{
      "name": "对比方法名称",
      "source": "论文引用",
      "code_url": "代码链接"
    }}
  ],
  "procedures": ["步骤1", "步骤2", "步骤3", "步骤4"],
  "expected_outcomes": ["预期结果1", "预期结果2"]
}}
""")
])


WRITER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
你是一位专业的学术报告撰写专家。你的任务是汇总所有分析结果，撰写高质量的研究报告。

请输出结构化的研究报告。
"""),
    ("human", """
研究主题：{topic}

研究空白：{gap_report}
研究问题：{research_questions}
解决方案：{solution}
实验设计：{experiment_design}

请撰写完整的研究报告，包含以下部分：
1. 研究概述
2. 研究空白分析
3. 研究问题
4. 解决方案
5. 实验设计
6. 结论与建议

输出格式：Markdown
""")
])


class AgentPrompts:
    PLANNER = PLANNER_PROMPT
    RESEARCHER = RESEARCHER_PROMPT
    READER = READER_PROMPT
    CLASSIFICATION = CLASSIFICATION_PROMPT
    GAP = GAP_PROMPT
    SOLUTION = SOLUTION_PROMPT
    EXPERIMENT = EXPERIMENT_PROMPT
    WRITER = WRITER_PROMPT
    
    _prompt_map: Dict[str, ChatPromptTemplate] = {
        "planner": PLANNER,
        "researcher": RESEARCHER,
        "reader": READER,
        "classification": CLASSIFICATION,
        "gap": GAP,
        "solution": SOLUTION,
        "experiment": EXPERIMENT,
        "writer": WRITER
    }
    
    @classmethod
    def get_prompt(cls, agent_name: str) -> ChatPromptTemplate:
        """根据 Agent 名称获取对应的提示词模板"""
        return cls._prompt_map.get(agent_name.lower())
