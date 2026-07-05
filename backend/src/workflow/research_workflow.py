from typing import TypedDict, List, Dict, Any
from pathlib import Path
from langgraph.graph import StateGraph, END
from src.agents.planner import PlannerAgent
from src.agents.researcher import ResearchAgent
from src.agents.reader import ReadingAgent
from src.agents.gap import GapAgent
from src.agents.critic import CriticAgent
from src.agents.solution import SolutionAgent
from src.agents.experiment import ExperimentAgent
from src.schemas.paper import Paper
from src.utils.logger import get_logger
from src.utils.config import settings
import json
import time
from uuid import uuid4

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
    _session_id: str
    _venues: List[str]
    _year: str
    _next: str  # internal routing key


class ResearchWorkflow:

    def __init__(self, memory_system=None):
        self.memory = memory_system
        self.max_iterations = settings.max_critic_iterations

        cached_llm = None
        if self.memory and self.memory._enabled:
            try:
                cached_llm = self.memory.create_cached_llm()
            except Exception:
                logger.warning("Failed to create cached LLM — falling back to uncached.")

        self.planner = PlannerAgent(cached_llm=cached_llm)
        self.researcher = ResearchAgent()
        self.reader = ReadingAgent(cached_llm=cached_llm)
        self.gap_agent = GapAgent(cached_llm=cached_llm)
        self.critic_agent = CriticAgent(cached_llm=cached_llm)
        self.solution_agent = SolutionAgent(cached_llm=cached_llm)
        self.experiment_agent = ExperimentAgent(cached_llm=cached_llm)

        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(ResearchState)

        workflow.add_node("plan", self._plan_node)
        workflow.add_node("research", self._research_node)
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
        workflow.add_conditional_edges(
            "decide_loop",
            lambda s: s["_next"],
            {"solution": "solution", "gap_analysis": "gap_analysis"}
        )
        workflow.add_edge("solution", "experiment")
        workflow.add_edge("experiment", "package")
        workflow.add_edge("package", END)

        workflow.set_entry_point("plan")
        return workflow.compile()

    # ── nodes ──────────────────────────────────────────────────

    def _record(self, state: ResearchState, node_name: str, agent_name: str,
                step: int, input_preview: str, output_preview: str, elapsed: float = 0):
        logger.info(f"  [{node_name}] {elapsed:.1f}s — {output_preview[:80]}")
        if self.memory and self.memory.working_memory:
            self.memory.working_memory.record(
                session_id=state.get("_session_id", ""),
                node_name=node_name, agent_name=agent_name, step_number=step,
                input_preview=f"[{elapsed:.1f}s] {input_preview[:450]}",
                output_preview=output_preview[:500],
            )

    def _plan_node(self, state: ResearchState) -> ResearchState:
        t0 = time.time()
        plan = self.planner.plan_research(state["topic"])
        self._record(state, "plan", "planner", 1,
                     f"topic: {state['topic']}",
                     f"{len(plan.get('keywords', []))} keywords, {len(plan.get('subtopics', []))} subtopics",
                     time.time() - t0)
        return {"plan": plan}

    def _research_node(self, state: ResearchState) -> ResearchState:
        t0 = time.time()
        keywords = state["plan"].get("keywords", [state["topic"]])
        venues = state.get("_venues") or [v.strip() for v in settings.search_venues.split(",") if v.strip()]
        year = state.get("_year") or None
        papers = self.researcher.search_papers(keywords, state["max_papers"], venues=venues, year=year)
        paper_table_json = self.researcher.generate_paper_table_json(papers)
        self._record(state, "research", "researcher", 2,
                     f"keywords: {keywords}", f"{len(papers)} papers found",
                     time.time() - t0)
        return {"papers": papers, "paper_table_json": paper_table_json}

    def _read_node(self, state: ResearchState) -> ResearchState:
        t0 = time.time()
        analyses = self.reader.analyze_papers(state["papers"])
        self._record(state, "read", "reader", 3,
                     f"{len(state['papers'])} papers", f"{len(analyses)} analyses done",
                     time.time() - t0)
        if self.memory and self.memory.knowledge:
            for a in analyses:
                try:
                    self.memory.knowledge.save_analysis(
                        session_id=state.get("_session_id", ""),
                        paper_title=a.get("title", ""), analysis=a)
                except Exception:
                    pass
        return {"paper_analyses": analyses, "gap_iteration": 1}

    def _gap_analysis_node(self, state: ResearchState) -> ResearchState:
        t0 = time.time()
        iteration = state.get("gap_iteration", 1)
        feedback = state.get("critic_feedback", {})
        gap_data = self.gap_agent.identify_gaps(state["paper_analyses"], {}, critic_feedback=feedback)
        self._record(state, "gap_analysis", "gap", 3 + iteration,
                     f"{len(state['paper_analyses'])} analyses", f"{len(gap_data.get('research_gaps', []))} gaps",
                     time.time() - t0)
        return {"gap_data": gap_data, "gap_iteration": iteration + 1}

    def _critic_node(self, state: ResearchState) -> ResearchState:
        t0 = time.time()
        iteration = state.get("gap_iteration", 1)
        papers_text = "\n\n".join([
            f"{p.title}\n{', '.join(p.authors)}\n{p.abstract}" for p in state["papers"]
        ])
        feedback = self.critic_agent.review_gaps(
            topic=state["topic"], papers=papers_text,
            gap_analysis=json.dumps(state["gap_data"], ensure_ascii=False))
        fb = feedback.model_dump()
        self._record(state, "critic", "critic", 3 + iteration + 1,
                     f"review gaps", f"confidence={fb.get('confidence', '?')}/5",
                     time.time() - t0)
        return {"critic_feedback": fb}

    def _decide_loop_node(self, state: ResearchState) -> ResearchState:
        iteration = state.get("gap_iteration", 1)
        confidence = state.get("critic_feedback", {}).get("confidence", 0)
        if iteration < self.max_iterations and confidence < 4:
            logger.info(f"  [decide] → gap_analysis (iter={iteration} conf={confidence})")
            return {"_next": "gap_analysis"}
        logger.info(f"  [decide] → solution (iter={iteration} conf={confidence})")
        final_gap = json.dumps(state["gap_data"], ensure_ascii=False, indent=2)
        return {"_next": "solution", "final_gap_json": final_gap}

    def _solution_node(self, state: ResearchState) -> ResearchState:
        t0 = time.time()
        g = state["gap_data"]
        data = self.solution_agent.propose_solution(
            g.get("research_gaps", []), g.get("research_questions", []))
        report = self.solution_agent.generate_solution_report(solution=data)
        self._record(state, "solution", "solution", 10,
                     f"{len(g.get('research_gaps', []))} gaps", f"approach: {data.get('approach', '')[:200]}",
                     time.time() - t0)
        return {"solution_data": data, "solution": report}

    def _experiment_node(self, state: ResearchState) -> ResearchState:
        t0 = time.time()
        data = self.experiment_agent.design_experiment(state["solution_data"])
        report = self.experiment_agent.generate_experiment_report(experiment=data)
        self._record(state, "experiment", "experiment", 11,
                     f"solution", f"{len(data.get('datasets', []))} datasets, {len(data.get('baselines', []))} baselines",
                     time.time() - t0)
        return {"experiment_data": data, "experiment_design": report}

    def _package_node(self, state: ResearchState) -> ResearchState:
        t0 = time.time()
        final_gap = state.get("final_gap_json",
                              json.dumps(state["gap_data"], ensure_ascii=False, indent=2))
        package = {
            "papers_table.json": state.get("paper_table_json", "{}"),
            "final_gap.json": final_gap,
        }
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)
        for name, content in package.items():
            (output_dir / name).write_text(content, encoding="utf-8")

        if self.memory and self.memory.session:
            try:
                self.memory.session.complete_session(
                    session_id=state.get("_session_id", ""),
                    summary=state["topic"],
                    paper_count=len(state.get("papers", [])))
            except Exception:
                pass
        self._record(state, "package", "package", 12, "done", f"{len(package)} files written",
                     time.time() - t0)
        return {"research_package": package}

    # ── run ────────────────────────────────────────────────────

    def run(self, topic: str, max_papers: int = 10, session_id: str = None,
            venues: list = None, year_start: int = None, year_end: int = None) -> Dict[str, str]:
        year = f"{year_start}-{year_end}" if year_start and year_end else None
        logger.info(f"Starting research: {topic} (venues={venues}, year={year})")
        session_id = session_id or uuid4().hex[:16]

        state = {
            "topic": topic, "max_papers": max_papers,
            "_venues": venues or [], "_year": year or "",
            "plan": {}, "papers": [], "paper_table_json": "",
            "paper_analyses": [], "gap_data": {}, "gap_iteration": 1,
            "critic_feedback": {}, "final_gap_json": "",
            "solution_data": {}, "solution": "",
            "experiment_data": {}, "experiment_design": "",
            "research_package": {}, "_session_id": session_id,
            "_venues": venues or [], "_year": year or "", "_next": "",
        }

        if self.memory and self.memory.session:
            try:
                self.memory.session.create_session(session_id=session_id, topic=topic)
            except Exception:
                pass

        try:
            result = self.graph.invoke(state)
            return result["research_package"]
        except Exception as e:
            if self.memory and self.memory.session:
                try:
                    self.memory.session.fail_session(session_id, str(e))
                except Exception:
                    pass
            raise
