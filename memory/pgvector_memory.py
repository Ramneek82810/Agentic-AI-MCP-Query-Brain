"""
Key asynchronous functions for managing user messages, embedding, and context:

1. ensure_schema() -> None
    - Purpose: Initialize or migrate the database schema.
    - Actions: Creates necessary tables and extensions (e.g., for embedding, conversations history, summaries).
    - Usuage: Call once at startup or during schema migration.
    - Notes: Safe to call multiple times; will not overwrite existing tables.
    
2. store_message(user_id: str, message:str)-> None
    - Purpose: persist a user message and its embedding for future retrieval.
    - Actions:
        - computes embedding for the message using the embedding model.
        - stores message, embedding, timestamp, and metadata in the database.
    - Usage: Call whenever a new user message is received.
    - Notes: Async for non-blocking database/ embedding operations.
    
3. search_similar(user_id: str, query: str, top_k:int=3)-> List[Tuple[str,float]]
    - Purpose: Retrieve messages most semantically similar to a query for the specified user.
    - Returns: A list of tuples: (message_text, similarity_distance)
    - Paramaters:
        - top_k: number of most similar messages to return.
    - Usage: useful for context retrieval or argumnting responses.
    - Notes: Lower distance indicate higher similarity.
    
4. get_context_for_query(user_id:str, query: str, top_k:int=3, recent_window:int=3)->Dict[str, Any]
    - Purpose: Aggregate contextual information for generating responses.
    - Returns: Dictionary with the following keys:
        - "similar": top_k messages from semantic search
        - "recent": most recent recent_window messages
        - "summary": optional one-line user history summary
    - Usuage: use this as context input for AI reasoning or response generation.
    
5. summarize_user_history(user_id: str)->str
    - Purpose: Generate a concise summary of a user's conversation history.
    - Actions:
        - Summarizes past messages into a single line or brief paragraph.
        - Upserts the summary into the `conversation_summaries` table for quick retrieval.
    - Returns: The summary string.
    - Usage: Optional but recommended for improving AI personalization and reducing context lenght.
"""

import os
import time
import asyncio
import logging
from typing import List, Tuple, Dict, Any, Optional

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import register_default_json, Json
from openai import AsyncOpenAI

load_dotenv()
logger = logging.getLogger(__name__)

PG_DB = os.getenv("POSTGRES_DB")
PG_USER = os.getenv("POSTGRES_USER")
PG_PASS = os.getenv("POSTGRES_PASSWORD")
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBED_DIM = 1536  
SUMMARY_TRIGGER_THRESHOLD = 50  

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not set. Embedding calls will fail until it's provided.")
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

def _connect():
    """
    Returns a psycopg2 connection (sync). We call DB work inside asyncio.to_thread
    to avoid blocking the event loop.
    """
    return psycopg2.connect(
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASS,
        host=PG_HOST,
        port=PG_PORT
    )
    
def _ensure_schema_sync():
    sqls=[
        "CREATE EXTENSION IF NOT EXISTS vector;",
        f"""
        CREATE TABLE IF NOT EXISTS chat_history (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL REFERENCES user_vendor_info(user_id) ON DELETE CASCADE,
            message TEXT NOT NULL,
            embedding vector({EMBED_DIM}),
            created_at TIMESTAMP DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS conversation_summaries (
            user_id INT PRIMARY KEY REFERENCES user_vendor_info(user_id) ON DELETE CASCADE,
            summary TEXT,
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """
    ]
    conn = _connect()
    cur = conn.cursor()
    for s in sqls:
        cur.execute(s)
    conn.commit()
    cur.close()
    conn.close()
    logger.info("pgvector schema ensured")
    
def _insert_message_sync(user_id:int, message: str, embedding:List[float]):
    conn=_connect()
    cur=conn.cursor()
    cur.execute(
        "INSERT INTO chat_history (user_id, message, embedding) VALUES (%s, %s, %s)",
        (user_id, message, embedding)
    )
    conn.commit()
    cur.close()
    conn.close()
    
def _search_similar_sync(user_id:int, query_embedding:List[float], top_k:int=3)->List[Tuple[str, float]]:
    conn=_connect()
    cur=conn.cursor()
    cur.execute(
        """
        SELECT message, embedding <=> %s AS distance
        FROM chat_history
        WHERE user_id = %s
        ORDER BY embedding <=> %s
        LIMIT %s
        """,
        (query_embedding, user_id, query_embedding, top_k)
    )
    rows=cur.fetchall()
    cur.close()
    conn.close()
    return rows

def _fetch_recent_sync(user_id: int, limit:int=3)-> List[Tuple[int, str]]:
    conn=_connect()
    cur=conn.cursor()
    cur.execute(
        "SELECT id, message FROM chat_history WHERE user_id=%s ORDER BY created_at DESC LIMIT %s",
        (user_id, limit)
    )
    rows=cur.fetchall()
    cur.close()
    conn.close()
    return rows

def _get_summary_sync(user_id:int)->Optional[str]:
    conn=_connect()
    cur=conn.cursor()
    cur.execute("SELECT summary FROM conversation_summaries WHERE user_id = %s", (user_id,))
    r= cur.fetchone()
    cur.close()
    conn.close()
    return r[0] if r else None

def _upsert_summary_sync(user_id:int, summary:str):
    conn=_connect()
    cur=conn.cursor()
    cur.execute("""
        INSERT INTO conversation_summaries (user_id, summary, updated_at)
        VALUES (%s, %s, NOW())
        ON CONFLICT (user_id) DO UPDATE SET summary = EXCLUDED.summary, updated_at = NOW()
    """, (user_id, summary))
    conn.commit()
    cur.close()
    conn.close()
    
async def ensure_schema():
    """Call once at startup (await ensure_schema())."""
    await asyncio.to_thread(_ensure_schema_sync)
    
async def embed_text(text:str)-> List[float]:
    """
    Uses OpenAI to create an embedding for `text`.
    Returns list[float].
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not configured")
    try:
        resp= await openai_client.embeddings.create(model=EMBEDDING_MODEL, input=text)
        emb= resp.data[0].embedding
        return emb
    except Exception as e:
        logger.exception("OpenAI embedding failed")
        raise
    
async def store_message(user_id:int, message:str):
    print(f" Storing message for user={user_id}: {message[:50]}...")
    """
    Create embedding and store message+embedding into chat_history.
    This runs DB work in a thread to avoid blocking.
    """
    emb=await embed_text(message)
    await asyncio.to_thread(_insert_message_sync, user_id, message, emb)
    return True


async def search_similar(user_id: int, query: str, top_k: int=3)-> List[Tuple[str, float]]:
    """
    Returns [(message, distance),...] sorted by increasing distance (more similar first).
    """
    q_emb= await embed_text(query)
    rows=await asyncio.to_thread(_search_similar_sync, user_id, q_emb, top_k)
    return rows

async def fetch_recent(user_id: int, window: int=3)-> List[str]:
    rows=await asyncio.to_thread(_fetch_recent_sync, user_id,window)
    messages=[r[1] for r in reversed(rows)]
    return messages

async def get_summary(user_id: int)-> Optional[str]:
    return await asyncio.to_thread(_get_summary_sync, user_id)

async def upsert_summary(user_id: int, summary: str):
    return await asyncio.to_thread(_upsert_summary_sync, user_id, summary)

async def summarize_user_history(user_id: int, sample_limit: int=50)-> str:
    """
    Optional: build a compact summary of user's recent history by asking the OpenAI model
    to summarize the last N messages. Upserts into conversation_summaries.
    """
    recent=await fetch_recent(user_id, window=sample_limit)
    if not recent:
        return ""
    text_to_summarize="\n\n".join(recent[-sample_limit:])
    system=(
        "You are a summarizer that extracts a short (2-3 sentences) memory summary"
        "from chat messages. keep it concise, factual, and useful for future retrieval."
    )
    try: 
        resp=await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content": system},
                {"role":"user","content":f"Summarize the following messages into a short memory:\n \n {text_to_summarize}"}
            ],
            temperature=0.0,
            max_tokens=200
        )
        summary=resp.choices[0].message.content.strip()
        await upsert_summary(user_id, summary)
        return summary
    except Exception:
        logger.exception ("Failed to summarize user history")
        return ""
    
async def get_context_for_query(user_id:int, query:str, top_k: int=3, recent_window: int=3)->Dict[str, Any]:
    """
    Return:
    {
        "similar":[{"message": ..., "distance": ...}, ...],
        "recent":[ ... ],
        "summary": "..." or None    
    }
    """
    
    sim_task=asyncio.create_task(search_similar(user_id, query, top_k=top_k))
    recent_task=asyncio.create_task(fetch_recent(user_id, window=recent_window))
    summary_task=asyncio.create_task(get_summary(user_id))
    
    similar_rows= await sim_task
    recent_msgs=await recent_task
    summary=await summary_task
    
    similar=[{"message":r[0], "distance":float(r[1])} for r in similar_rows]
    return {"similar":similar, "recent":recent_msgs, "summary":summary}