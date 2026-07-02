from typing import TypedDict, List, Dict, Any
from pathlib import Path
from langgraph.graph import StateGraph, END
from src.agents.planner import PlannerAgent
from src.agents.researcher import ResearchAgent
from src.agents.writer import WriterAgent
from src.agents.reader import ReadingAgent
from src.agents.gap import GapAgent
from src.agents.solution import SolutionAgent
from src.agents.experiment import ExperimentAgent
from src.agents.critic import CriticAgent
from src.schemas.paper import Paper
from src.utils.logger import get_logger
import json

logger = get_logger(__name__)


class ResearchState(TypedDict):
    topic: str
    max_papers: int
    plan: dict
    papers: List[Paper]
    paper_table_json: str
    paper_analyses: List[Dict[str, Any]]
    gap_data: Dict[str, Any]
    gap_iteration: int
    critic_feedback: Dict[str, Any]
    final_gap_json: str
    solution_data: Dict[str, Any]
    solution: str
    experiment_data: Dict[str, Any]
    experiment_design: str
    research_package: Dict[str, str]


class ResearchWorkflow:
    def __init__(self, include_full_analysis: bool = False):
        self.include_full_analysis = include_full_analysis
        self.planner = PlannerAgent()
        self.researcher = ResearchAgent()
        self.writer = WriterAgent()
        self.max_iterations = 3
        
        if include_full_analysis:
            self.reader = ReadingAgent()
            self.gap_agent = GapAgent()
            self.critic_agent = CriticAgent()
            self.solution_agent = SolutionAgent()
            self.experiment_agent = ExperimentAgent()
        
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(ResearchState)
        
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("research", self._research_node)
        
        if self.include_full_analysis:
            workflow.add_node("read", self._read_node)
            workflow.add_node("gap_analysis", self._gap_analysis_node)
            workflow.add_node("critic", self._critic_node)
            workflow.add_node("decide_loop", self._decide_loop_node)
            workflow.add_node("solution", self._solution_node)
            workflow.add_node("experiment", self._experiment_node)
            workflow.add_node("package", self._package_node)
            
            workflow.add_edge("plan", "research")
            workflow.add_edge("research", "read")
            workflow.add_edge("read", "gap_analysis")
            workflow.add_edge("gap_analysis", "critic")
            workflow.add_edge("critic", "decide_loop")
            workflow.add_edge("decide_loop", "solution")
            workflow.add_edge("solution", "experiment")
            workflow.add_edge("experiment", "package")
            workflow.add_edge("package", END)
            
            workflow.add_edge("decide_loop", "gap_analysis")
        else:
            workflow.add_node("write", self._write_node)
            
            workflow.add_edge("plan", "research")
            workflow.add_edge("research", "write")
            workflow.add_edge("write", END)
        
        workflow.set_entry_point("plan")
        
        return workflow.compile()
    
    def _plan_node(self, state: ResearchState) -> ResearchState:
        logger.info("Executing Planner node")
        plan = self.planner.plan_research(state["topic"])
        return {"plan": plan}
    
    def _research_node(self, state: ResearchState) -> ResearchState:
        logger.info("Executing Researcher node")
        keywords = state["plan"].get("keywords", [state["topic"]])
        papers = self.researcher.search_papers(keywords, state["max_papers"])
        paper_table_json = self.researcher.generate_paper_table_json(papers)
        return {"papers": papers, "paper_table_json": paper_table_json}
    
    def _read_node(self, state: ResearchState) -> ResearchState:
        logger.info("Executing Reader node")
        analyses = self.reader.analyze_papers(state["papers"])
        return {"paper_analyses": analyses, "gap_iteration": 1}
    
    def _gap_analysis_node(self, state: ResearchState) -> ResearchState:
        iteration = state.get("gap_iteration", 1)
        logger.info(f"Executing Gap Analysis node (iteration {iteration})")
        
        critic_feedback = state.get("critic_feedback", {})
        
        gap_data = self.gap_agent.identify_gaps(
            state["paper_analyses"], 
            {},
            critic_feedback=critic_feedback
        )
        
        return {"gap_data": gap_data}
    
    def _critic_node(self, state: ResearchState) -> ResearchState:
        iteration = state.get("gap_iteration", 1)
        logger.info(f"Executing Critic node (iteration {iteration})")
        
        papers_text = "\n\n".join([
            f"论文：{paper.title}\n作者：{', '.join(paper.authors)}\n摘要：{paper.abstract}"
            for paper in state["papers"]
        ])
        
        gap_analysis_str = json.dumps(state["gap_data"], ensure_ascii=False)
        
        feedback = self.critic_agent.review_gaps(
            topic=state["topic"],
            papers=papers_text,
            gap_analysis=gap_analysis_str
        )
        
        return {"critic_feedback": feedback.model_dump()}
    
    def _decide_loop_node(self, state: ResearchState) -> str:
        iteration = state.get("gap_iteration", 1)
        confidence = state.get("critic_feedback", {}).get("confidence", 0)
        
        logger.info(f"Loop decision: iteration={iteration}, confidence={confidence}")
        
        if iteration < self.max_iterations and confidence < 4:
            logger.info(f"Continuing to iteration {iteration + 1}")
            return "gap_analysis"
        else:
            logger.info("Finalizing gap analysis")
            final_gap_json = json.dumps(state["gap_data"], ensure_ascii=False, indent=2)
            state["final_gap_json"] = final_gap_json
            return "solution"
    
    def _solution_node(self, state: ResearchState) -> ResearchState:
        logger.info("Executing Solution node")
        gap_data = state["gap_data"]
        solution_data = self.solution_agent.propose_solution(
            gap_data.get("research_gaps", []),
            gap_data.get("research_questions", [])
        )
        solution = self.solution_agent.generate_solution_report(
            gap_data.get("research_gaps", []),
            gap_data.get("research_questions", [])
        )
        return {"solution_data": solution_data, "solution": solution}
    
    def _experiment_node(self, state: ResearchState) -> ResearchState:
        logger.info("Executing Experiment node")
        experiment_data = self.experiment_agent.design_experiment(state["solution_data"])
        experiment_design = self.experiment_agent.generate_experiment_report(state["solution_data"])
        return {"experiment_data": experiment_data, "experiment_design": experiment_design}
    
    def _package_node(self, state: ResearchState) -> ResearchState:
        logger.info("Executing Package node")
        
        final_gap_json = state.get("final_gap_json", json.dumps(state["gap_data"], ensure_ascii=False, indent=2))
        
        package = {
            "papers_table.json": state.get("paper_table_json", "{}"),
            "final_gap.json": final_gap_json
        }
        
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for filename, content in package.items():
            file_path = output_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Saved {filename} to {file_path}")
        
        return {"research_package": package}
    
    def _write_node(self, state: ResearchState) -> ResearchState:
        logger.info("Executing Writer node")
        report = self.writer.generate_report(state["topic"], state["papers"])
        return {"research_package": {"final_report.md": report}}
    
    def run(self, topic: str, max_papers: int = 10) -> Dict[str, str]:
        logger.info(f"Starting research workflow for topic: {topic}")
        
        initial_state = {
            "topic": topic,
            "max_papers": max_papers,
            "plan": {},
            "papers": [],
            "paper_table_json": "",
            "paper_analyses": [],
            "gap_data": {},
            "gap_iteration": 1,
            "critic_feedback": {},
            "final_gap_json": "",
            "solution_data": {},
            "solution": "",
            "experiment_data": {},
            "experiment_design": "",
            "research_package": {}
        }
        
        result = self.graph.invoke(initial_state)
        return result["research_package"]
