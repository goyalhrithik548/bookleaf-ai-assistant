from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

import logging
import os


logger = logging.getLogger(__name__)


class RagRetrievalError(Exception):
    pass


def build_vector_db():

    all_docs = []

    text_files = [
        "documents/publishing_rules.txt",
        "documents/royalty_policy.txt"
    ]

    for file in text_files:

        loader = TextLoader(file)

        documents = loader.load()

        all_docs.extend(documents)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    docs = splitter.split_documents(all_docs)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectorstore = FAISS.from_documents(
        docs,
        embeddings
    )

    os.makedirs("vector_store", exist_ok=True)

    vectorstore.save_local("vector_store")

    print("FAISS Vector DB Created")

def search_documents(user_query):

    try:
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        vectorstore = FAISS.load_local(
            "vector_store",
            embeddings,
            allow_dangerous_deserialization=True
        )

        results = vectorstore.similarity_search(
            user_query,
            k=3
        )

    except Exception as exc:
        logger.exception("RAG retrieval failed")
        raise RagRetrievalError("RAG retrieval failed") from exc

    if not results:
        return ""

    context = ""

    for doc in results:

        context += doc.page_content + "\n"

    return context.strip()
