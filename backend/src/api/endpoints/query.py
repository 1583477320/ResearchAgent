import uuid
from fastapi import APIRouter, BackgroundTasks
from src.schemas.request import ResearchRequest
from src.schemas.response import TaskStatus, ReportResponse
from src.workflow.research_workflow import ResearchWorkflow
from src.memory import MemorySystem
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

task_store = {}
report_store = {}

# Shared memory system instance (single DB connection reused across requests)
_memory: MemorySystem = None


def _get_memory() -> MemorySystem:
    global _memory
    if _memory is None:
        _memory = MemorySystem()
    return _memory


def _run_workflow_sync(topic: str, max_papers: int, task_id: str, venues: list = None,
                       year_start: int = None, year_end: int = None):
    """Run the research workflow synchronously (called from a thread pool)."""
    memory = _get_memory()
    try:
        workflow = ResearchWorkflow(memory_system=memory)
        report = workflow.run(topic, max_papers, session_id=task_id, venues=venues,
                              year_start=year_start, year_end=year_end)
        report_store[task_id] = report
        # Persist to disk so it survives restarts
        import json as _json
        from pathlib import Path as _Path
        _Path("output").mkdir(exist_ok=True)
        _Path(f"output/{task_id}.json").write_text(_json.dumps(report, ensure_ascii=False), encoding="utf-8")
        task_store[task_id] = {"status": "completed", "message": "Research completed"}
        logger.info(f"Research completed for task: {task_id}")
    except Exception as e:
        task_store[task_id] = {"status": "failed", "message": str(e)}
        if memory and memory.session:
            memory.session.fail(task_id, str(e))
        logger.error(f"Research failed for task {task_id}: {str(e)}")


@router.post("/api/query")
async def submit_query(request: ResearchRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    task_store[task_id] = {"status": "running", "message": "Starting research workflow"}
    logger.info(f"Received research request: {request.topic}")

    # FastAPI runs sync functions in a thread pool automatically
    background_tasks.add_task(
        _run_workflow_sync, request.topic, request.max_papers, task_id,
        request.venues, request.year_start, request.year_end
    )
    return {"task_id": task_id, "status": "running"}


@router.get("/api/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in task_store:
        return {"error": "Task not found"}
    status = task_store[task_id]

    # Enrich with progress info from memory timeline
    message = status["message"]
    progress = status.get("progress", 0.0)
    memory = _get_memory()
    if memory and memory.working_memory:
        timeline = memory.working_memory.timeline(task_id)
        if timeline:
            last = timeline[-1]
            node_names = [t["node_name"] for t in timeline]
            message = f"[{len(timeline)}/8] {last['node_name']}: {last['output_preview'][:100]}"
            progress = min(len(timeline) / 9, 0.95)

    return TaskStatus(
        task_id=task_id,
        status=status["status"],
        message=message,
        progress=progress,
    )


@router.get("/api/report/{task_id}")
async def get_report(task_id: str):
    if task_id in report_store:
        return ReportResponse(success=True, report={"content": report_store[task_id]})
    # Fallback: load from disk (survives server restart)
    from pathlib import Path as _Path
    disk_path = _Path(f"output/{task_id}.json")
    if disk_path.exists():
        import json as _json
        data = _json.loads(disk_path.read_text(encoding="utf-8"))
        return ReportResponse(success=True, report={"content": data})
    return ReportResponse(success=False, error="Report not found")


# ── History endpoints ────────────────────────────────────────────


@router.get("/api/history")
async def list_history(limit: int = 20, offset: int = 0):
    """List past research sessions, most recent first."""
    memory = _get_memory()
    if not memory.session:
        return {"sessions": [], "total": 0}
    sessions = memory.session.list_recent(limit=limit)
    total = memory.session.count()
    return {"sessions": sessions, "total": total}


@router.get("/api/history/{session_id}")
async def get_history_detail(session_id: str):
    """Get a session's detail including the step-by-step timeline."""
    memory = _get_memory()
    if not memory.session:
        return {"error": "Memory system not available"}

    session = memory.session.get(session_id)
    if not session:
        return {"error": "Session not found"}

    timeline = []
    if memory.working_memory:
        timeline = memory.working_memory.timeline(session_id)

    return {"session": session, "timeline": timeline}


@router.delete("/api/history/{session_id}")
async def delete_history(session_id: str):
    """Delete a research session and its working memory entries."""
    memory = _get_memory()
    if not memory.session:
        return {"error": "Memory system not available"}

    deleted = memory.session.delete(session_id)
    if not deleted:
        return {"error": "Session not found"}

    # Also clean up the in-memory stores
    task_store.pop(session_id, None)
    report_store.pop(session_id, None)

    return {"success": True, "deleted": session_id}


# ── Knowledge base endpoints ─────────────────────────────────────


@router.get("/api/knowledge/search")
async def search_knowledge(q: str = "", limit: int = 10):
    """FTS5 full-text search across accumulated paper analyses.

    Searches title, problem, method, dataset, limitation, and contribution fields.
    Supports FTS5 boolean syntax: "multi-task AND learning", "transformer OR attention".
    """
    memory = _get_memory()
    if not memory.knowledge:
        return {"results": [], "total": 0, "query": q}

    results = memory.knowledge.search(q, limit=limit)
    total = memory.knowledge.total()
    return {"results": results, "total": total, "query": q}


@router.get("/api/knowledge/stats")
async def knowledge_stats():
    """Return knowledge base statistics."""
    memory = _get_memory()
    if not memory.knowledge:
        return {"total_papers": 0, "total_sessions": 0}

    return {
        "total_papers": memory.knowledge.total(),
        "total_sessions": memory.session.count() if memory.session else 0,
    }


@router.get("/api/knowledge/semantic")
async def search_knowledge_semantic(q: str = "", limit: int = 5):
    """FAISS semantic search across paper analyses.

    Finds papers semantically similar to the query, not just keyword matches.
    Requires embedding_model_name to be configured in .env.
    Falls back to FTS if vector store is disabled.
    """
    memory = _get_memory()
    if not memory.knowledge:
        return {"results": [], "total": 0, "query": q, "mode": "none"}

    if memory.vector_store and memory.vector_store.enabled:
        results = memory.knowledge.search_semantic(q, limit=limit)
        mode = "semantic"
    else:
        results = memory.knowledge.search(q, limit=limit)
        mode = "fts_fallback"

    return {"results": results, "total": memory.knowledge.total(), "query": q, "mode": mode}


@router.post("/api/knowledge/reindex")
async def reindex_knowledge():
    """(Re)build the FAISS index from all existing paper analyses."""
    memory = _get_memory()
    if not memory.knowledge or not memory.vector_store:
        return {"indexed": 0, "error": "Vector store not available"}

    count = memory.knowledge.index_all()
    return {"indexed": count, "index_size": memory.vector_store.size}
