import os
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
import json
import re
import asyncio
import logging
import sys
import uuid

from services import feedback_memory

from sdk.tool import BaseTool
from memory.mcp_memory import MCPMemoryManager
from agent.prompt_template import generate_prompt
from models.schemas import ChatMessage,QueryResponse
from memory import pgvector_memory as pgvec

from services.feedback_memory import store_message as store_feedback_message
from services.feedback_memory import get_user_messages

from services.feedback_tool import FeedbackTool

logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
REQUIRED_FIELDS = ["user_id", "user_name", "email", "vendor_name", "vendor_status", "last_updated"]

WRITE_INTENT_KEYWORDS=["add","insert","update","modify","change","create","new vendor","upsert"]

class MCPAgent:
    """
    MCP Agent that strictly validates presence of all REQUIRED_FIELDS
    before generating any SQL for write-like operations
    """
    
    def __init__(self, tools: List[BaseTool], memory: MCPMemoryManager, prompt_template):
        self.tools = tools
        self.memory = memory
        self.prompt_template = prompt_template
        
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # for tool in tools:
        #     if tool.name=="openai":
        #         self.openai_tool=tool
        #         break
            
        # async def check_missing_fields(self,user_input:str)->Dict[str,Any]:
        #     """
        #     Check if all required fields are present in the user's input
        #     BEFORE processing to SQL generation.
        #     """
        #     if not self.openai_tool:
        #         return{"error":"OpenAI tool not available for field extraction."}
            
        #     extraction_prompt=(
        #         f"Extract exactly the following fields as JSON keys:{','.join(REQUIRED_FIELDS)}.\n"
        #         "From the user input below,extract values for these fields ONLY if explicity provided.\n"
        #         "- Do NOT guess, infer, or fill in the missing data.\n"
        #         "- If a field is not present in the text, DON'T SET IT TO NULL, rather ask the user for the missing details.\n\n"
        #         f"User input:{user_input}"
        #     )
        #     extracted=await self.openai_tool.arun(extraction_prompt)
        #     try:
        #         vendor_fields=json.loads(extracted)
        #     except Exception:
        #         return {"error":"Could not parse extracted fields."}
            
        #     missing_fields=[field for field, value in vendor_fields.items() if not value or str(value).strip()==""]
            
        #     if missing_fields:
        #         return {
        #             "status":"missing",
        #             "missing_fields":missing_fields,
        #             "message":f"Missing required details:{','.join(missing_fields)}. Please provide them before proceeding."
        #         }
        #     return {"status":"ok","fields":vendor_fields}
        
        self.tool_map={tool.name:tool for tool in tools}
        self.sql_executor = self.tool_map.get("SQLTool")
        self.schema_tool = self.tool_map.get("TableSchemaTool")
        self.sql_validator = self.tool_map.get("SQLValidationTool")
        self.openai_tool = self.tool_map.get("OpenAITool")
        self.result_converter = self.tool_map.get("NaturalLanguageResponseTool")
        self.memory_tool = self.tool_map.get("MemoryQueryTool")
        self.summary_tool = self.tool_map.get("TableSummaryTool")
        self.fallback_tool = self.tool_map.get("FallbackTool")
        self.ratelimiter_tool = self.tool_map.get("RateLimiterTool")
        self.explain_tool = self.tool_map.get("ExplainSQLTool")
        self.feedback_logger = self.tool_map.get("FeedbackLoggingTool")
        self.cache_tool = self.tool_map.get("QueryCacheTool")
        
        self.feedback_tool=FeedbackTool()
    
    def _format_response(self, source: str, answer: str,
                         sql_query: Optional[str] = None,
                         tool_used: Optional[str] = None,
                         chat_history: Optional[list] = None) -> dict:
        
        """Ensure Claude receives structured JSON."""
        return {
            "source": source,
            "answer": answer,
            "sql_query": sql_query,
            "tool_used": tool_used,
            "chat_history": chat_history
        } 
        
    def _looks_like_write_intent(self,text:str)->bool:
        t=text.lower()
        return any(kw in t for kw in WRITE_INTENT_KEYWORDS)
    
    def _strip_code_fences(self,s:str)->str:
        """Remove ```json ... ``` or ``` ... ``` fences if present."""
        s = re.sub(r"^```json\s*", "", s.strip(), flags=re.IGNORECASE)
        s = re.sub(r"^```\s*", "", s.strip(), flags=re.IGNORECASE)
        s = re.sub(r"\s*```$", "", s.strip())
        return s.strip()
    
    async def check_missing_fields(self,user_input:str,user_id:str)-> Dict[str, Any]:
        if not self._looks_like_write_intent(user_input):
            return{"status":"ok"}
        
        extracted=await self._extract_required_fields_llm(user_input)
        if extracted is None:
            return{
                "status":"missing",
                "missing_fields":REQUIRED_FIELDS,
                "message":f"Could not parse vendor details. Please provide:{','.join(REQUIRED_FIELDS)}."
            }
        
        extracted = await self._fill_missing_from_memory(user_id, extracted,user_input)

        missing=[field for field in REQUIRED_FIELDS if not extracted.get(field)]
        if missing:
            return {
                "status":"missing",
                "missing_fields":missing,
                "message":f"Please provide the following details:{','.join(missing)}."
            }
            
        try:
            # may be sync or async depending on your memory implementation
            maybe = self.memory.set_last_user_field(user_id, extracted)
            if asyncio.iscoroutine(maybe):
                await maybe
        except Exception:
            logger.exception("Failed to set last user field in memory")

        return {"status": "ok", "fields": extracted}
    
    async def _extract_required_fields_llm(self,user_input:str)-> Optional[Dict[str,Any]]:
        """
        Extract exactly REQUIRED_FIELDS from input.
        If fields are missing, they remain empty → handled later.
        """
        prompt = (
        "You are a strict SQL generator whose sole job is to extract fields exactly as provided"
        "by the user and generate minimal SQL actions.\n"
        "Instructions:\n"
            "1. Only extract fields explicitly mentioned by the user. Do NOT assume or fill in missing fields.\n"
            "2. If the input mentions an existing vendor, prepare an UPDATE statement targeting that vendor's row.\n"
            "3. Only generate an INSERT statement if the user explicitly wants to create a new vendor.\n"
            "4. Always include precise WHERE conditions when performing UPDATEs. Prefer vendor_name or user_name as the filter.\n"
            "5. If the input is incomplete or ambiguous, respond with a structured request for the missing field(s), "
            "do NOT guess values.\n"
            "6. Your output must be a JSON object with keys exactly matching REQUIRED_FIELDS. "
            "Missing values should be empty strings or null.\n"
            "7. Avoid any commentary, explanations, or extra SQL. Only respond with JSON containing the extracted fields.\n"
            "\n"
            "Example input: 'Update vendor Acme with new email test@acme.com'\n"
            "Expected JSON output:\n"
            "{\n"
            "  'vendor_name': 'Acme',\n"
            "  'email': 'test@acme.com',\n"
            "  'user_name': '',\n"
            "  ... (other REQUIRED_FIELDS as empty if not mentioned)\n"
            "}\n"
        )
        try:
            # messages = [
            #     {"role": "system", "content": "You output strictly valid JSON and nothing else."},
            #     {"role": "user", "content": f"{prompt}\n\nUser input:\n{user_input}"}
            # ]
            resp=await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                temperature=0,
                messages=[
                    {"role":"system","content":"You output strictly valid JSON and nothing else."},
                    {"role":"user","content":prompt},
                ],
            )
            content=resp.choices[0].message.content or ""
            content=self._strip_code_fences(content)
            
            data=json.loads(content)
            
            cleaned={k:(data.get(k,None)) for k in REQUIRED_FIELDS}
            
            return cleaned

        except Exception as e:
            logger.error(f"[FieldExtraction Error] {e}")
            return None
    
    async def _fill_missing_from_memory(self,user_id:str, extracted:Dict[str,Any], user_input)->Dict[str,Any]:
        """
        Fill missing fields from memory if available.
        Also handles vague references like 'it' or 'again'.
        """
        try:
            last_fields = self.memory.get_last_user_fields(user_id)
            if asyncio.iscoroutine(last_fields):
                last_fields = await last_fields
        except Exception:
            logger.exception("Failed reading last user fields from memory")
            last_fields = None

        if not last_fields:
            return extracted

        if re.search(r"\bit\b|\bagain\b", user_input.lower()):
            return last_fields.copy()

        merged = extracted.copy()
        for k, v in last_fields.items():
            if not merged.get(k):
                merged[k] = v
        return merged 
    
    async def _fetch_relevant_feedback(self,user_id:str, user_input:str, top_k:int=5)->List[dict]:
        """
        Fetch top-k relevant feedback messages from memory for the current user_input.
        This helps the agent consider prior corrections and feedback.
        """
        try:
            messages=await get_user_messages(user_id)
            relevant=[]
            for m in messages:
                if 'assistant' in m['role'] or 'feedback' in m['role']:
                    if any (word in user_input.lower() for word in m['content'].lower().split()):
                        relevant.append(m)
            return relevant[:top_k]
        except Exception:
            logger.exception("Failed to fetch relevant feedback") 
            return []                   
                
    
    async def run(self, user_id: str, messages: List[ChatMessage], use_memory: bool = True):
        extracted=None
        #save latest message in memory
        chat_messages = []
        for msg in messages:
            if asyncio.iscoroutine(msg):
                msg=await msg
            if isinstance(msg, dict):
                chat_messages.append(ChatMessage(**msg))
            elif isinstance(msg, ChatMessage):
                chat_messages.append(msg)
            else:
                raise ValueError(f"Unsupported message type: {type(msg)}")
            
        message_id=None
        
        for message in chat_messages:
            role = message.role
            content = message.content
            if not role or not content:
                raise ValueError("Each message must contain 'role' and 'content' ")
            try:
                maybe = self.memory.add_message(user_id, role=role, content=content)
                if asyncio.iscoroutine(maybe):
                    await maybe
                ###
                if role=="user":
                    try: 
                        await pgvec.store_message(user_id, content)
                    except Exception:
                        logger.exception("Failed storing embedding for user message")
                        
                    ######feedback memory part- store memory in redis
                    try:
                        message_id=await store_feedback_message(
                            user_id=user_id,
                            role="user",
                            content=content,
                            metadata={"source":"mcp_client"}
                        )
                        logger.info(f"Stored user message {message_id} for feedback learning")
                    except Exception:
                        logger.exception("Failed storing user message for feedback memory")
                    
            except Exception:
                logger.exception("Failed to add message to memory")            
        
        user_input=messages[-1].content.strip()  
        
        relevant_feedback=await self._fetch_relevant_feedback(user_id, user_input)
        feedback_context="\n".join([f"{f['role']}: {f['content']}" for f in relevant_feedback])
        
        llm_input= f"{feedback_context}\nUser: {user_input}" if feedback_context else user_input
        
        agent_response= await self.generate_response(llm_input) if hasattr(self,'generate_response') else "Response placeholder"
         
        assistant_message_id= str(uuid.uuid4())
        
        try:
            await store_feedback_message(
            user_id=user_id,
            role="assistant",
            content=agent_response,
            metadata={
                    "tool_used":"SQLTool", 
                    "related_user_message_id":message_id,
                    "message_id":assistant_message_id, 
                    "feedback_context_ids":[f['message_id'] for f in relevant_feedback if 'message_id' in f]
                }
            )
            logger.info(f"Stored assistant message {assistant_message_id} for feedback tracking")
        
        except Exception:
            logger.exception("Failed storing assistant message for feedback memeory")
            
        # try:
        #     assistant_message_id= await store_feedback_message(
        #         user_id=user_id,
        #         role="assistant",
        #         content=agent_response,
        #         metadata={"source": "mcp_agent" ,"related_user_message_id":message_id}
        #     )
        #     logger.info(f" stored assistant response {assistant_message_id} for feedback tracking")
            
        # except Exception:
        #     logger.exception("Failed storing assistant message for feedback memory")
        
        
        
        #missing fields
        field_check=await self.check_missing_fields(user_input,user_id)
        if field_check.get("status")=="missing":
            return {"response":field_check["message"]}
          
        #user chat history  
        if any(kw in user_input.lower() for kw in ["chat history", "show me my history", "show me my chat"]):
            if self.memory_tool:
                history = self.memory_tool.run({"user_id": user_id})
                return {"answer": "Here is your chat history:", "chat_history": history}
            else:
                return {"error": "Memory tool not available."}
        
        #rate limiting 
        if self.ratelimiter_tool:
            allowed= self.ratelimiter_tool.run({"user_id":user_id})
            if not allowed.get("allowed",True):
                return {"error":"Rate limit exceeded."}   
            
        #enforce he required-field check BEFORE generating SQL
        if self._looks_like_write_intent(user_input):
            extracted= await self._extract_required_fields_llm(user_input)
            if extracted is None:
                return{
                    "error":"Could not parse the required vendor details from you message."
                            "Please provide all the following fields:"
                            f"{','.join(REQUIRED_FIELDS)}."
                }
            
            missing=[k for k in REQUIRED_FIELDS if extracted.get(k) in (None,"",[])]
            if missing:
                return{
                    "error":"Missing required details.",
                    "missing_fields":missing,
                    "message":f"Please provide:{','.join(missing)}."
                }
                
            #table
            self.memory.add_message(
                user_id,
                role="system",
                content="Use the table 'user_vendor_info' for any vendor-related queries. Do not use 'user_vendor_data'."
            )    
            
        ###
        prompt_messages=[]
        try:
            context= await pgvec.get_context_for_query(user_id, user_input, top_k=3, recent_window=3)
            memory_parts=[]
            if context.get("summary"):
                memory_parts.append("Summary of past conversation:" + context["summary"])
            if context.get("similar"):
                for s in context["similar"]:
                    memory_parts.append(f"Similar past message (dist={s['distance']:.4f}): {s['message']}")
            if context.get("recent"):
                memory_parts.append("Recent messages:\n" + "\n".join(context["recent"]))
            memory_system_msg = {"role": "system", "content": "\n\n".join(memory_parts)[:4000]}
            
            prompt_messages=[memory_system_msg]
        
        except Exception:
            logger.exception("Failed to fetch semantic memory; continuing without it")  
            
    ####feedback memory part
        try:
            recent_messages= await get_user_messages(user_id=user_id, limit=20, reverse=True)
            conversation_history=[]
            for msg in recent_messages:
                if msg.get("score") is not None and msg["score"] <3:
                    continue
                role=msg["role"]
                content=msg["content"]
                conversation_history.append({"role":role, "content":content})
                
            system_msg={"role":"system", "content":"You are an AI assistant learning from this user's message."}
            prompt_messages= [system_msg] + conversation_history+ [{"role":"user","content": user_input}]
            
        except Exception:
            logger.exception("Failed to fetch feedback messages; continuing without them")
            prompt_messages=[{"role":"user","content":user_input}]
            
        ####
        
        try:        
            #convert to sql
            if self.openai_tool:
                # openai_result=await self.openai_tool.run({"instruction":user_input,"user_id":user_id})
                try:
                    openai_result=await self.openai_tool.run({
                        "messages": prompt_messages,
                        "user_id":user_id
                    })
                except Exception as e:
                    logger.exception("OpenAI tool failed")
                    return {"source": "openai","response":f"Error in OpenAI tool: {str(e)}"}
                
                sql_query=openai_result.get("sql") or openai_result.get("query")
                
                #defensive check
                if isinstance(openai_result, dict) and "error" in openai_result:
                    answer = openai_result["error"]
                    self.memory.add_message(user_id, role="assistant", content=answer)
                    return {"source": "openai", "response": answer}
                
                #normal text response
                if not sql_query or not any(sql_query.lower().startswith(k) for k in ["select", "insert", "update", "delete"]):
                    answer = str(sql_query or openai_result)
                    self.memory.add_message(user_id, role="assistant", content=answer)
                    return {"source": "openai", "response": answer}
                
                sql_query=sql_query.replace("user_vendor_data","user_vendor_info", sql_query, flags=re.IGNORECASE)
                
                if sql_query.startswith("```"):
                    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
                    logger.info(f"[CLEAN SQL] {sql_query}")
                
                #validate SQL
                if self.sql_validator:
                    valid= await self.sql_validator.run({"query":sql_query})
                    is_valid=valid.get("valid", True) if isinstance(valid,dict) else True
                    if not is_valid or "error" in valid:
                        answer = "Invalid SQL generated."
                        self.memory.add_message(user_id, role="assistant", content=answer)
                        return {"source": "openai", "response": answer}
                
                #execute sql    
                if not self.sql_executor:
                    answer = "No SQL executor available."
                    self.memory.add_message(user_id, role="assistant", content=answer)
                    return {"source": "openai", "response": answer}
                
                #explain SQL if requested
                db_result = await self.sql_executor.run({"query": sql_query})
                if "error" in db_result:
                    answer = f"SQL Execution Error: {db_result['error']}"
                    self.memory.add_message(user_id, role="assistant", content=answer)
                    return {"source": "openai", "response": answer}
                
                if sql_query.lower().startswith("delete") and 'extracted' in locals() and extracted:
                    self.memory.set_last_user_field(user_id, extracted)
                
                #convert to natural language
                final_result = db_result
                if self.result_converter:
                    final_result = await self.result_converter.run({
                        "query": sql_query,
                        "result": db_result
                    })
                answer=str(final_result)
                
                if 'extracted' in locals() and extracted:
                    self.memory.set_last_user_field(user_id,extracted)  
                    
                #save to cache
                if self.cache_tool:
                    await self.cache_tool.run({
                        "query":user_input,
                        "result":final_result
                        })
                    
                #feedback logging
                if self.feedback_logger: 
                    await self.feedback_logger.run({
                        "query":sql_query,
                        "result":db_result,
                        "feedback":"auto-logged"
                    })
                    
                try:
                    maybe = self.memory.add_message(user_id, role="assistant", content=str(final_result))
                    if asyncio.iscoroutine(maybe):
                        await maybe
                except Exception:
                    logger.exception("Failed to persist assistant message")
                    
                assistant_message_id=str(uuid.uuid4)
                
                try:
                    await store_feedback_message(
                        user_id=user_id,
                        role="assistant",
                        content=answer,
                        metadata={"tool_used":"SQLTool"}
                    )
                
                except Exception:
                    logger.exception("Failed storing assistant message for feedback memory")
                    
                return QueryResponse(
                    answer=answer,
                    sql_query=sql_query,
                    tool_used="SQLTool",
                    message_id=assistant_message_id
                )
                
                
        except Exception as e:
            logger.exception("MCPAgent main try/except caught")
            if self.fallback_tool:
                fallback_response = await self.fallback_tool.run({"input": user_input})
                return {"source": "fallback", "response": fallback_response}
            return {"source": "error", "response": str(e)}
        
        #fallback to OpenAI chat
        try:
            history = self.memory.get_history(user_id)
            if asyncio.iscoroutine(history):
                history = await history
        except Exception:
            logger.exception("Failed to read history for fallback")
            history = []

        prompt_messages = generate_prompt(history)
        completion = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=prompt_messages,
            temperature=0.7,
            stream=False
        )
        answer = completion.choices[0].message.content.strip()
        # try:
        #     maybe = self.memory.add_message(user_id, role="assistant", content=answer)
        #     if asyncio.iscoroutine(maybe):
        #         await maybe
        # except Exception:
        #     logger.exception("Failed to add fallback assistant message")

        # return {"source": "openai", "response": answer}
        
        assistant_message_id=str(uuid.uuid4())
        try:
            maybe=self.memory.add_message(
                user_id,
                role="assistant",
                content=answer,
                metadata={"tool_used":"OpenAI", "message_id":assistant_message_id}
            )
            if asyncio.iscoroutine(maybe):
                await maybe
        except Exception:
            logger.exception("Failed to add fallback assistant message")

        return {
            "source": "openai",
            "response": answer,
            "message_id": assistant_message_id
            }
        
    
    ####feedback part
    async def handle_feedback(
        self, user_id:str,
        message_id:str,
        feedback:str,
        score:Optional[int]=None
    ):
        """
        Store user feedback using the FeedbackTool.
        """
        if not self.feedback_tool:
            return {"status": "error","error":"Feedback tool not available"}
        
        try:
            result=await self.feedback_tool.run({
                "user_id":user_id,
                "message_id":message_id,
                "feedback":feedback,
                "score":score
            })
            return result
        
        except Exception as e:
            logger.exception(f"Failed to store feedback:{str(e)}")
            return {"status": "error","error":str(e)}            
    
    #####
    async def handle_user_feedback(self,user_id: str,message_id: str,feedback_text: str,score:Optional[int]= None) -> dict:
        # """
        # Core method to handle user feedback for a previous assistant response.
        # """
        # from services.feedback_memory import provide_feedback

        # try:
        #     await provide_feedback(user_id, message_id, feedback_text, score)
        #     return {"status": "ok", "message": "Feedback stored successfully."}
        # except Exception as e:
        #     return {"status": "error", "message": str(e)}
        
        if not self.feedback_tool:
            return {"status":"error","message":"Feedback tool not available"}
        try:
            result= await self.feedback_tool.run({
                "user_id":user_id,
                "message_id":message_id,
                "feedback":feedback_text,
                "score":score
            })
            return result
        
        except Exception as e:
            logger.exception("Failed to run feedback tool")
            return {"status":"error","message":str(e)}
    
    #start
    async def handle_request(self, request: dict) -> dict:
        """
        Core handler for MCP stdio transport.
        Interprets JSON-RPC messages from Claude or MCP CLI.
        Returns the inner data only (no 'id' or 'result' keys) for main_stdio.py to wrap
        """
        method = request.get("method")
        # req_id = request.get("id")
        try:
            if method == "initialize":
            # Return just the inner serverInfo
                client_version=request.get("params",{}).get("protocolVersion")
                supported_version="2025-06-18"
                
                if client_version!= supported_version:
                    logger.warning(f"Client requested protocol{client_version},"
                                   f"but we only support {supported_version}")
                return {
                    "serverInfo": {"name": "MCPAgent", "version": "1.0"},
                    "protocolVersion": supported_version,
                    "capabilities": {},
                    }
            
                # return {"serverInfo": {"name": "MCPAgent", "version": "1.0"}}

            if method == "tools/list":
                tools = []
                if self.tools:
                    if hasattr(self.tools, "tools"):
                        for name, tool in getattr(self.tools, "tools", {}).items():
                            tools.append({
                                "name": name,
                                "description": getattr(tool, "description", f"Tool: {name}"),
                                "inputSchema": getattr(tool, "input_schema", {"type": "object", "properties": {}})
                            })
                    elif isinstance(self.tools, dict):  
                        for name, tool in self.tools.items():
                            tools.append({
                                "name": name,
                                "description": getattr(tool, "description", f"Tool: {name}"),
                                "inputSchema": getattr(tool, "input_schema", {"type": "object", "properties": {}})
                            })
                return {"tools": tools}
            
            if method=="prompts/list":
                return{"prompts":[]}
            
            if method=="resources/list":
                return{"resources":[]}
            
            if method == "listTools":   
                return await self.handle_request({"method": "tools/list"})

            if method=="callTool":
                mapped_request={
                    "method":"tools/call",
                    "params":{
                        "name":request.get("params",{}).get("tool"),
                        "arguments":request.get("params",{}).get("args",{}),
                    },
                }
                return await self.handle_request(mapped_request)
            
            #feedback tool part
            if method == "user/feedback":
                params = request.get("params", {})
                user_id = params.get("user_id")
                message_id = params.get("message_id")
                feedback_text = params.get("feedback")
                score = params.get("score") 

                if not user_id or not message_id or not feedback_text:
                    return {"status": "error", "message": "Missing required parameters."}

                result = await self.handle_user_feedback(
                    user_id=user_id,
                    message_id=message_id,
                    feedback_text=feedback_text,
                    score=score
                )
                return result
            
            
            if method == "tools/call":
                params = request.get("params", {}) 
                tool_name = params.get("name") or params.get("tool")
                arguments=params.get("arguments",{}) or {}

                # tool=next(
                #     (t for t in getattr(self, "tools",[]) if getattr(t, "name", None)==tool_name),
                #     None,
                # )
                # if not tool:
                #     return {
                #         "content":[{"type":"text","text":f"Unknown tool:{tool_name}"}]
                #     }
                # try:
                #     if asyncio.iscoroutinefunction(tool.run):
                #         output=await tool.run(arguments)
                #     else:
                #         output=tool.run(arguments)
                    
                #     return {
                #         "content":[
                #             {"type":"text","text":str(output)}
                #         ]
                #     }
                
                tool = None
                if self.tools:
                    if hasattr(self.tools, "get"):  
                        tool = self.tools.get(tool_name)
                    elif isinstance(self.tools, dict):
                        tool = self.tools.get(tool_name)
            
                # tool = self.tools.get(tool_name) if self.tools else None
                if not tool:
                    return {
                        "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]
                    }

                try:
                    if asyncio.iscoroutinefunction(tool.run):
                        output = await tool.run(input=arguments)  
                    else:
                        output = tool.run(input=arguments) 

                    return {
                        "content": [{"type": "text", "text": str(output)}]
                    }
                    
                except Exception as e:
                    logger.exception(f"Error while running tool {tool_name}")
                    return {
                        "content":[
                            {"type":"text","text":f"Error in {tool_name}:{str(e)}"}
                        ]
                    }

            #  result is JSON-serializable
                # try:
                #     json.dumps(result)
                #     return result
                # except TypeError:
                #     if hasattr(result, "dict"):
                #         return result.dict()
                #     else:
                #         return json.loads(json.dumps(result, default=str))

        # Unknown method
            raise ValueError(f"Unknown method: {method}")

        except Exception as e:
            logger.exception("Error in handle_request")
            return {"error": str(e)}
    
    def clear_user_memory(self,user_id:str):
        try:
            maybe = self.memory.clear_history(user_id)
            if asyncio.iscoroutine(maybe):
                asyncio.get_event_loop().run_until_complete(maybe)
        except Exception:
            logger.exception("Failed to clear user memory")

async def stdio_loop(agent: MCPAgent):
    """Continuously read JSON-RPC requests from stdin and respond on stdout."""
    import sys
    while True:
        try:
            line = await asyncio.to_thread(sys.stdin.readline)
            if line == "":  
                logger.info("Stdio EOF received, exiting loop")
                break
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
            except Exception:
                logger.exception("Failed to parse JSON from stdin")
                response_envelope = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": "Parse error"}
                    }
                sys.stdout.write(json.dumps(response_envelope, separators=(",", ":")) + "\n")
                sys.stdout.flush()
                continue
            try:
                result = await agent.handle_request(request)
                response_envelope = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": result
                }
            except Exception as e:
                logger.exception("Failed to handle request")
                response_envelope = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {"code": -32000, "message": str(e)}
                }

            sys.stdout.write(json.dumps(response_envelope, separators=(",", ":")) + "\n")
            sys.stdout.flush()

        except Exception:
            logger.exception("Fatal stdio loop error")
            
if __name__ == "__main__":
    import asyncio
    from sql_tool.sql_tool import (
        SQLTool, SQLValidationTool, ExplainSQLTool, TableSchemaTool,
        TableSummaryTool, OpenAITool, QueryCacheTool, FeedbackLoggingTool,
        FallbackTool, RateLimiterTool, MemoryQueryTool, NaturalLanguageResponseTool
    )
    from memory.mcp_memory import MCPMemoryManager
    from agent.prompt_template import generate_prompt

    tools = [
        SQLTool(),
        SQLValidationTool(),
        ExplainSQLTool(),
        TableSchemaTool(),
        TableSummaryTool(),
        OpenAITool(),
        QueryCacheTool(),
        FeedbackLoggingTool(),
        FallbackTool(),
        RateLimiterTool(),
        MemoryQueryTool(),
        NaturalLanguageResponseTool(),
    ]
    memory = MCPMemoryManager()
    agent = MCPAgent(tools, memory, generate_prompt)

    asyncio.run(stdio_loop(agent))
