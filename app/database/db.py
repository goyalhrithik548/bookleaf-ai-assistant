import logging

from app.database.supabase_client import SupabaseClientError, get_supabase_client


logger = logging.getLogger(__name__)


class DatabaseError(RuntimeError):
    pass


class DatabaseConnectionError(DatabaseError):
    pass


class EmptyResultError(DatabaseError):
    pass


class MultipleResultsError(DatabaseError):
    pass


class InvalidDatabaseResponseError(DatabaseError):
    pass


class SchemaMismatchError(DatabaseError):
    pass


def get_table(table_name):
    try:
        return get_supabase_client().table(table_name)

    except SupabaseClientError as exc:
        logger.error("Supabase table access failed for %s", table_name)
        raise DatabaseConnectionError("Database connection failed") from exc


def execute_supabase_query(query_builder, operation_name):
    try:
        response = query_builder.execute()

    except Exception as exc:
        message = str(exc)

        if "42703" in message or "does not exist" in message:
            logger.warning("Supabase schema mismatch during operation: %s", operation_name)
            raise SchemaMismatchError("Database schema mismatch") from exc

        logger.error("Supabase operation failed: %s (%s)", operation_name, exc.__class__.__name__)
        raise DatabaseConnectionError("Database connection failed") from exc

    data = getattr(response, "data", None)

    if not isinstance(data, list):
        logger.error("Invalid Supabase response for operation: %s", operation_name)
        raise InvalidDatabaseResponseError("Invalid database response")

    return data


def require_single_record(records, empty_message, multiple_message):
    if not records:
        raise EmptyResultError(empty_message)

    if len(records) > 1:
        raise MultipleResultsError(multiple_message)

    return records[0]
