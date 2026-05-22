import logging

from fastapi import APIRouter

from app.services.memory_service import get_chat_history
from app.rag.rag_service import RagRetrievalError, search_documents
from app.services.intent_service import classify_intent
from app.services.router_service import route_query
from app.services.database_service import (
    AuthorNotFoundError,
    DatabaseConnectionError,
    MultipleAuthorsFoundError,
    fetch_author_data
)
from app.services.response_service import generate_response
from app.services.logging_service import log_query

# AUTHOR PROFILE IMPORT
from app.database.queries import get_author_by_email


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat")
def chat(payload: dict):

    try:

        query = payload.get("query")
        email = payload.get("email")
        session_id = payload.get("session_id")

        # =====================================
        # VALIDATION
        # =====================================
        if not query or not str(query).strip():

            return {
                "success": False,
                "message": "Query is required"
            }

        # =====================================
        # STEP 1 → GET CHAT HISTORY
        # =====================================
        history = get_chat_history(session_id)

        # =====================================
        # PERSONALIZED AUTHOR PROFILE QUERIES
        # =====================================
        lower_query = query.lower()

        if email:

            try:
                author = get_author_by_email(email)

            except Exception:
                author = None

            if author:

                if "book title" in lower_query:

                    return {
                        "success": True,
                        "intent": "author_book_title",
                        "response": (
                            f'Your book title is '
                            f'"{author.get("book_title")}".'
                        )
                    }

                if "instagram" in lower_query:

                    return {
                        "success": True,
                        "intent": "author_instagram",
                        "response": (
                            f'Your Instagram handle is '
                            f'"{author.get("instagram_handle")}".'
                        )
                    }

                if "phone" in lower_query or "mobile" in lower_query:

                    return {
                        "success": True,
                        "intent": "author_phone",
                        "response": (
                            f'Your registered phone number is '
                            f'"{author.get("phone")}".'
                        )
                    }

                if (
                    "who am i" in lower_query
                    or "my name" in lower_query
                ):

                    return {
                        "success": True,
                        "intent": "author_identity",
                        "response": (
                            f'You are '
                            f'{author.get("author_name")}.'
                        )
                    }

        # =====================================
        # STEP 2 → INTENT DETECTION
        # =====================================
        intent_result = classify_intent(
            query=query,
            history=history
        )

        # =====================================
        # HUMAN ESCALATION RULE
        # =====================================
        if intent_result["confidence"] < 0.80:

            log_query(
                user_query=query,
                detected_intent=intent_result["intent"],
                confidence_score=(
                    intent_result["confidence"]
                ),
                ai_response=(
                    "Escalated to human agent"
                ),
                escalation=True
            )

            return {
                "success": False,
                "escalate": True,
                "message": (
                    "Confidence score too low. "
                    "Escalating to human agent."
                ),
                "confidence": (
                    intent_result["confidence"]
                )
            }

        # =====================================
        # STEP 3 → ROUTING
        # =====================================
        route = route_query(intent_result)

        # =====================================
        # KNOWLEDGE BASE ROUTE
        # =====================================
        if route["route"] == "knowledge_base":

            try:

                rag_context = search_documents(query)

            except RagRetrievalError:

                return {
                    "success": False,
                    "message": "RAG retrieval failed"
                }

            if not rag_context:

                return {
                    "success": False,
                    "message": (
                        "No matching knowledge "
                        "base content found"
                    )
                }

            final_response = generate_response(
                user_query=query,
                database_result=(
                    "Knowledge Base Query"
                ),
                session_id=session_id,
                rag_context=rag_context,
                email=email
            )

            log_query(
                user_query=query,
                detected_intent=(
                    intent_result["intent"]
                ),
                confidence_score=(
                    intent_result["confidence"]
                ),
                ai_response=final_response,
                escalation=False
            )

            return {
                "success": True,
                "intent": (
                    intent_result["intent"]
                ),
                "response": final_response
            }

        # =====================================
        # DATABASE ROUTE
        # =====================================
        if route["route"] == "database":

            try:

                data = fetch_author_data(
                    email=email,
                    intent=(
                        intent_result["intent"]
                    )
                )

            except AuthorNotFoundError as exc:

                return {
                    "success": False,
                    "message": str(exc)
                }

            except MultipleAuthorsFoundError as exc:

                return {
                    "success": False,
                    "message": str(exc)
                }

            except DatabaseConnectionError as exc:

                return {
                    "success": False,
                    "message": str(exc)
                }

            except ValueError as exc:

                return {
                    "success": False,
                    "message": str(exc)
                }

            try:

                rag_context = search_documents(query)

            except RagRetrievalError:

                return {
                    "success": False,
                    "message": "RAG retrieval failed"
                }

            final_response = generate_response(
                user_query=query,
                database_result=data,
                session_id=session_id,
                rag_context=rag_context,
                email=email
            )

            log_query(
                user_query=query,
                detected_intent=(
                    intent_result["intent"]
                ),
                confidence_score=(
                    intent_result["confidence"]
                ),
                ai_response=final_response,
                escalation=False
            )

            return {
                "success": True,
                "intent": (
                    intent_result["intent"]
                ),
                "response": final_response
            }

        return {
            "success": False,
            "message": "Unknown route"
        }

    except RuntimeError as exc:

        logger.exception(
            "Chat request failed"
        )

        return {
            "success": False,
            "message": str(exc)
        }

    except Exception:

        logger.exception(
            "Chat request failed"
        )

        return {
            "success": False,
            "message": "Chat request failed"
        }
