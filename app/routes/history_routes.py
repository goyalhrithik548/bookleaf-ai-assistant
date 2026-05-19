import logging

from fastapi import APIRouter
from app.services.memory_service import get_chat_history


logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/history/{session_id}")
def history(session_id: str):
    try:
        chats = get_chat_history(session_id)

        return {
            "success": True,
            "history": chats
        }

    except RuntimeError as exc:
        logger.exception("History retrieval failed")

        return {
            "success": False,
            "message": str(exc)
        }

    except Exception:
        logger.exception("Unexpected history retrieval failure")

        return {
            "success": False,
            "message": "History retrieval failed"
        }
