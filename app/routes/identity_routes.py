import logging

from fastapi import APIRouter

from app.database.db import DatabaseConnectionError, DatabaseError
from app.schemas.identity_schema import IdentityMatchRequest
from app.services.identity_service import (
    IdentityNotFoundError,
    MultipleIdentityMatchesError,
    unify_author_identity,
)


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/identity-match")
def identity_match(payload: IdentityMatchRequest):
    try:
        result = unify_author_identity(
            payload.profile_1,
            payload.profile_2
        )

        return {
            "success": True,
            "data": result
        }

    except ValueError as exc:
        logger.warning("Invalid identity match payload: %s", exc)

        return {
            "success": False,
            "message": str(exc)
        }

    except IdentityNotFoundError as exc:
        logger.info("Identity match returned no author: %s", exc)

        return {
            "success": False,
            "message": str(exc)
        }

    except MultipleIdentityMatchesError as exc:
        logger.info("Identity match returned multiple authors: %s", exc)

        return {
            "success": False,
            "message": str(exc)
        }

    except DatabaseConnectionError as exc:
        logger.exception("Identity database connection failed")

        return {
            "success": False,
            "message": str(exc)
        }

    except DatabaseError:
        logger.exception("Identity database response failed")

        return {
            "success": False,
            "message": "Database operation failed"
        }

    except Exception:
        logger.exception("Identity matching failed")

        return {
            "success": False,
            "message": "Identity matching failed"
        }
