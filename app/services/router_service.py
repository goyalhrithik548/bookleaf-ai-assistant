DATABASE_INTENTS = [
    "book_live_status",
    "royalty_status",
    "author_copy_status",
    "add_on_service_status",
    "dashboard_access"
]

RAG_INTENTS = [
    "knowledge_base_query",
    "publishing_rules",
    "royalty_policy"
]

def route_query(intent_result):

    intent = intent_result["intent"]

    if intent in DATABASE_INTENTS:
        return {
            "route": "database"
        }

    elif intent in RAG_INTENTS:
        return {
            "route": "knowledge_base"
        }

    return {
        "route": "fallback"
    }