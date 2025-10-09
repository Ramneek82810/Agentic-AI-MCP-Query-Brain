from typing import Any, Dict,List
import psycopg2
from psycopg2 import sql
from sdk.tool import BaseTool
import os
import re
import json
import time
import asyncio
from openai import AsyncOpenAI, OpenAI
from memory.mcp_memory import MCPMemoryManager
from fastapi import FastAPI, Request
from datetime import date, datetime
from dotenv import load_dotenv 
from sql_tool.db_setup import get_table_columns

import logging
logger = logging.getLogger(__name__)

load_dotenv()

def connect_postgres():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT")
    )
   
    
#execute sql queries
class SQLTool(BaseTool):
    name="SQLTool"
    description="Executes raw SQl queries on PostgreSQL."
    
    async def run(self,input:Dict[str,Any])->Any:
        query=input.get("query")
        user_id=input.get("user_id","default")
        if not query:
            return {"error":"Query not provided"}
        
        def serialize_value(value):
            if isinstance(value, (date, datetime)):
                return value.isoformat()
            return value
        
        try:
            conn=connect_postgres()
            cur=conn.cursor()
            
            logger.info(f"[SQLTool] Executing query: {query}")
            
            if query.strip().lower().startswith("insert") and "returning" not in query.lower():
                query = query.rstrip(";") + " RETURNING user_id;"
                
            cur.execute(query)
            
            if query.strip().lower().startswith("select"):
                result=cur.fetchall()
                columns=[desc[0] for desc in cur.description]
                #formatted=[dict(zip(columns,row)) for row in result]
                formatted = [{col: serialize_value(val) for col, val in zip(columns, row)} for row in result]
                
                
                unique = []
                seen = set()
                for row in formatted:
                    key = tuple(row.items())
                    if key not in seen:
                        seen.add(key)
                        unique.append(row)
                response = {"result": unique} if unique else {"info": "No data found."}
                
                memory=MCPMemoryManager()
                memory.add_message(user_id, role="assistant",content=json.dumps(response))
                if unique and "user_name" in unique[0]:
                    # memory=MCPMemoryManager()
                    last_entity={"type":"user_name","value":unique[0]["user_name"]}
                    memory.add_message(f"{user_id}_last_user",role="system",content=json.dumps(last_entity))
                
            elif query.strip().lower().startswith("insert"):
                inserted=cur.fetchall() if cur.description else []
                conn.commit()
                if inserted:
                    response = {"success": f"{len(inserted)} row(s) inserted successfully.", "ids": inserted}
                else:
                    response = {"error": "Insert executed but no rows returned. Check query."}
            
                MCPMemoryManager().add_message(user_id,role="assistant",content=json.dumps(response))
                
            elif query.strip().lower().startswith("update"):
                conn.commit()
                rows_affected=cur.rowcount
                if rows_affected<=0:
                    response={"error":"No matching record found to update."}
                else:
                    response={"success":f"{rows_affected} row(s) updated successfully."}
                    
                MCPMemoryManager().add_message(user_id,role="assistant",content=json.dumps(response))

            elif query.strip().lower().startswith("delete"):
                conn.commit()
                rows_affected=cur.rowcount
                if rows_affected<=0:
                    response={"error":"No matching record found to delete."}
                else:
                    response={"success":f"{rows_affected} row(s) deleted successfully."}
                    
                MCPMemoryManager().add_message(user_id,role="assistant",content=json.dumps(response))

            else:
                conn.commit()
                response={"success":"Query executed sucessfully."}
                MCPMemoryManager().add_message(user_id,role="assistant",content=json.dumps(response))

            cur.close()
            conn.close()
            return response
        
        except Exception as e:
            return {"error":str(e)}

#table schema information        
class TableSchemaTool(BaseTool):
    name="DBSchemaTool"
    description="Provides schema of all tables in the PostgreSQl DB."
    
    async def run(self,input:Dict[str,Any])->Any:
        try:
            conn=connect_postgres()
            cur=conn.cursor()
            cur.execute("""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema= 'public'
                ORDER BY table_name,ordinal_position       
            """)
            rows=cur.fetchall()
            schema={}
            for table,column,dtype in rows:
                schema.setdefault(table,[]).append({"column":column,"type":dtype})
            cur.close()
            conn.close()
            return schema
        
        except Exception as e:
            return {"error":str(e)}
        
#sql validation tool
class SQLValidationTool(BaseTool):
    name="SQLValidationTool"
    description="Checks for dangerous or malformed SQL queries."
    
    async def run(self,input:Dict[str,Any])->Any:
        query=input.get("query","").lower()
        unsafe_keywords=["drop","truncate","alter"]
        for word in unsafe_keywords:
            if word in query:
                return{"error":f"Unsafe SQL detected:{word}"}
        
        if query.startswith("update") and "where" not in query:
            return {"error":"Unsafe UPDATE: missing WHERE clause."}
        
        if query.startswith("delete") and "where" not in query:
            return{"error":"Unsafe DELETE: missing WHERE clause."}
        
        return {"status":"Query safe"}
    
#normal language to sql via GPT
class OpenAITool(BaseTool):
    name="OpenAITool"
    description="Converts natural language to SQL using gpt-3.5-turbo."
    
    async def _run(self, input: Dict[str, Any]) -> Any:
        instruction = input.get("instruction")
        user_id=input.get("user_id","default")
        
        if not instruction:
            return {"error": "No instruction provided."}
        
        memory=MCPMemoryManager()
        # last_message_history = memory.get_history(user_id) or []
        last_entity_history = memory.get_history(f"{user_id}_last_entity") or []
        
        last_entity = None
        if last_entity_history:
            try:
                last_entity = json.loads(last_entity_history[-1]["content"])
            except Exception:
                last_entity = {"value": last_entity_history[-1]["content"]}
        
        user_match = re.search(
            r"(user_id|user_name|email|vendor_id|vendor_name|last_updated)\s*[:=]?\s*([\w@.\-: ]+)?",
            instruction,
            re.IGNORECASE
        )
        if user_match and user_match.group(2):
            last_entity = {"type": user_match.group(1).lower(), "value": user_match.group(2).strip()}
            memory.add_message(f"{user_id}_last_entity", role="system", content=json.dumps(last_entity))
            
        else:
            match_id = re.search(r"\b\d{3,}\b", instruction) 
            if match_id:
                last_entity = {"type": "user_id", "value": match_id.group()}
                memory.add_message(
                    f"{user_id}_last_entity",
                    role="system",
                    content=json.dumps(last_entity)
                )

            elif re.search(r"[\w\.-]+@[\w\.-]+\.\w+", instruction): 
                email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", instruction)
                if email_match:
                    last_entity = {"type": "email", "value": email_match.group()}
                    memory.add_message(
                        f"{user_id}_last_entity",
                        role="system",
                        content=json.dumps(last_entity)
                    )

            else:
                match_name = re.search(r"(?:for|about)\s+([A-Za-z][A-Za-z0-9_-]*)", instruction, re.IGNORECASE)
                if match_name:
                    entity_value = match_name.group(1)
                    if entity_value.lower() not in ["of"]:
                        last_entity = {"type": "user_name", "value": entity_value}
                        memory.add_message(f"{user_id}_last_entity", role="system", content=json.dumps(last_entity))
                else:
                    last_entity_history = memory.get_history(f"{user_id}_last_entity") or []
                    last_entity=None
                    if last_entity_history:
                        try:
                            last_entity = json.loads(last_entity_history[-1]["content"])
                        except:
                            last_entity = None
            
        if last_entity and last_entity.get("value"):
            pronouns = ["it", "its", "them", "they", "he", "she", "his", "her", "their"]
            pattern = r"\b(" + "|".join(pronouns) + r")\b"
            instruction = re.sub(pattern, str(last_entity["value"]), instruction, flags=re.IGNORECASE)
        
        if last_entity and "value" in last_entity and last_entity["value"]:
            if last_entity["value"].lower() not in instruction.lower():
                instruction += f" for {last_entity['value']}"
                
        memory.add_message(user_id, role="user", content=instruction)
        
#         last_user = None
#         if last_user_history and isinstance(last_user_history, list):
#             # Get the last message stored
#             last_user_msg = last_user_history[-1]
#             if isinstance(last_user_msg, dict) and "content" in last_user_msg:
#                 last_user = last_user_msg["content"]

# # Replace pronouns with actual last_user if it exists
#         if last_user:
#             pronouns = ["it", "its", "them", "they"]
#             pattern = r"\b(" + "|".join(pronouns) + r")\b"
#             instruction = re.sub(pattern, str(last_user), instruction, flags=re.IGNORECASE)
        
        
#         match = re.search(r"(?:add|insert|new user)\s+([a-zA-Z0-9_]+)", instruction.lower())
#         if match:
#             memory.add_message(f"{user_id}_last_user",role="user",content= match.group(1))

        logger.info(f"[OpenAITool] Final instruction sent to OpenAI: {instruction}")
        logger.info(f"[OpenAITool] last_user: {last_entity}")
        
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        try:
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    
                    {
                        "role": "system",
                        "content": (
                            "You are an expert SQL generator for PostgreSQL.\n"
                            "Use only this table:\n\n"
                            "Table: user_vendor_info\n"
                            "Columns:\n"
                            "- user_id (int)\n"
                            "- user_name (text)\n"
                            "- email (text)\n"
                            "- vendor_id (text)\n"
                            "- vendor_name (text)\n"
                            "- vendor_status (text)\n"
                            "- last_updated (date)\n\n"
                            "- Important Rules:\n"
                            "1. Only use the columns explicity mentioned in the user's request.\n"
                            "2. If a column value is not provided by the user, set it to NULL (or leave unchanged for UPDATE).\n"
                            "3. Never invent or predict values such as email, vendor_id or user_id.\n"
                            "4. For INSERT: only include columns the user actually specified.\n"
                            "5. For UPDATE: only update columns the user explicity mentioned.\n"
                            "6. If the user refers to pronouns ('it', 'its', 'them', 'they'), assume they mean the last mentioned user: <last_user if exists>.\n"
                            "Do not ask for more context. Use last user from memory if needed:"
                            f"{last_entity if last_entity else 'unknown'}.\n"
                            "7. Always include a WHERE clause when updating/deleting,"
                            "using ILIKE for case-insensitive matching.\n"
                            "8. Always generate syntactically correct PostgreSQL.\n"
                            "Always use case-insensitive matching for text comparisons using ILIKE.\n"
                            "Generate valid PostgreSQL queries using this schema only.\n"
                            "9. You can generate SELECT, INSERT, UPDATE, or DELETE statements as needed.\n"
                            "Do not ask for more context. Use the last user from memory if needed."
                            "10. When the user uses pronouns like it, his, her, their, its, resolve them using the most recent result from memory (not just the text of the last query). Always prefer specific attributes like email, user_id, or vendor_id for SQL filtering"
                        ),
                    },
                    {"role": "user", "content": instruction},
                ],
            )
            sql_query = response.choices[0].message.content.strip()
            return {"query": sql_query}
        
        except Exception as e:
            return {"error": str(e)}

    async def run(self, input: Dict[str, Any]) -> Any:
        return await self._run(input)
    
#SQL to natural language for user
class NaturalLanguageResponseTool(BaseTool):
    name="NaturalLanguageResponseTool"
    description="Converts SQl results into natural language summary."
    
    async def run(self,input:Dict[str,Any])->Any:
        result=input.get("result")
        if isinstance(result,dict) and "result" in result:
            result=result["result"]
        if not result:
            return "No result provided."
        
        if isinstance(result,list):
            response_text="Here are the details:\n"
            for row in result:
                details=[]
                for col,val in row.items():
                    if val is not None:
                        details.append(f"- {col.replace('_',' ').title()}: {val}")
                if not details:
                    details.append(json.dumps(row))
                response_text+="\n".join(details)+"\n\n"
            return response_text.strip()
        
        elif isinstance(result,dict):
            if "error" in result:
                return f"{result['error']}"
            elif "success" in result:
                return f"{result['success']}"
            elif "info" in result:
                return result["info"]
            else:
                return json.dumps(result) 
        
        elif isinstance(result,str):
            return result
        
        else:
            return json.dumps(result)
        
        # else:
        #     return result if isinstance(result,str) else json.dumps(result)
    
#redis memory tool
class MemoryQueryTool(BaseTool):
    name="MemoryQueryTool"
    description="Fetches memory history from Redis for a user."
    
    async def run(self,input:Dict[str,Any])->Any:
        user_id=input.get("user_id")
        if not user_id:
            return {"error":"user_id is required"}
        memory=MCPMemoryManager()
        history=memory.get_history(user_id)
        return history if history else{"info":"No memory found"}        
    
#table content summary
class TableSummaryTool(BaseTool):
    name="TableSummaryTool"
    description="Summarizes the data in a specified table."
    
    async def run(self,input:Dict[str,Any])->Any:
        table=input.get("table")
        if not table:
            return {"error":"Table name not provided"}
        
        try:
            conn=connect_postgres()
            cur=conn.cursor()
            cur.execute(f"SELECT * FROM {table} LIMIT 5")
            rows=cur.fetchall()
            columns=[desc[0] for desc in cur.description]
            summary=[dict(zip(columns,row)) for row in rows]
            cur.close()
            conn.close()
            return summary
        
        except Exception as e:
            return {"error":str(e)}
        
#fallback tool for errors
class FallbackTool(BaseTool):
    name="FallbackTool"
    description="Handles errors and fallback cases gracefully."
    
    async def run(self,input:Dict[str,Any])->Any:
        return {"error":"Sorry the system couldn't process your request."}
    
#rate limiter tool
class RateLimiterTool(BaseTool):
    name="RateLimiterTool"
    description="Limits number of queries per user per minute."
    
    rate_limit=5
    store={}
    
    async def run(self,input:Dict[str,Any])->Any:
        user_id=input.get("user_id")
        now=time.time()
        self.store.setdefault(user_id,[]).append(now)
        
        recent=[t for t in self.store[user_id]if now - t<60]
        self.store[user_id]=recent
        
        if len(recent)>self.rate_limit:
            return {"allowed":False,"error":"Rate limit exceeded"}
        return {"allowed":True}
    
#explain SQL query in natural language
class ExplainSQLTool(BaseTool):
    name="ExplainSQLTool"
    description="Explain a SQL query in plain English."
    
    async def run(self,input:Dict[str,Any])->Any:
        query=input.get("query")
        if not query:
            return {"error":"Query missing"}
        client=AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        try:
            response=await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role":"system","content":"Explain what this SQL query does in simple English."},
                    {"role":"user","content":query}
                ]
            )
            return {"explanation":response.choices[0].message.content.strip()}
        except Exception as e:
            return {"error":str(e)}
    
#log feedback to file
class FeedbackLoggingTool(BaseTool):
    name="FeedbackLoggingTool"
    description="Logs user feedback to a file for monitoring."
    
    async def run(self,input:Dict[str,Any])->Any:
        feedback=input.get("feedback")
        with open("feedback_log.json","a") as f:
            json.dump({"feedback":feedback},f)
            f.write("\n")
        return {"status":"Feedback saved"}

#cache frequently used SQL
class QueryCacheTool(BaseTool):
    name="QueryCacheTool"
    description="Caches common query results to speed up response."
    
    cache={}

    async def run(self,input:Dict[str,Any])->Any:
        query=input.get("query")
        if query in self.cache:
            return {"cached":True, "result":self.cache[query]}
        return {"cached":False}
 
 
   
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="SQL Tool Microservice")

tools = {
    "sql_tool": SQLTool(),
    "schema_tool": TableSchemaTool(),
    "validation_tool": SQLValidationTool(),
    "openai_tool": OpenAITool(),
    "nl_response_tool": NaturalLanguageResponseTool(),
    "rate_limiter": RateLimiterTool(),
    "fallback_tool": FallbackTool(),
    "memory_tool": MemoryQueryTool(),
    "table_summary_tool": TableSummaryTool(),
    "explain_tool": ExplainSQLTool(),
    "feedback_tool": FeedbackLoggingTool(),
    "query_cache_tool": QueryCacheTool(),
}

@app.post("/{tool_name}")
async def run_tool(tool_name: str, request: Request):
    if tool_name not in tools:
        return {"error": "Tool not found"}
    data = await request.json()
    tool = tools[tool_name]
    if asyncio.iscoroutinefunction(tool.run):
        return await tool.run(data)
    else:
        return tool.run(data)

@app.get("/health")
def health():
    return {"status": "running"}

@app.get("/")
def root():
    return {"message": "Server is up"}

if __name__ == "__main__":
    uvicorn.run("sql_tool.sql_tool:app", host="0.0.0.0", port=8002,reload=True)