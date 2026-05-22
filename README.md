# BookPublishing AI Assistant

An AI-powered publishing support assistant built using FastAPI, Groq LLMs, RAG (Retrieval-Augmented Generation), FAISS vector search, and Supabase.

The assistant helps authors with:

* Royalty-related queries
* Publishing policies
* Dashboard/access support
* Author identity resolution
* Conversational memory
* Knowledge-base retrieval using RAG

---

# Features

* FastAPI backend
* AI intent classification using Groq
* Retrieval-Augmented Generation (RAG)
* FAISS vector database
* HuggingFace embeddings
* Supabase integration
* Author identity matching
* Chat memory/history
* Swagger API documentation
* Frontend chat interface

---

# Tech Stack

Backend:

* FastAPI
* Python

LLM:

* Groq
* llama-3.3-70b-versatile

RAG:

* FAISS
* LangChain
* HuggingFace Embeddings
* sentence-transformers/all-MiniLM-L6-v2

Database:

* Supabase

Frontend:

* HTML
* CSS
* JavaScript

---

# Project Structure

```bash
bookleaf-ai-assistant/
│
├── app/
│   ├── database/
│   ├── models/
│   ├── rag/
│   ├── routes/
│   ├── schemas/
│   ├── services/
│   ├── utils/
│   └── main.py
│
├── documents/
│   ├── publishing_rules.txt
│   └── royalty_policy.txt
│
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
│
├── vector_store/
├── requirements.txt
├── .env
└── README.md
```

---

# Setup Instructions

## 1. Clone Repository

```bash
git clone <your-repo-url>
cd bookleaf-ai-assistant
```

---

## 2. Create Virtual Environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Mac/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file in the root directory.

Example:

```env
GROQ_API_KEY=your_groq_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

IMPORTANT:

* Never upload your real `.env` file to GitHub
* Rotate exposed keys before deployment

---

# Build Vector Database

Before running the app, build the FAISS vector database.

Run:

```bash
python app/rag/build_db.py
```

This will:

* Load knowledge base documents
* Split text into chunks
* Generate embeddings
* Create FAISS vector store
* Save vectors inside `vector_store/`

---

# Run Backend Server

Start FastAPI server:

```bash
uvicorn app.main:app --reload --port 8001
```

Server runs on:

```bash
http://127.0.0.1:8001
```

---

# Frontend URL

Open in browser:

```bash
http://127.0.0.1:8001/frontend
```

---

# Swagger API Docs

Open:

```bash
http://127.0.0.1:8001/docs
```

---

# Main Functionalities

## Intent Classification

The assistant classifies user queries into intents such as:

* royalty_status
* dashboard_access
* author_copy_status
* knowledge_base_query
* unknown

Implemented using Groq LLM classification.

---

## RAG Pipeline

The assistant:

1. Loads publishing documents
2. Creates embeddings
3. Stores vectors in FAISS
4. Retrieves relevant context
5. Sends context to LLM for grounded answers

---

## Author Identity Resolution

The system can match author identities using:

* Email
* Phone number
* Instagram/social handles
* Fuzzy name matching

---

## Conversational Memory

Chat history is stored and reused for:

* Context continuity
* Better responses
* Personalized conversations

---

# Knowledge Base Documents

Knowledge documents are stored inside:

```bash
documents/
```

Current files:

* publishing_rules.txt
* royalty_policy.txt

You can add more `.txt` documents and rebuild the vector database.

---

# Example Workflow

1. User asks question
2. Intent classifier detects intent
3. Router decides:

   * Database route
   * RAG route
   * Fallback route
4. Relevant context retrieved
5. Groq generates response
6. Chat history saved

---

# Important Commands

Install dependencies:

```bash
pip install -r requirements.txt
```

Build vector DB:

```bash
python app/rag/build_db.py
```

Run backend:

```bash
uvicorn app.main:app --reload --port 8001
```

---

# Common Errors

## ModuleNotFoundError

Fix:

```bash
pip install -r requirements.txt
```

---

## Vector Store Missing

Fix:

```bash
python app/rag/build_db.py
```

---

## Invalid API Key

Check:

* GROQ_API_KEY
* SUPABASE credentials

inside `.env`

---

# API Endpoints

## Root Endpoint

```http
GET /
```

Returns API status.

---

## Chat Endpoint

```http
POST /chat
```

Main AI assistant endpoint.

---

## Identity Matching

```http
POST /identity/match
```

Matches author identities.

---

## Chat History

```http
GET /history/{session_id}
```

Fetches previous conversation history.

---

# Notes

* Uses FAISS for local vector search
* Uses Groq LLM for fast inference
* Uses Supabase for persistent storage
* Frontend is mounted directly using FastAPI static files

---

# Future Improvements

* Deployment support
* Authentication
* Streaming responses
* Better frontend UI
* Multi-document ingestion
* PDF support
* Admin dashboard
* Analytics

---

# Author

Hrithik Kumar

AI/ML Engineer | FastAPI | RAG Systems | NLP | LLM Applications
