import uuid
from fastapi import APIRouter, BackgroundTasks
from src.schemas.request import ResearchRequest
from src.schemas.response import TaskStatus, ReportResponse
from src.workflow.research_workflow import ResearchWorkflow
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

task_store = {}
report_store = {}


@router.post("/api/query")
async def submit_query(request: ResearchRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    task_store[task_id] = {"status": "running", "message": "Starting research workflow"}
    
    logger.info(f"Received research request: {request.topic}")
    
    async def run_workflow():
        try:
            workflow = ResearchWorkflow()
            report = workflow.run(request.topic, request.max_papers)
            
            report_store[task_id] = report
            
            with open(f"report_{task_id}.md", "w") as f:
                f.write(report)
            
            task_store[task_id] = {"status": "completed", "message": "Research completed"}
            logger.info(f"Research completed for task: {task_id}")
        except Exception as e:
            task_store[task_id] = {"status": "failed", "message": str(e)}
            logger.error(f"Research failed for task {task_id}: {str(e)}")
    
    background_tasks.add_task(run_workflow)
    
    return {"task_id": task_id, "status": "running"}


@router.get("/api/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in task_store:
        return {"error": "Task not found"}
    
    status = task_store[task_id]
    return TaskStatus(
        task_id=task_id,
        status=status["status"],
        message=status["message"]
    )


@router.get("/api/report/{task_id}")
async def get_report(task_id: str):
    if task_id not in report_store:
        return ReportResponse(
            success=False,
            error="Report not found or task not completed"
        )
    
    report = report_store[task_id]
    return ReportResponse(
        success=True,
        report={"content": report}
    )
