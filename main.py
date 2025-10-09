from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI,HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional,List
import uvicorn
from dotenv import load_dotenv
import logging
import asyncio
import socket
from pydantic import BaseModel

from sql_tool.sql_tool import OpenAITool, SQLTool, NaturalLanguageResponseTool
from agent.mcp_agent import MCPAgent
from memory.mcp_memory import MCPMemoryManager
from models.schemas import ChatMessage
from agent.prompt_template import generate_prompt
from sdk.tool_router import ToolRouter 
from services.tool_registry import get_available_tools
from mcp_tools import vartopia_tools

from services.feedback_memory import add_feedback

from sdk.tool_router import register_vartopia_tools, ToolRouter

logging.basicConfig(level=logging.INFO)

load_dotenv()

app = FastAPI(title="MCP SQL Agent Server", root_path="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
memory_manager = MCPMemoryManager()
# tools_list = get_available_tools()
# tools = {tool.name: tool for tool in tools_list}
# for tool in tools_list:
#     key = getattr(tool, "id", None) or getattr(tool, "tool_name", None) or str(tool)
#     tools[key] = tool

# vartopia_tools=register_vartopia_tools()
# for t in vartopia_tools:
#     tools[t.name]=t

# tool_router = ToolRouter(tools=tools)


from sdk.tool_router import register_all_tools

tools_list = register_all_tools()  
tool_router=ToolRouter(tools=tools_list)

agent = MCPAgent(
    memory=memory_manager,
    tools=tools_list,
    prompt_template=generate_prompt
    )

class Message(BaseModel):
    role: str
    content: str

class QueryRequestWrapper(BaseModel):
    user_id: str
    messages: List[ChatMessage]
    use_memory: Optional[bool] = True
    
##### Feedback memory
class FeedbackRequest(BaseModel):
    message_id: str
    feedback:str
    score:int=None

#helper function
def extract_sql(text: str) -> str:
    start = text.find("```sql")
    if start == -1:
        return text.strip() 

    start += len("```sql")
    end = text.find("```", start)
    if end == -1:
        return text[start:].strip()

    return text[start:end].strip()


#modify database
async def handle_user_prompt(user_prompt: str,user_id:str) -> str:
    openai_tool = OpenAITool()
    sql_tool = SQLTool()
    nl_tool = NaturalLanguageResponseTool()

    # Generate SQL from user prompt
    response = await openai_tool.run({"instruction": user_prompt})
    raw_sql = response.get("query", "") or response.get("sql") or ""
    raw_sql=raw_sql.strip()

    if not raw_sql:
        return "Sorry, I couldn't generate a query from your prompt."

    sql_query=extract_sql(raw_sql)
    if not sql_query:
        return "Sorry, I couldn't extract a valid SQL query."
    
    command = sql_query.split()[0].lower()

    # Execute INSERT/UPDATE/DELETE queries and return success/error message
    
    COMMAND_MAP = {
        # INSERT
        "insert": "insert",
        "add": "insert",
        "create": "insert",
        "new": "insert",
        "save": "insert",
        "register": "insert",

        # UPDATE
        "update": "update",
        "change": "update",
        "modify": "update",
        "edit": "update",
        "alter": "update",
        "correct": "update",
        "revise": "update",
        "adjust": "update",

        # DELETE
        "delete": "delete",
        "remove": "delete",
        "drop": "delete",
        "erase": "delete",
        "clear": "delete",
        "discard": "delete",
        "eliminate": "delete",

        # SELECT (fetch/fetching data)
        "select": "select",
        "get": "select",
        "fetch": "select",
        "find": "select",
        "show": "select",
        "list": "select",
        "display": "select",
        "retrieve": "select",
        "search": "select",
    }
    normalized_command=COMMAND_MAP.get(command.lower())
    
    if normalized_command in ["insert", "update", "delete"]:
        exec_result = await sql_tool.run({"query": sql_query})
        if "error" in exec_result:
            return f"Failed to execute query: {exec_result['error']}"
        else:
            if command=="insert":
                return "New data has been updated successfully."
            elif command=="update":
                return "Your existing data has been updated successfully."
            elif command=="delete":
                return "The requested data has been deleted successfully."
            
    # Execute SELECT queries and return a natural language summary
    elif command == "select":
        exec_result = await sql_tool.run({"query": sql_query})
        summary = await nl_tool.run(exec_result)
        return summary

    else:
        return None
 
def handle_smalltalk(user_prompt:str)->Optional[str]:
    text=user_prompt.lower().strip()
    if any(word in text for word in ["hi","hello","hey"]):
        return "Hello! How can I assist you today?"
    
    if "thank" in text:
        return "You're welcome!"  
    if any(word in text for word in ["bye","goodbye","see you"]):
        return "Goodbye! Have a great day!"
    if len(text.split())==1 and text.isalpha():
        return "I didn't quite get that. Could you please rephrase?"
    
    return None

#main endpoint
@app.post("/ask_agent")
async def ask_agent(request: Request):
    try:
        data = await request.json()
        logging.info(f"Incoming request: {data}")

        # Check if JSON-RPC (Claude-style)
        if "jsonrpc" in data and "params" in data:
            request_id = data.get("id")
            params = data.get("params", {})
            user_id = params.get("user_id", "default")
            messages = params.get("messages", [])

        # Otherwise assume React frontend format
        else:
            request_id = None
            user_id = data.get("user_id", "default")
            messages = data.get("messages", [])
            
        chat_messages = [ChatMessage(**m) for m in messages]

        # Run the agent
        result_text = await agent.run(
            user_id=user_id,
            messages=chat_messages,
            use_memory=True
        )
        
        # if asyncio.iscoroutine(result):
        #     result =await result

        # Return response in JSON-RPC if Claude frontend
        if request_id is not None:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"response": result_text}
            }

        # Otherwise return simple response for React
        return {"response": result_text} 

        # result = await agent.run(
        #     user_id=query.user_id,
        #     messages=query.messages,
        #     use_memory=query.use_memory
        # )
        # return {"response":result}
    
    except Exception as e:
        logging.error(f"Error in ask_agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# generic mcp tool runner for vartopia tools
@app.post("/run_tool/{tool_name}")
async def run_tool(tool_name:str, request:Request):
    body=await request.json()
    # inputs=body
    
    # user_id=body.get("user_id")
    # action=body.get("action")
    # params=body.get("params",{})
    
    # tool=tools_list.get(tool_name)
    tool=next((t for t in tools_list if t.name==tool_name),None)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool{tool_name} not found")
    
    # if not tool:
    #     raise HTTPException(
    #         status_code=404,
    #         detail={"code":"E_NOT_FOUND", "message":f"Tool '{tool_name} not found"}
    # )
        
    
    # if not user_id:
    #     raise HTTPException(status_code=400, detail="user_id is required")
    # if not action:
    #     raise HTTPException(status_code=400, detail="action is required")

    try:
        if asyncio.iscoroutinefunction(tool.run):
            result=await tool.run(body)
        else:
            result=tool.run(body)

        return {"status": "success", "data": result}
        
    except HTTPException as http_err:
        raise http_err
        
    except Exception as e:
        logging.exception(f"Error running tool {tool_name}")
        raise HTTPException(status_code=500, detail=str(e))

## feedback memory endpoint
@app.post("/feedback")
async def submit_feedback(feedback_request: FeedbackRequest):
    try: 
        await add_feedback(
            message_id=feedback_request.message_id,
            feedback=feedback_request.feedback,
            score=feedback_request.score
        )
        return {"status":"success", "message":"Feedback stored successfully"}
    except ValueError as e:
        return {"status":"error","message":str(e)}
    except Exception as e:
        return {"status":"error","message":"Internal server error"}
    
    
#backend is alive and responding
#http://localhost:8000/api/get_sessions/(user_id_here)
@app.get("/get_sessions/{user_id}")
def get_sessions(user_id: str):
    try:
        history = memory_manager.get_history(user_id)
        return {"sessions": [{"id": 1, "title": "Chat History", "messages": history}]}
    except Exception as e:
        return {"error": str(e)}

#mcp backend server is live 
#FASTAPI server is running inside docker successfully 
#test--http://127.0.0.1:8000
@app.get("/")
def read_root():
    return {"message": "MCP SQL Agent is running."}

import socket
#backend health, docker running backend smoothly
#ngnix is running---http://localhost/api/health
@app.get("/health")
def health_check():
    return {"status": "ok", "instance": socket.gethostname()}
    
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)