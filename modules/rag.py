from __future__ import annotations

from pathlib import Path
from typing import Iterable
import tiktoken

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from modules.config import get_settings
from modules.llm import get_embedding_model

settings = get_settings()

def read_text_files(root_path: Path) -> list[tuple[str, str]]:
    """ reads the text files under root folder """
    docs = []
    for path in root_path.rglob("*txt"):
        docs.append((str(path), path.read_text(encoding = "utf-8")))
    for path in root_path.rglob("*.md"):
        docs.append((str(path), path.read_text(encoding="utf-8")))
    return docs

def chunk_text(text: str, source: str, chunk_size_tokens: int = 400, chunk_overlap_tokens: int = 80) -> list[Document]:
    """
    Token-aware, overlapping chunking optimized for RAG using cl100k_base.
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    docs: list[Document] = []

    start = 0
    while start < len(tokens):
        end = min(start + chunk_size_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        docs.append(
            Document(
                page_content=chunk_text,
                metadata={"source": source, "start_token": start, "end_token": end},
            )
        )
        if end == len(tokens):
            break
        start = end - chunk_overlap_tokens

    return docs

def build_vector_store() -> Chroma:
    """ Vector store ChromaBD  """
    texts = read_text_files(settings.rag_docs_path)
    all_docs: list[Document] = []
    for source, content in texts:
        all_docs.extend(chunk_text(content, source))

    embeddings = get_embedding_model()
    vectorstore = Chroma.from_documents(
        documents=all_docs,
        embedding=embeddings,
        persist_directory=str(settings.vector_store_path),
    )
    return vectorstore

def get_retriever(vectorstore: Chroma, k: int = 4):
    """ Provides retriver interface """
    return vectorstore.as_retriever(search_kwargs={"k": k})

def format_docs(docs: Iterable[Document]) -> str:
    """ Formats Retrived docs """
    parts = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        parts.append(f"[{source}]\n{doc.page_content}")
    return "\n\n".join(parts)
