import redis
import json
import os
import socket
from typing import List, Dict,Optional, Any
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()

class MCPMemoryManager:
    MAX_HISTORY=5
    
    def __init__(self, redis_url=None):
        def can_resolve(host):
            try:
                socket.gethostbyname(host)
                return True
            except:
                return False

        redis_host = os.getenv("REDIS_HOST", "mcp_redis")
        if not can_resolve(redis_host):
            logger.warning(f"[MCPMemoryManager] Host '{redis_host}' not found, falling back to 'localhost'")
            redis_host = "localhost"

        redis_port = os.getenv("REDIS_PORT", "6379")
        redis_url = redis_url or f"redis://{redis_host}:{redis_port}"

        logger.info(f"[MCPMemoryManager] Connecting to Redis at {redis_url}")
        try:
            self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()  # Test connection
            logger.info("[MCPMemoryManager] Redis connection successful")
        except redis.RedisError as e:
            logger.error(f"[MCPMemoryManager] Redis connection failed: {e}")
            self.redis = None

    def add_message(self, user_id: str, role: str, content: str):
        """
        Add a message to user's history and keep only last N messages.
        """
        if self.redis:
            message = {"role": role, "content": content}
            key = f"user:{user_id}:history"
            self.redis.rpush(key, json.dumps(message))
            self.redis.ltrim(key,-self.MAX_HISTORY,-1)
        else:
            logger.warning(f"[MCPMemoryManager] Skipped adding message — Redis unavailable.")

    def get_history(self, user_id: str) -> List[Dict[str, str]]:
        """
        Get last N messages for the user.
        """
        if self.redis:
            key = f"user:{user_id}:history"
            messages = self.redis.lrange(key, 0, -1)
            return [json.loads(m) for m in messages]
        else:
            logger.warning(f"[MCPMemoryManager] Redis unavailable — returning empty history.")
            return []

    def clear_history(self, user_id: str):
        """
        Clear user's conversation history.
        """
        if self.redis:
            key = f"user:{user_id}:history"
            self.redis.delete(key)
        else:
            logger.warning(f"[MCPMemoryManager] Skipped clearing history — Redis unavailable.")

    def get_last_user_fields(self,user_id:str)->Optional[Dict[str,Any]]:
        """
        Retrieve last known fields provided by the user.
        """
        if not self.redis:
            return None
        key=f"user:{user_id}:last_fields"
        data=self.redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    def set_last_user_field(self,user_id:str,fields:Dict[str,Any]):
        """
        Replace last fields with given data.
        """
        if not self.redis:
            return None
        key=f"user:{user_id}:last_fields"
        self.redis.set(key,json.dumps(fields))
        
    def update_last_fields(self, user_id: str,new_fields: Dict[str,Any]):
        """
        Merge new fields with existing ones (partial update).
        """
        if not self.redis:
            return None
        existing=self.get_last_user_fields(user_id) or {}
        existing.update(new_fields)
        self.set_last_user_field(user_id, existing)
        
    def clear_last_fields(self,user_id:str):
        """
        Clear stored user fields.
        """
        if self.redis:
            key=f"user:{user_id}:last_fields"
            self.redis.delete(key)
     
    def get_missing_fields(self,user_id:str, required_fields:List[str])->List[str]:
        """
        Check which required fields are missing for the user.
        Example: required_fields=["user_id","user_name","email"]
        """       
        last_fields=self.get_last_user_fields(user_id)or {}
        missing=[f for f in required_fields if f not in last_fields or not last_fields[f]]
        return missing