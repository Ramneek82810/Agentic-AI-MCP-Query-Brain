from pydantic import BaseModel, Field
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str
    content: str

class QueryRequest(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    messages: List[ChatMessage] = Field(..., description="List of messages in OpenAI format")
    use_memory: bool = Field(..., description="Whether to use memory context or not")

class QueryResponse(BaseModel):
    answer: str
    thought_process: Optional[str] = None
    sql_query: Optional[str] = None
    sources: Optional[List[str]] = None
    tool_used:Optional[str]=None
    message_id: Optional[str]=None

class MemoryHistory(BaseModel):
    user_id: str
    history: List[ChatMessage]

class ToolMetadata(BaseModel):
    name: str
    description: str

class ToolExecutionLog(BaseModel):
    tool_name: str
    input_query: str
    output: str

class SimpleQueryRequest(BaseModel):
    text: str
