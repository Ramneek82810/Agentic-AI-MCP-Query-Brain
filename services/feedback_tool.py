import logging
from typing import Dict, Any, Optional
from services.feedback_memory import store_message, add_feedback, store_feedback_score, get_last_message_id

logger=logging.getLogger(__name__)

FEEDBACK_TOOL_PROMPT="""
You have access to a tool called `FeedbackTool` that allows you to capture user reactions to your responses.

Purpose:
Use this tool to log explicit user feedback about a specific assistant message.This enables continuous learning and refinement of responses based on real user input.

How to use FeedbackTool:
- Always call this tool only after the user explicity provides feedback (positive, negative, or suggestions).
- Input must include"
    - `user_id`: The ID of the user giving feedback.
    - `message_id`: The ID of the assistant message the feedback is about.
    - `feedback`: The free-text feedback provided by the user (e.g., "Too solw", "Very clear", "Need more detail").
    - `score` (optional): A numeric rating if available (e.g., 1-5)
    
Guidelines:
- Never invent feedback yourself - only store what the user provides.
- Always preserve the exact wording of the user's feedback.
- Use the tool as a way to let the system continuously learn and adapt to user preferences.
"""
class FeedbackTool:
    name="FeedbackTool"
    description="Store user feedback for specific assistant messages."
    guidance=FEEDBACK_TOOL_PROMPT,
    input_schema={
        "type":"object",
        "properties":{
            "user_id":{"type":"string"},
            "message_id": {"type": "string"},
            "feedback": {"type": "string"},
            "score": {"type": "integer"},
        },
        "required":["user_id","message_id","feedback"]
    }
    
    async def run(self, input: Dict[str, Any])-> Dict[str, Any]:
        user_id= input.get("user_id")
        message_id=input.get("message_id")
        feedback= input.get("feedback")
        score=input.get("score", None)
        
        if not feedback:
            return {"status":"error","error":"Missing message_id or feedback"}
        
        if message_id=="last_sql_query":
            message_id=await get_last_message_id(
                user_id, filter_role="assistant", filter_type="sql"
            )
            if not message_id:
                return {"status":"error","error":"No proevious SQL message found for user"}
        
        try:
            await add_feedback(message_id, feedback, score)
            logger.info(f"Stored feedback for message {message_id}")
            return {"status": "success","message_id": message_id}
        
        except Exception as e:
            logger.exception("Failed to store feedback")
            return {"status":"error", "error":str(e)}