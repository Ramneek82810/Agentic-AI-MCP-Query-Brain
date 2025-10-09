import os
import json
import time
import uuid
import logging
from typing import Optional, List, Dict, Any

import redis.asyncio as aioredis

logger=logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
REDIS_KEY_PREFIX = os.getenv("REDIS_KEY_PREFIX", "vartopia:")

_redis_client:Optional[aioredis.Redis]=None

async def init_redis_pool(url:str=REDIS_URL)-> aioredis.Redis:
    """
    Initialize and return an aync Redis client. Safe to call repeatedly;
    will reuse a single connection object at module level.
    """
    global _redis_client
    if _redis_client is None:
        logger.info("Initializing Redis client for feedback memory")
        _redis_client= aioredis.from_url(url, decode_responses=True)
        
        try:
            await _redis_client.ping()
        except Exception as e:
            logger.exception("Unable to connect to Redis at %s", url)
            raise
    return _redis_client

def _user_messages_zkey(user_id:str)->str:
    return f"{REDIS_KEY_PREFIX} user{user_id}:message"

def _message_hash_key(message_id:str)->str:
    return f"{REDIS_KEY_PREFIX} message:{message_id}"

async def store_message(
    user_id:str,
    role:str,
    content:str,
    metadata: Optional[Dict[str,Any]]=None,
)->str:
    """
    Store a single message for a user.
    - role:"user" or "assistant" or "system"
    - content : raw text
    - metadata: optional dict (eg. channel, request_id)
    Returns message_id (UUID).
    """
    r= await init_redis_pool()
    message_id=str(uuid.uuid4())
    ts= time.time()
    
    message_key= _message_hash_key(message_id)
    record={
        "user_id":user_id,
        "role":role,
        "content":content,
        "timestamp":str(ts),
        "feedback":"",
        "score":"",
        "metadata":json.dumps(metadata or {})
    }
    
    pipe= r.pipeline()
    pipe.hset(message_key, mapping=record)
    pipe.zadd(_user_messages_zkey(user_id),{message_id: ts})
    await pipe.execute()
    
    logger.debug("Stored message %s for user %s", message_id, user_id)
    return message_id

async def add_feedback(message_id: str, feedback:str, score:Optional[int]=None)->None:
    """
    Attach feedback to an existing message.
    - feedback: arbitrary text like "like", "dislike", "typo", "clarify", or longer freeform
    - score: optional interger rarting
    Raises valueError if message does not exist.
    """
    r= await init_redis_pool()
    message_key=_message_hash_key(message_id)
    exists= await r.exists(message_key)
    if not exists:
        logger.warning("Attempeted to add feedback to non-existent message %s", message_id)
        raise ValueError("message_id not found")
    
    fields={"feedback": feedback}
    if score is not None:
        fields["score"]=str(score)
    await r.hset(message_key, mapping=fields)
    logger.debug("Added feedback to message %s: %s (score=%s)", message_id, feedback, score)
    
async def get_user_messages(user_id: str, limit:int=100, reverse:bool=False)-> List[Dict[str, Any]]:
    """
    Retrieve up to `limit` messages for a user.
    - reverse = False => older-first, reverse = True => newest-first
    Returns a list of message dicts with parsed metadata.
    """
    r = await init_redis_pool()
    zkey= _user_messages_zkey(user_id)
    if reverse:
        message_ids= await r.zrevrange(zkey, 0, limit - 1)
    else:
        message_ids= await r.zrange(zkey, 0, limit -1 )
        
    if not message_ids:
        return []
    
    pipe= r.pipeline()
    for mid in message_ids:
        pipe.hgetall(_message_hash_key(mid))
    raw_results= await pipe.execute()
    
    out: List[Dict[str, Any]]=[]
    for mid, raw in zip(message_ids, raw_results):
        if not raw:
            continue
        item={
            "message_id": mid,
            "user_id": raw.get("user_id"),
            "role": raw.get("role"),
            "content": raw.get("content"),
            "timestamp": float(raw.get("timestamp")) if raw.get("timestamp") else None,
            "feedback": raw.get("feedback") or None,
            "score": int(raw.get("score")) if raw.get("score") else None,
            "metadata": json.loads(raw.get("metadata")) if raw.get("metadata") else {},
        }
        out.append(item)
    return out

async def delete_user_messages(user_id:str)-> int:
    """
    Remove all stored messages for a user. Returns number of deleted messages.
    Useful for GDPR / user reset flows.
    """
    r= await init_redis_pool()
    zkey=_user_messages_zkey(user_id)
    message_ids= await r.zrange(zkey, 0, -1)
    if not message_ids:
        return 0
    
    pipe= r.pipeline()
    for mid in message_ids:
        pipe.delete(_message_hash_key(mid))
    
    pipe.delete(zkey)
    await pipe.execute()
    
    logger.info("Deleted %d messages for user %s", len(message_ids), user_id)
    return len(message_ids)

async def update_message_content(message_id: str ,new_content: str)-> None:
    """
    Replace message content(useful for moderation or cleaning).
    """
    r=await init_redis_pool()
    message_key= _message_hash_key(message_id)
    exists= await r.exists(message_key)
    
    if not exists:
        raise ValueError("message_id not found")
    
    await r.hset(message_key, mapping={"content":new_content})
    logger.debug("Updated content for message %s", message_id)

def get_redis_client_sync()-> aioredis.Redis:
    """
    Returns the underlying redis client objects (may be None if not init'd).
    use init_redis_pool() first in async startup hooks.
    """
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized; call init_redis_pool() in startup")
    return _redis_client

async def store_feedback_score(user_id: str, message_id:str, score: int):
    """
    Store a feedback score (1-5) for a specific message in Redis.
    """
    r= await init_redis_pool()
    key= f"{REDIS_KEY_PREFIX} feedback:{user_id}:{message_id}"
    try:
        await r.hset(key, mapping={"score":str(score)})
        return True
    except Exception as e:
        logger.exception("Failed to store feedback score")
        return False

###
async def get_last_message_id(
    user_id:str,
    filter_role:Optional[str]=None,
    filter_type:Optional[str]=None
)-> Optional[str]:
    """
    Get the lastest message ID for a user.
    Optionally filter by role (assistant/user) or metadata type (e.g., 'sql').
    """
    messages= await get_user_messages(user_id, limit=50, reverse=True)
    for msg in messages:
        if filter_role and msg["role"] != filter_role:
            continue
        if filter_type and msg["metadata"].get("type")!=filter_type:
            continue
        return msg["message_id"]
    return None


async def provide_feedback(
    user_id: str,
    message_id: str,
    feedback_text: str,
    score: int = None
) -> None:
    """
    Attach feedback to a previously stored assistant message.
    This allows the agent to "learn" from user corrections or ratings.
    """
    from services.feedback_memory import add_feedback
    await add_feedback(message_id=message_id, feedback=feedback_text, score=score)

__all__=[
    "init_redis_pool",
    "store_message",
    "add_feedback",
    "get_user_messages",
    "delete_user_messages",
    "update_message_content",
    "get_redis_client_sync",
]