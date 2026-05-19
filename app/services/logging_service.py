import logging

from app.database.queries import log_query as log_query_to_supabase


logger = logging.getLogger(__name__)


def log_query(
    user_query,
    detected_intent,
    confidence_score,
    ai_response,
    escalation=False
):
    try:
        return log_query_to_supabase(
            query=user_query,
            detected_intent=detected_intent,
            confidence=confidence_score,
            escalated=escalation
        )

    except Exception:
        logger.exception("Failed to write query log")
        return []
