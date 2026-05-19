from groq import Groq
from dotenv import load_dotenv
import os

from app.services.memory_service import save_chat
from app.services.memory_service import get_chat_history

# NEW IMPORT
from app.database.queries import get_author_by_email

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def generate_response(
    user_query,
    database_result,
    session_id,
    rag_context=None,
    email=None
):

    # Fetch previous conversation memory
    history = get_chat_history(session_id)

    # ================================
    # FETCH AUTHOR DETAILS
    # ================================
    author = None
    author_context = ""

    if email:
        author = get_author_by_email(email)

    if author:
        author_context = f"""
Author Name: {author.get('author_name')}
Book Title: {author.get('book_title')}
Instagram Handle: {author.get('instagram_handle')}
Phone Number: {author.get('phone')}
Email: {author.get('email')}
"""

    # ================================
    # BASE SYSTEM PROMPT
    # ================================
    messages = [
        {
            "role": "system",
            "content": f"""
You are an AI publishing assistant for BookLeaf.

Your responsibilities:
- Help authors with royalty-related queries
- Explain publishing policies clearly
- Answer platform-related questions
- Use database information accurately
- Use knowledge base context whenever available
- Maintain conversational continuity using memory
- Use author profile information when available

AUTHOR PROFILE INFORMATION:
{author_context}

IMPORTANT:
- If author information is available, use it naturally.
- Answer personalized questions using the author profile.
- Never hallucinate missing author details.
- If information is unavailable, say so professionally.

Always provide professional, concise, and accurate answers.
"""
        }
    ]

    # ================================
    # ADD MEMORY
    # ================================
    messages.extend(history)

    # ================================
    # ADD RAG CONTEXT
    # ================================
    if rag_context:
        messages.append({
            "role": "system",
            "content": f"""
KNOWLEDGE BASE CONTEXT:

{rag_context}

Use this information to answer accurately.
"""
        })

    # ================================
    # CURRENT USER QUERY
    # ================================
    messages.append({
        "role": "user",
        "content": f"""
USER QUESTION:
{user_query}

DATABASE RESULT:
{database_result}
"""
    })

    # ================================
    # GENERATE RESPONSE
    # ================================
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )

    # Extract AI response
    response = completion.choices[0].message.content

    # ================================
    # SAVE CHAT MEMORY
    # ================================
    save_chat(
        session_id=session_id,
        email=email,
        query=user_query,
        response=response
    )

    return response