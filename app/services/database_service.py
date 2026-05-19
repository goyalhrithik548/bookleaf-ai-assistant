import logging

from app.database.db import (
    DatabaseConnectionError as SupabaseConnectionError,
    DatabaseError,
    EmptyResultError,
    MultipleResultsError,
)
from app.database.queries import find_author_by_email


logger = logging.getLogger(__name__)


class DatabaseServiceError(Exception):
    pass


class DatabaseConnectionError(DatabaseServiceError):
    pass


class AuthorNotFoundError(DatabaseServiceError):
    pass


class MultipleAuthorsFoundError(DatabaseServiceError):
    pass


DATABASE_INTENTS = {
    "book_live_status",
    "royalty_status",
    "author_copy_status",
    "add_on_service_status",
    "dashboard_access"
}


def fetch_author_data(email, intent):
    if intent not in DATABASE_INTENTS:
        raise ValueError("Unsupported database intent")

    try:
        author = find_author_by_email(email)

    except EmptyResultError as exc:
        raise AuthorNotFoundError("No matching author found") from exc

    except MultipleResultsError as exc:
        raise MultipleAuthorsFoundError("Multiple matching authors found") from exc

    except SupabaseConnectionError as exc:
        raise DatabaseConnectionError("Database connection failed") from exc

    except DatabaseError as exc:
        logger.exception("Invalid author database response")
        raise DatabaseConnectionError("Database connection failed") from exc

    logger.info("Fetched author data for intent=%s", intent)

    # Keep the existing downstream contract: response generation receives
    # a list of database rows.
    return [author]
