import logging

from app.database.db import DatabaseConnectionError, DatabaseError
from app.database.queries import get_chat_history as get_supabase_chat_history
from app.database.queries import save_chat_memory


logger = logging.getLogger(__name__)


def save_chat(session_id, email, query, response):
    try:
        return save_chat_memory(
            session_id=session_id,
            email=email,
            user_message=query,
            assistant_response=response
        )

    except DatabaseConnectionError as exc:
        logger.exception("Failed to save chat memory")
        raise RuntimeError("Database connection failed") from exc

    except DatabaseError as exc:
        logger.exception("Invalid chat memory database response")
        raise RuntimeError("Database operation failed") from exc


def get_chat_history(session_id):
    try:
        return get_supabase_chat_history(session_id)

    except DatabaseConnectionError as exc:
        logger.exception("Failed to retrieve chat history")
        raise RuntimeError("Database connection failed") from exc

    except DatabaseError as exc:
        logger.exception("Invalid chat history database response")
        raise RuntimeError("Database operation failed") from exc
