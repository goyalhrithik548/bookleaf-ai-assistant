import logging
import os

from dotenv import load_dotenv
from supabase import create_client


logger = logging.getLogger(__name__)

load_dotenv()


class SupabaseClientError(RuntimeError):
    """Raised when the Supabase client cannot be configured or created."""


_supabase_client = None


def get_supabase_client():
    """
    Create the Supabase client lazily so importing the FastAPI app does not
    crash before a request can return a clean JSON-safe error.
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        logger.error("Missing SUPABASE_URL or SUPABASE_KEY environment variable")
        raise SupabaseClientError("Database connection failed")

    try:
        _supabase_client = create_client(
            supabase_url,
            supabase_key
        )
        logger.info("Supabase client initialized")
        return _supabase_client

    except Exception as exc:
        logger.error("Failed to initialize Supabase client (%s)", exc.__class__.__name__)
        raise SupabaseClientError("Database connection failed") from exc
