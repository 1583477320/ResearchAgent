from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.endpoints import query_router, upload_router
from src.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(title="Research Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query_router)
app.include_router(upload_router)


@app.get("/")
async def root():
    return {"message": "Research Agent API is running"}


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Research Agent API server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
