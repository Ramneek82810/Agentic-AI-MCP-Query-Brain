import json
import logging
from typing import List,Dict
from models.schemas import ChatMessage

logger=logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def format_chat_history(history:List[Dict[str,str]])->str:
    """
    Converts list of ChatMessage dicts to a clean string format for prompt injection.
    """
    formatted=[]
    for message in history:
        formatted.append(f"{message['role'].capitalize()}:{message['content']}")
    return "\n".join(formatted)

def truncate_history(history:List[Dict[str,str]],max_tokens:int=2000)->List[Dict[str,str]]:
    """
    Naively truncates the oldest messages from the history to fit within token limits.
    """
    truncated=[]
    token_count=0
    for message in reversed(history):
        content_length=len(message['content'].split())
        if token_count+content_length>max_tokens:
            break
        truncated.insert(0,message)
        token_count+=content_length
    return truncated

def build_prompt(prompt_template:str,user_query:str,history:str,tool_description:str="")->str:
    """
    Injects all variables in to the final prompt to send to OpenAI agent.
    """
    return prompt_template.format(
        history=history,
        user_query=user_query,
        tool_description=tool_description
    )
    
def log_tool_usage(tool_name:str,input_text:str,output_text:str):
    """
    Log tool usage for debugging or monitoring.
    """
    logger.info(f"[Tool Used] {tool_name}")
    logger.info(f"Input: {input_text}")
    logger.info(f"Output: {output_text}")
    
def serialize_chat_message(role:str,content:str)->Dict[str,str]:
    """
    Returns a serialized chat message dictionary.
    """
    return {
        "role":role,
        "content":content
    }