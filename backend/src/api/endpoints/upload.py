from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from src.services.paper_repository import get_paper_repository
from src.utils.logger import get_logger
from pathlib import Path
import shutil
import os

logger = get_logger(__name__)

router = APIRouter()

ALLOWED_EXTENSIONS = {"pdf"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@router.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")
    
    try:
        repo = get_paper_repository("research_repo")
        
        temp_path = Path("/tmp") / file.filename
        with open(temp_path, "wb") as f:
            f.write(content)
        
        paper_id = repo.add_paper_from_pdf(temp_path, file.filename)
        
        os.remove(temp_path)
        
        logger.info(f"PDF uploaded successfully: {file.filename} -> {paper_id}")
        
        return {"success": True, "paper_id": paper_id, "message": "PDF uploaded and processed successfully"}
    except Exception as e:
        logger.error(f"Failed to upload PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")


@router.get("/api/papers")
async def get_uploaded_papers():
    try:
        repo = get_paper_repository("research_repo")
        papers = repo.get_all_papers()
        
        return {"success": True, "papers": papers}
    except Exception as e:
        logger.error(f"Failed to get papers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve papers: {str(e)}")


@router.delete("/api/papers/{paper_id}")
async def delete_paper(paper_id: str):
    try:
        repo = get_paper_repository("research_repo")
        success = repo.delete_paper(paper_id)
        
        if success:
            return {"success": True, "message": "Paper deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Paper not found")
    except Exception as e:
        logger.error(f"Failed to delete paper: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete paper: {str(e)}")
