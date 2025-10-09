from typing import Any, Dict, List, Optional
from sdk.tool import BaseTool
import inspect
import logging
from mcp_tools.vartopia_tools import VartopiaTool
from sql_tool.sql_tool import (
    SQLTool,
    TableSchemaTool,
    SQLValidationTool,
    OpenAITool,
    NaturalLanguageResponseTool,
    MemoryQueryTool,
    TableSummaryTool,
    FallbackTool,
    RateLimiterTool,
    ExplainSQLTool,
    FeedbackLoggingTool,
    QueryCacheTool
)

# class VartopiaWrapperTool(BaseTool):
#     @property
#     def name(self) -> str:
#         return "VartopiaTool"

#     @property
#     def description(self) -> str:
#         return (
#             "Handles all Vartopia API actions: list_vendors, list_programs, "
#             "get_program_schema, submit_deal"
#         )

# async def run(self, query: str, user_id: str, **kwargs):
#         vartopia = VartopiaTool()
#         return await vartopia.run(query=query, user_id=user_id, **kwargs)

def register_vartopia_tools() -> List[BaseTool]:
    """Returns a list of BaseTool instances for Vartopia APIs."""
    return [VartopiaTool()]


def register_sql_tools() -> List[BaseTool]:
    """
    Returns a list of BaseTool instances for all SQL-related operations.
    """
    return [
        SQLTool(),
        TableSchemaTool(),
        SQLValidationTool(),
        OpenAITool(),
        NaturalLanguageResponseTool(),
        MemoryQueryTool(),
        TableSummaryTool(),
        FallbackTool(),
        RateLimiterTool(),
        ExplainSQLTool(),
        FeedbackLoggingTool(),
        QueryCacheTool()
    ]


def register_all_tools() -> List[BaseTool]:
    """
    Returns a combined list of all tools (SQL + Vartopia) as BaseTool instances.
    """
    tools:List[BaseTool]=[]
    tools.extend(register_sql_tools())
    tools.extend(register_vartopia_tools())
    return tools

class ToolRouter:
    """
        Executes a specific tool by name with given keyword arguments.
        Expected format:
        {
            "tool_name": "VartopiaTool",
            "kwargs": { ... }
        }
        """
    def __init__(self, tools: List[BaseTool]):
        self.tools: Dict[str, BaseTool] = {tool.name: tool for tool in tools}

    async def try_handle(self, input_data: Dict[str, Any]) -> Optional[Any]:
        tool_name = input_data.get("tool_name")
        if not tool_name:
            logging.warning("[ToolRouter] No tool_name provided in input_data")
            return None

        tool = self.tools.get(tool_name)
        if not tool:
            logging.warning(f"[ToolRouter] Tool {tool_name} not found")
            return None

        kwargs = input_data.get("kwargs", {})
        run_func=getattr(tool,"run",None)
        
        if not run_func:
            logging.warning(f"[ToolRouter] Tool {tool_name} has no run() method")
            return None 
        
        try:            
            if inspect.iscoroutinefunction(run_func):
                return await run_func(**kwargs)
            else:
                return run_func (**kwargs)
        
        except Exception as e:
            logging.exception(f"[ToolRouter] Error running tool {tool_name}: {e}")
            return None