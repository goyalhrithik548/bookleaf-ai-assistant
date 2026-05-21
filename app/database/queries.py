import logging
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher

from app.database.db import (
    EmptyResultError,
    MultipleResultsError,
    SchemaMismatchError,
    execute_supabase_query,
    get_table,
    require_single_record,
)


logger = logging.getLogger(__name__)

AUTHOR_COLUMNS = "id,email,phone,author_name,instagram_handle,book_title"
NAME_MATCH_THRESHOLD = 0.8
_CHAT_MEMORY_SCHEMA = None
_QUERY_LOG_SCHEMA = None


def _utc_timestamp():
    return datetime.now(timezone.utc).isoformat()


def _normalize_text(value):
    if value is None:
        return ""

    return re.sub(r"\s+", " ", str(value).strip().lower())


def _normalize_email(value):
    return _normalize_text(value).replace("mailto:", "")


def _normalize_phone(value):
    return re.sub(r"\D", "", _normalize_text(value))


def _normalize_handle(value):
    return _normalize_text(value).lstrip("@")


def _name_similarity(name_1, name_2):
    normalized_name_1 = _normalize_text(name_1)
    normalized_name_2 = _normalize_text(name_2)

    if not normalized_name_1 or not normalized_name_2:
        return 0.0

    return SequenceMatcher(None, normalized_name_1, normalized_name_2).ratio()


def save_chat_memory(session_id, email, user_message, assistant_response):
    global _CHAT_MEMORY_SCHEMA

    if not session_id:
        logger.info("Skipping chat_memory save because session_id is missing")
        return []

    required_payload = {
        "session_id": session_id,
        "email": email,
        "user_message": user_message,
        "assistant_response": assistant_response,
        "timestamp": _utc_timestamp()
    }

    if _CHAT_MEMORY_SCHEMA in (None, "required"):
        try:
            data = execute_supabase_query(
                get_table("chat_memory").insert(required_payload),
                "save chat memory"
            )
            _CHAT_MEMORY_SCHEMA = "required"
            logger.info("Saved chat_memory row for session_id=%s", session_id)
            return data

        except SchemaMismatchError:
            _CHAT_MEMORY_SCHEMA = "role_messages"

    role_rows = [
        {
            "session_id": session_id,
            "role": "user",
            "message": user_message,
            "created_at": _utc_timestamp()
        },
        {
            "session_id": session_id,
            "role": "assistant",
            "message": assistant_response,
            "created_at": _utc_timestamp()
        }
    ]

    data = execute_supabase_query(
        get_table("chat_memory").insert(role_rows),
        "save chat memory role rows"
    )

    logger.info("Saved chat_memory role rows for session_id=%s", session_id)
    return data


def get_chat_history(session_id):
    global _CHAT_MEMORY_SCHEMA

    if not session_id:
        return []

    if _CHAT_MEMORY_SCHEMA in (None, "required"):
        try:
            rows = execute_supabase_query(
                get_table("chat_memory")
                .select("user_message,assistant_response,timestamp")
                .eq("session_id", session_id)
                .order("timestamp", desc=False),
                "get chat history"
            )
            _CHAT_MEMORY_SCHEMA = "required"

            messages = []

            for row in rows:
                user_message = row.get("user_message")
                assistant_response = row.get("assistant_response")

                if user_message:
                    messages.append({
                        "role": "user",
                        "content": user_message
                    })

                if assistant_response:
                    messages.append({
                        "role": "assistant",
                        "content": assistant_response
                    })

            logger.info("Loaded %s chat history messages for session_id=%s", len(messages), session_id)
            return messages

        except SchemaMismatchError:
            _CHAT_MEMORY_SCHEMA = "role_messages"

    rows = execute_supabase_query(
        get_table("chat_memory")
        .select("role,message,created_at")
        .eq("session_id", session_id)
        .order("created_at", desc=False),
        "get chat history role rows"
    )

    messages = []

    for row in rows:
        role = row.get("role")
        message = row.get("message")

        if role in {"user", "assistant"} and message:
            messages.append({
                "role": role,
                "content": message
            })

    logger.info("Loaded %s chat history messages for session_id=%s", len(messages), session_id)
    return messages


def log_query(query, detected_intent, confidence, escalated=False, ai_response""):
    global _QUERY_LOG_SCHEMA

    payload = {
        "query": query,
        "detected_intent": detected_intent,
        "confidence": confidence,
        "escalated": escalated,
        "ai_response": ai_response,
        "timestamp": _utc_timestamp()
    }

    data = execute_supabase_query(
        get_table("query_logs").insert(payload),
        "log query"
    )

    logger.info("Logged query with intent=%s confidence=%s", detected_intent, confidence)

    return data


def find_author_by_email(email):
    normalized_email = _normalize_email(email)

    if not normalized_email:
        raise ValueError("Email is required for this request")

    rows = execute_supabase_query(
        get_table("authors")
        .select(AUTHOR_COLUMNS)
        .eq("email", normalized_email),
        "find author by email"
    )

    author = require_single_record(
        rows,
        "No matching author found",
        "Multiple matching authors found"
    )

    logger.info("Found author by email")
    return author


def find_author_by_phone(phone):
    normalized_phone = _normalize_phone(phone)

    if not normalized_phone:
        raise ValueError("Phone is required for this request")

    rows = execute_supabase_query(
        get_table("authors")
        .select(AUTHOR_COLUMNS)
        .eq("phone", normalized_phone),
        "find author by phone"
    )

    author = require_single_record(
        rows,
        "No matching author found",
        "Multiple matching authors found"
    )

    logger.info("Found author by phone")
    return author


def find_author_by_instagram_handle(instagram_handle):
    normalized_handle = _normalize_handle(instagram_handle)

    if not normalized_handle:
        raise ValueError("Instagram handle is required for this request")

    rows = execute_supabase_query(
        get_table("authors")
        .select(AUTHOR_COLUMNS)
        .in_("instagram_handle", [normalized_handle, f"@{normalized_handle}"]),
        "find author by instagram handle"
    )

    author = require_single_record(
        rows,
        "No matching author found",
        "Multiple matching authors found"
    )

    logger.info("Found author by instagram handle")
    return author


def search_author_by_name(author_name):
    normalized_name = _normalize_text(author_name)

    if not normalized_name:
        raise ValueError("Author name is required for this request")

    rows = execute_supabase_query(
        get_table("authors")
        .select(AUTHOR_COLUMNS)
        .limit(100),
        "search author by name"
    )

    matches = []

    for row in rows:
        similarity = _name_similarity(normalized_name, row.get("author_name"))

        if similarity > NAME_MATCH_THRESHOLD:
            enriched_row = dict(row)
            enriched_row["_name_similarity"] = round(similarity, 2)
            matches.append(enriched_row)

    if not matches:
        raise EmptyResultError("No matching author found")

    matches.sort(key=lambda row: row.get("_name_similarity", 0), reverse=True)

    if len(matches) > 1:
        logger.info("Author name search returned multiple matches")
    else:
        logger.info("Author name search returned one match")

    return matches

def get_author_by_email(email):
    """
    Fetch single author using email.
    Used for personalized AI responses.
    """

    normalized_email = _normalize_email(email)

    if not normalized_email:
        return None

    rows = execute_supabase_query(
        get_table("authors")
        .select(AUTHOR_COLUMNS)
        .eq("email", normalized_email),
        "get author by email"
    )

    if not rows:
        return None

    return rows[0]
