from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def classify_intent(query, history=None):

    conversation_context = ""

    # ADD RECENT CHAT HISTORY
    if history:

        recent_history = history[-4:]

        for msg in recent_history:

            conversation_context += (
                f"{msg['role']}: {msg['content']}\n"
            )

    # INTENT CLASSIFICATION PROMPT
    prompt = f"""
Conversation History:
{conversation_context}

Current User Query:
{query}

You are an AI intent classifier for a publishing company.

Classify the user query into EXACTLY ONE of these intents:

- book_live_status
- royalty_status
- author_copy_status
- add_on_service_status
- dashboard_access
- knowledge_base_query
- unknown

Also provide a confidence score between 0 and 1.

IMPORTANT RULES:

1. Use "unknown" if the query is unrelated to:
   - publishing
   - books
   - royalties
   - author support
   - dashboard/platform operations

2. If the query is vague, emotional, random, unrelated,
   or unclear, return low confidence.

3. Return ONLY valid JSON.

EXAMPLE FOR UNKNOWN QUERY:

{{
    "intent": "unknown",
    "confidence": 0.20
}}

EXAMPLE FOR VALID QUERY:

{{
    "intent": "royalty_status",
    "confidence": 0.95
}}
"""

    # GROQ API CALL
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    result = response.choices[0].message.content

    print("RAW LLM RESPONSE:")
    print(result)

    # CLEAN MARKDOWN
    cleaned_result = (
        result
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    try:

        parsed_result = json.loads(cleaned_result)

        # SAFETY FALLBACKS
        if "intent" not in parsed_result:
            parsed_result["intent"] = "unknown"

        if "confidence" not in parsed_result:
            parsed_result["confidence"] = 0.0

        return parsed_result

    except Exception as e:

        print("JSON Parse Error:", e)

        return {
            "intent": "unknown",
            "confidence": 0.0
        }