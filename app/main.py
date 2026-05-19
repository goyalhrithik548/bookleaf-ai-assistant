import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.routes.routes import router
from app.routes.history_routes import router as history_router
from app.routes.identity_routes import router as identity_router

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Invalid request payload: %s", exc)

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Invalid request payload"
        }
    )

app.include_router(router)
app.include_router(history_router)
app.include_router(identity_router)

frontend_dir = Path(__file__).resolve().parent.parent / "frontend"

if frontend_dir.exists():
    app.mount(
        "/frontend",
        StaticFiles(directory=str(frontend_dir), html=True),
        name="frontend"
    )

@app.get("/")
def home():
    return {
        "message": "BookLeaf AI Assistant API Running"
    }
